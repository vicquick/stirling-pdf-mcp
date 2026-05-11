"""Layer-1 raw wrappers — Stirling `Convert` category (32 endpoints).

PDF <-> Word/Excel/PowerPoint/HTML/Markdown/Images/CSV/XML/EML/EPUB/PDF-A,
plus URL-to-PDF and vector-to-PDF.

This module ships the highest-traffic conversions as first-class tools;
remaining specialised conversions will be added in subsequent commits — each
follows the same shape so adding more is mechanical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_to_images(
    input_file: str,
    image_format: Literal["png", "jpeg", "gif", "webp"] = "png",
    single_or_multiple: Literal["single", "multiple"] = "multiple",
    color_type: Literal["color", "greyscale", "blackwhite"] = "color",
    dpi: int = 300,
) -> dict:
    """Render PDF pages to images.

    `single_or_multiple`:
      - `multiple` → one image per page, returned as ZIP
      - `single` → one tall image with all pages stacked

    `dpi` 72-600. 300 is print quality, 150 is web quality, 600 is for AEC
    drawings or fine-art reproduction.
    """
    suffix = ".zip" if single_or_multiple == "multiple" else f".{image_format}"
    return await get_client().post_form(
        "/api/v1/convert/pdf/img",
        input_files=[Path(input_file)],
        form_data={
            "imageFormat": image_format,
            "singleOrMultiple": single_or_multiple,
            "colorType": color_type,
            "dpi": dpi,
        },
        output_suffix=suffix,
        output_name_hint="rendered",
    )


@mcp.tool()
async def images_to_pdf(
    input_files: list[str],
    stretch: bool = False,
    auto_rotate: bool = True,
    color_type: Literal["color", "greyscale", "blackwhite"] = "color",
) -> dict:
    """Combine images (JPG/PNG/etc) into a single PDF.

    `stretch=True` fills each page with the image (may distort).
    `auto_rotate=True` rotates landscape images to landscape pages.
    """
    return await get_client().post_form(
        "/api/v1/convert/img/pdf",
        input_files=[Path(p) for p in input_files],
        form_data={
            "stretch": stretch,
            "autoRotate": auto_rotate,
            "colorType": color_type,
        },
        output_name_hint="from-images",
    )


@mcp.tool()
async def pdf_to_word(input_file: str, output_format: Literal["docx", "doc", "odt"] = "docx") -> dict:
    """Convert a PDF to an editable Word document (via LibreOffice).

    Quality depends heavily on the source PDF — text-based PDFs convert well,
    scanned PDFs without OCR convert poorly (run `pdf_ocr` first).
    """
    return await get_client().post_form(
        "/api/v1/convert/pdf/word",
        input_files=[Path(input_file)],
        form_data={"outputFormat": output_format},
        output_suffix=f".{output_format}",
        output_name_hint="word",
    )


@mcp.tool()
async def word_to_pdf(input_file: str) -> dict:
    """Convert a Word document (.docx/.doc/.odt) to PDF via LibreOffice."""
    return await get_client().post_form(
        "/api/v1/convert/file/pdf",
        input_files=[Path(input_file)],
        output_name_hint="from-word",
    )


@mcp.tool()
async def pdf_to_pdfa(
    input_file: str,
    output_format: Literal["pdfa-1b", "pdfa-1a", "pdfa-2b", "pdfa-3b"] = "pdfa-2b",
) -> dict:
    """Convert to PDF/A for long-term archival.

    Compliance levels:
      - `pdfa-1b` (oldest, broadest support, no transparency)
      - `pdfa-2b` (default, supports JPEG2000)
      - `pdfa-3b` (allows attachments — useful for embedded source files)
      - `pdfa-1a` / `pdfa-2a` (stricter, require tagged structure for accessibility)
    """
    return await get_client().post_form(
        "/api/v1/convert/pdf/pdfa",
        input_files=[Path(input_file)],
        form_data={"outputFormat": output_format},
        output_name_hint=output_format,
    )


@mcp.tool()
async def html_to_pdf(input_file: str, zoom: float = 1.0) -> dict:
    """Convert an HTML file to PDF (WeasyPrint).

    For URL-to-PDF use `url_to_pdf`. For Markdown use `markdown_to_pdf`.
    """
    return await get_client().post_form(
        "/api/v1/convert/html/pdf",
        input_files=[Path(input_file)],
        form_data={"zoom": zoom},
        output_name_hint="from-html",
    )


@mcp.tool()
async def url_to_pdf(url: str) -> dict:
    """Fetch a URL and render it to PDF.

    ⚠️ Stirling's URL-to-PDF requires `system.enableUrlToPDF=true` server-side
    AND is marked INTERNAL ONLY due to known SSRF risks. Don't expose to
    untrusted users.
    """
    return await get_client().post_form(
        "/api/v1/convert/url/pdf",
        form_data={"urlInput": url},
        output_name_hint="from-url",
    )


@mcp.tool()
async def pdf_to_markdown(input_file: str) -> dict:
    """Convert a PDF to Markdown."""
    return await get_client().post_form(
        "/api/v1/convert/pdf/markdown",
        input_files=[Path(input_file)],
        output_suffix=".md",
        output_name_hint="markdown",
    )


@mcp.tool()
async def markdown_to_pdf(input_file: str) -> dict:
    """Convert Markdown to PDF (via Pandoc/LaTeX or WeasyPrint depending on backend)."""
    return await get_client().post_form(
        "/api/v1/convert/markdown/pdf",
        input_files=[Path(input_file)],
        output_name_hint="from-markdown",
    )


@mcp.tool()
async def pdf_to_csv(input_file: str, page_id: int = 1) -> dict:
    """Extract tabular data from a single PDF page as CSV."""
    return await get_client().post_form(
        "/api/v1/convert/pdf/csv",
        input_files=[Path(input_file)],
        form_data={"pageId": page_id},
        output_suffix=".csv",
        output_name_hint=f"page-{page_id}",
    )


# TODO: add pdf_to_excel, pdf_to_pptx, pdf_to_xml, pdf_to_html, eml_to_pdf,
# epub_to_pdf, vector_to_pdf, book_to_pdf, file_to_pdf. Mechanical pattern.
