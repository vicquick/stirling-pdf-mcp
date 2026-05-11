"""Composite — Archive-to-PDF/A workflow.

OCR → compress → strip metadata → convert to PDF/A-1b/2b/3b.

The "make this PDF last 30 years" composite. Used for records management,
government archives, legal evidence preservation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.archive")


@mcp.tool()
async def archive_to_pdfa(
    input_file: str,
    pdfa_level: Literal["pdfa-1b", "pdfa-2b", "pdfa-3b"] = "pdfa-2b",
    ocr: bool = True,
    ocr_language: str = "eng",
    compress: bool = True,
    compress_level: int = 5,
    strip_metadata: bool = False,
    keep_metadata: dict[str, str] | None = None,
) -> dict:
    """Archive a PDF for long-term preservation.

    Workflow:
        1. OCR (if `ocr=True`) — scanned PDFs in PDF/A need searchable text
           for accessibility-compliant archives
        2. Compress (if `compress=True`) — image-heavy archives benefit
        3. Strip / preserve metadata
        4. Convert to PDF/A

    Args:
        pdfa_level:
            - `pdfa-1b` — most conservative, widest tool support, no transparency
            - `pdfa-2b` — modern default, allows JPEG2000 compression
            - `pdfa-3b` — allows attachments (embed source files)
        ocr: OCR before archiving (recommended)
        compress: compress images
        compress_level: 1-9 (5 balanced)
        strip_metadata: scrub author/title/etc — useful for anonymous archives
        keep_metadata: dict of metadata fields to *set* (overrides strip).
            Common: `{"title": "Annual Report 2025", "subject": "Q4", "keywords": "..."}`

    Returns:
        Archival PDF/A with `endpoints_chained` for audit.
    """
    client = get_client()
    work_file = Path(input_file)
    chained: list[str] = []

    if ocr:
        result = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[work_file],
            form_data={
                "languages": [ocr_language],
                "ocrType": "skip-text",
                "deskew": True,
                "clean": True,
            },
            output_name_hint="archive-ocr",
        )
        if result.get("success"):
            work_file = Path(result["output_path"])
            chained.append("ocr-pdf")

    if compress:
        result = await client.post_form(
            "/api/v1/misc/compress-pdf",
            input_files=[work_file],
            form_data={"optimizeLevel": compress_level},
            output_name_hint="archive-compressed",
        )
        if result.get("success"):
            work_file = Path(result["output_path"])
            chained.append("compress-pdf")

    if strip_metadata or keep_metadata:
        result = await client.post_form(
            "/api/v1/misc/update-metadata",
            input_files=[work_file],
            form_data={
                "deleteAll": strip_metadata,
                **{k: v for k, v in (keep_metadata or {}).items()},
            },
            output_name_hint="archive-metadata",
        )
        if result.get("success"):
            work_file = Path(result["output_path"])
            chained.append("update-metadata")

    result = await client.post_form(
        "/api/v1/convert/pdf/pdfa",
        input_files=[work_file],
        form_data={"outputFormat": pdfa_level},
        output_name_hint=f"archive-{pdfa_level}",
    )
    if not result.get("success"):
        return {"success": False, "stage": "pdfa-convert", "endpoints_chained": chained, **result}
    work_file = Path(result["output_path"])
    chained.append("pdf-to-pdfa")

    return {
        "success": True,
        "output_path": str(work_file),
        "size_bytes": work_file.stat().st_size,
        "pdfa_level": pdfa_level,
        "endpoints_chained": chained,
    }
