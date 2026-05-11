"""AEC cross-MCP composite — aec_drawings_to_ifc_refs.

Extract drawing titles + sheet numbers from a drawing-set PDF, link them to
IFC entities via ifc-mcp. Output: a JSON manifest mapping drawing→IFC GUIDs.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp
from stirling_mcp.utils.mcp_client import call_mcp_tool, CrossMCPError

log = logging.getLogger("stirling_mcp.composites.aec.ifc_refs")


SHEET_RE = re.compile(r"\b([A-Z]{1,2}[-_]?\d{2,4}(?:\.\d+)?)\b")


@mcp.tool()
async def aec_drawings_to_ifc_refs(
    drawings_pdf: str,
    ifc_file: str | None = None,
    ifc_mcp_url: str | None = None,
    ocr_language: str = "eng",
) -> dict:
    """OCR a drawings-set PDF, extract sheet numbers, look them up in an IFC.

    Workflow:
        1. OCR the PDF
        2. Extract text per page (best-effort; v1 extracts whole-doc text and
           groups occurrences by proximity to sheet markers)
        3. For each sheet number found, query ifc-mcp for IfcAnnotation or
           IfcDocumentReference entities matching the sheet name
        4. Return a manifest of `{sheet_number: [ifc_guid, ...]}`

    Configure ifc-mcp endpoint via env var ``IFC_MCP_URL`` (default
    ``http://ifc-mcp:8084/mcp/``).

    Args:
        drawings_pdf: path to drawings PDF
        ifc_file: optional IFC file path to load on the ifc-mcp side first
        ifc_mcp_url: override default endpoint
        ocr_language: ISO code

    Returns: `{success, manifest, sheet_count, matched_count}`
    """
    endpoint = ifc_mcp_url or SETTINGS.ifc_mcp_url or "http://ifc-mcp:8084/mcp/"

    client = get_client()
    work = Path(drawings_pdf)

    ocr = await client.post_form(
        "/api/v1/misc/ocr-pdf",
        input_files=[work],
        form_data={"languages": [ocr_language], "ocrType": "skip-text", "deskew": True},
        output_name_hint="ifc-refs-ocr",
    )
    if ocr.get("success"):
        work = Path(ocr["output_path"])

    txt = await client.post_form(
        "/api/v1/misc/extract-text",
        input_files=[work],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="ifc-refs-text",
    )
    if not txt.get("success"):
        return {"success": False, "stage": "extract-text", **txt}
    text = Path(txt["output_path"]).read_text(errors="ignore")[:50000]

    sheets = sorted({m.group(1).upper().replace("_", "-") for m in SHEET_RE.finditer(text)})
    if not sheets:
        return {"success": True, "manifest": {}, "sheet_count": 0, "matched_count": 0, "note": "no sheet numbers detected"}

    # Optionally load the IFC first
    chained: list[str] = ["ocr-pdf", "extract-text"]
    if ifc_file:
        try:
            await call_mcp_tool(endpoint, "ifc_load", {"file_path": ifc_file}, timeout=30)
            chained.append(f"ifc-mcp:ifc_load({ifc_file})")
        except CrossMCPError as e:
            return {"success": False, "stage": "ifc_load", "error": str(e), "endpoint": endpoint}

    # Query each sheet — ifc-mcp's exact tool name depends on version.
    # Try a couple of common patterns gracefully.
    manifest: dict[str, list[str]] = {}
    matched = 0
    for sheet in sheets:
        try:
            r = await call_mcp_tool(
                endpoint,
                "ifc_select",
                {"query": sheet, "limit": 5},
                timeout=15,
            )
            guids = []
            if isinstance(r, dict):
                guids = (
                    r.get("guids")
                    or r.get("matches")
                    or r.get("results")
                    or []
                )
            manifest[sheet] = guids
            if guids:
                matched += 1
        except CrossMCPError as e:
            manifest[sheet] = []
            log.warning("ifc lookup for %s failed: %s", sheet, e)

    chained.append(f"ifc-mcp:ifc_select × {len(sheets)}")

    return {
        "success": True,
        "manifest": manifest,
        "sheet_count": len(sheets),
        "matched_count": matched,
        "endpoint": endpoint,
        "endpoints_chained": chained,
    }
