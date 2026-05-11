"""Composite — pdf_to_audio.

OCR a PDF, extract text, send to a TTS service, return an audio file.
Cross-MCP: uses the existing TTS stack on bimavo (Edge TTS, Chatterbox,
or speaches — whichever is configured via TTS_ENDPOINT env var).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.audio")


@mcp.tool()
async def pdf_to_audio(
    input_file: str,
    voice: str = "en-US-AriaNeural",
    ocr_language: str = "eng",
    rate: str = "+0%",
    max_chars: int = 50000,
) -> dict:
    """Turn a PDF into a spoken-word audio file (MP3).

    Pipeline:
        1. OCR (skip if PDF already has text)
        2. Extract text
        3. POST text to TTS_ENDPOINT (defaults to local Edge TTS shim)
        4. Save MP3 to OUTPUT_DIR

    Configure the TTS backend via env var ``TTS_ENDPOINT`` — defaults to
    ``http://speaches:8000/v1/audio/speech`` (OpenAI-compatible). Other
    options on bimavo:

      - Edge TTS (free, cloud, very high quality):
        ``TTS_ENDPOINT=http://edge-tts:5050/v1/audio/speech``
      - Chatterbox (self-hosted, voice cloning):
        ``TTS_ENDPOINT=http://chatterbox:8123/v1/audio/speech``

    Args:
        voice: TTS voice ID (depends on backend)
        ocr_language: OCR language ISO code
        rate: speech-rate adjustment, e.g. ``"+10%"``, ``"-20%"``
        max_chars: cap to avoid runaway TTS jobs

    Returns: `{success, output_path (.mp3), text_length, voice}`
    """
    tts_url = os.environ.get(
        "TTS_ENDPOINT",
        "http://speaches:8000/v1/audio/speech",
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
            "clean": True,
        },
        output_name_hint="audio-ocr",
    )
    if ocr.get("success"):
        work = Path(ocr["output_path"])

    txt = await client.post_form(
        "/api/v1/convert/pdf/text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="audio-text",
    )
    if not txt.get("success") or not txt.get("output_path"):
        return {"success": False, "stage": "extract-text", **txt}

    text = Path(txt["output_path"]).read_text(errors="ignore")[:max_chars]
    if not text.strip():
        return {"success": False, "error": "no text extracted from PDF"}

    mp3_path = SETTINGS.output_dir / f"audio-{Path(input_file).stem}.mp3"
    async with httpx.AsyncClient(timeout=600.0) as h:
        try:
            r = await h.post(
                tts_url,
                json={
                    "model": "tts-1",
                    "voice": voice,
                    "input": text,
                    "response_format": "mp3",
                    "speed": 1.0,
                },
            )
        except httpx.HTTPError as e:
            return {"success": False, "error": f"TTS endpoint unreachable: {e}", "tts_url": tts_url}

    if r.status_code >= 400:
        return {
            "success": False,
            "error": f"TTS returned {r.status_code}: {r.text[:300]}",
            "tts_url": tts_url,
        }

    mp3_path.write_bytes(r.content)
    return {
        "success": True,
        "output_path": str(mp3_path),
        "size_bytes": mp3_path.stat().st_size,
        "text_length": len(text),
        "voice": voice,
        "tts_url": tts_url,
        "endpoints_chained": [
            "ocr-pdf",
            "extract-text",
            "tts (external)",
        ],
    }
