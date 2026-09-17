from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.models import PageData


def parse_html(html: str, base_url: str) -> PageData:
    soup = BeautifulSoup(html or "", "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
    gen = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "generator"})
    published = ""
    for attrs in (
        {"property": "article:published_time"}, {"name": "date"},
        {"name": "datePublished"}, {"itemprop": "datePublished"},
    ):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            published = tag.get("content", "").strip(); break
    if not published:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag: published = time_tag.get("datetime", "").strip()
    lang = (soup.html.get("lang", "") if soup.html else "").lower()
    scripts = [urljoin(base_url, x.get("src")) for x in soup.find_all("script", src=True)]
    links = [urljoin(base_url, x.get("href")) for x in soup.find_all("link", href=True)]
    inline = "\n".join(x.get_text(" ", strip=True) for x in soup.find_all("script") if not x.get("src"))
    for node in soup(["script", "style", "noscript", "template"]):
        node.decompose()
    visible = soup.get_text(" ", strip=True)
    host = (urlparse(base_url).hostname or "").lower()
    external = sorted({urlparse(x).hostname.lower() for x in scripts + links if urlparse(x).hostname and urlparse(x).hostname.lower() != host})
    return PageData(title, desc.get("content", "") if desc else "", gen.get("content", "") if gen else "", lang, scripts, links, external, visible, inline, published)
