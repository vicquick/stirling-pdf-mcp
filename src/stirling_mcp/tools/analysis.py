"""Layer-1 raw wrappers — Stirling `Analysis` category (8 endpoints).

Security info, page dimensions, text density, image count, font usage,
quality score.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp


@mcp.tool()
async def pdf_analyze_security(input_file: str) -> dict:
    """Report on a PDF's security posture.

    Returns: encryption status, key length, permission flags, whether passwords
    are set, presence of JavaScript / embedded files / external links.
    """
    return await get_client().post_form(
        "/api/v1/analysis/security-info",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_analyze_dimensions(input_file: str) -> dict:
    """Report each page's dimensions, rotation, and orientation.

    Useful for filtering mixed-size documents or detecting drawing sheets.
    """
    return await get_client().post_form(
        "/api/v1/analysis/page-dimensions",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )
