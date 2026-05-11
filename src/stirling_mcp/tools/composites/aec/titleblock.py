"""AEC composite — title-block OCR → metadata + smart rename."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.aec.titleblock")


SHEET_RE = re.compile(r"\b([A-Z]{1,2}[-_]?\d{2,4}(?:\.\d+)?)\b")
SCALE_RE = re.compile(r"\b(?:scale|maßstab|échelle)\s*[:=]?\s*([0-9]+\s*[:=]\s*[0-9]+)\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b")
PROJECT_RE = re.compile(r"(?:Project|Projekt|Projet)[:\s]+([A-Z][A-Za-z0-9 .,&\-]{3,60})")


@mcp.tool()
async def aec_titleblock_to_metadata(
    input_file: str,
    ocr: bool = True,
    rename: bool = True,
    output_subdir: str = "aec/titleblock",
) -> dict:
    """Read AEC drawing title-block via OCR, write extracted fields into PDF
    metadata, optionally rename file.

    Workflow:
        1. OCR (if `ocr=True`)
        2. Extract text
        3. Regex for sheet number, scale, date, project
        4. Set PDF metadata
        5. Rename file as `{sheet}_{project_slug}.pdf` if `rename=True`

    Args:
        ocr: run OCR before extraction
        rename: rename output file
        output_subdir: target folder for renamed output
    """
    client = get_client()
    work = Path(input_file)
    chained: list[str] = []

    if ocr:
        ocr_res = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[work],
            form_data={"languages": ["eng"], "ocrType": "skip-text"},
            output_name_hint="aec-tb-ocr",
        )
        if ocr_res.get("success"):
            work = Path(ocr_res["output_path"])
            chained.append("ocr-pdf")

    txt = await client.post_form(
        "/api/v1/convert/pdf/text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="aec-tb-text",
    )
    chained.append("extract-text")
    text = ""
    if txt.get("success"):
        text = Path(txt["output_path"]).read_text(errors="ignore")[:5000]

    sheet = (SHEET_RE.search(text) or [None, None])[1] if SHEET_RE.search(text) else None
    scale = (SCALE_RE.search(text) or [None, None])[1] if SCALE_RE.search(text) else None
    date = (DATE_RE.search(text) or [None, None])[1] if DATE_RE.search(text) else None
    project = (PROJECT_RE.search(text) or [None, None])[1] if PROJECT_RE.search(text) else None

    # Write metadata
    meta_set = await client.post_form(
        "/api/v1/misc/update-metadata",
        input_files=[work],
        form_data={
            "title": f"{sheet} {project}".strip() if sheet or project else None,
            "subject": f"Scale {scale}" if scale else None,
            "creator": "AEC drawing set",
            "keywords": f"sheet:{sheet or 'unknown'}, project:{project or 'unknown'}",
        },
        output_name_hint="aec-tb-meta",
    )
    if meta_set.get("success"):
        work = Path(meta_set["output_path"])
        chained.append("update-metadata")

    final_path = work
    if rename and sheet:
        target_dir = SETTINGS.output_dir / output_subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        project_slug = re.sub(r"[^A-Za-z0-9]+", "_", project or "untitled")[:40].strip("_")
        final_path = target_dir / f"{sheet}_{project_slug}.pdf"
        work.rename(final_path)
        chained.append("rename")

    return {
        "success": True,
        "output_path": str(final_path),
        "metadata": {"sheet": sheet, "scale": scale, "date": date, "project": project},
        "endpoints_chained": chained,
    }
