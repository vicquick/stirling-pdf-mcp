"""Layer-1 raw wrappers — Stirling `Misc` category (24 endpoints).

Compress, OCR, metadata, extract images/text, watermark, page numbers,
stamps, attachments, JS removal, link removal, repair, flatten.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.server import mcp


@mcp.tool()
async def pdf_compress(
    input_file: str,
    optimization_level: int = 5,
    convert_to_grayscale: bool = False,
    expected_output_size: str | None = None,
    linearize: bool = False,
) -> dict:
    """Reduce PDF size via Ghostscript-style optimization.

    `optimization_level` 1-9 trades quality for size — 1 = highest quality,
    9 = smallest file (heavy compression of images). 5 is a balanced default.
    `expected_output_size` ('500KB', '5MB') iteratively tunes settings to hit a
    target — slower but precise.
    `linearize` enables fast-web-view (linearised PDF) for streaming display.
    """
    return await get_client().post_form(
        "/api/v1/misc/compress-pdf",
        input_files=[Path(input_file)],
        form_data={
            "optimizeLevel": optimization_level,
            "expectedOutputSize": expected_output_size,
            "convertToGrayscale": convert_to_grayscale,
            "linearize": linearize,
        },
        output_name_hint="compressed",
    )


@mcp.tool()
async def pdf_ocr(
    input_file: str,
    languages: list[str] | None = None,
    sidecar: bool = False,
    deskew: bool = True,
    clean: bool = True,
    clean_final: bool = False,
    ocr_type: Literal["skip-text", "force-ocr", "Normal"] = "skip-text",
    remove_images_after: bool = False,
) -> dict:
    """Make a scanned PDF searchable via OCR (powered by OCRmyPDF + Tesseract).

    `languages` is a list of ISO codes — e.g. `["eng"]`, `["eng", "deu"]`,
    `["fra"]`. Multi-lang is slower but necessary for mixed-language documents.
    Defaults to English if not specified.

    Flags:
        deskew: rotate skewed pages straight before OCR (improves accuracy)
        clean: remove specks/noise pre-OCR (also improves accuracy)
        clean_final: keep the cleaned image in the output (slightly smaller file
            but loses original artistic noise — rarely wanted for archival)
        ocr_type: 'skip-text' skips pages that already have text (fastest, default).
            'force-ocr' re-OCRs even pages with text (use if existing OCR is bad).
        sidecar: also produce a .txt sidecar with extracted text
        remove_images_after: strip images post-OCR — useful for text-only archive
    """
    return await get_client().post_form(
        "/api/v1/misc/ocr-pdf",
        input_files=[Path(input_file)],
        form_data={
            "languages": languages or ["eng"],
            "sidecar": sidecar,
            "deskew": deskew,
            "clean": clean,
            "cleanFinal": clean_final,
            "ocrType": ocr_type,
            "removeImagesAfter": remove_images_after,
        },
        output_name_hint="ocr",
    )


@mcp.tool()
async def pdf_extract_images(
    input_file: str,
    format: Literal["png", "jpeg", "gif"] = "png",
    allow_duplicates: bool = False,
) -> dict:
    """Extract every embedded image from a PDF as a ZIP of image files.

    `format` controls output image type. `allow_duplicates=False` deduplicates
    identical images (saves disk for documents with repeated logos/icons).
    """
    return await get_client().post_form(
        "/api/v1/misc/extract-image-scans",
        input_files=[Path(input_file)],
        form_data={"format": format, "allowDuplicates": allow_duplicates},
        output_suffix=".zip",
        output_name_hint="images",
    )


@mcp.tool()
async def pdf_extract_text(
    input_file: str,
    output_format: Literal["txt", "html"] = "txt",
) -> dict:
    """Extract all text content from a PDF.

    Use this for downstream NLP / search / RAG storage. For PDFs without
    embedded text (scanned), run `pdf_ocr` first or use the composite
    `extract_searchable_text` which OCRs if needed then extracts.
    """
    return await get_client().post_form(
        "/api/v1/misc/extract-text",
        input_files=[Path(input_file)],
        form_data={"outputFormat": output_format},
        output_suffix=f".{output_format}",
        output_name_hint="text",
    )


@mcp.tool()
async def pdf_get_metadata(input_file: str) -> dict:
    """Read the metadata fields (title, author, subject, keywords, creator,
    producer, creation date, mod date, custom keys) of a PDF.
    """
    return await get_client().post_form(
        "/api/v1/misc/metadata",
        input_files=[Path(input_file)],
        output_suffix=".json",
    )


@mcp.tool()
async def pdf_update_metadata(
    input_file: str,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
    creator: str | None = None,
    producer: str | None = None,
    creation_date: str | None = None,
    modification_date: str | None = None,
    delete_all: bool = False,
) -> dict:
    """Set or clear PDF metadata fields.

    Any field left as None is left unchanged. `delete_all=True` strips all
    metadata first (then applies any provided fields) — used in privacy
    workflows where you want to scrub authorship before publication.
    Dates accept ISO 8601: `2026-05-11T10:00:00Z`.
    """
    return await get_client().post_form(
        "/api/v1/misc/update-metadata",
        input_files=[Path(input_file)],
        form_data={
            "title": title,
            "author": author,
            "subject": subject,
            "keywords": keywords,
            "creator": creator,
            "producer": producer,
            "creationDate": creation_date,
            "modificationDate": modification_date,
            "deleteAll": delete_all,
        },
        output_name_hint="metadata-updated",
    )


@mcp.tool()
async def pdf_add_watermark(
    input_file: str,
    watermark_text: str,
    alphabet: Literal["roman", "arabic", "japanese", "korean", "chinese"] = "roman",
    font_size: int = 30,
    rotation: int = 0,
    opacity: float = 0.5,
    width_spacer: int = 50,
    height_spacer: int = 50,
    color: str = "#d3d3d3",
    convert_pdf_to_image: bool = False,
) -> dict:
    """Stamp a tiled text watermark across every page.

    For 'CONFIDENTIAL' / 'DRAFT' / 'COPY' markings. `convert_pdf_to_image=True`
    rasterises the watermark into the page content so it cannot be removed by
    editing the PDF — slower but unforgeable.

    Colour accepts hex (`#RRGGBB`). Rotation in degrees.
    """
    return await get_client().post_form(
        "/api/v1/misc/add-watermark",
        input_files=[Path(input_file)],
        form_data={
            "watermarkText": watermark_text,
            "alphabet": alphabet,
            "fontSize": font_size,
            "rotation": rotation,
            "opacity": opacity,
            "widthSpacer": width_spacer,
            "heightSpacer": height_spacer,
            "customColor": color,
            "convertPDFToImage": convert_pdf_to_image,
        },
        output_name_hint="watermarked",
    )


@mcp.tool()
async def pdf_add_page_numbers(
    input_file: str,
    position: int = 5,
    starting_number: int = 1,
    pages_to_number: str = "all",
    custom_margin: Literal["small", "medium", "large", "x-large"] = "small",
    custom_text: str = "{n}",
    font_size: int = 12,
    font_type: Literal["Helvetica", "Courier", "Times-Roman"] = "Helvetica",
) -> dict:
    """Add page numbers to a PDF.

    `position` 1-9 maps to the 9-point grid (1=top-left, 5=center-bottom,
    9=bottom-right). `custom_text` accepts `{n}` for current page, `{total}`
    for total pages — e.g. `"Page {n} of {total}"`.
    """
    return await get_client().post_form(
        "/api/v1/misc/add-page-numbers",
        input_files=[Path(input_file)],
        form_data={
            "position": position,
            "startingNumber": starting_number,
            "pagesToNumber": pages_to_number,
            "customMargin": custom_margin,
            "customText": custom_text,
            "fontSize": font_size,
            "fontType": font_type,
        },
        output_name_hint="numbered",
    )


@mcp.tool()
async def pdf_add_stamp(
    input_file: str,
    stamp_text: str | None = None,
    stamp_image: str | None = None,
    page_numbers: str = "all",
    position: int = 5,
    rotation: int = 0,
    opacity: float = 0.5,
    override_x: float | None = None,
    override_y: float | None = None,
    font_size: int = 30,
    font_type: Literal["Helvetica", "Courier", "Times-Roman"] = "Helvetica",
    margin: Literal["small", "medium", "large", "x-large"] = "medium",
    custom_color: str = "#000000",
) -> dict:
    """Stamp text or an image onto pages.

    Either `stamp_text` OR `stamp_image` (path to PNG/JPG). For exact placement
    pass `override_x`/`override_y` (PDF coords, points). Otherwise `position` uses
    the 9-point grid.

    Common uses: "RECEIVED" stamps, logo stamps, approval seals.
    """
    return await get_client().post_form(
        "/api/v1/misc/add-stamp",
        input_files=[Path(input_file)],
        form_data={
            "stampText": stamp_text,
            "stampImage": stamp_image,  # Stirling expects a separate upload; for now we pass path
            "pageNumbers": page_numbers,
            "position": position,
            "rotation": rotation,
            "opacity": opacity,
            "overrideX": override_x,
            "overrideY": override_y,
            "fontSize": font_size,
            "fontType": font_type,
            "customMargin": margin,
            "customColor": custom_color,
        },
        output_name_hint="stamped",
    )


@mcp.tool()
async def pdf_flatten(input_file: str, flatten_only_forms: bool = False) -> dict:
    """Flatten annotations + form fields into the page content (un-editable after).

    Required step before signing or archiving — prevents downstream apps from
    removing redactions, signatures, or filled fields. `flatten_only_forms=True`
    keeps annotations interactive but bakes form fields.
    """
    return await get_client().post_form(
        "/api/v1/misc/flatten",
        input_files=[Path(input_file)],
        form_data={"flattenOnlyForms": flatten_only_forms},
        output_name_hint="flattened",
    )


@mcp.tool()
async def pdf_repair(input_file: str) -> dict:
    """Attempt to repair a corrupted/malformed PDF.

    Uses Ghostscript to re-write the PDF structure. Won't recover irrecoverable
    data but fixes common 'document is damaged' errors.
    """
    return await get_client().post_form(
        "/api/v1/misc/repair",
        input_files=[Path(input_file)],
        output_name_hint="repaired",
    )


@mcp.tool()
async def pdf_remove_javascript(input_file: str) -> dict:
    """Strip all JavaScript from a PDF.

    Security best practice for PDFs from untrusted sources — JS in PDFs can be
    an attack vector. Run this before forwarding suspect PDFs.
    """
    return await get_client().post_form(
        "/api/v1/misc/remove-javascript",
        input_files=[Path(input_file)],
        output_name_hint="js-removed",
    )


@mcp.tool()
async def pdf_remove_annotations(input_file: str) -> dict:
    """Strip all annotations (comments, notes, highlights) from a PDF."""
    return await get_client().post_form(
        "/api/v1/misc/remove-annotations",
        input_files=[Path(input_file)],
        output_name_hint="anno-removed",
    )


@mcp.tool()
async def pdf_remove_links(input_file: str) -> dict:
    """Strip all clickable links (internal + external) from a PDF."""
    return await get_client().post_form(
        "/api/v1/misc/remove-links",
        input_files=[Path(input_file)],
        output_name_hint="links-removed",
    )


@mcp.tool()
async def pdf_remove_blanks(input_file: str, threshold: int = 10, white_percent: float = 99.9) -> dict:
    """Detect and remove blank pages from a PDF.

    `threshold` 0-255 is the pixel-darkness cutoff. `white_percent` is the
    minimum % of pixels above the threshold for a page to be considered blank.
    Defaults match typical scanned-document blanks.
    """
    return await get_client().post_form(
        "/api/v1/misc/remove-blanks",
        input_files=[Path(input_file)],
        form_data={"threshold": threshold, "whitePercent": white_percent},
        output_name_hint="no-blanks",
    )


@mcp.tool()
async def pdf_unlock_forms(input_file: str) -> dict:
    """Make a flattened/locked PDF form interactive again.

    Use when you receive a 'locked' PDF form that should be fillable but isn't.
    Stirling re-creates the field structure when detectable.
    """
    return await get_client().post_form(
        "/api/v1/misc/unlock-pdf-forms",
        input_files=[Path(input_file)],
        output_name_hint="forms-unlocked",
    )
