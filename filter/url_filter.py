from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url: return ""
    if "://" not in url: url = "https://" + url
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname: return ""
    host = p.hostname.lower()
    if host.startswith("www."): host = host[4:]
    port = f":{p.port}" if p.port and not ((p.scheme == "http" and p.port == 80) or (p.scheme == "https" and p.port == 443)) else ""
    path = p.path.rstrip("/") or "/"
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING])
    return urlunsplit((p.scheme.lower(), host + port, path, query, ""))


def deduplicate(urls: list[str]) -> list[str]:
    seen: set[str] = set(); output: list[str] = []
    for url in urls:
        normalized = normalize_url(url)
        key = normalized.replace("http://", "https://", 1)
        if normalized and key not in seen: seen.add(key); output.append(normalized)
    return output


def exclude_domain_suffixes(urls: list[str], suffixes: list[str]) -> list[str]:
    """Exclude a domain and all its subdomains using hostname boundaries."""
    blocked = tuple(x.lower().strip().lstrip(".") for x in suffixes if x.strip())
    output: list[str] = []
    for url in urls:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
        if any(host == suffix or host.endswith("." + suffix) for suffix in blocked):
            continue
        output.append(url)
    return output


def site_id(url: str) -> str:
    host = urlsplit(url).hostname or url
    return hashlib.sha256(host.lower().encode()).hexdigest()[:16]
