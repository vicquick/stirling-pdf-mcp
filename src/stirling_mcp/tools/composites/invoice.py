"""Composite — Invoice prepare workflow.

Scan/PDF → OCR (if needed) → text extract → regex parse for date/vendor/total
→ rename by pattern → optional archive to PDF/A.

This is the daily-driver for AP clerks and finance ops.
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.invoice")


# Regexes — best-effort. For high-accuracy use Stirling's pdf-comment-agent
# with a structured-output prompt instead.
DATE_PATTERNS = [
    r"\b(?:Invoice\s*Date|Date|Datum|Rechnungsdatum)[:\s]*([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})",
    r"\b([0-9]{4}-[0-9]{2}-[0-9]{2})\b",
    r"\b([0-9]{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{4})\b",
]

VENDOR_PATTERNS = [
    r"(?:From|Bill from|Vendor|Lieferant)[:\s]+([A-Z][A-Za-z0-9 .&,\-]{2,60})",
    # First line that looks like a company name (heuristic — first non-empty
    # line containing a capital letter and not obviously a date)
]

TOTAL_PATTERNS = [
    r"(?:Total|Amount Due|Gesamtbetrag|Summe)[:\s]*(?:USD|EUR|€|\$|£|GBP)?\s*([0-9]{1,3}(?:[,.][0-9]{3})*(?:[.,][0-9]{2}))",
    r"(?:USD|EUR|€|\$|£|GBP)\s*([0-9]{1,3}(?:[,.][0-9]{3})*(?:[.,][0-9]{2}))",
]


def _extract_first_match(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def _safe_filename(s: str) -> str:
    out = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return out[:80] or "invoice"


@mcp.tool()
async def invoice_prepare(
    input_file: str,
    ocr_first: bool = True,
    ocr_language: str = "eng",
    name_pattern: str = "{date}_{vendor}_{total}",
    archive_pdfa: bool = False,
    output_subdir: str = "invoices",
) -> dict:
    """One-shot invoice processing: clean → OCR → extract → rename → optional archive.

    Workflow:
        1. OCR the PDF (if `ocr_first=True`) — needed for most scanned invoices
        2. Extract plain text
        3. Regex-parse date, vendor, total
        4. Rename output PDF via `name_pattern` (placeholders: `{date}`, `{vendor}`, `{total}`)
        5. Optionally convert to PDF/A-2b for long-term archive
        6. Move into OUTPUT_DIR / output_subdir

    Args:
        input_file: path to PDF (or scanned image converted to PDF)
        ocr_first: run OCR before extraction (recommended for scans)
        ocr_language: OCR language code (eng/deu/fra/...)
        name_pattern: template with `{date}`, `{vendor}`, `{total}` placeholders.
            Falls back to "unknown" when a field can't be detected.
        archive_pdfa: also produce a PDF/A-2b archival copy
        output_subdir: subfolder under OUTPUT_DIR for the named output

    Returns:
        dict with `output_path`, parsed `metadata` (date/vendor/total/raw_text_snippet),
        and `endpoints_chained`.
    """
    client = get_client()
    work_file = Path(input_file)
    chained: list[str] = []

    # 1. OCR
    if ocr_first:
        ocr = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[work_file],
            form_data={
                "languages": [ocr_language],
                "ocrType": "skip-text",
                "deskew": True,
                "clean": True,
            },
            output_name_hint="ocr-invoice",
        )
        if ocr.get("success"):
            work_file = Path(ocr["output_path"])
            chained.append("ocr-pdf")

    # 2. Extract text
    txt_result = await client.post_form(
        "/api/v1/convert/pdf/text",
        input_files=[work_file],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="invoice-text",
    )
    chained.append("extract-text")

    text = ""
    if txt_result.get("success") and txt_result.get("output_path"):
        txt_path = Path(txt_result["output_path"])
        if txt_path.exists():
            text = txt_path.read_text(errors="ignore")

    # 3. Parse
    parsed = {
        "date": _extract_first_match(text, DATE_PATTERNS),
        "vendor": _extract_first_match(text, VENDOR_PATTERNS),
        "total": _extract_first_match(text, TOTAL_PATTERNS),
        "raw_text_snippet": text[:500] if text else None,
    }

    # 4. Rename
    final_name = name_pattern.format(
        date=_safe_filename(parsed["date"] or "unknown"),
        vendor=_safe_filename(parsed["vendor"] or "unknown"),
        total=_safe_filename(parsed["total"] or "unknown"),
    )
    target_dir = SETTINGS.output_dir / output_subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    final_path = target_dir / f"{final_name}.pdf"
    shutil.copy2(work_file, final_path)
    chained.append("rename")

    # 5. PDF/A archive
    archive_path: str | None = None
    if archive_pdfa:
        pdfa = await client.post_form(
            "/api/v1/convert/pdf/pdfa",
            input_files=[final_path],
            form_data={"outputFormat": "pdfa-2b"},
            output_name_hint=f"{final_name}-pdfa",
        )
        if pdfa.get("success"):
            archive_path = pdfa["output_path"]
            chained.append("pdf-to-pdfa")

    return {
        "success": True,
        "output_path": str(final_path),
        "archive_path": archive_path,
        "metadata": parsed,
        "endpoints_chained": chained,
        "size_bytes": final_path.stat().st_size,
    }
