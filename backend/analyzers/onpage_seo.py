from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import urlparse


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "have", "has", "you", "your",
    "our", "about", "into", "their", "them", "they", "will", "can", "not", "but", "all", "any", "more", "than",
}


def _issue(severity: str, category: str, description: str, urls: list[str], recommendation: str) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "description": description,
        "affected_urls": urls,
        "recommendation": recommendation,
    }


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z]{3,}", text) if w.lower() not in STOPWORDS]


async def analyze_onpage(pages: list[dict[str, Any]]) -> dict[str, Any]:
    titles = [p.get("title", "").strip() for p in pages if p.get("title")]
    metas = [p.get("meta_description", "").strip() for p in pages if p.get("meta_description")]

    missing_titles = [p["url"] for p in pages if not p.get("title")]
    missing_metas = [p["url"] for p in pages if not p.get("meta_description")]

    title_counts = Counter(titles)
    meta_counts = Counter(metas)

    duplicate_titles = [t for t, c in title_counts.items() if c > 1]
    duplicate_metas = [m for m, c in meta_counts.items() if c > 1]

    thin_content_pages = [p["url"] for p in pages if p.get("word_count", 0) < 300]

    missing_alt_count = 0
    total_images = 0
    for p in pages:
        for img in p.get("images", []):
            total_images += 1
            if not img.get("has_alt"):
                missing_alt_count += 1

    page_tokens = []
    all_tokens = []
    densities = []
    for p in pages:
        tokens = _tokens(p.get("text_content", ""))
        page_tokens.append(tokens)
        all_tokens.extend(tokens)
        if tokens:
            top_word, top_freq = Counter(tokens).most_common(1)[0]
            densities.append((top_freq / len(tokens)) * 100)

    tf = Counter(all_tokens)
    top_keywords = [{"keyword": k, "count": c} for k, c in tf.most_common(10)]
    avg_keyword_density = round(sum(densities) / len(densities), 2) if densities else 0.0

    internal_linking_issues = []
    no_internal_links = [p["url"] for p in pages if len(p.get("internal_links", [])) == 0]
    if no_internal_links:
        internal_linking_issues.append(
            _issue("warning", "internal_links", "Pages with 0 internal links", no_internal_links[:20], "Add contextual internal links.")
        )

    h1_issues = []
    missing_h1 = [p["url"] for p in pages if len(p.get("h1", [])) == 0]
    multiple_h1 = [p["url"] for p in pages if len(p.get("h1", [])) > 1]
    if missing_h1:
        h1_issues.append(_issue("warning", "h1", "Missing H1", missing_h1[:20], "Add one clear H1."))
    if multiple_h1:
        h1_issues.append(_issue("info", "h1", "Multiple H1 tags", multiple_h1[:20], "Use one primary H1."))

    url_readability_issues = []
    for p in pages:
        path = urlparse(p["url"]).path
        if len(path) > 80 or re.search(r"[^a-zA-Z0-9/_\-]", path):
            url_readability_issues.append(p["url"])

    score = 100
    score -= min(len(missing_titles) * 2, 20)
    score -= min(len(missing_metas) * 2, 20)
    score -= min(len(thin_content_pages) * 2, 20)
    score -= min((missing_alt_count // 5) * 2, 15)
    score -= min(len(no_internal_links) * 2, 15)
    if avg_keyword_density > 3.0:
        score -= 10
    score = max(0, min(100, score))

    return {
        "score": score,
        "missing_titles": len(missing_titles),
        "missing_title_urls": missing_titles,
        "duplicate_titles": duplicate_titles,
        "missing_metas": len(missing_metas),
        "missing_meta_urls": missing_metas,
        "duplicate_metas": duplicate_metas,
        "thin_content_pages": thin_content_pages,
        "missing_alt_count": missing_alt_count,
        "total_images": total_images,
        "h1_issues": h1_issues,
        "avg_keyword_density": avg_keyword_density,
        "top_keywords": top_keywords,
        "internal_linking_issues": internal_linking_issues,
        "keyword_stuffing_flag": avg_keyword_density > 3.0,
        "url_readability_issues": url_readability_issues,
    }
