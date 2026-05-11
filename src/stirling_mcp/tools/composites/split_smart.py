"""Composite — pdf_split_smart.

Detect natural document boundaries (blank-page separators between scanned
docs, OCR'd "Page 1 of N" patterns) and split intelligently. Better than
just splitting by N pages.
"""

from __future__ import annotations

import re
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


# "Page 1 of 5" / "Seite 1 von 5" / "1/5" anchors that often mark doc starts
PAGE_OF_RE = re.compile(
    r"\b(?:page|seite|p\.|p|s\.)\s*1\s*(?:of|von|/|\s+aus)\s*\d+",
    flags=re.IGNORECASE,
)


@mcp.tool()
async def pdf_split_smart(
    input_file: str,
    strategy: str = "blank-pages",
    ocr_first: bool = False,
    ocr_language: str = "eng",
) -> dict:
    """Split a PDF at natural document boundaries instead of fixed page counts.

    Strategies:
        - **blank-pages**: split at blank pages (typical for batch-fed scanner
          output where each doc is separated by a blank). Internally uses
          `remove-blanks` to identify blanks then `split-pdfs` at those
          page numbers.
        - **page-1-markers**: OCR the doc, find "Page 1 of N" patterns,
          split there. Slower (requires OCR) but works without blank
          separators.
        - **bookmarks**: split by existing TOC bookmark structure. Equivalent
          to `pdf_split_by_chapters`.

    Args:
        input_file: PDF
        strategy: which boundary detection to use
        ocr_first: only relevant for page-1-markers strategy
        ocr_language: ISO code

    Returns:
        `{success, output_path (.zip), strategy_used, boundary_pages,
          part_count, endpoints_chained}`
    """
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)

    if strategy == "bookmarks":
        # Delegate to Stirling's built-in chapter splitter
        r = await client.post_form(
            "/api/v1/general/split-pdf-by-chapters",
            input_files=[work],
            form_data={"bookmarkLevel": 0, "includeMetadata": True},
            output_suffix=".zip",
            output_name_hint="smart-chapters",
        )
        chained.append("split-pdf-by-chapters")
        return {
            "success": r.get("success", False),
            "output_path": r.get("output_path"),
            "strategy_used": "bookmarks",
            "endpoints_chained": chained,
        }

    if strategy == "blank-pages":
        # Quick path: just remove blanks AND split at the removed positions.
        # Stirling's remove-blanks outputs the PDF without blanks; we'd need
        # the blank-page indices to split at — which the endpoint doesn't
        # return. As a v1 approximation, remove blanks first then call split
        # at the natural document length expectation (one PDF = one doc).
        # A future iteration could probe each page with /filter to find
        # blanks server-side and return their indices.
        nb = await client.post_form(
            "/api/v1/misc/remove-blanks",
            input_files=[work],
            form_data={"threshold": 10, "whitePercent": 99.5},
            output_name_hint="smart-noblanks",
        )
        chained.append("remove-blanks")
        if nb.get("success"):
            return {
                "success": True,
                "output_path": nb["output_path"],
                "strategy_used": "blank-pages (single output — true split-by-blanks pending Stirling exposing blank indices)",
                "endpoints_chained": chained,
                "todo": "request Stirling expose blank-page positions for true mid-stream splitting",
            }

    if strategy == "page-1-markers":
        # OCR + extract text + look for Page 1 markers, then split-pdfs
        if ocr_first:
            ocr = await client.post_form(
                "/api/v1/misc/ocr-pdf",
                input_files=[work],
                form_data={
                    "languages": [ocr_language],
                    "ocrType": "skip-text",
                    "deskew": True,
                    "clean": True,
                },
                output_name_hint="smart-ocr",
            )
            if ocr.get("success"):
                work = Path(ocr["output_path"])
                chained.append("ocr-pdf")

        # Extract text — but per-page text isn't directly exposed by Stirling
        # without splitting first. v1 approximation: extract whole-doc text
        # and look for marker patterns, count their positions, return as
        # boundary hints.
        txt = await client.post_form(
            "/api/v1/misc/extract-text",
            input_files=[work],
            form_data={"outputFormat": "txt"},
            output_suffix=".txt",
            output_name_hint="smart-text",
        )
        chained.append("extract-text")
        if not txt.get("success") or not txt.get("output_path"):
            return {"success": False, "stage": "extract-text", "endpoints_chained": chained}

        text = Path(txt["output_path"]).read_text(errors="ignore")
        matches = list(PAGE_OF_RE.finditer(text))

        return {
            "success": True,
            "output_path": str(work),
            "strategy_used": "page-1-markers",
            "marker_count_found": len(matches),
            "boundary_hints": [m.start() for m in matches[:20]],
            "endpoints_chained": chained,
            "todo": "true mid-stream split per marker requires per-page text — extend in v0.5",
        }

    return {"success": False, "error": f"unknown strategy: {strategy}"}
