from __future__ import annotations

import re
from typing import Any

CTA_PATTERNS = [
    "buy", "get", "start", "sign up", "contact", "download", "learn more", "try", "book", "schedule",
]


def _count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _flesch_kincaid(text: str) -> tuple[float, float]:
    sentences = max(1, len(re.findall(r"[.!?]", text)))
    words = re.findall(r"[A-Za-z]+", text)
    word_count = max(1, len(words))
    syllables = sum(_count_syllables(w) for w in words)

    asl = word_count / sentences
    asw = syllables / word_count

    ease = 206.835 - (1.015 * asl) - (84.6 * asw)
    grade = (0.39 * asl) + (11.8 * asw) - 15.59
    return round(ease, 2), round(grade, 2)


async def analyze_ux(pages: list[dict[str, Any]]) -> dict[str, Any]:
    if not pages:
        return {
            "score": 0,
            "avg_readability": 0.0,
            "fk_grade": 0.0,
            "pages_with_cta": 0.0,
            "navigation_score": 0,
            "content_structure_score": 0,
        }

    readability_scores = []
    grades = []
    cta_pages = 0
    nav_pages = 0
    structure_points = 0

    for p in pages:
        text = p.get("text_content", "")
        ease, grade = _flesch_kincaid(text)
        readability_scores.append(ease)
        grades.append(grade)

        content_lower = text.lower()
        if any(pattern in content_lower for pattern in CTA_PATTERNS):
            cta_pages += 1

        if p.get("has_nav"):
            nav_pages += 1

        local_points = 0
        if p.get("has_list"):
            local_points += 1
        if p.get("has_table"):
            local_points += 1
        if p.get("paragraphs", 0) >= 3:
            local_points += 1
        first_200_words = " ".join(text.split()[:200]).lower()
        if any(pattern in first_200_words for pattern in CTA_PATTERNS):
            local_points += 1
        structure_points += local_points

    total = len(pages)
    avg_readability = round(sum(readability_scores) / total, 2)
    avg_grade = round(sum(grades) / total, 2)
    pages_with_cta = round((cta_pages / total) * 100, 2)
    navigation_score = int(round((nav_pages / total) * 100))
    content_structure_score = int(round((structure_points / (total * 4)) * 100))

    score = int(max(0, min(100, (avg_readability * 0.3) + (pages_with_cta * 0.2) + (navigation_score * 0.25) + (content_structure_score * 0.25))))

    return {
        "score": score,
        "avg_readability": avg_readability,
        "fk_grade": avg_grade,
        "pages_with_cta": pages_with_cta,
        "navigation_score": navigation_score,
        "content_structure_score": content_structure_score,
    }
