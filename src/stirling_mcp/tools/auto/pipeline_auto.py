"""Auto-generated Stirling-PDF tool wrappers — category Pipeline.

Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.
"""

from __future__ import annotations

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

@mcp.tool()
async def pipeline_handledata(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """Execute automated PDF processing pipeline
    
    This endpoint processes multiple PDF files through a configurable pipeline of operations. Users provide files and a JSON configuration defining the sequence of operations to perform. Input:PDF Output:PDF/ZIP Type:MIMO
    
    Endpoint: ``POST /api/v1/pipeline/handleData``
    """
    from pathlib import Path
    return await get_client().post_form(
        '/api/v1/pipeline/handleData',
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {},
    )

