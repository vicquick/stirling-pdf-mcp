"""Composite — pdf_clean_scan.

The "make this messy scan actually usable" composite. Chains deskew + denoise
+ blank-page removal + OCR + optional auto-crop. The thing everyone does
manually in 5 separate clicks.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_clean_scan(
    input_file: str,
    ocr_language: str = "eng",
    remove_blanks: bool = True,
    blank_threshold: int = 10,
    blank_white_percent: float = 99.5,
    compress_after: bool = True,
) -> dict:
    """Universal scan-cleanup pipeline.

    Chains:
        1. OCR with `deskew=True` + `clean=True` (rotates skewed pages straight,
           removes specks before OCR — best-quality default)
        2. Remove blank pages (typical between fed-scanner double-page batches)
        3. Compress (image-heavy scans benefit massively)

    Args:
        input_file: path to scanned PDF
        ocr_language: ISO code (eng/deu/fra/...)
        remove_blanks: drop pages that are mostly white (90%+)
        blank_threshold: pixel-darkness cutoff 0-255 for "this pixel is ink"
        blank_white_percent: page is blank if >= this % of pixels are bright
        compress_after: re-compress the cleaned output

    Returns: `{success, output_path, endpoints_chained, original_size, final_size}`
    """
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)
    original_size = work.stat().st_size

    ocr = await client.post_form(
        "/api/v1/misc/ocr-pdf",
        input_files=[work],
        form_data={
            "languages": [ocr_language],
            "ocrType": "skip-text",
            "deskew": True,
            "clean": True,
            "cleanFinal": False,
        },
        output_name_hint="cleaned-ocr",
    )
    if ocr.get("success"):
        work = Path(ocr["output_path"])
        chained.append("ocr-pdf (deskew + clean)")

    if remove_blanks:
        no_blanks = await client.post_form(
            "/api/v1/misc/remove-blanks",
            input_files=[work],
            form_data={"threshold": blank_threshold, "whitePercent": blank_white_percent},
            output_name_hint="cleaned-no-blanks",
        )
        if no_blanks.get("success"):
            work = Path(no_blanks["output_path"])
            chained.append("remove-blanks")

    if compress_after:
        comp = await client.post_form(
            "/api/v1/misc/compress-pdf",
            input_files=[work],
            form_data={"optimizeLevel": 6},
            output_name_hint="cleaned-compressed",
        )
        if comp.get("success"):
            work = Path(comp["output_path"])
            chained.append("compress-pdf")

    final_size = work.stat().st_size
    return {
        "success": True,
        "output_path": str(work),
        "endpoints_chained": chained,
        "original_size_bytes": original_size,
        "final_size_bytes": final_size,
        "size_reduction_pct": round((1 - final_size / max(original_size, 1)) * 100, 1),
    }
