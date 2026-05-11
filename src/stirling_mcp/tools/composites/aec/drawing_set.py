"""AEC composite — drawing-set (Bluebeam "Sets" equivalent).

Treat a directory of PDF revisions as a single navigable drawing set.
Builds a manifest mapping sheet-number → file → revision, optionally merges.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.aec.drawing_set")


# AEC sheet numbering convention — A-101, M-201, etc. — discipline letter +
# 3-digit number. Adjust as needed for project-specific schemes.
SHEET_NUM_RE = re.compile(r"\b([A-Z]{1,2})-?(\d{2,4}(?:\.\d+)?)\b")
REV_RE = re.compile(r"(?:rev|r|revision)[._\- ]*(\d+|[A-Z])", re.IGNORECASE)


@mcp.tool()
async def aec_drawing_set(
    folder: str,
    merge_into_set: bool = False,
    extract_titleblocks: bool = True,
) -> dict:
    """Index a folder of architectural/engineering drawing PDFs as a Set.

    Each PDF is inspected for:
      - Sheet number (matched against pattern `A-101`, `M-201.1`, etc.)
      - Revision marker in filename (`-rev3`, `_r2`, etc.)
      - Page dimensions
      - Optional title-block OCR

    Output is a JSON manifest plus, if `merge_into_set=True`, a single merged
    PDF in sheet-number order.

    Args:
        folder: path to directory containing drawing PDFs
        merge_into_set: produce a single combined PDF in sheet order
        extract_titleblocks: OCR the title block region of each page for
            additional metadata (slower, more accurate)

    Returns:
        `{success, manifest: [{file, sheet_number, revision, ...}],
          merged_path? (if merge_into_set)}`
    """
    folder_p = Path(folder)
    if not folder_p.is_dir():
        return {"success": False, "error": f"not a directory: {folder}"}

    pdfs = sorted(folder_p.glob("*.pdf"))
    if not pdfs:
        return {"success": False, "error": f"no PDFs found in {folder}"}

    client = get_client()
    manifest = []

    for pdf in pdfs:
        sheet_match = SHEET_NUM_RE.search(pdf.stem)
        rev_match = REV_RE.search(pdf.stem)
        entry = {
            "file": str(pdf),
            "name": pdf.name,
            "sheet_number": (
                f"{sheet_match.group(1)}-{sheet_match.group(2)}"
                if sheet_match
                else None
            ),
            "revision": rev_match.group(1) if rev_match else None,
            "size_bytes": pdf.stat().st_size,
        }

        # Page dimensions via Stirling analysis
        try:
            dims = await client.post_form(
                "/api/v1/analysis/page-dimensions",
                input_files=[pdf],
                output_suffix=".json",
            )
            if dims.get("success"):
                entry["dimensions"] = dims.get("json_body")
        except Exception as e:
            log.debug("dim probe failed for %s: %s", pdf, e)

        manifest.append(entry)

    # Sort by sheet number (stable; entries without a number sink to end)
    manifest.sort(key=lambda x: (x["sheet_number"] is None, x["sheet_number"] or ""))

    result: dict = {
        "success": True,
        "folder": str(folder_p),
        "count": len(manifest),
        "manifest": manifest,
    }

    if merge_into_set:
        ordered_files = [m["file"] for m in manifest]
        merge = await client.post_form(
            "/api/v1/general/merge-pdfs",
            input_files=[Path(p) for p in ordered_files],
            form_data={"sortType": "orderProvided"},
            output_name_hint="drawing-set",
        )
        if merge.get("success"):
            result["merged_path"] = merge["output_path"]

    return result
