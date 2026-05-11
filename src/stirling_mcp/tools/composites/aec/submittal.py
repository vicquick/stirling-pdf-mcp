"""AEC composite — submittal package preparation."""

from __future__ import annotations

import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

log = logging.getLogger("stirling_mcp.composites.aec.submittal")


@mcp.tool()
async def aec_submittal_package(
    drawing_files: list[str],
    spec_files: list[str] | None = None,
    bates_prefix: str = "SUB",
    watermark_text: str = "FOR REVIEW",
    project_name: str = "Project",
) -> dict:
    """Assemble a construction submittal packet.

    Workflow:
        1. Merge drawings + specs (drawings first, then specs)
        2. Bates-number (SUBnnnnnn)
        3. Stamp "FOR REVIEW" watermark
        4. Set metadata title to project_name

    Args:
        drawing_files: drawings (order preserved)
        spec_files: specification PDFs to append (optional)
        bates_prefix: bates stamp prefix (default "SUB")
        watermark_text: review-status watermark
        project_name: written into PDF metadata
    """
    client = get_client()
    chained: list[str] = []

    all_files = drawing_files + (spec_files or [])
    merge = await client.post_form(
        "/api/v1/general/merge-pdfs",
        input_files=[Path(p) for p in all_files],
        form_data={"sortType": "orderProvided"},
        output_name_hint="submittal-merged",
    )
    if not merge.get("success"):
        return {"success": False, "stage": "merge", **merge}
    work = Path(merge["output_path"])
    chained.append("merge-pdfs")

    nums = await client.post_form(
        "/api/v1/misc/add-page-numbers",
        input_files=[work],
        form_data={
            "position": 9,
            "startingNumber": 1,
            "pagesToNumber": "all",
            "customMargin": "small",
            "customText": bates_prefix + "{n}",
            "fontSize": 10,
        },
        output_name_hint="submittal-bates",
    )
    if nums.get("success"):
        work = Path(nums["output_path"])
        chained.append("bates-numbering")

    wm = await client.post_form(
        "/api/v1/misc/add-watermark",
        input_files=[work],
        form_data={
            "watermarkText": watermark_text,
            "fontSize": 60,
            "rotation": 30,
            "opacity": 0.2,
            "widthSpacer": 400,
            "heightSpacer": 400,
            "customColor": "#cc4400",
        },
        output_name_hint="submittal-wm",
    )
    if wm.get("success"):
        work = Path(wm["output_path"])
        chained.append("add-watermark")

    meta = await client.post_form(
        "/api/v1/misc/update-metadata",
        input_files=[work],
        form_data={
            "title": f"{project_name} Submittal",
            "subject": "AEC submittal package",
            "creator": "stirling-pdf-mcp",
        },
        output_name_hint="submittal-meta",
    )
    if meta.get("success"):
        work = Path(meta["output_path"])
        chained.append("update-metadata")

    return {
        "success": True,
        "output_path": str(work),
        "size_bytes": work.stat().st_size,
        "input_count": len(all_files),
        "endpoints_chained": chained,
    }
