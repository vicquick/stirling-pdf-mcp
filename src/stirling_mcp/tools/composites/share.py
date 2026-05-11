"""Composite — password protect + Stirling sharing link."""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp


@mcp.tool()
async def password_protect_share(
    input_file: str,
    password: str,
    prevent_modify: bool = True,
    prevent_extract: bool = True,
) -> dict:
    """Encrypt a PDF for sharing.

    Applies AES-256, sets restrictive permissions by default. To also generate
    a Stirling-hosted share link, ensure `storage.sharing.enabled=true` on the
    backend and use the Storage API endpoints directly (see tag File Storage).

    Args:
        password: user password required to open
        prevent_modify: forbid edits
        prevent_extract: forbid copy/extract
    """
    return await get_client().post_form(
        "/api/v1/security/add-password",
        input_files=[Path(input_file)],
        form_data={
            "password": password,
            "ownerPassword": password,
            "keyLength": 256,
            "preventModify": prevent_modify,
            "preventExtractContent": prevent_extract,
        },
        output_name_hint="shared-protected",
    )
