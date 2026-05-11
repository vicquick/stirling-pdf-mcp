"""Composite — expense_report.

Multi-receipt batch processing: scan/OCR each, regex-extract amount + date +
vendor, build a summary cover page, merge with originals.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.expense")

AMOUNT_RE = re.compile(
    r"(?:total|amount|paid|sum|gesamt|betrag)?[:\s]*"
    r"(?:USD|EUR|€|\$|£|GBP|CHF)?\s*"
    r"([0-9]{1,3}(?:[,.][0-9]{3})*(?:[.,][0-9]{2}))",
    flags=re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4})\b"
)
VENDOR_HEURISTIC = re.compile(r"^([A-Z][A-Za-z0-9 .&,'\-]{2,40})\s*$", re.MULTILINE)


@mcp.tool()
async def expense_report(
    receipts: list[str],
    period_label: str = "Expense Report",
    ocr_language: str = "eng",
    include_originals: bool = True,
) -> dict:
    """Process a batch of receipt PDFs into a single expense report.

    Workflow per receipt:
        1. OCR
        2. Extract text
        3. Regex-parse first amount, first date, first vendor-looking line
    Then:
        4. Build a summary table page (Markdown → PDF via Stirling)
        5. Optionally append all original receipts after the summary

    Args:
        receipts: list of paths to receipt PDFs (one receipt per file)
        period_label: title shown on the summary page (e.g. "Q2 2026 expenses")
        ocr_language: OCR language
        include_originals: append each receipt after the summary page

    Returns:
        dict with `summary` (parsed rows + total), `output_path` (final PDF)
    """
    client = get_client()
    parsed_rows: list[dict] = []
    ocr_outputs: list[Path] = []

    for rp_str in receipts:
        rp = Path(rp_str)
        if not rp.exists():
            parsed_rows.append({"file": str(rp), "error": "not_found"})
            continue
        ocr = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[rp],
            form_data={
                "languages": [ocr_language],
                "ocrType": "skip-text",
                "deskew": True,
                "clean": True,
            },
            output_name_hint=f"exp-ocr-{rp.stem}",
        )
        ocr_path = Path(ocr["output_path"]) if ocr.get("success") else rp
        ocr_outputs.append(ocr_path)

        txt = await client.post_form(
            "/api/v1/misc/extract-text",
            input_files=[ocr_path],
            form_data={"outputFormat": "txt"},
            output_suffix=".txt",
            output_name_hint=f"exp-text-{rp.stem}",
        )
        text = ""
        if txt.get("success") and txt.get("output_path"):
            text = Path(txt["output_path"]).read_text(errors="ignore")[:2000]

        amt = AMOUNT_RE.search(text)
        date = DATE_RE.search(text)
        vendor = VENDOR_HEURISTIC.search(text)
        parsed_rows.append(
            {
                "file": rp.name,
                "vendor": vendor.group(1).strip() if vendor else "unknown",
                "date": date.group(1) if date else "unknown",
                "amount": amt.group(1) if amt else "unknown",
            }
        )

    # Sum amounts where possible (best-effort, handles commas + periods)
    total = 0.0
    parseable = 0
    for r in parsed_rows:
        amt_str = r.get("amount") or ""
        clean = amt_str.replace(",", ".")
        # strip thousands-separators (heuristic — assumes last dot is decimal)
        if clean.count(".") > 1:
            parts = clean.split(".")
            clean = "".join(parts[:-1]) + "." + parts[-1]
        try:
            total += float(clean)
            parseable += 1
        except ValueError:
            pass

    # Build a Markdown summary, convert to PDF, prepend
    md = [
        f"# {period_label}",
        f"\nGenerated {datetime.utcnow().isoformat()}Z",
        "\n## Items\n",
        "| File | Vendor | Date | Amount |",
        "|------|--------|------|--------|",
    ]
    for r in parsed_rows:
        md.append(
            f"| {r.get('file')} | {r.get('vendor')} | {r.get('date')} | {r.get('amount')} |"
        )
    md.append(f"\n**Auto-summed total ({parseable}/{len(parsed_rows)} parseable):** {total:.2f}")
    md_path = SETTINGS.output_dir / f"expense-summary-{datetime.utcnow():%H%M%S}.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    summary_pdf = await client.post_form(
        "/api/v1/convert/markdown/pdf",
        input_files=[md_path],
        output_name_hint="expense-summary",
    )
    if not summary_pdf.get("success"):
        return {
            "success": False,
            "stage": "summary-render",
            "rows": parsed_rows,
            "total": total,
            **summary_pdf,
        }
    summary_path = Path(summary_pdf["output_path"])

    final = summary_path
    if include_originals and ocr_outputs:
        merge = await client.post_form(
            "/api/v1/general/merge-pdfs",
            input_files=[summary_path, *ocr_outputs],
            form_data={"sortType": "orderProvided"},
            output_name_hint="expense-report",
        )
        if merge.get("success"):
            final = Path(merge["output_path"])

    return {
        "success": True,
        "output_path": str(final),
        "summary": {
            "period": period_label,
            "row_count": len(parsed_rows),
            "parseable_amounts": parseable,
            "total": total,
            "rows": parsed_rows,
        },
        "endpoints_chained": [
            "ocr-pdf (per receipt)",
            "extract-text (per receipt)",
            "markdown/pdf (summary render)",
            "merge-pdfs (summary + originals)",
        ],
    }
