"""Auto-generated Stirling-PDF tool wrappers — category Forms.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

@mcp.tool()
async def forms_modify_fields(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Modify existing form fields
    
    Updates existing fields in the provided PDF and returns the updated file
    
    Endpoint: ``POST /api/v1/form/modify-fields``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/modify-fields',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def forms_fields(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Inspect PDF form fields
    
    Returns metadata describing each field in the provided PDF form
    
    Endpoint: ``POST /api/v1/form/fields``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/fields',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def forms_fields_with_coordinates(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Inspect PDF form fields with widget coordinates
    
    Returns metadata describing each field in the provided PDF form, including precise widget coordinates for interactive rendering
    
    Endpoint: ``POST /api/v1/form/fields-with-coordinates``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/fields-with-coordinates',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def forms_extract_xlsx(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract form fields as XLSX
    
    Returns an Excel (XLSX) file containing all form field names and their current values
    
    Endpoint: ``POST /api/v1/form/extract-xlsx``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/extract-xlsx',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def forms_extract_csv(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Extract form fields as CSV
    
    Returns a CSV file containing all form field names and their current values
    
    Endpoint: ``POST /api/v1/form/extract-csv``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/extract-csv',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def forms_delete_fields(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Delete form fields
    
    Removes the specified fields from the PDF and returns the updated file
    
    Endpoint: ``POST /api/v1/form/delete-fields``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/form/delete-fields',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

