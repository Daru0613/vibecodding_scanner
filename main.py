from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

import yaml

from collector.commoncrawl_collector import CommonCrawlCollector
from collector.ct_collector import CTCollector
from collector.github_collector import GitHubCollector
from collector.public_link_collector import PublicLinkCollector
from collector.search_collector import SearchCollector
from core.http_client import SafeHttpClient
from core.models import Candidate
from core.pipeline import Pipeline
from core.progress import ProgressReporter
from core.state import CollectorState
from filter.url_filter import classify_url, exclude_domain_suffixes, is_public_http_url, normalize_url, site_id
from filter.result_filter import is_high_confidence_vibe
from storage.csv_writer import CsvWriter
from storage.jsonl_writer import JsonlWriter


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def build_collectors(settings: dict, selected: str | None = None):
    cfg = settings.get("collectors", {})
    collectors: list[tuple[str, object]] = []
    if cfg.get("public_files") and selected in (None, "seed"):
        collectors.append(("seed", PublicLinkCollector(cfg["public_files"])))
    if (cfg.get("search", True) or selected == "search") and selected in (None, "search"):
        collectors.append(("search", SearchCollector(cfg.get("search_queries", []), cfg.get("search_provider", "brave"))))
    if (cfg.get("github", True) or selected == "github") and selected in (None, "github"):
        collectors.append(("github", GitHubCollector(cfg.get("github_queries", []))))
    if (cfg.get("ct", False) or selected == "ct") and selected in (None, "ct"):
        collectors.append(("ct", CTCollector(cfg.get("ct_queries"))))
    if (cfg.get("commoncrawl", False) or selected == "commoncrawl") and selected in (None, "commoncrawl"):
        collectors.append(("commoncrawl", CommonCrawlCollector(cfg.get("commoncrawl_index", "latest"), cfg.get("commoncrawl_queries"))))
    return collectors


async def collect_candidates(settings: dict, limit: int, selected: str | None = None,
                             reporter: ProgressReporter | None = None) -> tuple[list[Candidate], int]:
    collectors = build_collectors(settings, selected)
    fetch_limit = min(max(limit * 3, limit), 3000)
    async def run_collector(name, collector):
        return name, await collector.collect(fetch_limit)
    groups = []
    raw_count = 0
    tasks = [run_collector(name, collector) for name, collector in collectors]
    for completed, task in enumerate(asyncio.as_completed(tasks), 1):
        _, group = await task
        groups.append(group)
        raw_count += len(group)
        if reporter:
            reporter.collection(completed, len(tasks), raw_count, limit)
    seen: set[str] = set()
    result: list[Candidate] = []
    excluded = 0
    excluded_suffixes = settings.get("collectors", {}).get("excluded_domain_suffixes", [])
    for group in groups:
        for item in group:
            normalized = normalize_url(item.url)
            url_type = classify_url(normalized)
            if (not is_public_http_url(normalized) or
                    not exclude_domain_suffixes([normalized], excluded_suffixes) or
                    url_type in {"REPOSITORY", "SOURCE_FILE", "DOCUMENT", "NON_HTML", "UNKNOWN"}):
                excluded += 1
                continue
            key = site_id(normalized)
            if normalized and key not in seen:
                seen.add(key)
                result.append(item)
                if len(result) >= limit:
                    return result, excluded
    return result, excluded


async def run(args) -> dict:
    started = time.monotonic()
    settings = load_yaml(args.settings)
    settings.setdefault("http", {})["global_concurrency"] = args.concurrency
    state = CollectorState(args.database)
    if not args.resume:
        state.reset()
        for output_name in (args.output, args.jsonl):
            path = Path(output_name)
            if path.is_file():
                path.unlink()

    reporter = ProgressReporter()
    candidates, pre_excluded = await collect_candidates(settings, args.limit, args.source, reporter)
    added, state_excluded = state.add_candidates(candidates)
    excluded = pre_excluded + state_excluded
    print(f"[READY] {len(candidates):,} unique candidates | {added:,} new | {excluded:,} non-site URLs excluded")

    client = SafeHttpClient(settings)
    pipeline = Pipeline(settings, load_yaml(args.signatures), client)
    csv_writer = CsvWriter(args.output)
    json_writer = JsonlWriter(args.jsonl)
    records = []
    planned = min(args.limit, state.counts()["pending"])
    reporter.start_scan(planned)

    def save_progress(index, total, row):
        duplicate_final = state.has_scanned_final(row.final_url or row.normalized_url)
        written = not duplicate_final and is_high_confidence_vibe(row)
        if args.country == "korea" and row.korea_class == "UNKNOWN": written = False
        if args.builder == "lovable" and row.lovable_class == "NO_LOVABLE_EVIDENCE": written = False
        if args.builder == "claude" and row.claude_class == "NO_CLAUDE_EVIDENCE": written = False
        if written:
            csv_writer.write(row)
            json_writer.write(row)
        item = Candidate(row.original_url, row.source, row.source_query, row.source_seen_at, row.collected_at)
        state.complete(item, row, written)
        reporter.scan(row.http_status, written, row.error)

    try:
        remaining = args.limit
        while remaining > 0:
            batch = state.pending(min(100, remaining))
            if not batch:
                break
            rows = await pipeline.scan_many(batch, save_progress)
            records.extend(rows)
            remaining -= len(batch)
    finally:
        csv_writer.close()
        json_writer.close()
        await client.close()
        counts = state.counts()
        state.close()

    runtime = time.monotonic() - started
    summary = {"collected": len(candidates), "unique": added, "excluded": excluded,
               "records": records, "requests": client.requests, "statuses": client.status_counts,
               "runtime": runtime, "state": counts}
    print_summary(summary)
    return summary


def print_summary(summary: dict) -> None:
    rows, statuses = summary["records"], summary["statuses"]
    count = lambda attr, value: sum(getattr(row, attr) == value for row in rows)
    response_times = [row.response_time_ms for row in rows if row.response_time_ms > 0]
    average = sum(response_times) / len(response_times) if response_times else 0
    print("\n====================================\nCollection Summary\n====================================")
    print(f"Collected              : {summary['collected']}")
    print(f"Unique                 : {summary['unique']}")
    print(f"Non-site URLs Excluded : {summary['excluded']}")
    print(f"Fetched                : {sum(200 <= row.http_status < 400 for row in rows)}")
    print(f"404                    : {statuses.get('404', 0)}")
    print(f"403                    : {statuses.get('403', 0)}")
    print(f"429                    : {statuses.get('429', 0)}")
    print(f"Timeout                : {sum('Timeout' in row.error for row in rows)}")
    print(f"KR                     : {count('korea_class', 'KR')}")
    print(f"KR Possible            : {count('korea_class', 'KR_POSSIBLE')}")
    print(f"Lovable Confirmed      : {count('lovable_class', 'LOVABLE_CONFIRMED')}")
    print(f"Lovable Probable       : {count('lovable_class', 'LOVABLE_PROBABLE')}")
    print(f"Claude Possible        : {count('claude_class', 'CLAUDE_POSSIBLE')}")
    print(f"Unknown                : {count('vibe_result', 'UNKNOWN')}")
    print(f"Needs Deep Scan        : {sum(row.needs_deep_scan for row in rows)}")
    print(f"Total HTTP Requests    : {summary['requests']}")
    print(f"Average Response Time  : {average:.0f}ms")
    print(f"Runtime                : {summary['runtime']:.1f}s")
    print("====================================")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser()
    command.add_argument("--limit", type=int, default=1000)
    command.add_argument("--source", choices=["commoncrawl", "ct", "github", "search", "seed"])
    command.add_argument("--country", choices=["korea"])
    command.add_argument("--builder", choices=["lovable", "claude"])
    command.add_argument("--output", default="results/csv/results.csv")
    command.add_argument("--jsonl", default="results/jsonl/results.jsonl")
    command.add_argument("--resume", action="store_true")
    command.add_argument("--concurrency", "--max-concurrency", dest="concurrency", type=int, default=5)
    command.add_argument("--database", "--cache", dest="database", default="collector.db")
    command.add_argument("--settings", default="config/settings.yaml")
    command.add_argument("--signatures", default="config/signatures.yaml")
    return command


if __name__ == "__main__":
    try:
        asyncio.run(run(parser().parse_args()))
    except KeyboardInterrupt:
        print("\n[STOP] Completed records were flushed. Continue with --resume.")
