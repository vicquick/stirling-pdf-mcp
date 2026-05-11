"""Composite — prepare_for_print and prepare_for_web."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.print_web")


@mcp.tool()
async def prepare_for_print(
    input_file: str,
    page_size: Literal["A0", "A1", "A2", "A3", "A4", "A5", "A6", "LETTER", "LEGAL"] = "A4",
    dpi: int = 300,
    grayscale: bool = False,
) -> dict:
    """Make a PDF print-ready.

    Steps: flatten → scale to target paper → optionally grayscale → compress.

    Note: True CMYK conversion isn't exposed by Stirling. For four-colour-press
    output, post-process the result with a CMYK conversion tool externally.
    """
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)

    flat = await client.post_form(
        "/api/v1/misc/flatten",
        input_files=[work],
        output_name_hint="print-flat",
    )
    if flat.get("success"):
        work = Path(flat["output_path"])
        chained.append("flatten")

    scaled = await client.post_form(
        "/api/v1/general/scale-pages",
        input_files=[work],
        form_data={"pageSize": page_size, "scaleFactor": 1.0},
        output_name_hint=f"print-{page_size}",
    )
    if scaled.get("success"):
        work = Path(scaled["output_path"])
        chained.append("scale-pages")

    if grayscale:
        comp = await client.post_form(
            "/api/v1/misc/compress-pdf",
            input_files=[work],
            form_data={"optimizeLevel": 3, "convertToGrayscale": True},
            output_name_hint="print-gray",
        )
        if comp.get("success"):
            work = Path(comp["output_path"])
            chained.append("compress-pdf(grayscale)")

    return {"success": True, "output_path": str(work), "endpoints_chained": chained}


@mcp.tool()
async def prepare_for_web(input_file: str, optimize_level: int = 7) -> dict:
    """Make a PDF web-ready: compress + linearise + strip metadata."""
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)

    comp = await client.post_form(
        "/api/v1/misc/compress-pdf",
        input_files=[work],
        form_data={"optimizeLevel": optimize_level, "linearize": True},
        output_name_hint="web-compressed",
    )
    if comp.get("success"):
        work = Path(comp["output_path"])
        chained.append("compress-pdf(linearised)")

    meta = await client.post_form(
        "/api/v1/misc/update-metadata",
        input_files=[work],
        form_data={"deleteAll": True},
        output_name_hint="web-stripped",
    )
    if meta.get("success"):
        work = Path(meta["output_path"])
        chained.append("strip-metadata")

    return {
        "success": True,
        "output_path": str(work),
        "size_bytes": work.stat().st_size,
        "endpoints_chained": chained,
    }
