"""Composite — pdf_translate.

Cross-MCP: OCR a PDF, send extracted text through your local LLM
(llama-server / llama-swap), receive translated text, regenerate as PDF.

This is a v1 approximation — full inline-on-page translation (preserving
layout) requires positional text extraction + per-region replacement which
Stirling doesn't yet expose. We instead produce a CLEAN translated PDF
(text-only, no layout fidelity) which is fine for translations of dense
text content (contracts, articles, books) and useless for posters or
infographics.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.translate")


@mcp.tool()
async def pdf_translate(
    input_file: str,
    target_language: str = "English",
    source_language: str = "auto",
    ocr_language: str = "eng",
    llm_endpoint: str | None = None,
    llm_model: str = "qwen3.5-35b",
    chunk_chars: int = 8000,
) -> dict:
    """Translate a PDF's text content via a local LLM, output a Markdown→PDF.

    Pipeline:
        1. OCR (skip if PDF has text)
        2. Extract text
        3. Chunk text into ~8000-char passes
        4. POST each chunk to LLM endpoint with a translation prompt
        5. Concatenate chunks
        6. Render to PDF via Stirling's /convert/markdown/pdf

    Configure LLM via ``LLAMA_ENDPOINT`` env var, defaults to bimavo's
    internal llama-swap router. Pass ``target_language`` as a natural-
    language string ("German", "Spanish", "Mandarin").

    Args:
        target_language: language to translate into (free text)
        source_language: source language hint (or 'auto' for LLM detection)
        ocr_language: ISO code for OCR pass
        llm_endpoint: override the default LLM endpoint
        llm_model: model name (depends on what your endpoint serves)
        chunk_chars: chars per translation pass (smaller = better quality)

    Returns: `{success, output_path (.pdf), source_chars, translated_chars}`
    """
    endpoint = llm_endpoint or os.environ.get(
        "LLAMA_ENDPOINT",
        "http://llama-swap:8080/v1/chat/completions",
    )

    client = get_client()
    work = Path(input_file)

    ocr = await client.post_form(
        "/api/v1/misc/ocr-pdf",
        input_files=[work],
        form_data={
            "languages": [ocr_language],
            "ocrType": "skip-text",
            "deskew": True,
        },
        output_name_hint="translate-ocr",
    )
    if ocr.get("success"):
        work = Path(ocr["output_path"])

    txt = await client.post_form(
        "/api/v1/misc/extract-text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="translate-text",
    )
    if not txt.get("success") or not txt.get("output_path"):
        return {"success": False, "stage": "extract-text", **txt}

    text = Path(txt["output_path"]).read_text(errors="ignore")
    if not text.strip():
        return {"success": False, "error": "no text extracted"}

    chunks = [text[i : i + chunk_chars] for i in range(0, len(text), chunk_chars)]
    log.info("Translating %d chunks via %s", len(chunks), endpoint)

    translated_parts: list[str] = []
    async with httpx.AsyncClient(timeout=300.0) as h:
        for idx, chunk in enumerate(chunks, 1):
            prompt = (
                f"Translate the following text from {source_language} to {target_language}. "
                "Preserve paragraph structure and Markdown formatting if any. "
                "Output ONLY the translation — no commentary, no source text.\n\n"
                f"---\n{chunk}\n---"
            )
            try:
                r = await h.post(
                    endpoint,
                    json={
                        "model": llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": int(chunk_chars * 1.3),
                    },
                )
            except httpx.HTTPError as e:
                return {
                    "success": False,
                    "error": f"LLM unreachable: {e}",
                    "endpoint": endpoint,
                }
            if r.status_code >= 400:
                return {
                    "success": False,
                    "error": f"LLM {r.status_code}: {r.text[:300]}",
                    "endpoint": endpoint,
                }
            data = r.json()
            content = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            translated_parts.append(content)
            log.debug("chunk %d/%d translated (%d chars)", idx, len(chunks), len(content))

    translated_text = "\n\n".join(translated_parts)
    md_path = SETTINGS.output_dir / f"translated-{Path(input_file).stem}.md"
    md_path.write_text(translated_text, encoding="utf-8")

    pdf = await client.post_form(
        "/api/v1/convert/markdown/pdf",
        input_files=[md_path],
        output_name_hint=f"translated-{target_language[:8]}",
    )

    return {
        "success": pdf.get("success", False),
        "output_path": pdf.get("output_path"),
        "source_chars": len(text),
        "translated_chars": len(translated_text),
        "target_language": target_language,
        "chunk_count": len(chunks),
        "endpoints_chained": [
            "ocr-pdf",
            "extract-text",
            f"LLM × {len(chunks)} chunks",
            "markdown/pdf",
        ],
    }
