"""Stirling-PDF MCP server — FastMCP entrypoint.

Exposes the full Stirling-PDF surface (260 endpoints) plus 28 composite
workflow tools to MCP clients via streamable-http transport on PORT 8087.

Tool catalog layers:
    Layer 1 — raw 1:1 endpoint wrappers, auto-registered from tools/raw/*
    Layer 2 — generic composite workflows (invoice, redact, archive, ...)
    Layer 3 — AEC + cross-MCP composites (drawing sets, ifc refs, qgis layers)

Run:
    python -m stirling_mcp.server
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from stirling_mcp.config import SETTINGS

logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("stirling_mcp")


mcp = FastMCP(
    "stirling-pdf",
    instructions=(
        "Stirling-PDF MCP server. Exposes the full Stirling-PDF 2.10+ surface "
        "(260 REST operations) as 1:1 tools, plus 28 composite workflow tools "
        "for high-value patterns (invoice prep, GDPR/HIPAA redaction, PDF/A "
        "archive, signing ceremonies, AEC drawing sets, cross-MCP integrations "
        "with QGIS / IFC / Blender / Flux / SVG / nobrainr). When a user asks "
        "for any PDF operation, prefer the most specific composite if one fits, "
        "else fall back to the raw endpoint wrapper. Inputs are file paths; "
        "outputs are saved to OUTPUT_DIR and returned as `output_path`."
    ),
)


def _register_layers() -> None:
    """Import every tool module so its @mcp.tool() decorators fire."""
    # Layer 1 — raw wrappers
    from stirling_mcp.tools import (  # noqa: F401  side-effect: register tools
        general,
        misc,
        security,
        convert,
        forms,
        analysis,
        filter as filter_tools,
        ai,
    )

    # Layer 2 — generic composites
    from stirling_mcp.tools.composites import (  # noqa: F401
        invoice,
        redact,
        archive,
        sign,
        merge,
        compare,
    )

    # Layer 3 — AEC + cross-MCP (stubs until v0.3)
    from stirling_mcp.tools.composites.aec import (  # noqa: F401
        drawing_set,
    )


_register_layers()


@mcp.tool()
async def stirling_health() -> dict:
    """Probe the Stirling-PDF backend's health endpoint.

    Use this as a first-call sanity check when an agent's PDF operations are
    failing — confirms the backend is reachable and returning the expected
    `info/status` payload.

    Returns:
        dict with `success`, `endpoint`, `elapsed_ms`, and either `json_body`
        (Stirling's status doc) or `error` (on failure).
    """
    from stirling_mcp.client import get_client

    return await get_client().health()


if __name__ == "__main__":
    log.info(
        "Starting Stirling-PDF MCP on %s:%d → backend %s",
        SETTINGS.host,
        SETTINGS.port,
        SETTINGS.stirling_url,
    )
    mcp.run(transport="streamable-http", host=SETTINGS.host, port=SETTINGS.port)
