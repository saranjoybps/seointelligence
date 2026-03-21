from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, AsyncIterator

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")
NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "1800"))
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
PROMPT_SAFETY_MARGIN = int(os.getenv("OLLAMA_PROMPT_SAFETY_MARGIN", "600"))

SYSTEM_PROMPT = """You are an elite SEO strategist and digital marketing expert with 15+ years of experience.
You analyze websites with surgical precision and provide actionable, data-driven recommendations.
You think like a growth hacker, SEO engineer, and content strategist combined.
Always be specific, cite the data provided, and prioritize recommendations by ROI impact."""

logger = logging.getLogger("seo-intelligence.ai")


class OllamaClient:
    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{OLLAMA_URL}/api/tags")
                return {"ok": response.status_code < 400, "status_code": response.status_code}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def stream_analysis(self, url: str, data: dict[str, Any], section_name: str | None = None) -> AsyncIterator[str]:
        request_payload = build_ai_input_payload(url, data, section_name=section_name)
        prompt = request_payload["prompt"]
        got_tokens = False
        chunk_count = 0
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": True,
                    "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
                },
            ) as response:
                if response.status_code >= 400:
                    raw = await response.aread()
                    body = raw.decode("utf-8", errors="ignore")[:400]
                    raise RuntimeError(
                        f"Ollama stream HTTP {response.status_code} on /api/generate. "
                        f"OLLAMA_URL={OLLAMA_URL}. Body sample: {body}"
                    )
                logger.info(
                    "Ollama stream started section=%s status=%s prompt_chars=%s tokens_est=%s",
                    section_name or "full",
                    response.status_code,
                    request_payload.get("prompt_characters"),
                    request_payload.get("input_token_estimate"),
                )
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Ollama stream non-JSON line section=%s sample=%s", section_name or "full", line[:180])
                        continue
                    if payload.get("error"):
                        logger.error("Ollama stream error section=%s payload=%s", section_name or "full", payload)
                        raise RuntimeError(str(payload["error"]))
                    if payload.get("done"):
                        logger.info("Ollama stream done section=%s chunks=%s", section_name or "full", chunk_count)
                        break
                    chunk = payload.get("response", "")
                    if chunk:
                        got_tokens = True
                        chunk_count += 1
                        logger.info("Ollama stream chunk section=%s index=%s chars=%s", section_name or "full", chunk_count, len(chunk))
                        yield chunk
        if not got_tokens:
            raise RuntimeError("Ollama returned no streamed tokens")

    async def generate_analysis_text(self, url: str, data: dict[str, Any], section_name: str | None = None) -> str:
        request_payload = build_ai_input_payload(url, data, section_name=section_name)
        prompt = request_payload["prompt"]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
                },
            )
            if response.status_code >= 400:
                body = response.text[:400]
                raise RuntimeError(
                    f"Ollama fallback HTTP {response.status_code} on /api/generate. "
                    f"OLLAMA_URL={OLLAMA_URL}. Body sample: {body}"
                )
            payload = response.json()
            logger.info(
                "Ollama fallback response section=%s status=%s has_error=%s response_chars=%s",
                section_name or "full",
                response.status_code,
                bool(payload.get("error")),
                len(str(payload.get("response", ""))),
            )
            if payload.get("error"):
                raise RuntimeError(str(payload["error"]))
            return str(payload.get("response", "")).strip()

    async def generate_action_plan(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        prompt = build_action_plan_prompt(data)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": "Return only valid JSON. Do not wrap in markdown.",
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2, "top_p": 0.9, "num_predict": 1200, "num_ctx": NUM_CTX},
                },
            )
            if response.status_code >= 400:
                body = response.text[:400]
                raise RuntimeError(
                    f"Ollama action-plan HTTP {response.status_code} on /api/generate. "
                    f"OLLAMA_URL={OLLAMA_URL}. Body sample: {body}"
                )
            body = response.json()
            if body.get("error"):
                raise RuntimeError(str(body["error"]))
            text = body.get("response", "[]")
            parsed = self._safe_json_list(text)
            if parsed:
                return [self._normalize_action(item) for item in parsed]
            return []

    @staticmethod
    def _safe_json_list(raw: str) -> list[dict[str, Any]]:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [x for x in loaded if isinstance(x, dict)]
            if isinstance(loaded, dict) and isinstance(loaded.get("actions"), list):
                return [x for x in loaded["actions"] if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass

        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return []
        try:
            loaded = json.loads(match.group(0))
            return [x for x in loaded if isinstance(x, dict)] if isinstance(loaded, list) else []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _normalize_action(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "priority": str(item.get("priority", "medium")).lower(),
            "category": str(item.get("category", "General")),
            "action": str(item.get("action", "")),
            "impact": str(item.get("impact", "")),
            "effort": str(item.get("effort", "")),
            "timeframe": str(item.get("timeframe", "")),
        }


def _limit(items: list[Any], n: int) -> list[Any]:
    return items[: max(0, n)]


def _issue_preview(issue: dict[str, Any], url_limit: int = 4) -> dict[str, Any]:
    return {
        "severity": issue.get("severity"),
        "category": issue.get("category"),
        "description": issue.get("description"),
        "sample_urls": _limit(issue.get("affected_urls", []), url_limit),
        "affected_count": len(issue.get("affected_urls", [])),
    }


def _prune_for_llm(data: dict[str, Any], tight: bool = False) -> dict[str, Any]:
    tech = data.get("technical", {})
    onpage = data.get("onpage", {})
    semantic = data.get("semantic", {})
    ux = data.get("ux", {})

    max_url_samples = 4 if not tight else 2
    max_keyword_items = 10 if not tight else 6
    max_entities = 14 if not tight else 8
    max_clusters = 4 if not tight else 2
    max_lsi = 12 if not tight else 6
    max_faq = 10 if not tight else 4
    max_content_gaps = 8 if not tight else 4

    pruned_issues = [_issue_preview(i, max_url_samples) for i in _limit(tech.get("issues", []), 8 if not tight else 5)]
    pruned_critical = [_issue_preview(i, max_url_samples) for i in _limit(tech.get("critical_issues", []), 5 if not tight else 3)]

    compact_clusters: list[dict[str, Any]] = []
    for c in _limit(semantic.get("topic_clusters", []), max_clusters):
        compact_clusters.append(
            {
                "label": c.get("label"),
                "page_count": len(c.get("pages", [])),
                "sample_pages": _limit(c.get("pages", []), max_url_samples),
                "keywords": _limit(c.get("keywords", []), 8 if not tight else 5),
            }
        )

    return {
        "technical": {
            "score": tech.get("score", 0),
            "https_status": tech.get("https_status", {}),
            "page_speed": {
                "fast": tech.get("page_speed", {}).get("fast", 0),
                "ok": tech.get("page_speed", {}).get("ok", 0),
                "slow": tech.get("page_speed", {}).get("slow", 0),
                "avg_response_ms": tech.get("page_speed", {}).get("avg_response_ms", 0),
                "slow_url_samples": _limit(tech.get("page_speed", {}).get("slow_urls", []), max_url_samples),
            },
            "broken_links_count": len(tech.get("broken_links", [])),
            "broken_link_samples": _limit(tech.get("broken_links", []), max_url_samples),
            "redirect_chains_count": len(tech.get("redirect_chains", [])),
            "canonical_issue_count": len(tech.get("canonical_issues", [])),
            "robots_txt": tech.get("robots_txt", {}),
            "sitemap": tech.get("sitemap", {}),
            "mobile_ready": tech.get("mobile_ready", False),
            "critical_issues": pruned_critical,
            "issues": pruned_issues,
            "h1_summary": tech.get("h1_summary", {}),
        },
        "onpage": {
            "score": onpage.get("score", 0),
            "missing_titles": onpage.get("missing_titles", 0),
            "missing_title_urls": _limit(onpage.get("missing_title_urls", []), max_url_samples),
            "missing_metas": onpage.get("missing_metas", 0),
            "missing_meta_urls": _limit(onpage.get("missing_meta_urls", []), max_url_samples),
            "thin_content_count": len(onpage.get("thin_content_pages", [])),
            "thin_content_samples": _limit(onpage.get("thin_content_pages", []), max_url_samples),
            "missing_alt_count": onpage.get("missing_alt_count", 0),
            "total_images": onpage.get("total_images", 0),
            "avg_keyword_density": onpage.get("avg_keyword_density", 0),
            "top_keywords": _limit(onpage.get("top_keywords", []), max_keyword_items),
            "keyword_stuffing_flag": onpage.get("keyword_stuffing_flag", False),
            "internal_linking_issues": [_issue_preview(i, max_url_samples) for i in _limit(onpage.get("internal_linking_issues", []), 4)],
            "url_readability_issue_count": len(onpage.get("url_readability_issues", [])),
            "url_readability_samples": _limit(onpage.get("url_readability_issues", []), max_url_samples),
        },
        "semantic": {
            "score": semantic.get("score", 0),
            "topical_authority_score": semantic.get("topical_authority_score", 0),
            "top_entities": _limit(semantic.get("top_entities", []), max_entities),
            "topic_clusters": compact_clusters,
            "content_gaps": _limit(semantic.get("content_gaps", []), max_content_gaps),
            "no_schema_count": len(semantic.get("no_schema_pages", [])),
            "no_schema_samples": _limit(semantic.get("no_schema_pages", []), max_url_samples),
            "lsi_keywords": _limit(semantic.get("lsi_keywords", []), max_lsi),
            "faq_opportunities": _limit(semantic.get("faq_opportunities", []), max_faq),
        },
        "ux": {
            "score": ux.get("score", 0),
            "avg_readability": ux.get("avg_readability", 0),
            "fk_grade": ux.get("fk_grade", 0),
            "pages_with_cta": ux.get("pages_with_cta", 0),
            "navigation_score": ux.get("navigation_score", 0),
            "content_structure_score": ux.get("content_structure_score", 0),
        },
    }


def build_analysis_prompt(url: str, data: dict[str, Any], section_name: str | None = None) -> str:
    technical = data.get("technical", {})
    onpage = data.get("onpage", {})
    semantic = data.get("semantic", {})
    ux = data.get("ux", {})

    broken_links = technical.get("broken_links")
    broken_links_count = technical.get("broken_links_count", len(broken_links) if isinstance(broken_links, list) else 0)

    redirect_chains = technical.get("redirect_chains")
    redirect_chains_count = technical.get(
        "redirect_chains_count",
        len(redirect_chains) if isinstance(redirect_chains, list) else 0,
    )

    thin_pages = onpage.get("thin_content_pages")
    thin_pages_count = onpage.get("thin_content_count", len(thin_pages) if isinstance(thin_pages, list) else 0)

    no_schema = semantic.get("no_schema_pages")
    no_schema_count = semantic.get("no_schema_count", len(no_schema) if isinstance(no_schema, list) else 0)

    section_header = "FULL WEBSITE SEO REVIEW"
    if section_name:
        section_header = f"{section_name.upper()} SEO REVIEW"

    return f"""
Perform a comprehensive SEO & digital marketing analysis for: {url}
Focus area: {section_header}

## NUMERICAL DATA SNAPSHOT
- Technical score: {technical.get('score', 0)}
- On-page score: {onpage.get('score', 0)}
- Semantic score: {semantic.get('score', 0)}
- UX score: {ux.get('score', 0)}
- Broken links: {broken_links_count}
- Redirect chains >2: {redirect_chains_count}
- Missing titles: {onpage.get('missing_titles', 0)}
- Missing meta descriptions: {onpage.get('missing_metas', 0)}
- Thin content pages: {thin_pages_count}
- Missing image alts: {onpage.get('missing_alt_count', 0)}
- Avg keyword density: {onpage.get('avg_keyword_density', 0)}
- Topical authority score: {semantic.get('topical_authority_score', 0)}
- Pages without schema: {no_schema_count}
- Avg readability: {ux.get('avg_readability', 0)}
- Flesch-Kincaid grade: {ux.get('fk_grade', 0)}
- Pages with CTA (%): {ux.get('pages_with_cta', 0)}

## RAW FINDINGS JSON
{json.dumps(data, separators=(",", ":"), ensure_ascii=True)}

Provide:
1) Executive summary (3 sentences)
2) Top 3 critical fixes with clear ROI rationale
3) Concrete actions tied only to this focus area
4) 30-day quick wins
5) KPI metrics to track
"""


def build_action_plan_prompt(data: dict[str, Any]) -> str:
    slim = _prune_for_llm(data, tight=True)
    return f"""
Using this SEO analysis data, generate a prioritized action plan.

Data:
{json.dumps(slim, separators=(",", ":"), ensure_ascii=True)}

Return ONLY a valid JSON array. No markdown, no commentary.
Each item must be:
{{
  "priority": "high|medium|low",
  "category": "string",
  "action": "string",
  "impact": "string",
  "effort": "string",
  "timeframe": "string"
}}

Return 8-15 actions sorted by business impact.
"""


def estimate_tokens(text: str) -> int:
    # Rough approximation used for observability; exact tokenization is model-specific.
    return max(1, int(round(len(text) / 4)))


def build_ai_input_payload(url: str, data: dict[str, Any], section_name: str | None = None) -> dict[str, Any]:
    max_input_tokens = max(500, NUM_CTX - NUM_PREDICT - PROMPT_SAFETY_MARGIN)

    pruned = _prune_for_llm(data, tight=False)
    prompt = build_analysis_prompt(url, pruned, section_name=section_name)
    input_tokens = estimate_tokens(prompt)
    trim_level = "normal"

    if input_tokens > max_input_tokens:
        pruned = _prune_for_llm(data, tight=True)
        prompt = build_analysis_prompt(url, pruned, section_name=section_name)
        input_tokens = estimate_tokens(prompt)
        trim_level = "tight"

    if input_tokens > max_input_tokens:
        # Last-resort minimal payload when context is very constrained.
        pruned = {
            "technical": {"score": data.get("technical", {}).get("score", 0), "issues": _limit(data.get("technical", {}).get("issues", []), 3)},
            "onpage": {"score": data.get("onpage", {}).get("score", 0), "top_keywords": _limit(data.get("onpage", {}).get("top_keywords", []), 5)},
            "semantic": {"score": data.get("semantic", {}).get("score", 0), "topical_authority_score": data.get("semantic", {}).get("topical_authority_score", 0)},
            "ux": {"score": data.get("ux", {}).get("score", 0), "avg_readability": data.get("ux", {}).get("avg_readability", 0)},
        }
        prompt = build_analysis_prompt(url, pruned, section_name=section_name)
        input_tokens = estimate_tokens(prompt)
        trim_level = "minimal"

    return {
        "model": MODEL,
        "url": url,
        "structured_data": pruned,
        "prompt": prompt,
        "prompt_characters": len(prompt),
        "input_token_estimate": input_tokens,
        "max_input_tokens_target": max_input_tokens,
        "num_predict": NUM_PREDICT,
        "num_ctx": NUM_CTX,
        "trim_level": trim_level,
        "section_name": section_name or "full",
    }
