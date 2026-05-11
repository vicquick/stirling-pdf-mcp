"""Auto-generated Stirling-PDF tool wrappers — category Misc.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

@mcp.tool()
async def misc_show_javascript(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Grabs all JS from a PDF and returns a single JS file with all code
    
    desc. Input:PDF Output:JS Type:SISO
    
    Endpoint: ``POST /api/v1/misc/show-javascript``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/show-javascript',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_scanner_effect(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Apply scanner effect to PDF
    
    Applies various effects to simulate a scanned document, including rotation, noise, and edge softening. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/scanner-effect``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/scanner-effect',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_replace_invert_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Replace-Invert Color PDF
    
    This endpoint accepts a PDF file and provides options to invert all colors, replace text and background colors, or convert to CMYK color space for printing. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/replace-invert-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/replace-invert-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_rename_attachment(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Rename attachment in PDF
    
    This endpoint renames an embedded attachment in a PDF. Input:PDF Output:PDF Type:MISO
    
    Endpoint: ``POST /api/v1/misc/rename-attachment``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/rename-attachment',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_list_attachments(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """List attachments in PDF
    
    This endpoint lists all embedded attachments in a PDF. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/misc/list-attachments``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/list-attachments',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_extract_images(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract images from a PDF file
    
    This endpoint extracts images from a given PDF file and returns them in a zip file. Users can specify the output image format. Input:PDF Output:IMAGE/ZIP Type:SIMO
    
    Endpoint: ``POST /api/v1/misc/extract-images``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/extract-images',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_extract_attachments(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract attachments from PDF
    
    This endpoint extracts all embedded attachments from a PDF into a ZIP archive. Input:PDF Output:ZIP Type:SISO
    
    Endpoint: ``POST /api/v1/misc/extract-attachments``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/extract-attachments',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_delete_attachment(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Delete attachment from PDF
    
    This endpoint deletes an embedded attachment from a PDF. Input:PDF Output:PDF Type:MISO
    
    Endpoint: ``POST /api/v1/misc/delete-attachment``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/delete-attachment',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_decompress_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Decompress PDF streams
    
    Fully decompresses all PDF streams including text content
    
    Endpoint: ``POST /api/v1/misc/decompress-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/decompress-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_auto_split_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Auto split PDF pages into separate documents
    
    This endpoint accepts a PDF file, scans each page for a specific QR code, and splits the document at the QR code boundaries. The output is a zip file containing each separate PDF document. Input:PDF Output:ZIP-PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/auto-split-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/auto-split-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_auto_rename(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract header from PDF file
    
    This endpoint accepts a PDF file and attempts to extract its title or header based on heuristics. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/auto-rename``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/auto-rename',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_add_image(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Overlay image onto a PDF file
    
    This endpoint overlays an image onto a PDF file at the specified coordinates. Supports both raster formats (PNG, JPEG, etc.) and vector format (SVG). SVG files are rendered as vector graphics for crisp output at any resolution. The image can be overlaid on every page of the PDF if specified. Input:PDF/IMAGE/SVG Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/add-image``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/add-image',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_add_comments(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Add sticky-note comments to a PDF at specified positions or anchored text
    
    Attaches PDF Text (sticky-note) annotations to the document. Each CommentSpec can either supply absolute coordinates or an `anchorText` hint; when provided, the tool locates the first matching line on the target page and anchors the icon there (falling back to the coordinates if no match). Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/misc/add-comments``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/add-comments',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def misc_add_attachments(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Add attachments to PDF
    
    This endpoint adds attachments to a PDF. Input:PDF, Output:PDF Type:MISO
    
    Endpoint: ``POST /api/v1/misc/add-attachments``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/misc/add-attachments',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

