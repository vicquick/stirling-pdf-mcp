"""Shared FastMCP instance.

Lives in its own module so that all tool modules import the SAME instance
regardless of whether the server is launched via ``python -m stirling_mcp.server``
(in which case server.py is loaded under both ``__main__`` and
``stirling_mcp.server``) or via a standard import.

The classic ``python -m`` double-import pitfall: tool modules importing the
FastMCP instance from ``stirling_mcp.server`` would get a freshly-constructed
copy that's distinct from the one being run as ``__main__``. All tools then
register on the wrong instance and disappear.
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP(
    "stirling-pdf",
    instructions=(
        "Stirling-PDF MCP server. Exposes the full Stirling-PDF 2.10+ surface "
        "(260 REST operations) as 1:1 tools, plus composite workflow tools for "
        "high-value patterns: invoice prep, GDPR/HIPAA/PCI redaction, PDF/A "
        "archive, signing ceremonies, AEC drawing sets (Bluebeam-style), and "
        "cross-MCP integrations with QGIS / IFC / Blender / Flux / SVG / "
        "nobrainr. When a user asks for any PDF operation, prefer the most "
        "specific composite if one fits, else fall back to the raw endpoint "
        "wrapper. Inputs are file paths; outputs are saved to OUTPUT_DIR and "
        "returned as ``output_path``."
    ),
)
