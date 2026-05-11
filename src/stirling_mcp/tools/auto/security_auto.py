"""Auto-generated Stirling-PDF tool wrappers — category Security.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

@mcp.tool()
async def security_timestamp_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Add RFC 3161 document timestamp to a PDF
    
    Contacts a trusted Time Stamp Authority (TSA) server and embeds an RFC 3161 document timestamp into the PDF. Only a SHA-256 hash of the document is sent to the TSA — the PDF itself never leaves the server. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/security/timestamp-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/security/timestamp-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def security_get_info_on_pdf(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Get comprehensive PDF information
    
    Extracts all available information from a PDF file. Input:PDF Output:JSON Type:SISO
    
    Endpoint: ``POST /api/v1/security/get-info-on-pdf``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/security/get-info-on-pdf',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )


@mcp.tool()
async def security_add_watermark(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Add watermark to a PDF file
    
    This endpoint adds a watermark to a given PDF file. Users can specify the watermark type (text or image), rotation, opacity, width spacer, and height spacer. Input:PDF Output:PDF Type:SISO
    
    Endpoint: ``POST /api/v1/security/add-watermark``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/security/add-watermark',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

