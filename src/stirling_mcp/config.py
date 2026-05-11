"""Stirling-PDF MCP — runtime configuration loaded from environment variables.

All values overridable via env. Defaults assume the MCP runs inside the same
Docker network as a Stirling-PDF container.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Stirling MCP server.

    Reads STIRLING_URL, STIRLING_API_KEY, OUTPUT_DIR, CACHE_DIR, LOG_LEVEL,
    PORT, HOST, MAX_CONCURRENT_REQUESTS, REQUEST_TIMEOUT, ENABLE_CACHE.
    """

    # Backend
    stirling_url: str
    stirling_api_key: str | None
    request_timeout: float
    max_concurrent_requests: int

    # MCP server
    host: str
    port: int

    # Output handling
    output_dir: Path
    cache_dir: Path
    enable_cache: bool

    # Cross-MCP
    qgis_mcp_url: str | None
    ifc_mcp_url: str | None
    nobrainr_url: str | None

    # Logging
    log_level: str


def load_settings() -> Settings:
    output_dir = Path(os.environ.get("OUTPUT_DIR", "/output"))
    cache_dir = Path(os.environ.get("CACHE_DIR", "/cache"))
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        stirling_url=os.environ.get(
            "STIRLING_URL", "http://stirling-pdf:8080"
        ).rstrip("/"),
        stirling_api_key=os.environ.get("STIRLING_API_KEY") or None,
        request_timeout=float(os.environ.get("REQUEST_TIMEOUT", "300")),
        max_concurrent_requests=int(os.environ.get("MAX_CONCURRENT_REQUESTS", "4")),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8087")),
        output_dir=output_dir,
        cache_dir=cache_dir,
        enable_cache=os.environ.get("ENABLE_CACHE", "true").lower() == "true",
        qgis_mcp_url=os.environ.get("QGIS_MCP_URL"),
        ifc_mcp_url=os.environ.get("IFC_MCP_URL"),
        nobrainr_url=os.environ.get("NOBRAINR_URL"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )


SETTINGS = load_settings()
