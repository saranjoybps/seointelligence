from __future__ import annotations

import re
from collections import Counter
from itertools import combinations
from typing import Any

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "have", "has", "you", "your",
    "our", "about", "into", "their", "them", "they", "will", "can", "not", "but", "all", "any", "more", "than",
}


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z]{3,}", text) if w.lower() not in STOPWORDS]


def _extract_entities(text: str) -> list[str]:
    entities = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text)
    return [e.strip() for e in entities if len(e.strip()) > 2]


async def analyze_semantic(pages: list[dict[str, Any]]) -> dict[str, Any]:
    entity_counter: Counter[str] = Counter()
    page_keyword_map: dict[str, set[str]] = {}
    no_schema_pages: list[str] = []
    faq_opportunities: set[str] = set()
    content_gaps: list[str] = []

    co_occurrence: Counter[tuple[str, str]] = Counter()

    for page in pages:
        text = page.get("text_content", "")
        tokens = _tokens(text)
        token_counts = Counter(tokens)
        top_terms = {term for term, _ in token_counts.most_common(12)}
        page_keyword_map[page["url"]] = top_terms

        entities = _extract_entities(text)
        entity_counter.update(entities)

        if not page.get("schema_markup"):
            no_schema_pages.append(page["url"])

        if page.get("word_count", 0) < 100:
            content_gaps.append(f"Expand low-depth page: {page['url']}")

        questions = re.findall(r"([^\n\r?.!]{0,120}\?)", text)
        for q in questions[:5]:
            q = q.strip()
            if 10 <= len(q) <= 120:
                faq_opportunities.add(q)

        unique_terms = list(top_terms)[:10]
        for a, b in combinations(sorted(unique_terms), 2):
            co_occurrence[(a, b)] += 1

    urls = list(page_keyword_map.keys())
    used: set[str] = set()
    clusters: list[dict[str, Any]] = []

    for url in urls:
        if url in used:
            continue
        used.add(url)
        seed = page_keyword_map[url]
        cluster_urls = [url]
        cluster_keywords = set(seed)

        for other in urls:
            if other in used:
                continue
            overlap = len(seed & page_keyword_map[other])
            if overlap >= 3:
                used.add(other)
                cluster_urls.append(other)
                cluster_keywords |= page_keyword_map[other]

        clusters.append(
            {
                "label": ", ".join(list(cluster_keywords)[:3]) if cluster_keywords else "General",
                "pages": cluster_urls,
                "keywords": list(cluster_keywords)[:12],
            }
        )

    lsi_keywords = [
        f"{a} {b}"
        for (a, b), _ in co_occurrence.most_common(20)
        if a not in STOPWORDS and b not in STOPWORDS
    ]

    topical_authority_score = 0.0
    if pages:
        keyword_breadth = len(set().union(*page_keyword_map.values())) if page_keyword_map else 0
        cluster_factor = len(clusters)
        topical_authority_score = round(min(100.0, (keyword_breadth * 0.8) + (cluster_factor * 5)), 2)

    score = int(max(0, min(100, 55 + min(len(clusters) * 4, 20) + min(len(entity_counter) // 5, 15) - min(len(no_schema_pages), 20))))

    return {
        "score": score,
        "top_entities": [e for e, _ in entity_counter.most_common(30)],
        "topic_clusters": clusters,
        "content_gaps": content_gaps[:50],
        "no_schema_pages": no_schema_pages,
        "lsi_keywords": lsi_keywords[:30],
        "faq_opportunities": list(faq_opportunities)[:30],
        "topical_authority_score": topical_authority_score,
    }
