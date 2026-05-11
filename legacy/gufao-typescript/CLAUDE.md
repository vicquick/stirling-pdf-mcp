# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP server for Stirling PDF - a Model Context Protocol server that integrates with Stirling PDF to provide PDF manipulation capabilities as MCP tools.

## License

GPL-3.0 - All code modifications must comply with GPL-3.0 requirements.

## Implementation Status

✅ **IMPLEMENTED** - The MCP server is fully functional with 10 core tools for PDF manipulation.

## Architecture

This is an MCP (Model Context Protocol) server that:
- Connects to a Stirling PDF instance (self-hosted PDF manipulation service)
- Exposes Stirling PDF operations as MCP tools
- Handles authentication via X-API-KEY header
- Routes requests to Stirling PDF REST API
- Uses stdio transport for communication with MCP clients

### MCP Server Pattern

The implementation follows the standard MCP server pattern:
- **Tool definitions** - 10 tools exposing PDF operations (src/index.ts lines 585-714)
- **Request handlers** - Maps MCP tool calls to Stirling PDF API calls
- **Configuration** - Environment variables for endpoint URL and API key
- **Transport layer** - stdio transport for Claude Desktop integration

### Integration with Stirling PDF

The server implements these Stirling PDF API endpoints:

**Implemented Tools:**
1. `merge_pdfs` - POST /api/v1/general/merge-pdfs
2. `split_pdf` - POST /api/v1/general/split-pages
3. `compress_pdf` - POST /api/v1/misc/compress-pdf
4. `convert_pdf_to_images` - POST /api/v1/convert/pdf/img
5. `rotate_pdf` - POST /api/v1/general/rotate-pdf
6. `add_watermark` - POST /api/v1/misc/add-watermark
7. `remove_pages` - POST /api/v1/general/remove-pages
8. `extract_images` - POST /api/v1/general/extract-images
9. `convert_images_to_pdf` - POST /api/v1/convert/img/pdf
10. `ocr_pdf` - POST /api/v1/misc/ocr-pdf

**File Handling:**
- All files passed as base64 data URLs
- Converted to Buffer for API calls via `base64ToBuffer()` function
- Results returned as base64 data URLs via `bufferToBase64DataUrl()` function
- ZIP files for operations that produce multiple files (split, extract images)

**Authentication:**
- Uses X-API-KEY header when STIRLING_PDF_API_KEY environment variable is set
- Gracefully handles unauthenticated instances

**Error Handling:**
- Comprehensive try/catch blocks in all tool functions
- User-friendly error messages via `formatError()` function
- 2-minute timeout for all API calls
- Input validation via `validateRequired()` and `validateUrl()` functions

## Implementation Details

### Key Files

- **src/index.ts** - Main server implementation (~950 lines)
  - Utility functions (lines 24-105)
  - Tool implementations (lines 107-558)
  - MCP server setup (lines 560-780)
  - Server startup (lines 782-810)

- **package.json** - Dependencies and scripts
  - Uses @modelcontextprotocol/sdk for MCP
  - Uses form-data for multipart uploads
  - TypeScript 5.3+ with strict mode

- **tsconfig.json** - TypeScript configuration
  - Strict mode enabled
  - ES2022 target
  - ESNext modules with bundler resolution

- **Dockerfile** - Multi-stage build
  - Node 20 slim base image
  - TypeScript compilation in container
  - Non-root user for security

### Architecture Decisions

1. **TypeScript Strict Mode** - All code uses strict type checking for safety
2. **Base64 Data URLs** - Standard format for file exchange in MCP
3. **FormData for Uploads** - Stirling PDF uses multipart/form-data for file uploads
4. **Stderr Logging** - All logs to stderr to keep stdout clean for MCP protocol
5. **Input Validation** - Every user input is validated before use
6. **Error Handling** - Comprehensive try/catch blocks with user-friendly messages
7. **Timeout Protection** - 2-minute timeout on all API calls to prevent hangs

### Environment Variables

- `STIRLING_PDF_URL` - Stirling PDF instance URL (default: http://localhost:8080)
- `STIRLING_PDF_API_KEY` - Optional API key for authentication

### Docker Secrets

When deployed via Docker MCP:
- STIRLING_PDF_URL - Configured via `docker mcp secret set`
- STIRLING_PDF_API_KEY - Configured via `docker mcp secret set`

### File Format Handling

**Input (from MCP client):**
```
data:application/pdf;base64,JVBERi0xLjQK...
data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
```

**Processing:**
1. Extract base64 data via `base64ToBuffer()`
2. Create FormData with Buffer
3. POST to Stirling PDF API
4. Receive Buffer response
5. Convert to base64 data URL via `bufferToBase64DataUrl()`

**Output (to MCP client):**
```
✅ Success message

📄 Result (base64 data URL):
data:application/pdf;base64,JVBERi0xLjQK...
```

### API Integration Pattern

All tool functions follow this pattern:

```typescript
async function toolName(param: string = ""): Promise<string> {
  logger.info(`Operation description`);

  try {
    // 1. Validate inputs
    validateRequired(param, "param");

    // 2. Prepare FormData
    const formData = new FormData();
    const buffer = base64ToBuffer(fileInput);
    formData.append("fileInput", buffer, "filename.pdf");
    formData.append("param", value);

    // 3. Call Stirling PDF API
    const resultBuffer = await callStirlingAPI("/api/v1/endpoint", formData);

    // 4. Convert result
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    // 5. Return formatted result
    return `✅ Success message\n\n📄 Result:\n${resultBase64}`;
  } catch (error) {
    logger.error("Error:", error);
    return formatError(error);
  }
}
```

### Type Safety

All functions have explicit TypeScript types:
- All parameters have type annotations
- All return types are specified
- No `any` types except for FormData body (required by fetch API)
- Comprehensive error type guards

### Security Considerations

1. **Non-root user** - Docker container runs as mcpuser (UID 1000)
2. **Secret management** - All credentials via Docker secrets or environment variables
3. **Input validation** - All user inputs validated before use
4. **No data logging** - File contents never logged (privacy)
5. **Timeout protection** - All API calls have 2-minute timeout
6. **Local processing** - Stirling PDF runs locally, no external data transmission

## Development Guidelines

### Adding New Tools

To add a new Stirling PDF operation:

1. **Implement tool function** in src/index.ts following the pattern above
2. **Add tool definition** to TOOLS array with proper schema
3. **Add case** to CallToolRequestSchema handler
4. **Test locally** with `npm run dev`
5. **Update README.md** with new tool documentation
6. **Update custom.yaml** catalog with new tool name
7. **Rebuild** Docker image

### Testing

```bash
# Local development with hot reload
npm run dev

# Type checking
npm run typecheck

# Production build
npm run build && npm start
```

### Debugging

All logs go to stderr:
```bash
# View logs in development
npm run dev

# View logs in Docker
docker logs <container-name>
```

### Code Style

- Use async/await (not callbacks or .then())
- Validate all inputs at function entry
- Return user-friendly formatted strings
- Log to stderr, never stdout
- Use TypeScript strict mode
- No `any` types unless required by external API
- Use descriptive variable names
- Add JSDoc comments for complex functions

## Future Enhancements

Potential additions (not yet implemented):

1. **PDF/A Conversion** - Convert PDFs to PDF/A format
2. **Encryption/Decryption** - Add password protection
3. **Form Operations** - Fill PDF forms, extract form data
4. **Signature Operations** - Add/verify digital signatures
5. **Metadata Operations** - Edit PDF metadata
6. **Page Reordering** - Rearrange pages in custom order
7. **Batch Operations** - Process multiple PDFs in one call
8. **Preset Management** - Save and reuse operation presets

## Troubleshooting

### Common Issues

1. **Connection refused** - Stirling PDF not running or wrong URL
   - Fix: Use `host.docker.internal:8080` for host-based Stirling PDF

2. **Authentication errors** - API key not set or incorrect
   - Fix: Set STIRLING_PDF_API_KEY secret correctly

3. **Timeout errors** - Large PDF files taking too long
   - Fix: Increase timeout in src/index.ts line 70 (default: 120000ms)

4. **Memory errors** - Very large PDF files
   - Fix: Increase Node.js memory: `NODE_OPTIONS=--max-old-space-size=4096`

## References

- Stirling PDF API: https://docs.stirlingpdf.com/API/
- MCP Specification: https://modelcontextprotocol.io/
- TypeScript Handbook: https://www.typescriptlang.org/docs/
