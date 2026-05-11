"""Layer-1 raw wrappers — Stirling `AI Tools` category (2 endpoints).

pdf-comment-agent (LLM annotates the PDF with comments)
math-auditor-agent (checks numerical consistency in invoices / engineering calcs)
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_ai_comment(input_file: str, prompt: str) -> dict:
    """Run Stirling's pdf-comment-agent — an LLM that annotates the PDF with
    inline comments based on the given prompt.

    Examples:
      - prompt: "Flag any inconsistent dates or contradictory claims"
      - prompt: "Mark up the paragraphs that need legal review"
      - prompt: "Add a comment summarising each section"

    Requires Stirling's AI backend to be configured (LLM API key on the server).
    """
    return await get_client().post_form(
        "/api/v1/ai/tools/pdf-comment-agent",
        input_files=[Path(input_file)],
        form_data={"prompt": prompt},
        output_name_hint="ai-commented",
    )


@mcp.tool()
async def pdf_ai_math_audit(input_file: str) -> dict:
    """Run Stirling's math-auditor-agent — checks numerical consistency
    (sums, totals, sub-totals, calculations) and flags discrepancies.

    Useful for invoices, expense reports, engineering calculation sheets,
    financial statements.
    """
    return await get_client().post_form(
        "/api/v1/ai/tools/math-auditor-agent",
        input_files=[Path(input_file)],
        output_name_hint="math-audited",
    )
