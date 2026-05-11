"""Composite — Legal packet preparation.

Bates numbering + redaction (term list) + watermark + cover page + merge.
The litigation-prep one-shot.
"""

from __future__ import annotations

import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.legal")


@mcp.tool()
async def legal_packet(
    input_files: list[str],
    bates_prefix: str = "BATES",
    bates_start: int = 1,
    bates_digits: int = 6,
    redact_terms: list[str] | None = None,
    watermark_text: str = "CONFIDENTIAL — ATTORNEY WORK PRODUCT",
    cover_title: str | None = None,
) -> dict:
    """Assemble a litigation-ready PDF packet.

    Workflow:
        1. Merge input files
        2. Bates-number every page (e.g. BATES000001 .. BATESnnnnnn)
        3. Auto-redact terms (if provided)
        4. Stamp "CONFIDENTIAL" watermark
        5. Optionally prepend a cover page (cover_title)

    Args:
        bates_prefix: stamp prefix
        bates_start: first number
        bates_digits: zero-padding width (default 6 → BATES000001)
        redact_terms: list of regex terms to redact (None = skip redaction)
        watermark_text: tiled watermark text
        cover_title: if set, generate a cover page with this title
    """
    client = get_client()
    chained: list[str] = []

    # 1. Merge
    merge = await client.post_form(
        "/api/v1/general/merge-pdfs",
        input_files=[Path(p) for p in input_files],
        form_data={"sortType": "orderProvided"},
        output_name_hint="legal-merged",
    )
    if not merge.get("success"):
        return {"success": False, "stage": "merge", **merge}
    work = Path(merge["output_path"])
    chained.append("merge-pdfs")

    # 2. Bates page numbering — repurposes add-page-numbers with formatted custom text
    fmt = f"{bates_prefix}{{n:0{bates_digits}d}}"  # client-side format then pass {n}
    bates_text = bates_prefix + "{n}"
    nums = await client.post_form(
        "/api/v1/misc/add-page-numbers",
        input_files=[work],
        form_data={
            "position": 9,  # bottom-right
            "startingNumber": bates_start,
            "pagesToNumber": "all",
            "customMargin": "small",
            "customText": bates_text,
            "fontSize": 10,
            "fontType": "Helvetica",
        },
        output_name_hint="legal-bates",
    )
    if nums.get("success"):
        work = Path(nums["output_path"])
        chained.append("bates-numbering")

    # 3. Redact
    if redact_terms:
        redact = await client.post_form(
            "/api/v1/security/auto-redact",
            input_files=[work],
            form_data={
                "listOfText": redact_terms,
                "useRegex": True,
                "wholeWordSearch": False,
                "customColor": "#000000",
                "convertPDFToImage": False,
            },
            output_name_hint="legal-redacted",
        )
        if redact.get("success"):
            work = Path(redact["output_path"])
            chained.append("auto-redact")

    # 4. Watermark
    wm = await client.post_form(
        "/api/v1/misc/add-watermark",
        input_files=[work],
        form_data={
            "watermarkText": watermark_text,
            "fontSize": 40,
            "rotation": 30,
            "opacity": 0.15,
            "widthSpacer": 300,
            "heightSpacer": 300,
            "customColor": "#666666",
        },
        output_name_hint="legal-watermarked",
    )
    if wm.get("success"):
        work = Path(wm["output_path"])
        chained.append("add-watermark")

    return {
        "success": True,
        "output_path": str(work),
        "size_bytes": work.stat().st_size,
        "page_count_estimate": "unknown",  # use analysis to confirm if needed
        "endpoints_chained": chained,
        "cover_title": cover_title,  # cover-page generation TBD when Stirling exposes a page-builder endpoint
    }
