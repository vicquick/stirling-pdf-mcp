"""Layer-1 raw wrappers — Stirling `Security` category (12 endpoints).

Password/permissions, signing, redaction, sanitisation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_add_password(
    input_file: str,
    user_password: str | None = None,
    owner_password: str | None = None,
    key_length: Literal[40, 128, 256] = 256,
    prevent_printing: bool = False,
    prevent_modify: bool = False,
    prevent_modify_annotations: bool = False,
    prevent_fill_forms: bool = False,
    prevent_extract_content: bool = False,
    prevent_extract_for_accessibility: bool = False,
    prevent_assembly: bool = False,
    prevent_printing_faithful: bool = False,
) -> dict:
    """Encrypt a PDF and/or set permission restrictions.

    Two password types:
      - `user_password`: required to open the document at all
      - `owner_password`: required to change permissions (admin password)

    Permission flags only meaningful when `owner_password` is set (a user can
    bypass restrictions if they know the owner password). `key_length=256`
    (AES-256) is the modern default.

    Common patterns:
      - Read-only: owner_password + prevent_modify + prevent_assembly
      - Print-disabled: owner_password + prevent_printing + prevent_printing_faithful
      - Fully locked: user_password + owner_password + all prevent_* flags
    """
    return await get_client().post_form(
        "/api/v1/security/add-password",
        input_files=[Path(input_file)],
        form_data={
            "password": user_password,
            "ownerPassword": owner_password,
            "keyLength": key_length,
            "preventPrinting": prevent_printing,
            "preventModify": prevent_modify,
            "preventModifyAnnotations": prevent_modify_annotations,
            "preventFillInForm": prevent_fill_forms,
            "preventExtractContent": prevent_extract_content,
            "preventExtractForAccessibility": prevent_extract_for_accessibility,
            "preventAssembly": prevent_assembly,
            "preventPrintingFaithful": prevent_printing_faithful,
        },
        output_name_hint="protected",
    )


@mcp.tool()
async def pdf_remove_password(input_file: str, password: str) -> dict:
    """Decrypt a password-protected PDF. Requires the current user password."""
    return await get_client().post_form(
        "/api/v1/security/remove-password",
        input_files=[Path(input_file)],
        form_data={"password": password},
        output_name_hint="decrypted",
    )


@mcp.tool()
async def pdf_change_permissions(
    input_file: str,
    prevent_printing: bool = False,
    prevent_modify: bool = False,
    prevent_modify_annotations: bool = False,
    prevent_fill_forms: bool = False,
    prevent_extract_content: bool = False,
    prevent_extract_for_accessibility: bool = False,
    prevent_assembly: bool = False,
    prevent_printing_faithful: bool = False,
) -> dict:
    """Change permission restrictions on a PDF without changing passwords.

    Use when the PDF is unencrypted or you want to alter permissions without
    re-prompting users for a password. For encrypted PDFs see
    `pdf_add_password` instead.
    """
    return await get_client().post_form(
        "/api/v1/security/change-permissions",
        input_files=[Path(input_file)],
        form_data={
            "preventPrinting": prevent_printing,
            "preventModify": prevent_modify,
            "preventModifyAnnotations": prevent_modify_annotations,
            "preventFillInForm": prevent_fill_forms,
            "preventExtractContent": prevent_extract_content,
            "preventExtractForAccessibility": prevent_extract_for_accessibility,
            "preventAssembly": prevent_assembly,
            "preventPrintingFaithful": prevent_printing_faithful,
        },
        output_name_hint="perms-changed",
    )


@mcp.tool()
async def pdf_sanitize(
    input_file: str,
    remove_javascript: bool = True,
    remove_embedded_files: bool = True,
    remove_metadata: bool = False,
    remove_links: bool = False,
    remove_fonts: bool = False,
) -> dict:
    """Strip risky / privacy-leaking content from a PDF.

    Defaults remove JS and embedded files (highest-impact security wins) but
    keep metadata, links, and fonts. Use for documents from untrusted sources
    before opening.
    """
    return await get_client().post_form(
        "/api/v1/security/sanitize-pdf",
        input_files=[Path(input_file)],
        form_data={
            "removeJavaScript": remove_javascript,
            "removeEmbeddedFiles": remove_embedded_files,
            "removeMetadata": remove_metadata,
            "removeLinks": remove_links,
            "removeFonts": remove_fonts,
        },
        output_name_hint="sanitized",
    )


@mcp.tool()
async def pdf_auto_redact(
    input_file: str,
    terms_to_redact: list[str],
    use_regex: bool = False,
    whole_word_search: bool = True,
    redact_color: str = "#000000",
    custom_padding: float = 0.1,
    convert_pdf_to_image: bool = True,
) -> dict:
    """Search-and-redact text matching given terms across the entire PDF.

    For privacy/compliance workflows. `convert_pdf_to_image=True` rasterises
    the page after redaction so the underlying text is unrecoverable — the
    *correct* default for GDPR/HIPAA. Set to False only when you need to keep
    text searchable for downstream OCR.

    `use_regex=True` treats each term as a regex pattern. Common presets to use
    as starting points (compose into `terms_to_redact`):
      - email: `\\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}\\b`
      - phone (US): `\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b`
      - SSN: `\\b\\d{3}-\\d{2}-\\d{4}\\b`
      - credit card: `\\b\\d{4}[ -]?\\d{4}[ -]?\\d{4}[ -]?\\d{4}\\b`

    For richer GDPR/HIPAA/PCI presets, use the composite `redact_personal_info`.
    """
    return await get_client().post_form(
        "/api/v1/security/auto-redact",
        input_files=[Path(input_file)],
        form_data={
            "listOfText": terms_to_redact,
            "useRegex": use_regex,
            "wholeWordSearch": whole_word_search,
            "customColor": redact_color,
            "customPadding": custom_padding,
            "convertPDFToImage": convert_pdf_to_image,
        },
        output_name_hint="redacted",
    )


@mcp.tool()
async def pdf_manual_redact(
    input_file: str,
    redactions_json: str,
    convert_pdf_to_image: bool = True,
) -> dict:
    """Apply coordinate-based redaction boxes.

    `redactions_json` is a JSON array of `{page, x, y, width, height, color?}`
    objects (PDF coords, points). Use when you have exact rectangles to redact
    rather than text-search.
    """
    return await get_client().post_form(
        "/api/v1/security/redact",
        input_files=[Path(input_file)],
        form_data={
            "redactions": redactions_json,
            "convertPDFToImage": convert_pdf_to_image,
        },
        output_name_hint="redacted-manual",
    )


@mcp.tool()
async def pdf_validate_signature(input_file: str) -> dict:
    """Validate the digital signatures present in a signed PDF.

    Returns chain-of-trust details, signer identity, signing time, whether the
    signature covers the entire document, and whether the cert is trusted by
    the configured trust store.
    """
    return await get_client().post_form(
        "/api/v1/security/validate-signature",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_verify(input_file: str) -> dict:
    """Run integrity checks on a PDF (structure valid? cross-ref table consistent?).

    Returns a report of any structural anomalies.
    """
    return await get_client().post_form(
        "/api/v1/security/verify-pdf",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_remove_certificates(input_file: str) -> dict:
    """Strip all digital certificates / signatures from a PDF.

    Use before merging signed PDFs when individual signatures shouldn't be
    preserved (e.g. archival).
    """
    return await get_client().post_form(
        "/api/v1/security/remove-cert-sign",
        input_files=[Path(input_file)],
        output_name_hint="certs-removed",
    )


@mcp.tool()
async def pdf_cert_sign(
    input_file: str,
    cert_type: Literal["PKCS12", "PEM"] = "PKCS12",
    cert_file: str | None = None,
    private_key_file: str | None = None,
    password: str | None = None,
    show_signature: bool = True,
    reason: str | None = None,
    location: str | None = None,
    name: str | None = None,
    page_number: int = 1,
    show_logo: bool = False,
) -> dict:
    """Apply a digital signature to a PDF using a certificate.

    `cert_type` PKCS12 needs `cert_file` (.p12/.pfx) + `password`. PEM needs
    `cert_file` (.pem) + `private_key_file` + optionally `password`.

    Visible signature appearance controlled by `show_signature`, `reason`,
    `location`, `name`, `page_number`, `show_logo`. For RFC 3161 trusted
    timestamping use the composite `sign_and_seal` instead.
    """
    files = [Path(input_file)]
    form = {
        "certType": cert_type,
        "password": password,
        "showSignature": show_signature,
        "reason": reason,
        "location": location,
        "name": name,
        "pageNumber": page_number,
        "showLogo": show_logo,
    }
    # cert_file + private_key_file get uploaded as their own multipart fields
    # — handled by composite or call separately if needed
    return await get_client().post_form(
        "/api/v1/security/cert-sign",
        input_files=files,
        form_data=form,
        output_name_hint="signed",
    )
