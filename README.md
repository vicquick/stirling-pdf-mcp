# Stirling-PDF MCP

A Model Context Protocol server that wraps the full [Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) v2.10+ surface (≈260 REST operations) plus a curated layer of **composite workflow tools** for high-value patterns the raw endpoints don't expose directly — invoice prep, GDPR/HIPAA redaction, PDF/A archival, signing ceremonies, AEC drawing sets, and cross-MCP integrations with QGIS / IFC / Blender / Flux / SVG / nobrainr.

Built with Python 3.12 + [FastMCP](https://github.com/jlowin/fastmcp), runs as a single Docker container, transports over streamable-http on port 8087.

> **Heritage**: forked from [gufao/mcp-server-stirling-pdf](https://github.com/gufao/mcp-server-stirling-pdf) (10-tool TypeScript starter, MIT). Full Python rewrite — gufao's original is preserved at `legacy/gufao-typescript/`. See `CREDITS.md`.

## Why this MCP exists

The MCP registry today has ~zero composite/workflow PDF servers — almost every PDF MCP is a 1:1 endpoint wrapper. Wrapping Stirling-PDF's 260 endpoints 1:1 costs your LLM ~15k tokens of permanent context and offers no intelligence over hitting the REST API directly with an OpenAPI spec.

This server inverts that: a richly-described **raw layer** for any-op-on-demand, plus a **composite layer** of task-shaped tools where a user says _"I need this change in my PDF"_ and a single MCP call returns the finished result.

## Architecture

```
Layer 1 — Raw wrappers (per Stirling category)
   general/  misc/  security/  convert/  forms/  filter/  analysis/  ai/
Layer 2 — Generic composites
   invoice_prepare        redact_personal_info     archive_to_pdfa
   sign_and_seal          merge_with_toc           compare_versions
   …
Layer 3 — AEC + cross-MCP composites
   aec_drawing_set        aec_titleblock_to_metadata
   aec_drawings_to_ifc_refs       aec_georeferenced_to_qgis
   blender_render_to_pdf  flux_images_to_pdf       svg_diagrams_to_pdf
   pdf_to_memory          pdf_search_memory        pdf_to_audio
```

See [`docs/PLAN.md`](docs/PLAN.md) for the full design and [`docs/RESEARCH.md`](docs/RESEARCH.md) for the workflow-tool research that informed the catalogue.

## Quickstart

```bash
cp .env.example .env  # then edit STIRLING_URL and STIRLING_API_KEY
docker build -t stirling-pdf-mcp .
docker run --rm -p 8087:8087 --env-file .env stirling-pdf-mcp
```

Or via the bundled Coolify deployment in `aec-web/mcp/` (VPN-only, Traefik-fronted, internal Docker DNS to Stirling).

## Configuration

All via env vars — see [`.env.example`](.env.example).

Required:
- `STIRLING_URL` — backend Stirling-PDF base URL (internal Docker DNS preferred)
- `STIRLING_API_KEY` — service-account API key generated in Stirling admin

Optional:
- `MAX_CONCURRENT_REQUESTS` (default 4)
- `REQUEST_TIMEOUT` (default 300s)
- `ENABLE_CACHE` (default true)
- `QGIS_MCP_URL`, `IFC_MCP_URL`, `NOBRAINR_URL` — for Layer 3 cross-MCP composites

## Status

| Layer | Status |
|---|---|
| Foundation (client, retries, multipart, caching, health) | ✅ M0 |
| Raw wrappers — general, misc, security, convert (10/10/9/9 of category endpoints) | 🚧 M0.5 |
| Raw wrappers — full 260 coverage | 🚧 M1 |
| Composites — invoice, redact, archive, sign, merge, compare | ✅ M0.5 |
| Composites — legal, form_batch, book, print/web, expense, stamp, share | 🚧 M2 |
| AEC composites — drawing_set | ✅ stub |
| AEC composites — titleblock, submittal, RFI, IFC refs, QGIS, render | 🚧 M3 |
| Cross-MCP — pdf_to_memory, blender→pdf, flux→pdf, svg→pdf, pdf→tts | 🚧 M3 |
| Production hardening — observability, tests, golden-paths | 🚧 M4 |

## Contributing

This repo is intentionally hackable: every tool lives in its own ≤200-line module, raw and composite are cleanly separated, the Stirling client is the single I/O choke point. Add a new tool: drop a function with `@mcp.tool()`, hook into the registry in `server.py:_register_layers()`.

## License

Apache-2.0 (matching gufao's original).
