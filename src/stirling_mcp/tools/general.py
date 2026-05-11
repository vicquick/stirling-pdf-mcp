"""Layer-1 raw wrappers — Stirling `General` category (19 endpoints).

Merge, split, rotate, remove pages, reorganise, multi-page layout, scale.
Each tool is a thin pass-through to Stirling with rich docstrings so the LLM
can pick the right one without reading external docs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_merge(
    input_files: list[str],
    sort_type: Literal["orderProvided", "byFileName", "byDateModified", "byDateCreated", "byPDFTitle"] = "orderProvided",
    remove_certs: bool = False,
    remove_attachments: bool = False,
) -> dict:
    """Merge multiple PDFs into a single PDF.

    Use when the user has 2+ PDFs and wants one combined document. Page order
    follows `sort_type`: `orderProvided` (default — uses the order of
    `input_files`), `byFileName` (alphabetical), `byDateModified`/`byDateCreated`
    (timestamp), `byPDFTitle` (PDF metadata title).

    Args:
        input_files: list of paths to PDF files to merge
        sort_type: how to order pages across files
        remove_certs: drop digital certificates from merged output (recommended
            when merging signed PDFs that don't need to keep individual signatures)
        remove_attachments: drop file attachments embedded in source PDFs

    Returns: `{success, output_path, size_bytes, ...}`
    """
    return await get_client().post_form(
        "/api/v1/general/merge-pdfs",
        input_files=[Path(p) for p in input_files],
        form_data={
            "sortType": sort_type,
            "removeCertSign": remove_certs,
            "removeFileAttachments": remove_attachments,
        },
        output_name_hint="merged",
    )


@mcp.tool()
async def pdf_split_by_pages(input_file: str, page_numbers: str) -> dict:
    """Split a PDF at specified page numbers, producing a ZIP of part-files.

    Page expressions accept comma-separated values, ranges, and the `all` keyword.
    Examples: `"5"` → split before page 5; `"5,10,15"` → 3 splits; `"all"` →
    one file per page; `"2-4,8"` → splits at page 2 and 8 plus auto inside 2-4.

    Args:
        input_file: path to PDF
        page_numbers: split-point expression

    Returns: `{success, output_path}` — output_path is a .zip
    """
    return await get_client().post_form(
        "/api/v1/general/split-pdfs",
        input_files=[Path(input_file)],
        form_data={"pageNumbers": page_numbers},
        output_suffix=".zip",
        output_name_hint="split",
    )


@mcp.tool()
async def pdf_split_by_size(
    input_file: str,
    threshold: str = "10MB",
    split_type: Literal["size", "pageCount", "documentCount"] = "size",
) -> dict:
    """Split a PDF into parts capped at a size or page count.

    `split_type` controls the threshold semantics:
      - `size` — bytes per output, e.g. `10MB`, `500KB`
      - `pageCount` — pages per output, e.g. `50`
      - `documentCount` — total number of output PDFs, e.g. `3`

    Output is a ZIP of the resulting PDFs.
    """
    return await get_client().post_form(
        "/api/v1/general/split-by-size-or-count",
        input_files=[Path(input_file)],
        form_data={"threshold": threshold, "splitType": split_type},
        output_suffix=".zip",
        output_name_hint="split-by-size",
    )


@mcp.tool()
async def pdf_split_by_sections(
    input_file: str,
    horizontal_divisions: int = 0,
    vertical_divisions: int = 0,
    merge: bool = False,
) -> dict:
    """Split each page of a PDF into a grid of sub-pages.

    Useful for spreads (2-up posters → individual pages) or chopping
    architectural drawings into tiles.

    Args:
        horizontal_divisions: cuts along the X axis (e.g. 1 = split in half left/right)
        vertical_divisions: cuts along the Y axis
        merge: combine all sub-pages back into a single PDF instead of zipping
    """
    return await get_client().post_form(
        "/api/v1/general/split-pdf-by-sections",
        input_files=[Path(input_file)],
        form_data={
            "horizontalDivisions": horizontal_divisions,
            "verticalDivisions": vertical_divisions,
            "merge": merge,
        },
        output_suffix=".pdf" if merge else ".zip",
        output_name_hint="split-sections",
    )


@mcp.tool()
async def pdf_split_by_chapters(
    input_file: str,
    bookmark_level: int = 0,
    include_metadata: bool = True,
) -> dict:
    """Split a PDF by its bookmark/TOC structure.

    `bookmark_level` 0 = top level chapters only. 1 = sections within chapters.
    Requires that the source PDF has bookmarks set; if not, use `pdf_split_by_pages`.
    """
    return await get_client().post_form(
        "/api/v1/general/split-pdf-by-chapters",
        input_files=[Path(input_file)],
        form_data={
            "bookmarkLevel": bookmark_level,
            "includeMetadata": include_metadata,
        },
        output_suffix=".zip",
        output_name_hint="split-chapters",
    )


@mcp.tool()
async def pdf_rotate(input_file: str, angle: Literal[90, 180, 270] = 90) -> dict:
    """Rotate every page of a PDF by 90/180/270 degrees clockwise.

    To rotate only specific pages, use `pdf_reorganize_pages` with a rotation
    parameter instead.
    """
    return await get_client().post_form(
        "/api/v1/general/rotate-pdf",
        input_files=[Path(input_file)],
        form_data={"angle": angle},
        output_name_hint="rotated",
    )


@mcp.tool()
async def pdf_remove_pages(input_file: str, page_numbers: str) -> dict:
    """Remove specified pages from a PDF.

    `page_numbers` accepts the same expression syntax as `pdf_split_by_pages`:
    comma-separated values + ranges. e.g. `"1,3,5-7"`.
    """
    return await get_client().post_form(
        "/api/v1/general/remove-pages",
        input_files=[Path(input_file)],
        form_data={"pageNumbers": page_numbers},
        output_name_hint="pages-removed",
    )


@mcp.tool()
async def pdf_reorganize_pages(
    input_file: str,
    page_numbers: str,
) -> dict:
    """Reorder pages of a PDF.

    `page_numbers` is the desired order, e.g. `"3,1,2,4"` → page 3 first, then 1,
    then 2, then 4. Pages not listed are dropped.
    """
    return await get_client().post_form(
        "/api/v1/general/rearrange-pages",
        input_files=[Path(input_file)],
        form_data={"pageNumbers": page_numbers},
        output_name_hint="reorganized",
    )


@mcp.tool()
async def pdf_multi_page_layout(
    input_file: str,
    pages_per_sheet: Literal[2, 3, 4, 8, 9, 16] = 2,
    add_border: bool = False,
) -> dict:
    """Combine N source pages onto one output page (n-up layout).

    Common values: 2 (booklet), 4 (handout), 9 (contact sheet). Use `add_border`
    to draw a thin frame around each sub-page for clarity.
    """
    return await get_client().post_form(
        "/api/v1/general/multi-page-layout",
        input_files=[Path(input_file)],
        form_data={
            "pagesPerSheet": pages_per_sheet,
            "addBorder": add_border,
        },
        output_name_hint=f"{pages_per_sheet}up",
    )


@mcp.tool()
async def pdf_scale_pages(
    input_file: str,
    page_size: Literal["A0", "A1", "A2", "A3", "A4", "A5", "A6", "LETTER", "LEGAL", "KEEP"] = "A4",
    scale_factor: float = 1.0,
) -> dict:
    """Resize PDF pages to a target paper size or apply a uniform scale factor.

    Use `page_size=KEEP` and a `scale_factor` (e.g. 0.5 to shrink to half) when
    you want proportional resize. Use a specific page size to conform to a
    paper standard.
    """
    return await get_client().post_form(
        "/api/v1/general/scale-pages",
        input_files=[Path(input_file)],
        form_data={"pageSize": page_size, "scaleFactor": scale_factor},
        output_name_hint=f"scaled-{page_size}",
    )
