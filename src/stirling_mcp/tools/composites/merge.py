"""Composite — Merge with TOC.

Merge several PDFs, detect or generate bookmarks, add page numbers.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp


@mcp.tool()
async def merge_with_toc(
    input_files: list[str],
    add_page_numbers: bool = True,
    page_numbers_position: int = 5,
    sort_type: str = "orderProvided",
) -> dict:
    """Merge PDFs, then add page numbers (Stirling can't auto-generate TOC
    bookmarks from headings yet — that's a v0.3 enhancement using the AI
    comment agent to detect chapter starts).

    Use for: book publishing, report compilation, archive bundles.
    """
    client = get_client()
    chained: list[str] = []

    merge = await client.post_form(
        "/api/v1/general/merge-pdfs",
        input_files=[Path(p) for p in input_files],
        form_data={"sortType": sort_type},
        output_name_hint="merged",
    )
    if not merge.get("success"):
        return {"success": False, "stage": "merge", **merge}
    work_file = Path(merge["output_path"])
    chained.append("merge-pdfs")

    if add_page_numbers:
        nums = await client.post_form(
            "/api/v1/misc/add-page-numbers",
            input_files=[work_file],
            form_data={
                "position": page_numbers_position,
                "startingNumber": 1,
                "pagesToNumber": "all",
                "customMargin": "small",
                "customText": "Page {n} of {total}",
                "fontSize": 10,
                "fontType": "Helvetica",
            },
            output_name_hint="merged-numbered",
        )
        if nums.get("success"):
            work_file = Path(nums["output_path"])
            chained.append("add-page-numbers")

    return {
        "success": True,
        "output_path": str(work_file),
        "size_bytes": work_file.stat().st_size,
        "input_count": len(input_files),
        "endpoints_chained": chained,
    }
