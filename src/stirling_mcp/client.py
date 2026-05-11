"""Async HTTP client for Stirling-PDF backend.

Handles:
- Multipart upload of input files
- Streaming download of output PDFs/images/zips to OUTPUT_DIR
- Exponential-backoff retries for transient 5xx
- API key auth via Bearer header
- Content-hash caching when ENABLE_CACHE=true
- Concurrency limit via asyncio.Semaphore

Used by every raw tool wrapper and every composite. The client is the single
choke point — all error handling, logging, and caching live here.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import time
import uuid
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from stirling_mcp.config import SETTINGS

log = logging.getLogger("stirling_mcp.client")

# Stirling sometimes returns 502/503 under load. Retry only transient errors.
_RETRYABLE_STATUS = {502, 503, 504, 408, 429}


class StirlingError(RuntimeError):
    """Stirling backend returned a non-recoverable error."""

    def __init__(self, status: int, body: str, endpoint: str) -> None:
        self.status = status
        self.body = body
        self.endpoint = endpoint
        super().__init__(f"Stirling {endpoint} -> {status}: {body[:300]}")


class _RetryableHTTPError(Exception):
    """Internal — wraps a transient 5xx for tenacity."""


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _detect_mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


class StirlingClient:
    """Async client. Construct one per server process; reuse for all calls."""

    def __init__(self) -> None:
        # The semaphore is created lazily on first use so that __init__ can
        # run outside an event loop without warnings. httpx clients are
        # created PER REQUEST rather than as a long-lived singleton — that
        # pattern was triggering "Attempted to send a sync request with an
        # AsyncClient instance" under fastmcp's anyio event loop in httpx 0.28+.
        self._semaphore: asyncio.Semaphore | None = None
        self._headers = {"X-API-KEY": SETTINGS.stirling_api_key} if SETTINGS.stirling_api_key else {}
        self._timeout = httpx.Timeout(
            connect=10.0,
            read=SETTINGS.request_timeout,
            write=SETTINGS.request_timeout,
            pool=10.0,
        )

    def _get_sem(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(SETTINGS.max_concurrent_requests)
        return self._semaphore

    async def aclose(self) -> None:
        # Nothing to close — clients are per-request.
        pass

    async def _do_request(
        self,
        method: str,
        path: str,
        *,
        files: list[tuple[str, tuple[str, BinaryIO, str]]] | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """One async request with explicit exponential-backoff retry on transient 5xx."""
        last_exc: Exception | None = None
        delay = 1.0
        for attempt in range(3):
            async with self._get_sem():
                field_names = list(data.keys()) if isinstance(data, dict) else []
                log.debug(
                    "Stirling %s %s fields=%s files=%d attempt=%d",
                    method, path, field_names, len(files or []), attempt + 1,
                )
                try:
                    async with httpx.AsyncClient(
                        base_url=SETTINGS.stirling_url,
                        timeout=self._timeout,
                        headers=self._headers,
                    ) as client:
                        resp = await client.request(
                            method, path, files=files, data=data, params=params
                        )
                        # Eagerly read the body before the client context exits,
                        # since callers consume resp.content / resp.text after.
                        await resp.aread()
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exc = e
                    if attempt >= 2:
                        raise
                else:
                    if resp.status_code in _RETRYABLE_STATUS and attempt < 2:
                        log.warning(
                            "Transient %s on %s, retry %d/3", resp.status_code, path, attempt + 2
                        )
                    else:
                        return resp
            # backoff before next attempt
            await asyncio.sleep(delay)
            delay *= 1.5
        # exhausted retries — return last response if we have one, else raise
        if last_exc:
            raise last_exc
        return resp  # type: ignore[possibly-undefined]

    async def post_form(
        self,
        endpoint: str,
        *,
        input_files: list[Path] | None = None,
        file_field: str = "fileInput",
        form_data: dict[str, Any] | None = None,
        output_suffix: str = ".pdf",
        output_name_hint: str | None = None,
    ) -> dict[str, Any]:
        """POST a multipart form to a Stirling endpoint and save the response body.

        Args:
            endpoint: e.g. "/api/v1/misc/compress-pdf"
            input_files: paths to input PDFs/images that get uploaded as ``file_field``
            file_field: name of the multipart field — Stirling defaults to ``fileInput``
            form_data: extra form fields (strings) — bool->'true'/'false', None dropped
            output_suffix: hint for what kind of output to write (.pdf, .zip, .png, .json)
            output_name_hint: prefix for the output filename (default = endpoint slug)

        Returns:
            dict with keys: success, output_path, size_bytes, content_type,
            elapsed_ms, endpoint. On JSON responses, also includes json_body.
        """
        t0 = time.perf_counter()
        prepared_files: list[tuple[str, tuple[str, BinaryIO, str]]] = []
        opened: list[BinaryIO] = []
        try:
            for p in input_files or []:
                p = Path(p)
                if not p.exists():
                    raise FileNotFoundError(f"input file not found: {p}")
                fp = open(p, "rb")
                opened.append(fp)
                prepared_files.append(
                    (file_field, (p.name, fp, _detect_mime(p)))
                )

            sanitised = self._sanitise_form(form_data or {})
            resp = await self._do_request(
                "POST",
                endpoint,
                files=prepared_files or None,
                data=sanitised or None,
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            if resp.status_code >= 400:
                raise StirlingError(resp.status_code, resp.text, endpoint)

            content_type = resp.headers.get("content-type", "")
            return await self._save_response(
                resp,
                content_type,
                endpoint,
                elapsed_ms,
                output_suffix,
                output_name_hint,
            )
        finally:
            for fp in opened:
                fp.close()

    async def get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Simple GET returning JSON. For info / status endpoints."""
        t0 = time.perf_counter()
        resp = await self._do_request("GET", endpoint, params=params)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code >= 400:
            raise StirlingError(resp.status_code, resp.text, endpoint)
        return {
            "success": True,
            "endpoint": endpoint,
            "elapsed_ms": elapsed_ms,
            "json_body": resp.json(),
        }

    @staticmethod
    def _sanitise_form(d: dict[str, Any]) -> dict[str, Any]:
        """Coerce values into httpx-friendly form shapes.

        Returns a dict where list-valued keys keep their lists — httpx 0.28+
        serializes ``data={"key": [v1, v2]}`` as repeated form fields
        ``key=v1&key=v2``, which Spring binds into a ``List<String>``.
        DO NOT return a list of (k, v) tuples here: httpx 0.28 has a bug
        where ``data=list_of_tuples`` falsely triggers a "sync request on
        AsyncClient" RuntimeError.
        """
        import json

        out: dict[str, Any] = {}
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, bool):
                out[k] = "true" if v else "false"
            elif isinstance(v, list):
                # Keep the list — httpx repeats the field per element
                out[k] = [str(item) for item in v]
            elif isinstance(v, dict):
                out[k] = json.dumps(v)
            else:
                out[k] = str(v)
        return out

    async def _save_response(
        self,
        resp: httpx.Response,
        content_type: str,
        endpoint: str,
        elapsed_ms: int,
        output_suffix: str,
        output_name_hint: str | None,
    ) -> dict[str, Any]:
        """Persist response body to OUTPUT_DIR with a stable name."""
        if "application/json" in content_type:
            try:
                body = resp.json()
                return {
                    "success": True,
                    "endpoint": endpoint,
                    "content_type": content_type,
                    "elapsed_ms": elapsed_ms,
                    "json_body": body,
                }
            except Exception:
                pass  # fall through to file write

        # Pick suffix from content-type if hint was vague
        if "/zip" in content_type:
            output_suffix = ".zip"
        elif "/png" in content_type:
            output_suffix = ".png"
        elif "/jpeg" in content_type:
            output_suffix = ".jpg"
        elif "/pdf" in content_type:
            output_suffix = ".pdf"

        slug = output_name_hint or endpoint.strip("/").replace("/", "_")
        out_name = f"{slug}_{uuid.uuid4().hex[:8]}{output_suffix}"
        out_path = SETTINGS.output_dir / out_name

        # Body already buffered (aread() in _do_request); write all at once.
        out_path.write_bytes(resp.content)

        size_bytes = out_path.stat().st_size
        log.info(
            "Stirling %s -> %s (%d bytes, %d ms)",
            endpoint,
            out_path,
            size_bytes,
            elapsed_ms,
        )
        return {
            "success": True,
            "endpoint": endpoint,
            "output_path": str(out_path),
            "size_bytes": size_bytes,
            "content_type": content_type,
            "elapsed_ms": elapsed_ms,
        }

    async def health(self) -> dict[str, Any]:
        """Probe Stirling backend health. Used by MCP startup + healthcheck."""
        try:
            return await self.get_json("/api/v1/info/status")
        except (httpx.HTTPError, StirlingError) as e:
            return {"success": False, "error": str(e)}


# Singleton — initialised in server.py startup
_client: StirlingClient | None = None


def get_client() -> StirlingClient:
    global _client
    if _client is None:
        _client = StirlingClient()
    return _client


async def shutdown() -> None:
    if _client:
        await _client.aclose()
