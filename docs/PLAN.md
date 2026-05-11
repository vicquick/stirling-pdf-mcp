# Stirling-PDF MCP — Master Plan

> Living document. Forked conceptually from `gufao/mcp-server-stirling-pdf` (10-tool TypeScript starter, MIT). Full Python rewrite onto FastMCP + streamable-http to match the AEC MCP stack (flux-mcp, ifc-mcp, qgis-mcp, blender-mcp, svg-mcp, postgres-mcp). Public repo, attribution preserved.

## Target

A single MCP container that exposes the entire useful surface of Stirling-PDF 2.10+ (≈260 REST operations) as well-described, task-shaped tools to LLM agents on the VPN-side mcp namespace. Goal: any PDF question or workflow imaginable answerable via one MCP call.

## Stack alignment

| Choice | Value | Rationale |
|---|---|---|
| Language | Python 3.12 | Matches flux-mcp, qgis-mcp, blender-mcp |
| MCP framework | FastMCP (latest) | Already in flux-mcp |
| Transport | streamable-http | Already proven with metamcp |
| HTTP client | `httpx` async + `aiohttp` for multipart | Replaces gufao's TS axios |
| Deploy | Coolify, Dockerfile build, `vicquick/stirling-pdf-mcp` repo | Same as flux-mcp |
| Folder | `/opt/stirling-pdf-mcp` | Same as `/opt/flux-mcp` |
| Port | 8087 | Next free after flux's 8086 |
| Network | `mcp` + `coolify` Docker networks | So stirling backend reachable internally |
| Auth to Stirling | dedicated MCP service-account API key | scoped per Stirling user — see decisions |

## Tool layers

### Layer 0 — Foundation

- async retry-with-backoff
- multipart upload with stream
- response → structured dict with `success`, `output_path`, `metadata`, `warnings`, `error`
- job tracker for Stirling async ops (poll `/api/v1/general/job/{jobId}`)
- content-hash result cache (skip recompute on identical input + params)
- pre-flight on boot: probe `/api/v1/info/status`, fail-fast if backend down
- structured logging (matches flux-mcp pattern)

### Layer 1 — Raw endpoint wrappers (target: full 260 coverage)

User decision 2026-05-11: ship **all** user-facing endpoints, not just a curated 80. Admin/auth/audit/team-mgmt/proprietary-UI-data still skipped (not LLM-relevant), but every general/convert/security/misc/forms/filter/analysis/AI/signing endpoint is wrapped.

Kept and exposed per category:

**General (10)** — merge, split-by-pages/size/sections/chapters, rotate, remove-pages, reorganise, n-up layout, scale

**Convert (20)** — pdf↔images/jpg/png, images→pdf, pdf↔word/excel/pptx/html/markdown/csv/xml, pdf→pdfa, url→pdf, eml→pdf, epub→pdf

**Security (10)** — encrypt, decrypt, add/remove password, change permissions, watermark (text+image), sign, validate signature, sanitise, auto-redact (regex/preset), manual-redact (coords)

**Misc (20)** — compress, optimize, repair, metadata get/set/strip, OCR, extract images, extract text, JS show/remove, links remove, blanks remove, certs remove, annotations remove, flatten, page numbers, attachments add/remove, unlock-forms, stamp

**Forms (5)** — modify-fields, fill (dict), fill-batch (CSV), extract-data, flatten

**Filter (6)** — by page size / orientation / page count / text content / image content / rotation

**Analysis (6)** — security info, page dimensions, text density, image count, font usage, quality score

**Pipeline (1)** — `pipeline_run` exposing Stirling's own multi-step pipeline engine

**AI Tools (2)** — pdf-comment-agent, math-auditor-agent

### Layer 2 — Workflow composites (≈18 tools — the differentiator)

Each composes 2-6 raw ops behind one tool description:

| Tool | Composition |
|---|---|
| `invoice_prepare` | clean → OCR → extract amount/date/vendor → rename by pattern |
| `archive_to_pdfa` | OCR → compress → pdfa-1b → strip-metadata |
| `redact_personal_info` | OCR → regex match (preset: gdpr/hipaa/custom) → redact → flatten → watermark "REDACTED" |
| `prepare_for_print` | flatten → rasterise → CMYK → page-size → outline-fonts |
| `prepare_for_web` | compress → linearise → pdfa-1b → strip-metadata |
| `sign_and_archive` | sign (cert) → rfc3161 timestamp → pdfa → archive-name |
| `merge_with_toc` | merge → detect headings → bookmarks → page numbers |
| `form_fill_batch` | iterate CSV → fill template → optional email each |
| `book_publish` | combine → TOC → cover → page-numbers → optimise |
| `legal_packet` | bates-number → redact (term list) → watermark → combine |
| `image_album` | n-up → TOC → title page → optimise |
| `manuscript_package` | images→pdf → OCR → watermark → combine |
| `expense_report` | scan-batch → receipt OCR → table → summary page |
| `compare_versions` | diff (text + visual) → annotate → report |
| `extract_table_data` | OCR → table detect → CSV |
| `stamp_with_qr` | generate QR → stamp at coords |
| `password_protect_share` | encrypt → produce share link (Stirling sharing) |
| `pdf_to_audio` | OCR → TTS via your existing TTS stack |

### Layer 3 — AEC + cross-MCP

| Tool | Talks to |
|---|---|
| `pdf_to_qgis_layer` | qgis-mcp — georeferenced PDF → vector layer |
| `pdf_drawings_to_ifc_refs` | ifc-mcp — link drawings to IFC entities |
| `blender_render_to_pdf` | blender-mcp — render scene → assemble PDF |
| `flux_images_to_pdf` | flux-mcp — generate images → compile PDF |
| `svg_diagrams_to_pdf` | svg-mcp — combine SVGs → PDF |
| `pdf_to_memory` | nobrainr — extract text → store + tag |
| `pdf_search_memory` | nobrainr — semantic search over stored PDFs |
| `extract_drawings_aec_dpi` | (standalone) high-DPI extract for CAD reference |

## Deployment

- Coolify app, project `aec` (or wherever MetaMCP is grouped), environment `mcp`
- Repo: `vicquick/stirling-pdf-mcp`, branch `main`
- Build pack: `dockerfile`, base_directory `/`, dockerfile `/Dockerfile`
- Networks: `mcp` (talks to stirling backend), `coolify` (Traefik if needed)
- VPN-only Traefik middleware OR no FQDN at all (metamcp connects via internal Docker DNS)
- Env vars: `STIRLING_URL`, `STIRLING_API_KEY`, `LOG_LEVEL`, `OUTPUT_DIR`, `CACHE_DIR`, optional `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for AI Tools passthrough
- Health: probes both own port 8087 and Stirling `/api/v1/info/status`
- Pinned image tag: build from source per commit, no floating

## MetaMCP registration

- Add as a server in metamcp dashboard under the existing AEC namespace
- Connect via internal `http://stirling-pdf-mcp.coolify:8087/mcp` (streamable-http)
- Document tools in metamcp namespace UI

## Public repo flow

1. Fork `gufao/mcp-server-stirling-pdf` → `vicquick/stirling-pdf-mcp` (preserves attribution graph)
2. Branch `rewrite/python-fastmcp` from main
3. Empty `src/index.ts`, add Python skeleton, CREDITS.md preserving gufao
4. README explains: forked for attribution, ground-up Python rewrite, 80+/18+/8+ tools across 3 layers
5. CI: github actions for lint + type + smoke test against a self-hosted Stirling
6. Tagged releases for each layer milestone (v0.1 = Layer 0+1 partial, v0.2 = all of Layer 1, v0.3 = Layer 2, v0.4 = Layer 3)

## Roadmap milestones

- **M0** Foundation + 5 smoke tools (merge/split/rotate/compress/OCR) — deployable proof
- **M1** All Layer 1 raw wrappers (~80 tools)
- **M2** All Layer 2 composites (~18 tools)
- **M3** Layer 3 cross-MCP integrations
- **M4** Hardening: caching, concurrency limits, observability, golden-path tests

## Open decisions

See `docs/DECISIONS.md` for tracked decisions.
