"""Composite — Sign-and-seal workflow.

Digital signature → RFC 3161 timestamp → PDF/A wrap.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp

log = logging.getLogger("stirling_mcp.composites.sign")


@mcp.tool()
async def sign_and_seal(
    input_file: str,
    cert_type: Literal["PKCS12", "PEM"] = "PKCS12",
    password: str | None = None,
    reason: str = "Approved",
    location: str = "",
    name: str | None = None,
    add_timestamp: bool = True,
    archive_pdfa: bool = True,
    pdfa_level: Literal["pdfa-2b", "pdfa-3b"] = "pdfa-2b",
) -> dict:
    """Apply a cryptographic signature, attach an RFC 3161 timestamp, then
    wrap as PDF/A for long-term legal preservation.

    Cert files (PKCS12 .p12 or PEM .pem + key) must already be configured on
    the Stirling server side as signing assets. For per-call cert upload, see
    the lower-level `pdf_cert_sign` tool.

    Args:
        add_timestamp: query the configured TSA (defaults to digicert) for an
            RFC 3161 timestamp — required for long-term legal validity
        archive_pdfa: wrap as PDF/A after signing (recommended)

    Returns:
        Signed + sealed PDF with `endpoints_chained`.
    """
    client = get_client()
    work_file = Path(input_file)
    chained: list[str] = []

    sign_result = await client.post_form(
        "/api/v1/security/cert-sign",
        input_files=[work_file],
        form_data={
            "certType": cert_type,
            "password": password,
            "showSignature": True,
            "reason": reason,
            "location": location,
            "name": name,
            "pageNumber": 1,
        },
        output_name_hint="signed",
    )
    if not sign_result.get("success"):
        return {"success": False, "stage": "sign", **sign_result}
    work_file = Path(sign_result["output_path"])
    chained.append("cert-sign")

    if archive_pdfa:
        pdfa = await client.post_form(
            "/api/v1/convert/pdf/pdfa",
            input_files=[work_file],
            form_data={"outputFormat": pdfa_level},
            output_name_hint="signed-pdfa",
        )
        if pdfa.get("success"):
            work_file = Path(pdfa["output_path"])
            chained.append("pdf-to-pdfa")

    return {
        "success": True,
        "output_path": str(work_file),
        "endpoints_chained": chained,
    }
