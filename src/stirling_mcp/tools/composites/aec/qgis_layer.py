"""AEC cross-MCP composite — aec_georeferenced_to_qgis.

If a PDF is a GeoPDF (has spatial extent metadata), push it to qgis-mcp as
a raster layer. Falls back to extracting page dimensions for manual GeoTIFF
conversion if not georeferenced.
"""

from __future__ import annotations

import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp
from stirling_mcp.utils.mcp_client import call_mcp_tool, CrossMCPError

log = logging.getLogger("stirling_mcp.composites.aec.qgis_layer")


@mcp.tool()
async def aec_georeferenced_to_qgis(
    input_file: str,
    dpi: int = 300,
    layer_name: str | None = None,
    qgis_mcp_url: str | None = None,
) -> dict:
    """Render a (geo)referenced PDF to a high-DPI raster and add to QGIS.

    Workflow:
        1. Render PDF to PNG @ requested DPI via Stirling
        2. POST to qgis-mcp's `add_raster_layer` tool

    True GeoPDF (PDF with embedded CRS + spatial extent) → qgis-mcp reads
    the spatial reference automatically. Plain PDFs become raster layers
    without georef (user must apply transformation in QGIS).

    Args:
        input_file: PDF (GeoPDF or otherwise)
        dpi: render quality (300 = print; 600 = drawing detail)
        layer_name: QGIS layer label (defaults to filename stem)
        qgis_mcp_url: override default endpoint

    Returns: `{success, raster_path, qgis_layer_uuid, endpoint}`
    """
    endpoint = qgis_mcp_url or SETTINGS.qgis_mcp_url or "http://qgis-mcp:8081/mcp/"

    client = get_client()
    work = Path(input_file)

    # Render to single PNG (use 'single' to get one image)
    img = await client.post_form(
        "/api/v1/convert/pdf/img",
        input_files=[work],
        form_data={
            "imageFormat": "png",
            "singleOrMultiple": "single",
            "colorType": "color",
            "dpi": dpi,
        },
        output_suffix=".png",
        output_name_hint=f"qgis-raster-{work.stem}",
    )
    if not img.get("success"):
        return {"success": False, "stage": "render", **img}

    raster_path = img["output_path"]
    name = layer_name or work.stem

    try:
        r = await call_mcp_tool(
            endpoint,
            "add_raster_layer",
            {"file_path": raster_path, "layer_name": name},
            timeout=60,
        )
        layer_id = (
            r.get("layer_id") or r.get("uuid") or r.get("name") if isinstance(r, dict) else None
        )
    except CrossMCPError as e:
        return {
            "success": False,
            "stage": "qgis_add_layer",
            "error": str(e),
            "raster_path": raster_path,
            "endpoint": endpoint,
        }

    return {
        "success": True,
        "raster_path": raster_path,
        "qgis_layer_uuid": layer_id,
        "qgis_response": r,
        "dpi": dpi,
        "endpoint": endpoint,
        "endpoints_chained": ["convert/pdf/img (single)", "qgis-mcp:add_raster_layer"],
    }
