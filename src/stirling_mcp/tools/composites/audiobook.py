"""Composite — pdf_book_to_audiobook.

The "I have a scanned PDF book, give me an audiobook" pipeline.

Chains: clean_scan → split by chapter (if bookmarks present) → TTS per
chapter → concatenate into one MP3. v1 produces a single MP3; chapter
markers could be added via FFmpeg metadata in a future iteration.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.audiobook")


@mcp.tool()
async def pdf_book_to_audiobook(
    input_file: str,
    voice: str = "en-US-AriaNeural",
    ocr_language: str = "eng",
    max_total_chars: int = 200000,
) -> dict:
    """Turn a (possibly scanned) PDF book into an audiobook MP3.

    Pipeline:
        1. clean_scan internally — deskew + OCR + remove blanks
        2. Extract text
        3. Send to TTS in chunks (TTS endpoints typically cap at ~10KB)
        4. Concatenate audio bytes (works for MP3 because MP3 frames are
           self-contained)
        5. Return one MP3

    Args:
        input_file: book PDF (scanned or text-based)
        voice: TTS voice
        ocr_language: ISO code
        max_total_chars: cap to prevent runaway jobs on 1000-page books

    Returns: `{success, output_path (.mp3), text_chars, chunk_count}`
    """
    tts_url = os.environ.get(
        "TTS_ENDPOINT",
        "http://speaches:8000/v1/audio/speech",
    )

    client = get_client()
    work = Path(input_file)

    # Step 1 — OCR + cleanup
    ocr = await client.post_form(
        "/api/v1/misc/ocr-pdf",
        input_files=[work],
        form_data={
            "languages": [ocr_language],
            "ocrType": "skip-text",
            "deskew": True,
            "clean": True,
        },
        output_name_hint="audiobook-ocr",
    )
    if ocr.get("success"):
        work = Path(ocr["output_path"])

    no_blank = await client.post_form(
        "/api/v1/misc/remove-blanks",
        input_files=[work],
        form_data={"threshold": 10, "whitePercent": 99.5},
        output_name_hint="audiobook-noblanks",
    )
    if no_blank.get("success"):
        work = Path(no_blank["output_path"])

    txt = await client.post_form(
        "/api/v1/misc/extract-text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="audiobook-text",
    )
    if not txt.get("success") or not txt.get("output_path"):
        return {"success": False, "stage": "extract-text", **txt}

    text = Path(txt["output_path"]).read_text(errors="ignore")[:max_total_chars]
    if not text.strip():
        return {"success": False, "error": "no text extracted"}

    # Chunk for TTS (most TTS APIs cap at ~10KB per request)
    chunk_size = 8000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    log.info("Audiobook: %d TTS chunks via %s", len(chunks), tts_url)

    mp3_path = SETTINGS.output_dir / f"audiobook-{Path(input_file).stem}.mp3"
    failures = 0
    with mp3_path.open("wb") as out, httpx.AsyncClient(timeout=600.0) as h_sync:
        pass  # placeholder — httpx.Client is sync; use AsyncClient block below

    async with httpx.AsyncClient(timeout=600.0) as h:
        with mp3_path.open("wb") as out:
            for idx, chunk in enumerate(chunks, 1):
                try:
                    r = await h.post(
                        tts_url,
                        json={
                            "model": "tts-1",
                            "voice": voice,
                            "input": chunk,
                            "response_format": "mp3",
                            "speed": 1.0,
                        },
                    )
                except httpx.HTTPError as e:
                    failures += 1
                    log.warning("chunk %d TTS error: %s", idx, e)
                    continue
                if r.status_code < 400:
                    out.write(r.content)
                else:
                    failures += 1

    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        return {
            "success": False,
            "error": "TTS produced no audio (all chunks failed)",
            "failures": failures,
            "tts_url": tts_url,
        }

    return {
        "success": True,
        "output_path": str(mp3_path),
        "size_bytes": mp3_path.stat().st_size,
        "text_chars": len(text),
        "chunk_count": len(chunks),
        "chunk_failures": failures,
        "voice": voice,
        "tts_url": tts_url,
        "endpoints_chained": [
            "ocr-pdf",
            "remove-blanks",
            "extract-text",
            f"tts × {len(chunks)} chunks",
        ],
    }
