from __future__ import annotations

import hashlib
import ipaddress
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
GITHUB_HOSTS = {"github.com", "gist.github.com", "api.github.com", "raw.githubusercontent.com", "opengraph.githubassets.com"}
PLATFORM_ROOTS = {"lovable.app", "vercel.app", "netlify.app", "pages.dev", "replit.app", "base44.app", "railway.app"}


def classify_url(url: str) -> str:
    parsed = urlsplit(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    if host in GITHUB_HOSTS or host.endswith(".githubusercontent.com"):
        return "REPOSITORY" if host == "github.com" and len([x for x in path.split("/") if x]) <= 2 else "SOURCE_FILE"
    if host in PLATFORM_ROOTS:
        return "DOCUMENT"
    if path.endswith((".pdf", ".doc", ".docx", ".txt", ".md")):
        return "DOCUMENT"
    if path.endswith((".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".exe")):
        return "NON_HTML"
    return "DEPLOYMENT_SITE" if host else "UNKNOWN"


def is_public_http_url(url: str) -> bool:
    parsed = urlsplit(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in ("http", "https") or not host:
        return False
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or
                address.is_reserved or address.is_multicast or address.is_unspecified)


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
