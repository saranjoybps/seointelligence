from __future__ import annotations

from collections import Counter
from typing import Any
from urllib.parse import urlparse


def _issue(severity: str, category: str, description: str, urls: list[str], recommendation: str) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "description": description,
        "affected_urls": urls,
        "recommendation": recommendation,
    }


async def analyze_technical(
    pages: list[dict[str, Any]],
    root_url: str,
    robots_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    robots_data = robots_data or {}

    total = max(len(pages), 1)
    https_pages = [p for p in pages if p.get("is_https")]
    mixed_http_pages = [p["url"] for p in pages if not p.get("is_https")]

    fast = sum(1 for p in pages if p.get("response_time_ms", 0) < 200)
    ok = sum(1 for p in pages if 200 <= p.get("response_time_ms", 0) <= 500)
    slow_pages = [p["url"] for p in pages if p.get("response_time_ms", 0) > 500]

    broken_links = [p["url"] for p in pages if p.get("status_code", 0) >= 400 or p.get("status_code", 0) == 0]
    redirect_chains = [
        {
            "url": p["url"],
            "hops": len(p.get("redirect_chain", [])) - 1,
            "chain": p.get("redirect_chain", []),
        }
        for p in pages
        if len(p.get("redirect_chain", [])) > 3
    ]

    canonical_issues = []
    for p in pages:
        canonical = (p.get("canonical") or "").strip()
        if not canonical:
            canonical_issues.append(
                _issue("warning", "canonical", "Missing canonical tag", [p["url"]], "Add a self-referencing canonical tag.")
            )
            continue
        c_host = urlparse(canonical if canonical.startswith("http") else p["url"]).netloc
        if c_host and c_host != urlparse(root_url).netloc:
            canonical_issues.append(
                _issue(
                    "warning",
                    "canonical",
                    "Canonical points to a different host",
                    [p["url"]],
                    "Verify cross-domain canonical target is intentional.",
                )
            )

    h1_missing = [p["url"] for p in pages if len(p.get("h1", [])) == 0]
    h1_multiple = [p["url"] for p in pages if len(p.get("h1", [])) > 1]

    mobile_ready = sum(1 for p in pages if p.get("viewport")) / total >= 0.9

    critical_issues = []
    if mixed_http_pages:
        critical_issues.append(
            _issue("critical", "https", "HTTP pages detected", mixed_http_pages[:20], "Force HTTPS and update internal links.")
        )
    if broken_links:
        critical_issues.append(
            _issue("critical", "broken_links", "Broken pages detected", broken_links[:20], "Fix links and server errors (4xx/5xx).")
        )

    issues = list(canonical_issues)
    if redirect_chains:
        issues.append(
            _issue(
                "warning",
                "redirects",
                "Redirect chains over 2 hops",
                [r["url"] for r in redirect_chains][:20],
                "Flatten redirects to a single hop.",
            )
        )
    if h1_missing:
        issues.append(_issue("warning", "h1", "Pages missing H1", h1_missing[:20], "Add one clear H1 per page."))
    if h1_multiple:
        issues.append(_issue("info", "h1", "Pages with multiple H1 tags", h1_multiple[:20], "Consolidate to one primary H1."))
    if slow_pages:
        issues.append(
            _issue(
                "warning",
                "performance",
                "Slow response times detected",
                slow_pages[:20],
                "Optimize server response and heavy resources.",
            )
        )

    score = 100
    score -= min(len(critical_issues) * 15, 45)
    score -= min(len(issues) * 5, 35)
    if not robots_data.get("robots_found"):
        score -= 5
    if not robots_data.get("sitemap_found"):
        score -= 5
    score = max(0, min(100, score))

    return {
        "score": score,
        "https_status": {
            "secure_pages": len(https_pages),
            "insecure_pages": len(mixed_http_pages),
            "insecure_urls": mixed_http_pages,
        },
        "page_speed": {
            "fast": fast,
            "ok": ok,
            "slow": len(slow_pages),
            "slow_urls": slow_pages,
            "avg_response_ms": round(sum(p.get("response_time_ms", 0) for p in pages) / total, 2),
        },
        "broken_links": broken_links,
        "redirect_chains": redirect_chains,
        "canonical_issues": canonical_issues,
        "robots_txt": {
            "found": robots_data.get("robots_found", False),
            "disallowed_paths": robots_data.get("disallowed_paths", []),
        },
        "sitemap": {
            "found": robots_data.get("sitemap_found", False),
            "listed_urls": len(robots_data.get("sitemap_urls", [])),
            "crawled_urls": len(pages),
        },
        "mobile_ready": mobile_ready,
        "critical_issues": critical_issues,
        "issues": issues,
        "h1_summary": dict(Counter({"missing": len(h1_missing), "multiple": len(h1_multiple)})),
    }
