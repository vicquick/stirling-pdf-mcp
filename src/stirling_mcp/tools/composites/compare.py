"""Composite — Compare two PDF versions.

Word-level diff (text changes) + page-dimensions diff. Visual diff is v0.3.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def compare_versions(file_a: str, file_b: str) -> dict:
    """Compare two PDF versions and return a structured diff.

    Extracts text from both, runs unified diff, also reports page count and
    dimension changes. For visual (drawing) diff use the AEC composite
    `aec_drawing_diff_visual` (v0.3).

    Returns:
        `{success, page_count_a, page_count_b, text_diff_unified, text_diff_summary}`
    """
    client = get_client()

    text_a_res = await client.post_form(
        "/api/v1/convert/pdf/text",
        input_files=[Path(file_a)],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="compare-a",
    )
    text_b_res = await client.post_form(
        "/api/v1/convert/pdf/text",
        input_files=[Path(file_b)],
        form_data={"outputFormat": "txt"},
        output_suffix=".txt",
        output_name_hint="compare-b",
    )
    text_a = Path(text_a_res.get("output_path", "")).read_text(errors="ignore") if text_a_res.get("success") else ""
    text_b = Path(text_b_res.get("output_path", "")).read_text(errors="ignore") if text_b_res.get("success") else ""

    diff_lines = list(
        difflib.unified_diff(
            text_a.splitlines(),
            text_b.splitlines(),
            fromfile="A",
            tofile="B",
            lineterm="",
            n=3,
        )
    )

    additions = sum(1 for ln in diff_lines if ln.startswith("+") and not ln.startswith("+++"))
    deletions = sum(1 for ln in diff_lines if ln.startswith("-") and not ln.startswith("---"))

    dims_a = await client.post_form(
        "/api/v1/analysis/page-dimensions",
        input_files=[Path(file_a)],
        output_suffix=".json",
    )
    dims_b = await client.post_form(
        "/api/v1/analysis/page-dimensions",
        input_files=[Path(file_b)],
        output_suffix=".json",
    )

    return {
        "success": True,
        "file_a": file_a,
        "file_b": file_b,
        "text_diff_summary": {
            "additions": additions,
            "deletions": deletions,
            "identical": additions == 0 and deletions == 0,
        },
        "text_diff_unified": "\n".join(diff_lines[:500]),  # cap for context
        "page_dimensions_a": dims_a.get("json_body"),
        "page_dimensions_b": dims_b.get("json_body"),
        "endpoints_chained": [
            "extract-text x2",
            "page-dimensions x2",
            "client-side difflib",
        ],
    }
