# Stirling PDF MCP Server

A Model Context Protocol (MCP) server that provides secure integration with Stirling PDF, enabling AI assistants to perform comprehensive PDF manipulation operations.

Built with TypeScript for type safety and modern development practices.

## Recent Updates

**v1.1.0** - December 2025
- ✅ **Fixed multipart/form-data handling** - Switched from native `fetch` to `axios` for reliable file uploads from Docker containers
- ✅ **Fixed watermark functionality** - Resolved "colorString is null" error by ensuring `customColor` parameter is properly sent
- ✅ **Improved error handling** - Now displays actual error messages from Stirling PDF API
- ✅ **Verified Docker MCP Gateway compatibility** - Fully tested with Docker Desktop MCP Toolkit

## Purpose

This MCP server provides a secure interface for AI assistants to interact with a self-hosted Stirling PDF instance, enabling powerful PDF manipulation capabilities directly from Claude Desktop or other MCP-compatible clients.

## Features

### Current Implementation

- **`merge_pdfs`** - Merge multiple PDF files into a single document
- **`split_pdf`** - Split a PDF into multiple files at specified page numbers
- **`compress_pdf`** - Compress PDF files to reduce size with configurable optimization levels
- **`convert_pdf_to_images`** - Convert PDF pages to image files (PNG, JPG, GIF)
- **`rotate_pdf`** - Rotate pages in a PDF document
- **`add_watermark`** - Add text watermarks to PDF documents
- **`remove_pages`** - Remove specified pages from a PDF
- **`extract_images`** - Extract all images from a PDF document
- **`convert_images_to_pdf`** - Convert one or more images to a PDF document
- **`ocr_pdf`** - Perform OCR on a PDF to make it searchable

## Prerequisites

- **Node.js 20 or higher**
- **Docker Desktop with MCP Toolkit enabled**
- **Docker MCP CLI plugin** (`docker mcp` command)
- **Stirling PDF instance** - A running Stirling PDF server (self-hosted or accessible)
  - Download from: https://github.com/Stirling-Tools/Stirling-PDF
  - Quick start with Docker: `docker run -d -p 8080:8080 frooodle/s-pdf:latest`

### Get Your Stirling PDF Instance

You need a running Stirling PDF instance to use this MCP server. Options:

1. **Docker (Recommended)**:
   ```bash
   docker run -d \
     -p 8080:8080 \
     -v ./configs:/configs \
     -v ./logs:/logs \
     -e DOCKER_ENABLE_SECURITY=false \
     --name stirling-pdf \
     frooodle/s-pdf:latest
   ```

2. **Docker Compose**: See the [official documentation](https://docs.stirlingpdf.com/)

3. **Self-hosted**: Follow the [installation guide](https://github.com/Stirling-Tools/Stirling-PDF)

## Installation

### Step 1: Save the Files

```bash
# Project files are already in the repository
cd mcp-server-stirling-pdf
```

### Step 2: Install Dependencies

```bash
npm install
```

**Key Dependencies**:
- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `axios` - HTTP client for reliable multipart/form-data uploads
- `form-data` - Multipart form data library
- `typescript` - Type-safe development

### Step 3: Build TypeScript

```bash
npm run build
```

### Step 4: Build Docker Image

```bash
docker build -t stirling-pdf-mcp-server .
```

### Step 5: Set Up Secrets

```bash
# Set your Stirling PDF instance URL
docker mcp secret set STIRLING_PDF_URL="http://host.docker.internal:8080"

# If your Stirling PDF has authentication enabled, set the API key
docker mcp secret set STIRLING_PDF_API_KEY="your-api-key-here"

# Verify secrets
docker mcp secret list
```

**Note**: Use `http://host.docker.internal:8080` to connect to Stirling PDF running on your host machine.

### Step 6: Create Custom Catalog

```bash
# Create catalogs directory if it doesn't exist
mkdir -p ~/.docker/mcp/catalogs

# Create or edit custom.yaml
nano ~/.docker/mcp/catalogs/custom.yaml
```

Add this entry to custom.yaml:

```yaml
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  stirling-pdf:
    description: "MCP server for Stirling PDF - comprehensive PDF manipulation capabilities"
    title: "Stirling PDF"
    type: server
    dateAdded: "2025-12-17T00:00:00Z"
    image: stirling-pdf-mcp-server:latest
    ref: ""
    readme: ""
    toolsUrl: ""
    source: ""
    upstream: ""
    icon: ""
    tools:
      - name: merge_pdfs
      - name: split_pdf
      - name: compress_pdf
      - name: convert_pdf_to_images
      - name: rotate_pdf
      - name: add_watermark
      - name: remove_pages
      - name: extract_images
      - name: convert_images_to_pdf
      - name: ocr_pdf
    secrets:
      - name: STIRLING_PDF_URL
        env: STIRLING_PDF_URL
        example: "http://host.docker.internal:8080"
      - name: STIRLING_PDF_API_KEY
        env: STIRLING_PDF_API_KEY
        example: "your-api-key-here"
    metadata:
      category: productivity
      tags:
        - pdf
        - documents
        - conversion
        - ocr
      license: GPL-3.0
      owner: local
```

### Step 7: Update Registry

```bash
# Edit registry file
nano ~/.docker/mcp/registry.yaml
```

Add this entry under the existing `registry:` key:

```yaml
registry:
  # ... existing servers ...
  stirling-pdf:
    ref: ""
```

**IMPORTANT**: The entry must be under the `registry:` key, not at the root level.

### Step 8: Configure Claude Desktop

Find your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Edit the file and add your custom catalog to the args array:

```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/Users/your_username/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/custom.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

Replace `/Users/your_username` with your actual home directory path:

- **macOS**: `/Users/your_username`
- **Windows**: `C:\\Users\\your_username` (use double backslashes)
- **Linux**: `/home/your_username`

### Step 9: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Start Claude Desktop again
3. Your Stirling PDF tools should now appear!

### Step 10: Test Your Server

```bash
# Verify it appears in the list
docker mcp server list | grep stirling

# Test the server manually (optional)
docker run --rm -i \
  -e STIRLING_PDF_URL=http://host.docker.internal:8080 \
  -e STIRLING_PDF_API_KEY=your-api-key \
  stirling-pdf-mcp-server:latest \
  node /app/dist/index.js <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
EOF

# You should see a JSON response listing all 10 tools

# Check logs if needed
docker ps
docker logs <container_name>
```

**Testing in Claude Desktop**: After restarting Claude, ask:
- "What PDF tools do you have available?"
- "Add a watermark saying 'TEST' to this PDF" (upload a PDF file)

## Development

### Local Development

```bash
# Install dependencies
npm install

# Run in development mode with auto-reload
npm run dev

# Type check
npm run typecheck

# Build
npm run build

# Run production build
npm start
```

### Local Testing

```bash
# Set environment variables for testing
export STIRLING_PDF_URL="http://localhost:8080"
export STIRLING_PDF_API_KEY="test-key"

# Run directly
npm start
```

## Usage Examples

In Claude Desktop, you can ask:

### Merging PDFs
- "Merge these two PDF files into one"
- "Combine all the PDF documents I just sent you"

### Splitting PDFs
- "Split this PDF at pages 3 and 7"
- "Break this PDF into separate files at page 5"

### Compressing PDFs
- "Compress this PDF to make it smaller"
- "Reduce the file size of this PDF with high compression"

### Converting PDFs
- "Convert this PDF to PNG images at 300 DPI"
- "Turn these images into a single PDF"

### Rotating PDFs
- "Rotate all pages in this PDF 90 degrees"
- "Rotate pages 2, 3, and 4 by 180 degrees"

### Watermarking
- "Add a 'DRAFT' watermark to this PDF"
- "Add 'CONFIDENTIAL' as a watermark with 30% opacity"

### Page Operations
- "Remove pages 1, 3, and 5 from this PDF"
- "Extract all images from this PDF"

### OCR
- "Make this scanned PDF searchable using OCR"
- "Perform OCR on this PDF in English and Spanish"

## Architecture

```
Claude Desktop → MCP Gateway → Stirling PDF MCP Server → Stirling PDF Instance
                       ↓
            Docker Desktop Secrets
              (URL, API Key)
```

### Technical Stack

- **Language**: TypeScript (strict mode)
- **HTTP Client**: Axios (for reliable multipart/form-data handling)
- **MCP SDK**: @modelcontextprotocol/sdk
- **Transport**: stdio (standard input/output)
- **Form Data**: form-data library for multipart uploads
- **Runtime**: Node.js 20+

## File Format

All PDF and image files are passed as **base64 data URLs**. Claude Desktop handles this automatically when you upload files.

Example format:
```
data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKM...
```

## TypeScript Benefits

- **Type Safety**: Catch errors at compile time
- **Better IDE Support**: Enhanced autocomplete and refactoring
- **Modern JavaScript**: Use latest ECMAScript features
- **Maintainability**: Self-documenting code with types
- **API Type Definitions**: Strongly typed Stirling PDF API interactions

## Adding New Tools

1. Define the tool function in `src/index.ts`:

```typescript
async function myNewTool(param: string): Promise<string> {
  try {
    validateRequired(param, "param");

    const formData = new FormData();
    const buffer = base64ToBuffer(param); // Convert base64 data URL to Buffer
    formData.append("fileInput", buffer, "input.pdf");
    // Add additional parameters as needed
    formData.append("paramName", "paramValue");

    const resultBuffer = await callStirlingAPI("/api/v1/endpoint", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Success message\n\n📄 Result:\n${resultBase64}`;
  } catch (error) {
    logger.error("Error:", error);
    return formatError(error);
  }
}
```

**Note**: The `callStirlingAPI` function uses axios for reliable multipart/form-data handling. All file uploads must use `Buffer` objects, not the raw FormData from the browser.

2. Add tool definition to `TOOLS` array:

```typescript
{
  name: "my_new_tool",
  description: "What it does",
  inputSchema: {
    type: "object",
    properties: {
      param: { type: "string", description: "Description" }
    },
    required: ["param"]
  }
}
```

3. Add case to tool handler:

```typescript
case "my_new_tool": {
  const param = (args?.param as string) || "";
  return {
    content: [{ type: "text", text: await myNewTool(param) }]
  };
}
```

4. Rebuild and redeploy:

```bash
npm run build
docker build -t stirling-pdf-mcp-server .
```

## Troubleshooting

### Tools Not Appearing

- Verify Docker image built successfully: `docker images | grep stirling-pdf`
- Check catalog file syntax: `cat ~/.docker/mcp/catalogs/custom.yaml`
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop completely

### Connection Errors

- Verify Stirling PDF is running: `curl http://localhost:8080`
- Check if using correct URL in secrets: `docker mcp secret list`
- Use `host.docker.internal` instead of `localhost` for host-based Stirling PDF
- Check firewall settings

### Authentication Errors

- Verify secrets are set: `docker mcp secret list`
- Check if Stirling PDF has security enabled
- Verify API key is correct in Stirling PDF settings
- Test API key with curl: `curl -H "X-API-KEY: your-key" http://localhost:8080/api/v1/info/status`

### Build Errors

- Check TypeScript version compatibility: `npm run typecheck`
- Ensure all dependencies are installed: `npm install`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

### PDF Operation Failures

- Check file size limits in Stirling PDF configuration
- Verify PDF files are valid and not corrupted
- Check Stirling PDF logs: `docker logs stirling-pdf`
- Ensure timeout is sufficient for large files (default: 2 minutes)

### Watermark Errors (colorString is null)

If you see `Cannot invoke "String.startsWith(String)" because "colorString" is null`:
- This error occurs when the `customColor` parameter is missing or malformed
- The MCP server automatically includes `customColor=#000000` (black watermark)
- This was fixed in the latest version by using axios instead of fetch
- If you modified the code, ensure `customColor` parameter is included in watermark requests

### HTTP 400/500 Errors from Stirling PDF

- **Verify you're using axios**: The native Node.js `fetch` API has issues with multipart/form-data from Docker containers
- **Check parameter format**: Stirling PDF is sensitive to parameter formats
- **Review Stirling PDF logs**: `docker logs stirling-pdf --tail 50` shows the actual Java errors
- **Test with curl**: Verify the API works outside the MCP server:
  ```bash
  curl -X POST http://localhost:8080/api/v1/security/add-watermark \
    -H "X-API-KEY: your-key" \
    -F "fileInput=@test.pdf" \
    -F "watermarkType=text" \
    -F "watermarkText=TEST" \
    -F "customColor=#000000"
  ```

## Security Considerations

- All secrets stored in Docker Desktop secrets (never hardcoded)
- API key transmitted securely via X-API-KEY header
- Running as non-root user in Docker container
- Sensitive data never logged
- Input validation on all parameters
- Timeout protection on external calls (2 minute timeout)
- Stirling PDF runs locally - no data sent to external services

## Stirling PDF API Reference

For complete Stirling PDF API documentation, visit:
- Your instance: `http://your-instance:port/swagger-ui/index.html`
- Official docs: https://docs.stirlingpdf.com/API/

## Sources

- [Stirling PDF API Documentation](https://docs.stirlingpdf.com/API/)
- [Stirling PDF GitHub Repository](https://github.com/Stirling-Tools/Stirling-PDF)
- [Stirling PDF Getting Started Guide](https://docs.stirlingpdf.com/)
- [API Reference on DeepWiki](https://deepwiki.com/Stirling-Tools/Stirling-PDF/4-api-reference)

## License

GPL-3.0

## Contributing

This project follows the GPL-3.0 license. All modifications must comply with GPL-3.0 requirements.

## Built by 18X Labs

Empowering AI assistants with comprehensive PDF manipulation capabilities.