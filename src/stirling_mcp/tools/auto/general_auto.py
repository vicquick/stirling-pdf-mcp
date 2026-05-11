"""Auto-generated Stirling-PDF tool wrappers — category General.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

@mcp.tool()
async def general_split_pages(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Split a PDF file into separate documents
    
    This endpoint splits a given PDF file into separate documents based on the specified page numbers or ranges. Users can specify pages using individual numbers, ranges, or 'all' for every page. Input:PDF Output:PDF Type:SIMO
    
    Endpoint: ``POST /api/v1/general/split-pages``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/split-pages',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_split_for_poster_print(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Split large PDF pages into smaller printable chunks
    
    This endpoint splits large or oddly-sized PDF pages into smaller chunks suitable for printing on standard paper sizes (e.g., A4, Letter). Divides each page into a grid of smaller pages using Apache PDFBox. Input: PDF Output: ZIP-PDF Type: SISO
    
    Endpoint: ``POST /api/v1/general/split-for-poster-print``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/split-for-poster-print',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_send_email(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Send an email with an attachment
    
    This endpoint sends an email with an attachment. Input:PDF Output:Success/Failure Type:MISO
    
    Endpoint: ``POST /api/v1/general/send-email``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/send-email',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_remove_image_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Remove images from PDF
    
    This endpoint removes all embedded images from a PDF file and returns the modified document. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/general/remove-image-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/remove-image-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_pdf_to_single_page(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Convert a multi-page PDF into a single long page PDF
    
    This endpoint converts a multi-page PDF document into a single paged PDF document. The width of the single page will be same as the input's width, but the height will be the sum of all the pages' heights. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/general/pdf-to-single-page``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/pdf-to-single-page',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_overlay_pdfs(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Overlay PDF files in various modes
    
    Overlay PDF files onto a base PDF with different modes: Sequential, Interleaved, or Fixed Repeat. Input:PDF Output:PDF Type:MIMO
    
    Endpoint: ``POST /api/v1/general/overlay-pdfs``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/overlay-pdfs',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_extract_bookmarks(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract PDF Bookmarks
    
    Extracts bookmarks/table of contents from a PDF document as JSON.
    
    Endpoint: ``POST /api/v1/general/extract-bookmarks``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/extract-bookmarks',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_edit_table_of_contents(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Edit Table of Contents
    
    Add or edit bookmarks/table of contents in a PDF document.
    
    Endpoint: ``POST /api/v1/general/edit-table-of-contents``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/edit-table-of-contents',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_crop(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Crops a PDF document
    
    This operation takes an input PDF file and crops it according to the given coordinates. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/general/crop``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/crop',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def general_booklet_imposition(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Create a booklet with proper page imposition
    
    This operation combines page reordering for booklet printing with multi-page layout. It rearranges pages in the correct order for booklet printing and places multiple pages on each sheet for proper folding and binding. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/general/booklet-imposition``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/general/booklet-imposition',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

