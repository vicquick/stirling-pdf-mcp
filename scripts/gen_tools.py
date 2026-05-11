#!/usr/bin/env python3
"""Generate Layer-1 MCP tool wrappers from Stirling-PDF's OpenAPI spec.

Reads the OpenAPI JSON (downloaded from `/v1/api-docs` of a live Stirling
instance, or supplied as a local file), produces one Python module per
Stirling tag category, registers all endpoints as MCP tools.

Endpoints already covered by hand-curated tools (in tools/general.py,
tools/misc.py etc.) are skipped to avoid duplication — the hand-curated
modules have richer docstrings and edge-case handling.

Run:
    python scripts/gen_tools.py \
        --spec /tmp/stirling-openapi.json \
        --out src/stirling_mcp/tools/auto

The output is grouped: one module per tag. Each module imports
`@mcp.tool()` from `stirling_mcp.server` and the Stirling client, exposes
each endpoint as `<category>_<operationid_or_path_slug>`.

Excluded tags (admin-only / not LLM-useful):
    Authentication, Admin Settings, Admin Job Management,
    Admin License Management, Admin - Server Certificate,
    Audit, Database, User, Team, Invite, Workflow Participant,
    Proprietary UI Data, UI Data, Info, Job Management,
    File Storage, Signature Assets, Saved Signatures, Signing Sessions
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Tags we wrap. Everything else is admin/auth/UI plumbing.
WRAP_TAGS = {
    "General",
    "Convert",
    "Security",
    "Misc",
    "Forms",
    "Filter",
    "Analysis",
    "AI Tools",
    "Pipeline",
}

# Paths already covered by hand-curated wrappers in tools/general.py etc.
# Auto-gen will skip these.
HAND_CURATED_PATHS = {
    # general.py
    "/api/v1/general/merge-pdfs",
    "/api/v1/general/split-pdfs",
    "/api/v1/general/split-by-size-or-count",
    "/api/v1/general/split-pdf-by-sections",
    "/api/v1/general/split-pdf-by-chapters",
    "/api/v1/general/rotate-pdf",
    "/api/v1/general/remove-pages",
    "/api/v1/general/rearrange-pages",
    "/api/v1/general/multi-page-layout",
    "/api/v1/general/scale-pages",
    # misc.py
    "/api/v1/misc/compress-pdf",
    "/api/v1/misc/ocr-pdf",
    "/api/v1/misc/extract-image-scans",
    "/api/v1/misc/extract-text",
    "/api/v1/misc/metadata",
    "/api/v1/misc/update-metadata",
    "/api/v1/misc/add-watermark",
    "/api/v1/misc/add-page-numbers",
    "/api/v1/misc/add-stamp",
    "/api/v1/misc/flatten",
    "/api/v1/misc/repair",
    "/api/v1/misc/remove-javascript",
    "/api/v1/misc/remove-annotations",
    "/api/v1/misc/remove-links",
    "/api/v1/misc/remove-blanks",
    "/api/v1/misc/unlock-pdf-forms",
    # security.py
    "/api/v1/security/add-password",
    "/api/v1/security/remove-password",
    "/api/v1/security/change-permissions",
    "/api/v1/security/sanitize-pdf",
    "/api/v1/security/auto-redact",
    "/api/v1/security/redact",
    "/api/v1/security/validate-signature",
    "/api/v1/security/verify-pdf",
    "/api/v1/security/remove-cert-sign",
    "/api/v1/security/cert-sign",
    # convert.py
    "/api/v1/convert/pdf/img",
    "/api/v1/convert/img/pdf",
    "/api/v1/convert/pdf/word",
    "/api/v1/convert/file/pdf",
    "/api/v1/convert/pdf/pdfa",
    "/api/v1/convert/html/pdf",
    "/api/v1/convert/url/pdf",
    "/api/v1/convert/pdf/markdown",
    "/api/v1/convert/markdown/pdf",
    "/api/v1/convert/pdf/csv",
    # forms.py
    "/api/v1/form/fill",
    "/api/v1/form/extract",
    "/api/v1/form/flatten",
    # analysis.py
    "/api/v1/analysis/security-info",
    "/api/v1/analysis/page-dimensions",
    # filter.py
    "/api/v1/filter/filter-page-size",
    "/api/v1/filter/filter-page-count",
    # ai.py
    "/api/v1/ai/tools/pdf-comment-agent",
    "/api/v1/ai/tools/math-auditor-agent",
}


def slugify(text: str) -> str:
    """Convert a path or operation name into a snake_case Python identifier."""
    text = re.sub(r"\{[^}]+\}", "by", text)  # {id} -> by
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    # Avoid keyword clashes
    if text in {"import", "from", "class", "def", "return", "filter"}:
        text = f"{text}_"
    return text


def tool_name_for(path: str, method: str, tag: str) -> str:
    """Generate a stable, unique MCP tool name.

    Strategy: tag prefix + slug of the **full path minus /api/v1/**. Including
    the full subpath avoids collisions when many endpoints end with the same
    last segment (e.g. `/convert/url/pdf`, `/convert/img/pdf`, `/convert/file/pdf`
    all end in `pdf`).
    """
    relevant = path.replace("/api/v1/", "").replace("/api/v1", "")
    op_slug = slugify(relevant)
    tag_slug = slugify(tag)
    # Drop tag prefix if the path already starts with it (common Stirling case)
    if op_slug.startswith(tag_slug + "_"):
        op_slug = op_slug[len(tag_slug) + 1 :]
    name = f"{tag_slug}_{op_slug}"
    if method.lower() != "post":
        name = f"{name}_{method.lower()}"
    return name


def docstring_for(op: dict, path: str, method: str) -> str:
    """Compose a clean docstring from OpenAPI summary + description."""
    parts: list[str] = []
    summary = (op.get("summary") or "").strip()
    description = (op.get("description") or "").strip()
    if summary:
        parts.append(summary)
    if description and description != summary:
        parts.append("")
        parts.append(description[:600])  # keep things scannable
    parts.append("")
    parts.append(f"Endpoint: ``{method.upper()} {path}``")
    return "\n    ".join(parts)


def emit_tool(path: str, method: str, op: dict, tag: str) -> str:
    """Emit one Python function string for a single endpoint."""
    name = tool_name_for(path, method, tag)
    docstring = docstring_for(op, path, method)

    # Most Stirling endpoints are POST multipart. GET endpoints return JSON.
    is_get = method.lower() == "get"

    if is_get:
        # Path-parameter endpoints: hoist {id} into a kwarg
        path_params = re.findall(r"\{([^}]+)\}", path)
        params_str = ", ".join(f"{p}: str" for p in path_params)
        if params_str:
            path_replace = "f\"" + path + "\""
        else:
            path_replace = repr(path)

        return f'''
@mcp.tool()
async def {name}({params_str}) -> dict:
    """{docstring}
    """
    return await get_client().get_json({path_replace})
'''

    # POST: form data. Most Stirling POSTs accept a `fileInput` multipart field
    # plus optional form fields. We expose `input_files` + a generic
    # `form_data` dict so the LLM can pass any params the spec describes.
    return f'''
@mcp.tool()
async def {name}(
    input_files: list[str] | None = None,
    form_data: dict | None = None,
) -> dict:
    """{docstring}
    """
    from pathlib import Path
    return await get_client().post_form(
        {path!r},
        input_files=[Path(p) for p in (input_files or [])],
        form_data=form_data or {{}},
    )
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="path to OpenAPI JSON")
    ap.add_argument("--out", required=True, help="output directory for generated modules")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    paths: dict = spec.get("paths", {})

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "__init__.py").write_text(
        '"""Auto-generated Stirling-PDF MCP tool wrappers.\n\n'
        "Do NOT edit by hand. Run `scripts/gen_tools.py` to regenerate.\n"
        "Curated, high-touch tools live in the parent ``tools/`` directory.\n"
        '"""\n'
    )

    by_tag: dict[str, list[str]] = defaultdict(list)
    total = 0
    skipped_handcurated = 0
    skipped_admin = 0

    for path, methods in paths.items():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                continue
            tags = op.get("tags", ["untagged"])
            tag = tags[0] if tags else "untagged"
            if tag not in WRAP_TAGS:
                skipped_admin += 1
                continue
            if path in HAND_CURATED_PATHS:
                skipped_handcurated += 1
                continue
            by_tag[tag].append(emit_tool(path, method, op, tag))
            total += 1

    # Header for each tag module
    header = (
        '"""Auto-generated Stirling-PDF tool wrappers — category {tag}.\n\n'
        "Generated from the live Stirling OpenAPI spec. See ``scripts/gen_tools.py``.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n"
        "from stirling_mcp.client import get_client\n"
        "from stirling_mcp.server import mcp\n"
    )

    written: list[str] = []
    for tag, fns in by_tag.items():
        module_name = re.sub(r"[^a-z]+", "_", tag.lower()).strip("_") + "_auto"
        module_path = out_dir / f"{module_name}.py"
        module_path.write_text(header.format(tag=tag) + "\n".join(fns) + "\n")
        written.append(str(module_path))

    summary = f"""\
gen_tools.py: emitted {total} tool wrappers across {len(by_tag)} tag modules.
   skipped {skipped_handcurated} paths covered by hand-curated tools.
   skipped {skipped_admin} paths in admin/auth/UI tag categories.

Modules:
"""
    for w in written:
        summary += f"  - {w}\n"
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
