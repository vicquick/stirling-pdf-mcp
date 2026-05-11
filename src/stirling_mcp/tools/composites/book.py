"""Composite — book_publish.

Compile a list of chapter PDFs (+ optional cover image) into a book-ready
PDF with page numbers and metadata. TOC bookmark generation is a future
enhancement once Stirling exposes a bookmark-add endpoint or we integrate
with PyPDF in-process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def book_publish(
    chapter_files: list[str],
    title: str,
    author: str = "",
    cover_image: str | None = None,
    page_number_position: int = 5,
    optimize_level: int = 5,
    output_format: Literal["pdf", "pdfa-2b"] = "pdf",
) -> dict:
    """Compile chapters into a publication-ready PDF.

    Workflow:
        1. (Optional) convert cover image to first PDF page
        2. Merge cover + chapters in order
        3. Add page numbers (skip cover if present)
        4. Set metadata (title, author, creator)
        5. Optimise / optionally convert to PDF/A for archival

    Args:
        chapter_files: ordered list of chapter PDFs
        title: book title (written into metadata + used in filename)
        author: written into metadata
        cover_image: optional path to PNG/JPG cover (placed as first page)
        page_number_position: 1-9 grid (default 5 = bottom-centre)
        optimize_level: compression 1-9
        output_format: 'pdf' (default) or 'pdfa-2b' for archive

    Returns: `{success, output_path, page_count_estimate, endpoints_chained}`
    """
    client = get_client()
    chained: list[str] = []
    pieces: list[Path] = []

    if cover_image:
        cover = await client.post_form(
            "/api/v1/convert/img/pdf",
            input_files=[Path(cover_image)],
            form_data={"stretch": True, "autoRotate": True},
            output_name_hint="book-cover",
        )
        if cover.get("success"):
            pieces.append(Path(cover["output_path"]))
            chained.append("img/pdf (cover)")

    pieces.extend(Path(p) for p in chapter_files)

    merge = await client.post_form(
        "/api/v1/general/merge-pdfs",
        input_files=pieces,
        form_data={"sortType": "orderProvided"},
        output_name_hint="book-merged",
    )
    if not merge.get("success"):
        return {"success": False, "stage": "merge", **merge}
    work = Path(merge["output_path"])
    chained.append("merge-pdfs")

    nums = await client.post_form(
        "/api/v1/misc/add-page-numbers",
        input_files=[work],
        form_data={
            "position": page_number_position,
            "startingNumber": 2 if cover_image else 1,
            "pagesToNumber": "2-" if cover_image else "all",
            "customMargin": "small",
            "customText": "{n}",
            "fontSize": 11,
            "fontType": "Helvetica",
        },
        output_name_hint="book-numbered",
    )
    if nums.get("success"):
        work = Path(nums["output_path"])
        chained.append("add-page-numbers")

    meta = await client.post_form(
        "/api/v1/misc/update-metadata",
        input_files=[work],
        form_data={
            "title": title,
            "author": author,
            "creator": "stirling-pdf-mcp / book_publish",
            "subject": "Book / compiled chapters",
        },
        output_name_hint="book-meta",
    )
    if meta.get("success"):
        work = Path(meta["output_path"])
        chained.append("update-metadata")

    if optimize_level >= 1:
        comp = await client.post_form(
            "/api/v1/misc/compress-pdf",
            input_files=[work],
            form_data={"optimizeLevel": optimize_level},
            output_name_hint="book-compressed",
        )
        if comp.get("success"):
            work = Path(comp["output_path"])
            chained.append("compress-pdf")

    if output_format == "pdfa-2b":
        pdfa = await client.post_form(
            "/api/v1/convert/pdf/pdfa",
            input_files=[work],
            form_data={"outputFormat": "pdfa-2b"},
            output_name_hint="book-pdfa",
        )
        if pdfa.get("success"):
            work = Path(pdfa["output_path"])
            chained.append("pdf-to-pdfa")

    return {
        "success": True,
        "output_path": str(work),
        "size_bytes": work.stat().st_size,
        "chapter_count": len(chapter_files),
        "has_cover": cover_image is not None,
        "title": title,
        "endpoints_chained": chained,
    }
