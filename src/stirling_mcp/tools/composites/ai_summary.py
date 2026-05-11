"""Composite — ai_summarise_pdf (LLM-driven cover page summary)."""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def ai_summarise_pdf(
    input_file: str,
    prompt: str = "Summarise this document in 3-5 bullet points covering main topics, key findings, and any action items.",
) -> dict:
    """Run Stirling's pdf-comment-agent with a summary prompt.

    Returns the commented PDF (Stirling inserts the summary as annotations).
    For a structured summary you can pass into a downstream pipeline, use the
    raw `pdf_ai_comment` and post-process the resulting annotations.
    """
    return await get_client().post_form(
        "/api/v1/ai/tools/pdf-comment-agent",
        input_files=[Path(input_file)],
        form_data={"prompt": prompt},
        output_name_hint="summarised",
    )
