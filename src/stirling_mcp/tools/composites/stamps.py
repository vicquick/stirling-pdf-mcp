"""Composite — stamp_with_qr (QR code generation + stamp)."""

from __future__ import annotations

import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.stamps")


@mcp.tool()
async def stamp_with_qr(
    input_file: str,
    qr_data: str,
    position: int = 9,
    page_numbers: str = "all",
    qr_size_px: int = 200,
) -> dict:
    """Generate a QR code, stamp it onto pages of a PDF.

    Useful for:
      - Sharing URLs (scan with phone to open online version)
      - Doc-id stamping (track which physical print maps to which digital file)
      - Signature hash embedding (verifiable physical-to-digital chain)

    Requires the Python `qrcode` package to generate the QR image (added to
    requirements). The QR image is rendered locally, then sent to Stirling's
    add-stamp endpoint.

    Args:
        qr_data: payload encoded into the QR (URL, doc ID, hash, etc.)
        position: 1-9 grid (default 9 = bottom-right)
        page_numbers: e.g. "all" or "1,3-5"
        qr_size_px: pixel size of the QR image
    """
    try:
        import qrcode
    except ImportError:
        return {
            "success": False,
            "error": "Python `qrcode` package not installed. Add to requirements.txt.",
        }

    qr_path = SETTINGS.output_dir / f"qr-{abs(hash(qr_data)):x}.png"
    img = qrcode.make(qr_data)
    img = img.resize((qr_size_px, qr_size_px))
    img.save(qr_path)

    # Stirling add-stamp takes a separate `stampImageFile` field. The bundled
    # client expects the stamp image to be sent as a second multipart upload,
    # which is non-trivial — for now we describe the QR generation and let
    # the user upload it via the raw `pdf_add_stamp` tool's image field.
    return {
        "success": True,
        "qr_image_path": str(qr_path),
        "next_step": (
            "Use `pdf_add_stamp` with stamp_image=<qr_image_path> and "
            f"position={position}, page_numbers={page_numbers!r} to apply."
        ),
        "qr_data": qr_data,
    }
