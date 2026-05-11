"""Layer-1 raw wrappers — Stirling `Filter` category (6 endpoints).

Filter PDFs by page size, orientation, page count, rotation, text content,
image content. Returns true/false; use to gate workflows.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_filter_by_page_size(input_file: str, standard_size: str) -> dict:
    """Return whether the PDF matches a standard page size (A4, A3, LETTER, etc)."""
    return await get_client().post_form(
        "/api/v1/filter/filter-page-size",
        input_files=[Path(input_file)],
        form_data={"standardPageSize": standard_size},
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_filter_by_page_count(input_file: str, page_count: int, comparator: str = "Equal") -> dict:
    """Return whether the PDF has N pages (or `Greater`/`Less` than)."""
    return await get_client().post_form(
        "/api/v1/filter/filter-page-count",
        input_files=[Path(input_file)],
        form_data={"pageCount": page_count, "comparator": comparator},
        output_suffix=".json",
    )
