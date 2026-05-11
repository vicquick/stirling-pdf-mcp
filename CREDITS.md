# Credits

## Forked from

[gufao/mcp-server-stirling-pdf](https://github.com/gufao/mcp-server-stirling-pdf) — 10-tool TypeScript MCP server for Stirling-PDF, MIT-licensed. Released v1.1.0 in December 2025.

gufao's contribution:
- First public MCP integration for Stirling-PDF
- Solved Docker MCP Gateway multipart-upload compatibility (axios over native fetch)
- Established the basic tool surface (merge, split, compress, OCR, watermark, rotate, remove pages, extract images, images→pdf, convert pdf→images)

This fork pivots to **Python + FastMCP** to align with the host project's MCP fleet ([flux-mcp](https://github.com/vicquick/flux-mcp), [qgis-mcp](https://github.com/vicquick/qgis-mcp), [blender-mcp](https://github.com/vicquick/blender-mcp), ifc-mcp, postgres-mcp, svg-mcp) — all Python + FastMCP + streamable-http.

gufao's original TypeScript is preserved in [`legacy/gufao-typescript/`](legacy/gufao-typescript/) as historical reference.

## Backend

[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) — the powerful open-source PDF editing platform this MCP wraps. None of this would matter without the 60+ tools and 260 REST endpoints Stirling exposes.

## Research influences

The composite-tool catalogue was informed by:

- [Nutrient (formerly PSPDFKit)](https://www.nutrient.io/sdk/web) — for the comprehensive baseline feature surface and industry-vertical breakdown (Legal / Finance / Healthcare / Education / Government / Construction).
- [Bluebeam Revu](https://support.bluebeam.com/) — for the AEC-specific workflow idioms (Sets, Markups List, Quantity Takeoff, Tool Chest, Studio Sessions).
- [LangChain](https://python.langchain.com/) — for the document-loader patterns that established the "agent + PDF" interface in the LLM era.
- The wider [Model Context Protocol](https://modelcontextprotocol.io/) ecosystem — for setting the bar of what a great MCP server feels like.

## Maintainers

- @vicquick — initial Python rewrite, AEC integration, composite design.

Pull requests welcome.
