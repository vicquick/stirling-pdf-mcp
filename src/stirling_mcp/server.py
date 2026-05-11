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

from starlette.requests import Request
from starlette.responses import JSONResponse

from stirling_mcp.app import mcp
from stirling_mcp.config import SETTINGS

logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("stirling_mcp")


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

    # Auto-generated raw wrappers (Layer 1 fill-out)
    from stirling_mcp.tools.auto import (  # noqa: F401
        general_auto,
        misc_auto,
        security_auto,
        convert_auto,
        forms_auto,
        filter_auto,
        analysis_auto,
        pipeline_auto,
    )

    # Layer 2 — generic composites
    from stirling_mcp.tools.composites import (  # noqa: F401
        invoice,
        redact,
        archive,
        sign,
        merge,
        compare,
        legal,
        form_batch,
        print_web,
        share,
        stamps,
        ai_summary,
        memory,
    )

    # Layer 3 — AEC + cross-MCP
    from stirling_mcp.tools.composites.aec import (  # noqa: F401
        drawing_set,
        titleblock,
        submittal,
    )


_register_layers()


@mcp.custom_route("/health", methods=["GET"])
async def http_health(request: Request) -> JSONResponse:
    """HTTP healthcheck endpoint. Always 200 OK; backend probe is the
    `stirling_health` MCP tool."""
    return JSONResponse({"status": "ok", "name": "stirling-pdf-mcp"})


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
    import os

    # FastMCP <0.5 reads host/port from FASTMCP_HOST / FASTMCP_PORT env vars
    os.environ.setdefault("FASTMCP_HOST", SETTINGS.host)
    os.environ.setdefault("FASTMCP_PORT", str(SETTINGS.port))
    log.info(
        "Starting Stirling-PDF MCP on %s:%d → backend %s",
        SETTINGS.host,
        SETTINGS.port,
        SETTINGS.stirling_url,
    )
    # Pass host/port if FastMCP accepts them, else they're already in env
    try:
        mcp.run(transport="streamable-http", host=SETTINGS.host, port=SETTINGS.port)
    except TypeError:
        mcp.run(transport="streamable-http")
