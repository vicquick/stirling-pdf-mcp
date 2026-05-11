"""Auto-generated Stirling-PDF tool wrappers — category Analysis.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

@mcp.tool()
async def analysis_page_count(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get PDF page count
    
    Returns total number of pages in PDF. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/page-count``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/page-count',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def analysis_form_fields(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get form field information
    
    Returns count and details of form fields. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/form-fields``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/form-fields',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def analysis_font_info(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get font information
    
    Returns list of fonts used in the document. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/font-info``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/font-info',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def analysis_document_properties(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get PDF document properties
    
    Returns title, author, subject, etc. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/document-properties``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/document-properties',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def analysis_basic_info(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get basic PDF information
    
    Returns page count, version, file size. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/basic-info``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/basic-info',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def analysis_annotation_info(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get annotation information
    
    Returns count and types of annotations. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/analysis/annotation-info``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/analysis/annotation-info',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

