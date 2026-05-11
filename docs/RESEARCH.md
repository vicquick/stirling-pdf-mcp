# Research: Composite Workflow Universe for a Stirling-PDF MCP

> Output of `/gpt-researcher` pass on 2026-05-11. Informs `PLAN.md` Layer 2 + Layer 3 tool design.

## TL;DR

- The four highest-volume PDF workflow domains across the industry are **document review/compare/sign** (legal), **statement/ID extraction** (finance/onboarding), **HIPAA-grade redaction** (healthcare/government), and **drawing markup + quantity takeoff** (AEC). Wrapping any of these as a single MCP tool delivers 10× more value than mirroring the underlying endpoint surface. [^1][^2]
- **AEC-specific** workflows have a known shape from Bluebeam Revu: "Sets" (treat a folder of revisions as one navigable doc), "Markups List + custom columns" (turn annotations into a structured table), "Quantity Takeoff" (calibrated measurement → Excel via Quantity Link), "Studio Sessions" (real-time multi-party markup), "Tool Chest" (reusable markup library). Stirling-PDF doesn't ship these as primitives, but most can be **composed from its 260 raw endpoints**. [^3][^4][^5]
- **Nutrient (formerly PSPDFKit)** is the strongest baseline-feature reference: 17+ annotation types, form creation+fill, electronic + PKI digital signatures, search-and-redact, **word-level text comparison + vector-based visual comparison** (latter ideal for technical drawings), built-in OCR 30+ languages, full Office conversion both ways, PDF/A archival, AI Assistant for Q&A/summary/translate. Stirling-PDF covers most of this surface; gaps are where MCP composites add value. [^2]
- The **MCP server ecosystem** has converged on 1:1 endpoint wrappers (`fetch`, `filesystem`, `git`, `memory`, `time`, `sequential-thinking` as reference) — almost no composite/workflow servers exist. A workflow-shaped Stirling MCP would be a meaningful contribution to the registry, not just one of N. [^6]
- **Stirling-PDF itself** already ships a `Pipeline` feature for no-code multi-step chaining + a "Multi-Tool" (upload once, chain operations) mode. These are pre-built primitives the MCP composites should delegate to where possible, instead of re-implementing chains client-side. [^1][^7]

## Background

A Stirling-PDF MCP server has 260 REST endpoints available to wrap. The naive design is a 260-tool 1:1 mirror, which costs the LLM ≈ 10-15k tokens of permanent context for tool schemas and provides little intelligence over just letting the LLM hit the REST API directly with an OpenAPI spec. The strategic design wraps **task-shaped composites** that span 2-8 endpoints behind one tool, giving the LLM a single named action ("redact_personal_info") that internally orchestrates the chain. This research catalogues which composites actually exist in the wild — to avoid speculative tool design and to surface the "we never thought of that" workflows.

## Findings

### Sub-question 1 — Industry-typical PDF workflows

The dominant industry workflows reduce to about a dozen patterns that appear repeatedly across Nutrient's vertical solutions [^2] and Stirling-PDF's own functionality catalogue [^1]:

- **Invoice / statement processing**: scan → OCR → extract amount/vendor/date → name-by-pattern → archive
- **Onboarding form intake**: fill template fields from a CSV → flatten → email-or-store
- **Contract redaction**: search-and-redact (term list or regex preset) → watermark "redacted" → flatten → audit log
- **Document comparison**: word-level diff OR vector-visual diff → highlight changes → annotated report
- **Long-term archival**: OCR → compress → convert to PDF/A-1b → strip metadata → catalogue
- **Signing ceremonies**: certify signer → apply digital signature with PKI → optional RFC 3161 timestamp → seal as PDF/A
- **Splitting / merging by chapter / section** with auto-generated TOC + bookmarks
- **AI summary / Q&A** over PDF content (Nutrient's "AI Assistant", LangChain's PDF loaders are the same shape) [^2]

Stirling-PDF has direct primitives or close approximations for every one of these. Composites would chain them and add the missing connective tissue (template-driven naming, regex presets, audit log).

### Sub-question 2 — AEC-specific PDF workflows

Bluebeam Revu's feature set is the de-facto AEC reference. Five idioms appear consistently across community write-ups [^3][^4][^5]:

1. **Sets** — open a folder of related PDFs (revisions, amendments) as a single browsable view with revision tracking. The MCP equivalent: a tool that ingests a directory and returns a logical "set" object (page index, revision graph, hot-key navigation hints).
2. **Markups List + custom columns** — annotations are not just visual marks; they're structured rows with attributes (estimator, division, status, $/unit). Export to Excel via "Quantity Link". The MCP equivalent: extract annotations → structured table → CSV/Excel/JSON.
3. **Quantity Takeoff** — calibrate scale once, then measure lengths/areas/volumes with persistent markups. Stirling can't render-calibrate but can extract dimensions from text/title-block via OCR and analysis.
4. **Studio Sessions** — real-time multi-party markup. Out of scope for a stateless MCP, but a **session-like async workflow** ("comment-batch and broadcast") is feasible.
5. **Tool Chest** — reusable markup template library. The MCP equivalent: stamp templates / signature library, which Stirling already exposes via `Saved Signatures` (4 endpoints) and `Signature Assets`.

Additional AEC patterns mentioned in tradecraft guides: **submittal preparation** (combine → stamp → review log → cover page), **RFI packets** (template-fill + attach drawings + auto-number), **specification management** (CSI division splitting + watermarking), **drawing sheet management** (extract title-block metadata → rename), **bates numbering** (sequential per-page numbering for litigation).

### Sub-question 3 — Compliance & redaction workflows

The redaction-specific patterns are well-documented in the security space [^2]:

- **Search-and-redact** with preset regex packages: GDPR (names, EU IDs, addresses), HIPAA (SSN, MRN, DOB, names), PCI (card numbers, CVV), custom (term list per project).
- **Visual masking + content removal**: redaction must overwrite the content layer, not just paint a box. Stirling's `Security` category has both auto-redact and manual-redact endpoints.
- **Flatten after redact**: critical step — un-flattened annotations can be removed by the recipient.
- **PDF/A-3 archival** for redacted-and-signed records, with embedded provenance metadata.
- **Multi-party signing ceremonies**: sequential or parallel signers, RFC 3161 timestamps from a trusted TSA. Stirling has 15 `Signing Sessions` endpoints — enough to build the ceremony.

### Sub-question 4 — Modern multi-agent PDF automation patterns

The official MCP servers repository [^6] retired its curated third-party list in favour of the [MCP Registry](https://registry.modelcontextprotocol.io/). Inspecting both, the dominant pattern across document-touching MCPs is **single-purpose 1:1 wrappers**. There is no widely-adopted "workflow MCP" for PDFs. Reference servers (`fetch`, `filesystem`, `memory`, `sequential-thinking`) are all primitive. This is an opportunity gap — a composite-tool PDF MCP would be a notable contribution.

LangChain's PDF document loaders ecosystem (`PyPDFLoader`, `UnstructuredPDFLoader`, `PyMuPDFLoader`) is the dominant agent-PDF interface today, but it stops at "load text into context". Real workflows (redact, sign, split, OCR, compare) are handled outside the agent loop. An MCP that wraps those operations brings them inside the loop.

### Sub-question 5 — Stirling-PDF specific

Stirling ships its own **Pipeline** feature (no-code multi-step chaining direct in the UI, also exposed via API) [^7][^1] and a **Multi-Tool** (upload once, chain operations without re-uploading) [^1]. These are the right primitives for our composites to delegate to where the chain is sequential and Stirling-internal. The MCP composite layer should expose Stirling's Pipeline as `pipeline_run(steps[])` and prefer it over client-side orchestration when possible — it keeps file IO inside the backend and avoids the multipart round-trip per step.

Stirling also ships two AI Tools: `pdf-comment-agent` and `math-auditor-agent`. The comment-agent fills the LangChain-style "agentic annotation" gap; the math-auditor checks numerical consistency (invoices, engineering calcs). Both are usable LLM-on-LLM wrappers.

### Sub-question 6 — Cross-tool workflows

Given the user's existing MCP fleet (qgis-mcp, ifc-mcp, blender-mcp, flux-mcp, svg-mcp, nobrainr memory), several cross-tool composites are uniquely possible:

- **PDF→QGIS layer**: georeferenced PDF + qgis-mcp `add_raster_layer` → instant survey reference
- **PDF drawing → IFC entity links**: OCR drawing title-block → match GUIDs → ifc-mcp `bim_add_classification`
- **Blender render → PDF report**: blender-mcp `render_image` → images_to_pdf with template
- **Flux image → PDF**: flux-mcp `generate_image` → branded PDF page
- **SVG diagrams → PDF**: svg-mcp output → vector-preserving PDF
- **PDF → nobrainr memory**: extract text + entities → store in knowledge graph for semantic search
- **PDF → audio**: OCR → existing TTS stack (Edge TTS / Chatterbox) → audio summary

These are not available in any other MCP and would be unique value the Stirling MCP brings to the AEC namespace.

## Composite-tool catalogue (the deliverable)

Prioritised: P0 = essential, P1 = high-value, P2 = nice-to-have.

| # | Tool name | One-line description | Composition (Stirling endpoints + cross-MCP) | Persona | Frequency | Priority |
|---|---|---|---|---|---|---|
| 1 | `invoice_prepare` | Scan/PDF → OCR → extract date/vendor/total → rename by pattern → archive | OCR → extract text → regex parse → metadata set → store | Finance, AP clerks | Daily | P0 |
| 2 | `redact_personal_info` | GDPR/HIPAA/PCI/custom preset redaction with audit log | OCR → regex match → auto-redact → flatten → watermark → metadata note | Legal, compliance | Weekly | P0 |
| 3 | `archive_to_pdfa` | Convert to PDF/A-1b for long-term archival with cleanup | OCR → compress → strip metadata → pdfa convert | Records mgmt, gov | Daily-batch | P0 |
| 4 | `sign_and_seal` | Certified digital signature with RFC 3161 timestamp + PDF/A wrap | sign → cert-sign session → timestamp → pdfa | Legal, exec | Weekly | P0 |
| 5 | `merge_with_toc` | Merge documents and auto-generate bookmarks + page numbers + TOC | merge → detect headings → bookmarks → page numbers | Anyone publishing | Weekly | P0 |
| 6 | `compare_versions` | Word + visual diff between two PDFs, annotated report | analysis security-info → page-dim compare → text diff → visual diff annotation | Legal, AEC reviewers | Weekly | P0 |
| 7 | `form_fill_batch` | Read CSV → fill template per row → optional email delivery | form fill (loop) → flatten → mail relay | HR, onboarding | Monthly batch | P1 |
| 8 | `extract_table_data` | OCR page range → detect tables → CSV/JSON | OCR → analysis text-density → table heuristic → CSV | Data ops, finance | Daily | P1 |
| 9 | `legal_packet` | Bates-number + redact term list + watermark + cover page + combine | bates stamp → redact → watermark → cover → merge | Litigation prep | Weekly | P1 |
| 10 | `book_publish` | Compile chapters with cover, TOC, page numbers, optimisation | merge → bookmarks → page numbers → optimise → pdfa | Publishers, authors | Monthly | P1 |
| 11 | `prepare_for_print` | Flatten, rasterise, CMYK, set page size, outline fonts | flatten → convert pdf-to-images at 300dpi → re-convert to CMYK PDF → page-size | Print shops, design | Project | P1 |
| 12 | `prepare_for_web` | Compress, linearise, strip metadata, pdfa-1b | compress → metadata strip → pdfa | Web publish | Per upload | P1 |
| 13 | `expense_report` | Multi-receipt scan → per-receipt OCR → summary table + per-page receipts | OCR (batch) → extract → table page generation → merge with receipts | Anyone w/ travel | Monthly | P1 |
| 14 | `stamp_with_qr` | Generate QR (URL, doc-id, signature hash) → stamp at coords | QR encode → stamp at xy on page N | Logistics, AEC | Project | P1 |
| 15 | `password_protect_share` | Encrypt + Stirling sharing link with expiry | encrypt → set permissions → sharing endpoint | All users | Daily | P1 |
| 16 | `image_album` | Images → n-up layout → title page → TOC → optimise | images_to_pdf → n-up → cover → bookmarks → optimise | Marketing, real estate | Per album | P2 |
| 17 | `manuscript_package` | Loose images → OCR'd PDF → watermark → combine | images_to_pdf → OCR → watermark → merge | Academia, journalism | Per submission | P2 |
| 18 | `pdf_to_audio` | OCR → TTS → MP3 with chapter marks | OCR → text extract → cross-MCP TTS (Edge/Chatterbox) → audio | Accessibility, commute | Per doc | P2 |
| 19 | `extract_form_inbox` | Watch a folder, auto-fill template per detected form, route to recipient | scheduled watch → detect → form-fill → email | Ops automation | Recurring | P2 |
| 20 | `ai_summarise_pdf` | LLM summary + key-points + topic-tags written into the PDF as a cover page | text extract → LLM summarise (your llama-server) → cover generation → merge | Research, ops | Per doc | P1 |

### AEC-flavoured composites (uniquely valuable given user's stack)

| # | Tool name | Composition | Why it's only possible here |
|---|---|---|---|
| 21 | `aec_drawing_set` | Treat folder of revisions as one navigable "Set" — index revisions, build navigation manifest, optional unified PDF preview | filter by-page-size → group by sheet number → revision-graph → optional merge | Reproduces Bluebeam's "Sets" concept on Stirling primitives |
| 22 | `aec_extract_high_dpi_drawings` | Extract drawings at 300/600 DPI for CAD reference and overlay in QGIS/Blender | pdf-to-images at high DPI → optional cross-MCP store | Feeds qgis-mcp + blender-mcp |
| 23 | `aec_titleblock_to_metadata` | OCR title-block of each page → extract sheet number/discipline/date → write into PDF metadata + filename | OCR → regex/LLM parse → metadata set → rename | AEC-specific, not in any other MCP |
| 24 | `aec_submittal_package` | Cover sheet (auto) + drawings + specs + watermark + review log + bates | template render → merge → watermark → bates → cover | Bluebeam-equivalent submittal prep |
| 25 | `aec_rfi_packet` | Generate RFI cover (template-fill) + attach referenced drawings + auto-number | form fill → merge with extracted drawings | Bluebeam-equivalent RFI workflow |
| 26 | `aec_drawings_to_ifc_refs` | Extract drawing titles + grid refs → match IFC `IfcAnnotation` via ifc-mcp | OCR → grid parse → cross-MCP ifc-mcp link | Unique to your stack — no external tool combines these |
| 27 | `aec_georeferenced_to_qgis` | Detect GeoPDF → push to qgis-mcp `add_raster_layer` with CRS | analysis page-dim + georef detect → qgis-mcp call | Cross-MCP, unique |
| 28 | `aec_render_to_pdf_report` | blender-mcp render → arrange n-up → cover → optimise | cross-MCP flux/blender/svg → assemble PDF | Cross-MCP composite report |

### "We never thought of that" workflows surfaced by the research

- **Vector-based visual document comparison** for technical drawings (Nutrient ships this; Stirling doesn't directly but can approximate via pdf-to-images + image diff). High-value for AEC change-detection between drawing revisions. Add as `aec_drawing_diff_visual`. [^2]
- **PDF Quantity Link → Excel** from extracted annotations and measurements. Useful in non-AEC contexts too (any structured-annotation workflow). Add as `extract_annotations_to_table`. [^4]
- **PDF/UA (accessibility) compliance** generation — Stirling doesn't expose it directly, but a composite of tagging + alt-text extraction + LLM-fill could deliver a "make this PDF accessible" tool. WCAG 2.2 AA is increasingly a procurement requirement. Add as `make_accessible` (P2). [^2]
- **Math auditing across documents** — Stirling's `math-auditor-agent` is single-doc; a composite that runs it across a batch and produces a cross-reference report is novel. Add as `audit_math_consistency` (P2). [^1]
- **Real-time "Studio Session" emulation** via webhook-driven async annotation broadcast — niche but a possible v2 differentiator. [^3]

## Open questions / contradictions

- Stirling-PDF's `Pipeline` endpoint is one operation (`POST /api/v1/pipeline/handleData`) but the docs describe a richer no-code chain editor. Need to inspect actual payload shape before deciding whether MCP composites should always delegate to Pipeline or sometimes orchestrate client-side. **Action**: read `/api/v1/pipeline/handleData` spec + try a 2-step chain manually before designing composites.
- Visual-diff for AEC drawings is the marquee Bluebeam/Nutrient feature; Stirling lacks a true vector-aware diff. Approximating via pdf-to-images + pixel diff is lossy. Need to decide: ship lossy approximation, integrate an external lib (e.g. `pdfdiff` Python), or skip until Stirling adds it.
- Some industry composites (e.g. `prepare_for_print` CMYK conversion) require capabilities Stirling may or may not expose. Need a pass through the 32 Convert endpoints to confirm CMYK support before promising it.

## Sources

[^1]: Stirling-PDF docs landing — feature catalogue and Multi-Tool/Pipeline descriptions. <https://docs.stirlingpdf.com/>
[^2]: Nutrient (formerly PSPDFKit) Web SDK page — comprehensive feature surface and industry-vertical breakdown (Legal, Finance, Healthcare, Education, Government, Construction). <https://www.nutrient.io/sdk/web>
[^3]: Working with Sets — Bluebeam Technical Support docs. <https://support.bluebeam.com/online-help/revu20/Content/RevuHelp/Menus/Window/Panels/Sets/Working-with-Sets--TV.htm>
[^4]: 5 Ways to Use Bluebeam Revu for Quantity Takeoff and Estimation — Taradigm. <https://www.taradigm.com/5-ways-to-use-bluebeam-revu-for-quantity-takeoff-and-estimation/>
[^5]: Top 20 Helpful Tips & Tricks for Bluebeam Revu — Microsol Resources. <https://microsolresources.com/tech-resources/article/top-20-tips-tricks-bluebeam-revu-3/>
[^6]: Official MCP Servers repository and registry. <https://github.com/modelcontextprotocol/servers> + <https://registry.modelcontextprotocol.io/>
[^7]: Stirling-PDF GitHub README — Pipeline ("no-code pipelines direct in UI with APIs to process millions of PDFs") and Multi-Tool descriptions. <https://github.com/Stirling-Tools/Stirling-PDF>
