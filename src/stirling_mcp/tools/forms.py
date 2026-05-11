"""Layer-1 raw wrappers — Stirling `Forms` category (7 endpoints).

Modify fields, fill, extract data, flatten forms.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp


@mcp.tool()
async def pdf_form_fill(input_file: str, field_values: dict[str, str]) -> dict:
    """Fill an interactive PDF form with provided field values.

    `field_values` maps form field name → value. Get field names first with
    `pdf_form_extract_fields` if you don't know them.

    For batch filling across many rows (e.g. one PDF per CSV row), use the
    composite `form_fill_batch`.
    """
    return await get_client().post_form(
        "/api/v1/form/fill",
        input_files=[Path(input_file)],
        form_data={"fieldValues": field_values},
        output_name_hint="filled",
    )


@mcp.tool()
async def pdf_form_extract_fields(input_file: str) -> dict:
    """List all form fields in a PDF (names, types, current values, options).

    Returns a JSON structure you can inspect to discover what to pass to
    `pdf_form_fill`.
    """
    return await get_client().post_form(
        "/api/v1/form/extract",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_form_flatten(input_file: str) -> dict:
    """Flatten form fields into static page content (un-editable after).

    Use after filling forms when you want to lock in values and prevent further
    editing. Required before signing.
    """
    return await get_client().post_form(
        "/api/v1/form/flatten",
        input_files=[Path(input_file)],
        output_name_hint="form-flattened",
    )
