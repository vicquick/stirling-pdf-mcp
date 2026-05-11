"""Minimal MCP-over-Streamable-HTTP client for cross-MCP composites.

Used by Layer-3 composites that need to call other MCP servers in the same
namespace (ifc-mcp, qgis-mcp, blender-mcp, flux-mcp, nobrainr, svg-mcp).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx

log = logging.getLogger("stirling_mcp.utils.mcp_client")


class CrossMCPError(RuntimeError):
    pass


async def call_mcp_tool(
    endpoint: str,
    tool_name: str,
    args: dict[str, Any],
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Call a tool on another Streamable-HTTP MCP server.

    Args:
        endpoint: full URL to MCP server (e.g. ``http://qgis-mcp:8081/mcp/``)
        tool_name: tool to invoke
        args: arguments dict
        timeout: request timeout

    Returns:
        Parsed dict result. If the tool returned structured content, that's
        returned directly. Otherwise the raw text block.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if not endpoint.endswith("/"):
        endpoint = endpoint + "/"
    client_name = f"stirling-mcp-{uuid.uuid4().hex[:6]}"

    async with httpx.AsyncClient(timeout=timeout) as h:
        # Initialize
        init = await h.post(
            endpoint,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": client_name, "version": "1.0"},
                },
            },
            follow_redirects=True,
        )
        sid = init.headers.get("mcp-session-id")
        if not sid:
            raise CrossMCPError(f"no session id from {endpoint}: {init.text[:200]}")
        h2 = {**headers, "Mcp-Session-Id": sid}
        await h.post(
            endpoint,
            headers=h2,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            follow_redirects=True,
        )

        # tools/call
        r = await h.post(
            endpoint,
            headers=h2,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
            follow_redirects=True,
        )

    # Parse SSE response
    for line in r.text.splitlines():
        if line.startswith("data: "):
            try:
                d = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            result = d.get("result", {})
            if result.get("isError"):
                content = result.get("content", [])
                err = content[0].get("text", "") if content else "unknown error"
                raise CrossMCPError(f"{tool_name}@{endpoint}: {err[:300]}")
            struct = result.get("structuredContent")
            if struct:
                return struct
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    return {"text": content[0]["text"]}
            return result
    raise CrossMCPError(f"no SSE data from {endpoint}")
