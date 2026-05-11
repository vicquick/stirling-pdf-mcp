"""Composite — extract_table_data.

Multi-page table extraction. Stirling has /convert/pdf/csv per single page —
we OCR if needed, then iterate pages, then optionally combine into one CSV.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp


@mcp.tool()
async def extract_table_data(
    input_file: str,
    page_range: str = "all",
    ocr_first: bool = True,
    ocr_language: str = "eng",
    combine: bool = True,
) -> dict:
    """Extract tabular data from a PDF as CSV.

    Stirling's /convert/pdf/csv works one page at a time. This composite:
        1. OCR (if needed and `ocr_first`) — needed for scanned tables
        2. Detect page count
        3. Iterate the requested page range, extract per-page CSV
        4. Optionally combine pages into one CSV with sheet markers

    Args:
        input_file: PDF
        page_range: "all" | "1-5,7" | "3" — pages to extract from
        ocr_first: run OCR before extraction (recommended for scans)
        ocr_language: ISO code
        combine: produce one merged CSV (vs. one CSV per page in a ZIP)

    Returns: `{success, output_path, page_count_extracted}`
    """
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)

    if ocr_first:
        ocr = await client.post_form(
            "/api/v1/misc/ocr-pdf",
            input_files=[work],
            form_data={
                "languages": [ocr_language],
                "ocrType": "skip-text",
                "deskew": True,
                "clean": True,
            },
            output_name_hint="table-ocr",
        )
        if ocr.get("success"):
            work = Path(ocr["output_path"])
            chained.append("ocr-pdf")

    # Get page count via analysis
    dims = await client.post_form(
        "/api/v1/analysis/page-dimensions",
        input_files=[work],
        output_suffix=".json",
    )
    chained.append("analysis/page-dimensions")
    if dims.get("success") and dims.get("json_body"):
        body = dims["json_body"]
        # body shape: list of page dicts OR a wrapper — try both
        if isinstance(body, list):
            page_count = len(body)
        elif isinstance(body, dict):
            page_count = len(body.get("pages") or body.get("pageDimensions") or [])
        else:
            page_count = 1
    else:
        page_count = 1

    # Parse page_range
    pages: list[int] = []
    if page_range == "all":
        pages = list(range(1, page_count + 1))
    else:
        for part in page_range.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                pages.extend(range(int(a), int(b) + 1))
            else:
                pages.append(int(part))
    pages = [p for p in pages if 1 <= p <= page_count]

    # Extract per-page CSV
    csv_paths: list[Path] = []
    for p in pages:
        csv = await client.post_form(
            "/api/v1/convert/pdf/csv",
            input_files=[work],
            form_data={"pageId": p},
            output_suffix=".csv",
            output_name_hint=f"table-p{p}",
        )
        if csv.get("success") and csv.get("output_path"):
            csv_paths.append(Path(csv["output_path"]))

    chained.append(f"convert/pdf/csv × {len(csv_paths)}")

    if not csv_paths:
        return {"success": False, "error": "no table CSV extracted", "endpoints_chained": chained}

    if combine and len(csv_paths) > 1:
        merged = SETTINGS.output_dir / f"tables-combined-{Path(input_file).stem}.csv"
        with merged.open("w", encoding="utf-8") as out:
            for p, csv_p in zip(pages, csv_paths):
                out.write(f"# --- page {p} ---\n")
                out.write(csv_p.read_text(errors="ignore"))
                out.write("\n")
        chained.append("combine (client-side)")
        return {
            "success": True,
            "output_path": str(merged),
            "page_count_extracted": len(csv_paths),
            "endpoints_chained": chained,
        }

    return {
        "success": True,
        "output_path": str(csv_paths[0]) if len(csv_paths) == 1 else None,
        "csv_paths": [str(p) for p in csv_paths],
        "page_count_extracted": len(csv_paths),
        "endpoints_chained": chained,
    }
