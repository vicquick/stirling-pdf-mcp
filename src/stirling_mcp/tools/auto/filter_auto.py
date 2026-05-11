"""Auto-generated Stirling-PDF tool wrappers — category Filter.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

@mcp.tool()
async def filter__filter_filter_page_rotation(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Checks if a PDF is of a certain rotation
    
    Input:PDF Output:Boolean Type:SISO
    
    Endpoint: ``POST /api/v1/filter/filter-page-rotation``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/filter/filter-page-rotation',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def filter__filter_filter_file_size(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Checks if a PDF is a set file size
    
    Input:PDF Output:Boolean Type:SISO
    
    Endpoint: ``POST /api/v1/filter/filter-file-size``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/filter/filter-file-size',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def filter__filter_filter_contains_text(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Checks if a PDF contains set text, returns true if does
    
    Input:PDF Output:Boolean Type:SISO
    
    Endpoint: ``POST /api/v1/filter/filter-contains-text``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/filter/filter-contains-text',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def filter__filter_filter_contains_image(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Checks if a PDF contains an image
    
    Input:PDF Output:Boolean Type:SISO
    
    Endpoint: ``POST /api/v1/filter/filter-contains-image``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/filter/filter-contains-image',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

