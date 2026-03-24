from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ai.ollama_client import OllamaClient, build_ai_input_payload
from analyzers.onpage_seo import analyze_onpage
from analyzers.semantic_seo import analyze_semantic
from analyzers.technical_seo import analyze_technical
from analyzers.ux_signals import analyze_ux
from crawler.deep_crawler import DeepCrawler
from models.schemas import AnalysisRequest, TechnicalInsightRequest
from storage.json_store import JsonStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-intelligence")

app = FastAPI(title="SEO Intelligence API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = JsonStore(ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "24")))


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


@app.get("/api/health")
async def health() -> dict[str, Any]:
    ollama = OllamaClient()
    o_status = await ollama.health()
    return {"status": "ok", "ollama": o_status, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str) -> dict[str, Any]:
    result = await store.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@app.post("/api/ai/url-insight")
async def ai_url_insight(request: AnalysisRequest) -> dict[str, Any]:
    normalized_url = store.normalize_url(request.url)
    ollama = OllamaClient()
    health = await ollama.health()
    if not health.get("ok"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama endpoint unavailable. "
                f"Expected {os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/generate"
            ),
        )
    try:
        return await ollama.generate_url_only_insight(normalized_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"URL insight generation failed: {exc}") from exc


@app.post("/api/ai/technical-insight")
async def ai_technical_insight(request: TechnicalInsightRequest) -> dict[str, Any]:
    normalized_url = store.normalize_url(request.url)
    ollama = OllamaClient()
    health = await ollama.health()
    if not health.get("ok"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama endpoint unavailable. "
                f"Expected {os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/generate"
            ),
        )
    try:
        return await ollama.generate_technical_only_insight(normalized_url, request.technical or {})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Technical insight generation failed: {exc}") from exc


@app.post("/api/analyze/stream")
async def analyze_stream(request: AnalysisRequest) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        analysis_id = str(uuid.uuid4())
        normalized_url = store.normalize_url(request.url)

        yield _sse({"phase": "init", "message": "Preparing analysis", "analysis_id": analysis_id, "progress": 1})

        cached = await store.get_cached(normalized_url)
        if cached:
            yield _sse(
                {
                    "phase": "complete",
                    "message": "Returning cached analysis (within 24h)",
                    "analysis_id": cached.get("analysis_id", analysis_id),
                    "cached": True,
                    "progress": 100,
                    "data": cached,
                    "action_plan": cached.get("action_plan", []),
                }
            )
            return

        try:
            max_pages = min(max(request.max_pages or 50, 1), int(os.getenv("MAX_CRAWL_PAGES", "100")))
            crawler = DeepCrawler(
                normalized_url,
                max_pages=max_pages,
                include_subdomains=request.include_subdomains,
                concurrency=int(os.getenv("CRAWL_CONCURRENCY", "10")),
            )

            yield _sse({"phase": "crawling", "message": "Starting deep crawl...", "progress": 5, "analysis_id": analysis_id})
            pages = await crawler.crawl()
            yield _sse(
                {
                    "phase": "crawling",
                    "message": f"Crawled {len(pages)} pages",
                    "progress": 25,
                    "analysis_id": analysis_id,
                    "data": {"pages": len(pages), "errors": len(crawler.crawl_errors)},
                }
            )

            yield _sse({"phase": "technical", "message": "Analyzing technical SEO...", "progress": 35, "analysis_id": analysis_id})
            technical = await analyze_technical(pages, normalized_url, crawler.robots_data)
            yield _sse({"phase": "technical", "data": technical, "progress": 50, "analysis_id": analysis_id})

            yield _sse({"phase": "onpage", "message": "Analyzing on-page factors...", "progress": 55, "analysis_id": analysis_id})
            onpage = await analyze_onpage(pages)
            yield _sse({"phase": "onpage", "data": onpage, "progress": 65, "analysis_id": analysis_id})

            yield _sse({"phase": "semantic", "message": "Running semantic analysis...", "progress": 70, "analysis_id": analysis_id})
            semantic = await analyze_semantic(pages)
            yield _sse({"phase": "semantic", "data": semantic, "progress": 80, "analysis_id": analysis_id})

            yield _sse({"phase": "ux", "message": "Analyzing UX signals...", "progress": 85, "analysis_id": analysis_id})
            ux = await analyze_ux(pages)
            yield _sse({"phase": "ux", "data": ux, "progress": 88, "analysis_id": analysis_id})

            full_data = {"technical": technical, "onpage": onpage, "semantic": semantic, "ux": ux}
            base_payload = {
                "analysis_id": analysis_id,
                "url": normalized_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "technical": technical,
                "onpage": onpage,
                "semantic": semantic,
                "ux": ux,
                "ai_analysis": "",
                "action_plan": [],
                "crawl_errors": crawler.crawl_errors,
            }
            await store.save_analysis(analysis_id, base_payload)
            await store.set_cached(normalized_url, base_payload)
            yield _sse(
                {
                    "phase": "core_complete",
                    "message": "Core SEO analysis is ready",
                    "analysis_id": analysis_id,
                    "progress": 89,
                    "data": base_payload,
                    "action_plan": [],
                }
            )

            ai_chunks: list[str] = []
            ollama = OllamaClient()
            ollama_health = await ollama.health()
            if not ollama_health.get("ok"):
                yield _sse(
                    {
                        "phase": "warning",
                        "message": (
                            "AI insights skipped: Ollama endpoint unavailable. "
                            f"Expected {os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/generate"
                        ),
                        "analysis_id": analysis_id,
                        "data": {"section": "ai", "health": ollama_health},
                    }
                )
                action_plan = []
            else:
                ai_sections = [
                    ("onpage", {"onpage": onpage}, "On-Page SEO"),
                    ("technical", {"technical": technical}, "Technical SEO"),
                    ("semantic", {"semantic": semantic}, "Semantic SEO"),
                    ("ux", {"ux": ux}, "UX Signals"),
                ]

                for idx, (section_key, section_payload, section_label) in enumerate(ai_sections, start=1):
                    section_chunks: list[str] = []
                    try:
                        ai_input_payload = build_ai_input_payload(normalized_url, section_payload, section_name=section_key)
                        ai_debug_payload = {k: v for k, v in ai_input_payload.items() if k != "prompt"}
                        logger.info(
                            "AI input payload for Ollama section=%s: %s",
                            section_key,
                            json.dumps(ai_debug_payload, ensure_ascii=True),
                        )

                        yield _sse(
                            {
                                "phase": "ai",
                                "message": f"Generating AI insights for {section_label} ({idx}/4)...",
                                "progress": 90,
                                "analysis_id": analysis_id,
                                "data": ai_debug_payload,
                            }
                        )

                        heading = f"\n\n## {section_label} Insights\n"
                        ai_chunks.append(heading)
                        yield _sse({"phase": "ai_stream", "chunk": heading, "analysis_id": analysis_id, "data": {"section": section_key}})

                        async for chunk in ollama.stream_analysis(normalized_url, section_payload, section_name=section_key):
                            section_chunks.append(chunk)
                            ai_chunks.append(chunk)
                            yield _sse(
                                {
                                    "phase": "ai_stream",
                                    "chunk": chunk,
                                    "analysis_id": analysis_id,
                                    "data": {"section": section_key},
                                }
                            )
                    except Exception as exc:
                        logger.exception("AI section pipeline failed for section=%s", section_key)
                        yield _sse(
                            {
                                "phase": "warning",
                                "message": f"AI section failed for {section_label}: {exc}",
                                "analysis_id": analysis_id,
                                "data": {"section": section_key},
                            }
                        )

                    if not section_chunks:
                        try:
                            fallback_text = await ollama.generate_analysis_text(normalized_url, section_payload, section_name=section_key)
                            if fallback_text:
                                section_chunks.append(fallback_text)
                                ai_chunks.append(fallback_text)
                                yield _sse(
                                    {
                                        "phase": "ai_stream",
                                        "chunk": fallback_text,
                                        "analysis_id": analysis_id,
                                        "data": {"section": section_key, "fallback": True},
                                    }
                                )
                        except Exception as exc:
                            logger.exception("AI fallback generation failed for section=%s", section_key)
                            yield _sse(
                                {
                                    "phase": "warning",
                                    "message": f"AI fallback generation failed for {section_label}: {exc}",
                                    "analysis_id": analysis_id,
                                    "data": {"section": section_key},
                                }
                            )

                action_plan = []
                try:
                    action_plan = await ollama.generate_action_plan(full_data)
                except Exception as exc:
                    logger.exception("Action plan generation failed")
                    yield _sse({"phase": "warning", "message": f"Action plan generation failed: {exc}", "analysis_id": analysis_id})

            final_payload = {
                "analysis_id": analysis_id,
                "url": normalized_url,
                "created_at": base_payload["created_at"],
                "technical": technical,
                "onpage": onpage,
                "semantic": semantic,
                "ux": ux,
                "ai_analysis": "".join(ai_chunks),
                "action_plan": action_plan,
                "crawl_errors": crawler.crawl_errors,
            }

            await store.save_analysis(analysis_id, final_payload)
            await store.set_cached(normalized_url, final_payload)

            yield _sse(
                {
                    "phase": "complete",
                    "message": "Analysis complete",
                    "analysis_id": analysis_id,
                    "progress": 100,
                    "action_plan": action_plan,
                    "data": final_payload,
                }
            )
        except Exception as exc:
            logger.exception("Analysis failed")
            yield _sse({"phase": "error", "message": f"Analysis failed: {exc}", "analysis_id": analysis_id, "progress": 100})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
