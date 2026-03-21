from __future__ import annotations

import urllib.robotparser
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx


async def fetch_robots_and_sitemap(root_url: str, timeout: int = 20) -> dict[str, Any]:
    parsed = urlparse(root_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urljoin(base, "/robots.txt")
    sitemap_url = urljoin(base, "/sitemap.xml")

    robots_parser = urllib.robotparser.RobotFileParser()
    robots_text = ""
    robots_disallow: list[str] = []
    robots_ok = False
    sitemap_urls: list[str] = []
    sitemap_ok = False

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            robots_resp = await client.get(robots_url)
            if robots_resp.status_code < 400:
                robots_text = robots_resp.text
                robots_parser.parse(robots_text.splitlines())
                robots_ok = True
                for line in robots_text.splitlines():
                    if line.lower().startswith("disallow:"):
                        robots_disallow.append(line.split(":", 1)[-1].strip())
        except Exception:
            pass

        try:
            sitemap_resp = await client.get(sitemap_url)
            if sitemap_resp.status_code < 400 and sitemap_resp.text.strip().startswith("<"):
                root = ET.fromstring(sitemap_resp.text.encode("utf-8"))
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                sitemap_urls = [
                    loc.text.strip()
                    for loc in root.findall(".//sm:url/sm:loc", ns)
                    if loc.text and loc.text.strip()
                ]
                if not sitemap_urls:
                    sitemap_urls = [
                        loc.text.strip()
                        for loc in root.findall(".//url/loc")
                        if loc.text and loc.text.strip()
                    ]
                sitemap_ok = True
        except Exception:
            pass

    return {
        "robots_url": robots_url,
        "robots_found": robots_ok,
        "disallowed_paths": robots_disallow,
        "sitemap_url": sitemap_url,
        "sitemap_found": sitemap_ok,
        "sitemap_urls": sitemap_urls,
        "robots_parser": robots_parser,
    }
