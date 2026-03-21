from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from crawler.page_analyzer import analyze_page
from crawler.robots_sitemap import fetch_robots_and_sitemap


class DeepCrawler:
    def __init__(
        self,
        root_url: str,
        max_pages: int = 50,
        include_subdomains: bool = False,
        concurrency: int = 10,
        request_delay: float = 0.1,
    ):
        self.root_url = self._normalize_url(root_url)
        self.max_pages = max_pages
        self.include_subdomains = include_subdomains
        self.concurrency = concurrency
        self.request_delay = request_delay

        self.root_domain = urlparse(self.root_url).netloc
        self._seen: set[str] = set()
        self._depth: dict[str, int] = {}
        self._last_request_at: dict[str, float] = {}
        self._domain_locks: dict[str, asyncio.Lock] = {}

        self.crawl_errors: list[dict[str, str]] = []
        self.robots_data: dict[str, Any] = {}

    @staticmethod
    def _normalize_url(url: str) -> str:
        raw = url.strip()
        if not raw.startswith(("http://", "https://")):
            raw = f"https://{raw}"
        parsed = urlparse(raw)
        normalized = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
            path=parsed.path or "/",
            query="",
            fragment="",
        )
        return urlunparse(normalized)

    def _is_internal(self, url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        if netloc == self.root_domain:
            return True
        if self.include_subdomains and netloc.endswith(f".{self.root_domain}"):
            return True
        return False

    async def _throttle(self, domain: str) -> None:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        async with self._domain_locks[domain]:
            now = time.monotonic()
            last = self._last_request_at.get(domain, 0.0)
            delta = now - last
            if delta < self.request_delay:
                await asyncio.sleep(self.request_delay - delta)
            self._last_request_at[domain] = time.monotonic()

    async def _fetch(self, client: httpx.AsyncClient, url: str, depth: int) -> dict[str, Any]:
        parsed = urlparse(url)
        await self._throttle(parsed.netloc)
        start = time.perf_counter()
        try:
            response = await client.get(url)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            redirects = [str(r.url) for r in response.history] + [str(response.url)]
            return {
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "redirect_chain": redirects,
                "final_url": str(response.url),
                "html_content": response.text if "text/html" in response.headers.get("content-type", "") else "",
                "headers": dict(response.headers),
                "depth": depth,
                "error": None,
            }
        except Exception as exc:
            self.crawl_errors.append({"url": url, "error": str(exc)})
            return {
                "url": url,
                "status_code": 0,
                "response_time_ms": 0,
                "redirect_chain": [],
                "final_url": url,
                "html_content": "",
                "headers": {},
                "depth": depth,
                "error": str(exc),
            }

    @staticmethod
    def _extract_links(base_url: str, html: str) -> list[str]:
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in {"http", "https"}:
                continue
            clean = parsed._replace(query="", fragment="")
            links.append(urlunparse(clean))
        return links

    async def crawl(self) -> list[dict[str, Any]]:
        self.robots_data = await fetch_robots_and_sitemap(self.root_url)
        robots_parser = self.robots_data.get("robots_parser")

        queue = deque([(self.root_url, 0)])
        self._seen.add(self.root_url)
        self._depth[self.root_url] = 0
        crawled_raw: list[dict[str, Any]] = []

        semaphore = asyncio.Semaphore(self.concurrency)

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "SEOIntelligenceBot/1.0 (+https://local.dev)"},
        ) as client:
            while queue and len(crawled_raw) < self.max_pages:
                batch = []
                while queue and len(batch) < self.concurrency and len(crawled_raw) + len(batch) < self.max_pages:
                    batch.append(queue.popleft())

                async def worker(item: tuple[str, int]) -> dict[str, Any]:
                    url, depth = item
                    if robots_parser and not robots_parser.can_fetch("*", url):
                        return {
                            "url": url,
                            "status_code": 0,
                            "response_time_ms": 0,
                            "redirect_chain": [],
                            "final_url": url,
                            "html_content": "",
                            "headers": {},
                            "depth": depth,
                            "error": "Blocked by robots.txt",
                        }
                    async with semaphore:
                        return await self._fetch(client, url, depth)

                results = await asyncio.gather(*[worker(item) for item in batch])

                for page in results:
                    crawled_raw.append(page)
                    final_url = self._normalize_url(page.get("final_url") or page.get("url"))
                    depth = page.get("depth", 0)
                    for link in self._extract_links(final_url, page.get("html_content", "")):
                        normalized = self._normalize_url(link)
                        if normalized in self._seen:
                            continue
                        if not self._is_internal(normalized):
                            continue
                        if len(self._seen) >= self.max_pages * 5:
                            continue
                        self._seen.add(normalized)
                        self._depth[normalized] = depth + 1
                        queue.append((normalized, depth + 1))

        analyzed = [analyze_page(page, self.root_url) for page in crawled_raw]
        for item in analyzed:
            item["depth"] = self._depth.get(item["url"], item.get("depth", 0))
        return analyzed
