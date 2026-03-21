from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
ANALYSIS_DIR = DATA_DIR / "analysis"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

_LOCKS: dict[str, asyncio.Lock] = {
    "cache": asyncio.Lock(),
    "analysis": asyncio.Lock(),
}


class JsonStore:
    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc or parsed.path
        path = parsed.path if parsed.netloc else ""
        normalized = parsed._replace(scheme=scheme, netloc=netloc.lower(), path=path or "/", query="", fragment="")
        return urlunparse(normalized)

    @staticmethod
    def _url_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        tmp.replace(path)

    async def get_cached(self, url: str) -> Optional[dict[str, Any]]:
        normalized = self.normalize_url(url)
        key = self._url_key(normalized)
        path = CACHE_DIR / f"{key}.json"
        if not path.exists():
            return None
        async with _LOCKS["cache"]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                created_at = datetime.fromisoformat(data["created_at"])
                if datetime.now(timezone.utc) - created_at > self.ttl:
                    return None
                return data.get("result")
            except Exception:
                return None

    async def set_cached(self, url: str, result: dict[str, Any]) -> None:
        normalized = self.normalize_url(url)
        key = self._url_key(normalized)
        path = CACHE_DIR / f"{key}.json"
        payload = {
            "url": normalized,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
        }
        async with _LOCKS["cache"]:
            self._atomic_write(path, payload)

    async def save_analysis(self, analysis_id: str, payload: dict[str, Any]) -> None:
        path = ANALYSIS_DIR / f"{analysis_id}.json"
        async with _LOCKS["analysis"]:
            self._atomic_write(path, payload)

    async def get_analysis(self, analysis_id: str) -> Optional[dict[str, Any]]:
        path = ANALYSIS_DIR / f"{analysis_id}.json"
        if not path.exists():
            return None
        async with _LOCKS["analysis"]:
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None
