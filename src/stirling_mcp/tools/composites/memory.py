"""Cross-MCP composite — pdf_to_memory and pdf_search_memory.

Bridges Stirling-PDF and nobrainr's knowledge graph: extract text from a PDF,
store with tags/category, then semantic-search across stored PDFs.

Requires NOBRAINR_URL env var. If empty, both tools return success=False with
a hint.
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.server import mcp

log = logging.getLogger("stirling_mcp.composites.memory")


def _nobrainr_endpoint() -> str | None:
    base = SETTINGS.nobrainr_url
    if not base:
        return None
    return base.rstrip("/")


@mcp.tool()
async def pdf_to_memory(
    input_file: str,
    tags: list[str] | None = None,
    category: str = "documentation",
    ocr_if_needed: bool = True,
    summary: str | None = None,
) -> dict:
    """Extract text from a PDF and store as a nobrainr memory.

    Workflow:
        1. OCR (if needed and `ocr_if_needed=True`)
        2. Extract text
        3. POST to nobrainr's memory_store endpoint

    Args:
        tags: list of tags (e.g. ["contract", "2026-q1"])
        category: memory category (e.g. "documentation", "contract", "research")
        summary: optional one-line summary
    """
    nb = _nobrainr_endpoint()
    if not nb:
        return {"success": False, "error": "NOBRAINR_URL not configured"}

    client = get_client()
    work = Path(input_file)

    if ocr_if_needed:
        ocr = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[work],
            form_data={"languages": ["eng"], "ocrType": "skip-text"},
            output_name_hint="memory-ocr",
        )
        if ocr.get("success"):
            work = Path(ocr["output_path"])

    txt = await client.post_form(
        "/api/v1/misc/extract-text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="memory-text",
    )
    if not txt.get("success"):
        return {"success": False, "stage": "extract-text", **txt}

    text = Path(txt["output_path"]).read_text(errors="ignore")

    async with httpx.AsyncClient(timeout=30) as h:
        resp = await h.post(
            f"{nb}/tools/memory_store",
            json={
                "content": text[:20000],  # nobrainr chunks long content automatically
                "summary": summary or f"PDF: {work.name}",
                "tags": tags or ["pdf", "imported"],
                "category": category,
                "source_type": "agent",
                "source_machine": "bimavo",
                "metadata": {"source_pdf": str(input_file)},
            },
        )
        resp.raise_for_status()
        body = resp.json()

    return {
        "success": True,
        "stored": body,
        "text_length": len(text),
        "source_pdf": str(input_file),
    }


@mcp.tool()
async def pdf_search_memory(query: str, tags: list[str] | None = None, limit: int = 10) -> dict:
    """Semantic search across PDFs previously stored via `pdf_to_memory`.

    Returns top-k matching memories with their stored summaries + source PDF paths.
    """
    nb = _nobrainr_endpoint()
    if not nb:
        return {"success": False, "error": "NOBRAINR_URL not configured"}

    async with httpx.AsyncClient(timeout=15) as h:
        resp = await h.post(
            f"{nb}/tools/memory_search",
            json={"query": query, "tags": tags or ["pdf"], "limit": limit},
        )
        resp.raise_for_status()
        return {"success": True, "results": resp.json()}
