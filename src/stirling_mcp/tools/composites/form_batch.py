"""Composite — Batch form fill from CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.server import mcp

log = logging.getLogger("stirling_mcp.composites.form_batch")


@mcp.tool()
async def form_fill_batch(
    template_file: str,
    csv_file: str,
    output_subdir: str = "form_batch",
    flatten: bool = True,
    name_column: str | None = None,
) -> dict:
    """Fill a PDF form template once per row in a CSV.

    The CSV header row defines field names. Each subsequent row produces one
    filled PDF named by `name_column` (or row index if not provided).

    Args:
        template_file: path to a fillable PDF
        csv_file: CSV with header row matching PDF field names
        output_subdir: subfolder under OUTPUT_DIR
        flatten: bake fields into static content (recommended)
        name_column: CSV column to use for output filename
    """
    client = get_client()
    csv_p = Path(csv_file)
    tmpl_p = Path(template_file)
    target = SETTINGS.output_dir / output_subdir
    target.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with csv_p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            row_id = row.get(name_column, f"row{idx}") if name_column else f"row{idx}"
            fill = await client.post_form(
                "/api/v1/form/fill",
                input_files=[tmpl_p],
                form_data={"fieldValues": dict(row)},
                output_name_hint=f"form-{row_id}",
            )
            if not fill.get("success"):
                results.append({"row_id": row_id, "success": False, "error": fill})
                continue
            work = Path(fill["output_path"])

            if flatten:
                flat = await client.post_form(
                    "/api/v1/form/flatten",
                    input_files=[work],
                    output_name_hint=f"form-{row_id}-flat",
                )
                if flat.get("success"):
                    work = Path(flat["output_path"])

            final = target / f"{row_id}.pdf"
            work.rename(final)
            results.append({"row_id": row_id, "success": True, "output_path": str(final)})

    return {
        "success": all(r["success"] for r in results),
        "row_count": len(results),
        "results": results,
        "output_dir": str(target),
    }
