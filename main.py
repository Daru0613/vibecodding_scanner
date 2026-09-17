from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import yaml

from collector.commoncrawl_collector import CommonCrawlCollector
from collector.ct_collector import CTCollector
from collector.github_collector import GitHubCollector
from collector.public_link_collector import PublicLinkCollector
from collector.search_collector import SearchCollector
from core.cache import ResponseCache
from core.http_client import SafeHttpClient
from core.pipeline import Pipeline
from filter.url_filter import deduplicate, exclude_domain_suffixes
from storage.csv_writer import CsvWriter
from storage.jsonl_writer import JsonlWriter


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as handle: return yaml.safe_load(handle) or {}


async def collect_urls(settings: dict, limit: int) -> list[str]:
    cfg = settings.get("collectors", {}); collectors = []
    if cfg.get("public_files"): collectors.append(PublicLinkCollector(cfg["public_files"]))
    if cfg.get("search", True): collectors.append(SearchCollector(cfg.get("search_queries", []), cfg.get("search_provider", "brave")))
    if cfg.get("github", True): collectors.append(GitHubCollector(cfg.get("github_queries", [])))
    if cfg.get("ct", False): collectors.append(CTCollector(cfg.get("ct_queries")))
    if cfg.get("commoncrawl", False): collectors.append(CommonCrawlCollector(cfg.get("commoncrawl_index", "latest"), cfg.get("commoncrawl_queries")))
    results = await asyncio.gather(*(c.collect(limit) for c in collectors)) if collectors else []
    urls = deduplicate([url for group in results for url in group])
    urls = exclude_domain_suffixes(urls, cfg.get("excluded_domain_suffixes", []))
    return urls[:limit]


def progress(i, total, row):
    print(f"[{i}/{total}] FETCH {row.final_url} {row.http_status}")
    print(f"[{i}/{total}] KR score={row.korea_score} {row.korea_class}")
    print(f"[{i}/{total}] {row.builder} score={row.builder_score} {row.builder_class}")


async def run(args) -> None:
    started = time.monotonic(); settings = load_yaml(args.settings)
    settings["http"]["global_concurrency"] = args.max_concurrency
    urls = await collect_urls(settings, args.limit)
    if not args.resume:
        for output_path in (args.output, args.jsonl):
            path = Path(output_path)
            if path.is_file(): path.unlink()
    cache = ResponseCache(args.cache); client = SafeHttpClient(settings, cache); pipeline = Pipeline(settings, load_yaml(args.signatures), client)
    csv_writer = CsvWriter(args.output); json_writer = JsonlWriter(args.jsonl)
    completed = set()
    if args.resume and Path(args.jsonl).exists():
        for line in Path(args.jsonl).read_text(encoding="utf-8").splitlines():
            try: completed.add(json.loads(line)["original_url"])
            except Exception: pass
    pending = [u for u in urls if u not in completed]
    records = []
    def save_progress(index, total, row):
        progress(index, total, row)
        if not (args.country == "korea" and row.korea_class == "NON_KR_OR_UNKNOWN") and not (args.builder and row.builder != args.builder):
            csv_writer.write(row); json_writer.write(row)
    try:
        records = await pipeline.scan_many(pending, save_progress)
        """Results are persisted by the completion callback for interruption safety."""
    finally:
        csv_writer.close(); json_writer.close(); await client.close(); cache.close()
    runtime = time.monotonic()-started
    print_summary(len(urls), records, client, runtime)
    return {"candidates": len(urls), "records": records, "requests": client.requests, "cache_hits": client.cache_hits, "statuses": client.status_counts, "runtime": runtime}


def print_summary(collected, rows, client, runtime):
    count = lambda attr, value: sum(getattr(x, attr) == value for x in rows)
    print("\n================================\nScan Summary\n================================")
    print(f"Collected URLs     : {collected}\nUnique URLs        : {collected}\nAlive              : {sum(200 <= x.http_status < 400 for x in rows)}")
    print(f"KR Confirmed       : {count('korea_class','KR_CONFIRMED')}\nKR Possible        : {count('korea_class','KR_POSSIBLE')}")
    print(f"Vibe Confirmed     : {count('builder_class','CONFIRMED')}\nVibe Probable      : {count('builder_class','PROBABLE')}")
    print(f"HTTP Requests      : {client.requests}\nCache Hits         : {client.cache_hits}\nRuntime            : {runtime:.1f}s\n================================")


def parser():
    p = argparse.ArgumentParser(); p.add_argument("--limit", type=int, default=1000); p.add_argument("--country", choices=["korea"]); p.add_argument("--builder")
    p.add_argument("--output", default="results.csv"); p.add_argument("--jsonl", default="results.jsonl"); p.add_argument("--resume", action="store_true")
    p.add_argument("--max-concurrency", type=int, default=10); p.add_argument("--cache", default="cache.sqlite")
    p.add_argument("--settings", default="config/settings.yaml"); p.add_argument("--signatures", default="config/signatures.yaml"); return p


if __name__ == "__main__":
    try: asyncio.run(run(parser().parse_args()))
    except KeyboardInterrupt: print("\n[SKIP] interrupted; flushed records can be resumed with --resume")
