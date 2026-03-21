from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_schema_types(soup: BeautifulSoup) -> list[str]:
    schema_types: list[str] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                val = parsed.get("@type")
                if isinstance(val, str):
                    schema_types.append(val)
                elif isinstance(val, list):
                    schema_types.extend([v for v in val if isinstance(v, str)])
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and isinstance(item.get("@type"), str):
                        schema_types.append(item["@type"])
        except Exception:
            continue
    return sorted(set(schema_types))


def analyze_page(page: dict[str, Any], root_url: str) -> dict[str, Any]:
    html = page.get("html_content") or ""
    soup = BeautifulSoup(html, "lxml")

    title = _clean_text(soup.title.get_text()) if soup.title else ""
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    meta_description = _clean_text(meta_desc_tag.get("content", "")) if meta_desc_tag else ""

    canonical_tag = soup.find("link", attrs={"rel": re.compile(r"canonical", re.I)})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    def heads(name: str) -> list[str]:
        return [_clean_text(h.get_text()) for h in soup.find_all(name) if _clean_text(h.get_text())]

    h1 = heads("h1")
    h2 = heads("h2")
    h3 = heads("h3")
    h4_h6 = heads("h4") + heads("h5") + heads("h6")

    text_content = _clean_text(soup.get_text(" ", strip=True))
    word_count = len(text_content.split()) if text_content else 0

    images = []
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "").strip()
        if src:
            src = urljoin(page.get("final_url") or page.get("url"), src)
        images.append({"src": src, "alt": alt, "has_alt": bool(alt)})

    url = page.get("final_url") or page.get("url") or root_url
    root_netloc = urlparse(root_url).netloc
    internal_links: list[str] = []
    external_links: list[str] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith("#"):
            continue
        abs_url = urljoin(url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc == root_netloc:
            internal_links.append(abs_url)
        else:
            external_links.append(abs_url)

    og_tags = {}
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or "").strip()
        if prop.lower().startswith("og:"):
            og_tags[prop] = (meta.get("content") or "").strip()

    return {
        "url": url,
        "title": title,
        "meta_description": meta_description,
        "canonical": canonical,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4_h6": h4_h6,
        "word_count": word_count,
        "images": images,
        "internal_links": sorted(set(internal_links)),
        "external_links": sorted(set(external_links)),
        "schema_markup": _extract_schema_types(soup),
        "og_tags": og_tags,
        "page_size_kb": round(len(html.encode("utf-8")) / 1024, 2),
        "response_time_ms": page.get("response_time_ms", 0),
        "status_code": page.get("status_code", 0),
        "is_https": (urlparse(url).scheme == "https"),
        "redirect_chain": page.get("redirect_chain") or [],
        "text_content": text_content,
        "viewport": bool(soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})),
        "has_nav": bool(soup.find("nav") or soup.find("header")),
        "has_list": bool(soup.find("ul") or soup.find("ol")),
        "has_table": bool(soup.find("table")),
        "paragraphs": len(soup.find_all("p")),
    }
