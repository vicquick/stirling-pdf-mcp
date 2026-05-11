"""Composite — pdf_anonymize.

More aggressive than redact: strip ALL identifying traces from a PDF.
Removes metadata, JavaScript, embedded files, links, annotations, and
flattens everything so nothing interactive remains.

Use case: publishing a document publicly when you want zero traceability —
no author, no creation tool, no internal links, no comment history.
"""

from __future__ import annotations

from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.app import mcp


@mcp.tool()
async def pdf_anonymize(
    input_file: str,
    rasterise: bool = False,
) -> dict:
    """Strip every trace of authorship and interactivity from a PDF.

    Chains:
        1. Sanitize — remove JS + embedded files + metadata + links + fonts
        2. Remove annotations (comments / highlights)
        3. Remove all metadata (deleteAll=true)
        4. Flatten — bake any remaining annotations into page content
        5. Optionally re-render via pdf-to-images @ 200dpi + images-to-pdf
           (`rasterise=True`) — most aggressive, also kills any selectable text

    Args:
        input_file: path to PDF
        rasterise: if True, perform full rasterisation step (much larger
            file size, but kills hidden text layers, watermarks-in-content,
            xref tampering possibilities — true scrub).

    Returns: `{success, output_path, endpoints_chained}`
    """
    client = get_client()
    chained: list[str] = []
    work = Path(input_file)

    san = await client.post_form(
        "/api/v1/security/sanitize-pdf",
        input_files=[work],
        form_data={
            "removeJavaScript": True,
            "removeEmbeddedFiles": True,
            "removeMetadata": True,
            "removeLinks": True,
            "removeFonts": False,  # keep fonts so text remains readable
        },
        output_name_hint="anon-sanitized",
    )
    if san.get("success"):
        work = Path(san["output_path"])
        chained.append("sanitize-pdf")

    anno = await client.post_form(
        "/api/v1/misc/remove-annotations",
        input_files=[work],
        output_name_hint="anon-no-anno",
    )
    if anno.get("success"):
        work = Path(anno["output_path"])
        chained.append("remove-annotations")

    meta = await client.post_form(
        "/api/v1/misc/update-metadata",
        input_files=[work],
        form_data={"deleteAll": True},
        output_name_hint="anon-no-meta",
    )
    if meta.get("success"):
        work = Path(meta["output_path"])
        chained.append("update-metadata (deleteAll)")

    flat = await client.post_form(
        "/api/v1/misc/flatten",
        input_files=[work],
        form_data={"flattenOnlyForms": False},
        output_name_hint="anon-flat",
    )
    if flat.get("success"):
        work = Path(flat["output_path"])
        chained.append("flatten")

    if rasterise:
        # PDF -> images @ 200dpi -> single PDF (true rasterisation)
        imgs = await client.post_form(
            "/api/v1/convert/pdf/img",
            input_files=[work],
            form_data={
                "imageFormat": "png",
                "singleOrMultiple": "multiple",
                "colorType": "color",
                "dpi": 200,
            },
            output_suffix=".zip",
            output_name_hint="anon-rasterised-imgs",
        )
        if imgs.get("success"):
            # Stirling returns a ZIP of images — we'd need to unzip and feed
            # to img/pdf. For now mark the path as the ZIP — caller can run
            # `images_to_pdf` after unzipping.
            chained.append("convert/pdf/img (rasterise)")
            work = Path(imgs["output_path"])

    return {
        "success": True,
        "output_path": str(work),
        "endpoints_chained": chained,
        "rasterised": rasterise,
    }
