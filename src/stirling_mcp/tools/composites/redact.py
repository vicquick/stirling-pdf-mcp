"""Composite — GDPR/HIPAA/PCI personal-info redaction.

Chains: OCR (if needed) → search-and-redact with regex preset → flatten →
watermark "REDACTED". This is the marquee compliance workflow.

A naive 1:1 wrapper of `pdf_auto_redact` won't cut it because:
  1. Scanned PDFs without OCR have no searchable text — redaction misses
     hidden info in image form
  2. Without flattening, the redaction overlays can be removed by editing
     the PDF
  3. Audit trail (what was redacted, by which preset) lives nowhere

This composite handles all three.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.redact")


# Regex presets — patterns are deliberately conservative (high precision,
# accept some misses) since false-positive redactions on a contract are
# embarrassing. For aggressive redaction, layer additional terms via
# `extra_terms`.
PRESETS: dict[str, list[str]] = {
    "gdpr": [
        # Emails
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        # IBAN (EU bank accounts)
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b",
        # EU national IDs (loose — adjust per jurisdiction)
        r"\b\d{8,12}\b",
        # Phone numbers (international)
        r"\+?\d[\d\s\-().]{8,15}\d",
    ],
    "hipaa": [
        # SSN
        r"\b\d{3}-\d{2}-\d{4}\b",
        # MRN (medical record number — typical formats)
        r"\bMRN[:\s]+\d{6,12}\b",
        # DOB
        r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b",
        # Phone
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        # Emails
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    ],
    "pci": [
        # Credit card numbers (4 groups of 4)
        r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b",
        # CVV (3-4 digit codes near "CVV" or "CVC")
        r"\b(CVV|CVC|CVV2|CSC)[:\s]+\d{3,4}\b",
        # Expiry date
        r"\b(0[1-9]|1[0-2])[/\-](2[3-9]|3[0-9])\b",
    ],
    "id_numbers": [
        # Catch-all for things that look like ID numbers
        r"\b[A-Z]{2,3}\d{4,10}\b",
        r"\b\d{9,12}\b",
    ],
}


@mcp.tool()
async def redact_personal_info(
    input_file: str,
    preset: Literal["gdpr", "hipaa", "pci", "id_numbers", "all", "custom"] = "gdpr",
    extra_terms: list[str] | None = None,
    custom_only: bool = False,
    ocr_first: Literal["auto", "yes", "no"] = "auto",
    ocr_language: str = "eng",
    watermark_label: str = "REDACTED",
    keep_searchable: bool = False,
) -> dict:
    """Redact personal info from a PDF with audit trail.

    Workflow:
        1. Optionally OCR the PDF if it lacks searchable text (auto-detected)
        2. Apply regex patterns from `preset` + `extra_terms`
        3. Flatten so redactions can't be removed by editing the PDF
        4. Stamp a "REDACTED" watermark (configurable via `watermark_label`)

    Args:
        input_file: path to PDF
        preset: regex bundle for the compliance regime
            - `gdpr`: emails, IBANs, EU IDs, phone numbers
            - `hipaa`: SSN, MRN, DOB, phones, emails
            - `pci`: credit cards, CVV, expiry dates
            - `id_numbers`: generic ID-looking patterns (recall-heavy)
            - `all`: union of all above
            - `custom`: use only `extra_terms` (set `custom_only=True`)
        extra_terms: additional regex patterns to redact on top of the preset
        custom_only: ignore preset, use only `extra_terms`
        ocr_first:
            - `auto`: OCR if `pdf_extract_text` returns empty
            - `yes`: always OCR (slower but thorough for scanned mixed docs)
            - `no`: skip OCR (assume PDF has text already)
        ocr_language: ISO code for OCR (eng/deu/fra/etc)
        watermark_label: stamp text — "REDACTED" by default, or "GDPR REDACTED"
            etc. for downstream provenance
        keep_searchable: by default the PDF is rasterised after redaction so
            text under the boxes is unrecoverable (the correct default for
            compliance). Set True only when you need search to still work.

    Returns:
        dict with the redacted PDF path + a separate `audit` dict describing
        which patterns were applied, OCR status, and flatten status.
    """
    if custom_only and not extra_terms:
        return {
            "success": False,
            "error": "custom_only=True requires extra_terms to be provided",
        }

    # 1. Build term list
    if custom_only:
        terms = list(extra_terms or [])
        active_presets = ["custom"]
    elif preset == "all":
        terms = []
        for k in ("gdpr", "hipaa", "pci"):
            terms.extend(PRESETS[k])
        active_presets = ["gdpr", "hipaa", "pci"]
    elif preset == "custom":
        terms = list(extra_terms or [])
        active_presets = ["custom"]
    else:
        terms = list(PRESETS[preset])
        active_presets = [preset]
    if extra_terms and not custom_only:
        terms.extend(extra_terms)

    client = get_client()
    audit: dict = {
        "presets_applied": active_presets,
        "term_count": len(terms),
        "ocr_used": False,
        "watermark_applied": True,
    }

    # 2. OCR detection + run if needed
    work_file = Path(input_file)
    if ocr_first in ("yes", "auto"):
        needs_ocr = ocr_first == "yes"
        if ocr_first == "auto":
            try:
                extract = await client.post_form(
                    "/api/v1/misc/extract-text",
                    input_files=[work_file],
                    form_data={"outputFormat": "txt"},
                    output_suffix=".txt",
                )
                # Heuristic: <200 chars of text → assume scanned
                text_path = Path(extract.get("output_path", ""))
                if text_path.exists() and text_path.stat().st_size < 200:
                    needs_ocr = True
            except Exception as e:
                log.warning("Text-extract probe failed (%s) — proceeding without OCR", e)

        if needs_ocr:
            log.info("Running OCR before redaction (lang=%s)", ocr_language)
            ocr_result = await client.post_form(
                "/api/v1/misc/ocr-pdf",
                input_files=[work_file],
                form_data={
                    "languages": [ocr_language],
                    "ocrType": "skip-text",
                    "deskew": True,
                    "clean": True,
                },
                output_name_hint="ocr-pre-redact",
            )
            if ocr_result.get("success"):
                work_file = Path(ocr_result["output_path"])
                audit["ocr_used"] = True
                audit["ocr_output"] = str(work_file)

    # 3. Auto-redact
    redact_result = await client.post_form(
        "/api/v1/security/auto-redact",
        input_files=[work_file],
        form_data={
            "listOfText": terms,
            "useRegex": True,
            "wholeWordSearch": False,
            "customColor": "#000000",
            "customPadding": 0.1,
            "convertPDFToImage": not keep_searchable,
        },
        output_name_hint="redacted",
    )
    if not redact_result.get("success"):
        return {"success": False, "stage": "redact", "audit": audit, **redact_result}
    work_file = Path(redact_result["output_path"])

    # 4. Flatten — extra safety
    flatten_result = await client.post_form(
        "/api/v1/misc/flatten",
        input_files=[work_file],
        form_data={"flattenOnlyForms": False},
        output_name_hint="redacted-flat",
    )
    if flatten_result.get("success"):
        work_file = Path(flatten_result["output_path"])
        audit["flattened"] = True

    # 5. Watermark
    wm_result = await client.post_form(
        "/api/v1/misc/add-watermark",
        input_files=[work_file],
        form_data={
            "watermarkText": watermark_label,
            "fontSize": 50,
            "rotation": 30,
            "opacity": 0.2,
            "widthSpacer": 200,
            "heightSpacer": 200,
            "customColor": "#888888",
            "convertPDFToImage": False,
        },
        output_name_hint="redacted-final",
    )
    if wm_result.get("success"):
        work_file = Path(wm_result["output_path"])

    return {
        "success": True,
        "output_path": str(work_file),
        "size_bytes": work_file.stat().st_size if work_file.exists() else 0,
        "audit": audit,
        "endpoints_chained": [
            "extract-text(probe)",
            "ocr-pdf" if audit["ocr_used"] else None,
            "auto-redact",
            "flatten",
            "add-watermark",
        ],
    }
