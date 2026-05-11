"""AEC composite — visual drawing diff (Bluebeam-style change overlay).

Render two PDFs to high-DPI images, compute pixel-level diff, render the
diff as a third PDF where changes are highlighted. v1 uses Pillow for
pixel diff; v2 could integrate a true vector-aware diff (pdfdiff, gscompare).
"""

from __future__ import annotations

import logging
from pathlib import Path

from stirling_mcp.client import get_client
from stirling_mcp.config import SETTINGS
from stirling_mcp.app import mcp

log = logging.getLogger("stirling_mcp.composites.aec.visual_diff")


@mcp.tool()
async def aec_visual_diff(
    file_a: str,
    file_b: str,
    dpi: int = 200,
    diff_color: str = "#ff0066",
    threshold: int = 25,
) -> dict:
    """Visually diff two PDFs (per-page pixel comparison).

    Workflow:
        1. Render both PDFs to PNG at `dpi`
        2. Per matching page, compute the absolute pixel difference
        3. Highlight diffs in `diff_color` on a copy of page A
        4. Combine into a single review PDF

    This is a *raster* diff — fine for spotting "where did things change",
    not a substitute for a true vector-aware tool like Nutrient / Bluebeam
    when you need pixel-perfect annotations. Best for AEC drawing review
    where humans want a single "what changed between rev2 and rev3" PDF.

    Args:
        file_a: baseline PDF (typically the older revision)
        file_b: comparison PDF (typically the newer revision)
        dpi: render DPI (200 = good fidelity, 300 = print quality, slow)
        diff_color: hex colour to overlay changes
        threshold: pixel difference threshold 0-255 (lower = more sensitive)

    Returns: `{success, output_path, page_count, diff_pixel_counts_per_page}`
    """
    # Pillow import deferred so the rest of the MCP imports even without it
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageColor
        import io
        import zipfile
    except ImportError:
        return {
            "success": False,
            "error": "Pillow not installed. Add `Pillow` to requirements.txt.",
        }

    client = get_client()

    # Render both to PNG zips
    img_a = await client.post_form(
        "/api/v1/convert/pdf/img",
        input_files=[Path(file_a)],
        form_data={
            "imageFormat": "png",
            "singleOrMultiple": "multiple",
            "colorType": "color",
            "dpi": dpi,
        },
        output_suffix=".zip",
        output_name_hint=f"diff-a-{Path(file_a).stem}",
    )
    img_b = await client.post_form(
        "/api/v1/convert/pdf/img",
        input_files=[Path(file_b)],
        form_data={
            "imageFormat": "png",
            "singleOrMultiple": "multiple",
            "colorType": "color",
            "dpi": dpi,
        },
        output_suffix=".zip",
        output_name_hint=f"diff-b-{Path(file_b).stem}",
    )
    if not img_a.get("success") or not img_b.get("success"):
        return {"success": False, "stage": "render", "a": img_a, "b": img_b}

    # Unzip + diff
    def load_pages(zip_path: Path) -> list:
        out = []
        with zipfile.ZipFile(zip_path) as z:
            for name in sorted(z.namelist()):
                with z.open(name) as f:
                    out.append(Image.open(io.BytesIO(f.read())).convert("RGB"))
        return out

    pages_a = load_pages(Path(img_a["output_path"]))
    pages_b = load_pages(Path(img_b["output_path"]))
    n = min(len(pages_a), len(pages_b))

    diff_pages: list[Image.Image] = []
    diff_counts: list[int] = []
    color = ImageColor.getrgb(diff_color)

    for i in range(n):
        a, b = pages_a[i], pages_b[i]
        # Normalise sizes (resize B to A's dimensions if they differ)
        if a.size != b.size:
            b = b.resize(a.size)
        # Pixel diff
        diff = ImageChops.difference(a, b).convert("L")
        # Mask: pixels above threshold are "changed"
        mask = diff.point(lambda p: 255 if p > threshold else 0)
        diff_count = sum(mask.getdata()) // 255
        diff_counts.append(diff_count)
        # Overlay: paint changes onto a copy of A
        overlay = a.copy()
        red_layer = Image.new("RGB", a.size, color)
        overlay.paste(red_layer, (0, 0), mask)
        diff_pages.append(overlay)

    # Save combined PDF
    out_pdf = SETTINGS.output_dir / f"visual-diff-{Path(file_a).stem}-vs-{Path(file_b).stem}.pdf"
    if diff_pages:
        diff_pages[0].save(
            out_pdf,
            "PDF",
            resolution=dpi,
            save_all=True,
            append_images=diff_pages[1:],
        )

    return {
        "success": True,
        "output_path": str(out_pdf),
        "page_count": n,
        "diff_pixel_counts_per_page": diff_counts,
        "endpoints_chained": [
            "convert/pdf/img (file_a)",
            "convert/pdf/img (file_b)",
            "client-side pixel diff (Pillow)",
            "Pillow PDF assembly",
        ],
        "size_bytes": out_pdf.stat().st_size if out_pdf.exists() else 0,
    }
