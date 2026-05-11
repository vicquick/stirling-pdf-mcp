# Decision log

| # | Topic | Options | Decision | Date | Rationale |
|---|---|---|---|---|---|
| 1 | Language | TS (gufao native) vs Python+FastMCP | **Python + FastMCP, fork+rewrite** | 2026-05-11 | Matches flux-mcp/qgis-mcp/blender-mcp stack; preserves fork-graph attribution to gufao on GitHub |
| 2 | Repo strategy | Fork-and-rewrite vs standalone-with-credit | **Fork** | 2026-05-11 | `vicquick/stirling-pdf-mcp` forked from `gufao/mcp-server-stirling-pdf`, branch `rewrite/python-fastmcp` |
| 3 | Stirling auth | Service account vs per-user vs admin | **Dedicated service-account API key** | 2026-05-11 | Clean audit trail, revocable, scoped permissions, fits metamcp federation model |
| 4 | First-version scope | Staged vs full | **Layer 0-3 all upfront** | 2026-05-11 | User explicit: maximum capability, ~2 weeks, builds the full vision in one push |
| 5 | gpt-researcher pass | Yes vs skip | **Yes — deep research first** | 2026-05-11 | Inform Layer 2 composite list with industry workflows + AEC patterns before coding |
| 6 | AI Tools | Use existing keys vs skip | TBD | – | Decide after research surfaces actual use case for pdf-comment-agent / math-auditor-agent |
| 7 | Output dir | Bind mount vs stream-only | TBD | – | – |
| 8 | Concurrency limit | N parallel | TBD | – | – |
| 9 | Backend URL strategy | Internal Docker DNS vs FQDN | TBD | – | – |
