#!/usr/bin/env node

/**
 * Stirling PDF MCP Server
 * Provides integration with Stirling PDF for PDF manipulation operations
 *
 * @license GPL-3.0
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import FormData from "form-data";
import axios from "axios";

// Configuration from environment variables
const STIRLING_PDF_URL = process.env.STIRLING_PDF_URL || "http://localhost:8080";
const STIRLING_PDF_API_KEY = process.env.STIRLING_PDF_API_KEY || "";

// Logging configuration - log to stderr
const logger = {
  info: (...args: unknown[]) => console.error("[INFO]", ...args),
  error: (...args: unknown[]) => console.error("[ERROR]", ...args),
  warn: (...args: unknown[]) => console.error("[WARN]", ...args),
};

// === UTILITY FUNCTIONS ===

/**
 * Format error message for user display
 */
function formatError(error: unknown): string {
  if (error instanceof Error) {
    return `❌ Error: ${error.message}`;
  }
  return `❌ Error: ${String(error)}`;
}

/**
 * Validate required parameter
 */
function validateRequired(value: string | undefined, name: string): string {
  if (!value || value.trim() === "") {
    throw new Error(`${name} is required`);
  }
  return value.trim();
}

/**
 * Convert base64 string to Buffer
 */
function base64ToBuffer(base64: string): Buffer {
  // Remove data URL prefix if present
  const base64Data = base64.replace(/^data:[^;]+;base64,/, "");
  return Buffer.from(base64Data, "base64");
}

/**
 * Make authenticated request to Stirling PDF API
 */
async function callStirlingAPI(
  endpoint: string,
  formData: FormData
): Promise<Buffer> {
  const url = `${STIRLING_PDF_URL}${endpoint}`;

  logger.info(`Calling Stirling PDF API: ${endpoint}`);

  const headers: Record<string, string> = {
    ...formData.getHeaders(),
  };

  // Add API key if configured
  if (STIRLING_PDF_API_KEY) {
    headers["X-API-KEY"] = STIRLING_PDF_API_KEY;
  }

  try {
    const response = await axios.post(url, formData, {
      headers,
      responseType: 'arraybuffer',
      timeout: 120000, // 2 minute timeout for PDF operations
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
    });

    return Buffer.from(response.data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status || 'unknown';
      const statusText = error.response?.statusText || 'Unknown Error';
      const errorData = error.response?.data ? Buffer.from(error.response.data).toString('utf-8') : '';
      throw new Error(
        `Stirling PDF API returned ${status}: ${errorData || statusText}`
      );
    }
    throw error;
  }
}

/**
 * Convert Buffer to base64 data URL
 */
function bufferToBase64DataUrl(buffer: Buffer, mimeType: string = "application/pdf"): string {
  return `data:${mimeType};base64,${buffer.toString("base64")}`;
}

// === TOOL IMPLEMENTATIONS ===

/**
 * Merge multiple PDF files into a single PDF
 */
async function mergePDFs(
  pdfFiles: string[] = [],
  sortType: string = "orderProvided"
): Promise<string> {
  logger.info(`Merging ${pdfFiles.length} PDF files`);

  try {
    if (!pdfFiles || pdfFiles.length < 2) {
      throw new Error("At least 2 PDF files are required for merging");
    }

    const formData = new FormData();

    // Add each PDF file
    pdfFiles.forEach((base64Pdf, index) => {
      const buffer = base64ToBuffer(base64Pdf);
      formData.append("fileInput", buffer, `file${index + 1}.pdf`);
    });

    // Add sort type parameter
    formData.append("sortType", sortType);

    const resultBuffer = await callStirlingAPI("/api/v1/general/merge-pdfs", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully merged ${pdfFiles.length} PDF files\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in mergePDFs:", error);
    return formatError(error);
  }
}

/**
 * Split a PDF into multiple files
 */
async function splitPDF(
  pdfFile: string = "",
  pageNumbers: string = ""
): Promise<string> {
  logger.info(`Splitting PDF at pages: ${pageNumbers}`);

  try {
    validateRequired(pdfFile, "pdfFile");
    validateRequired(pageNumbers, "pageNumbers");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("pageNumbers", pageNumbers);

    const resultBuffer = await callStirlingAPI("/api/v1/general/split-pages", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer, "application/zip");

    return `✅ Successfully split PDF at pages: ${pageNumbers}\n\n📦 Result (ZIP file as base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in splitPDF:", error);
    return formatError(error);
  }
}

/**
 * Compress a PDF file
 */
async function compressPDF(
  pdfFile: string = "",
  optimizeLevel: string = "2"
): Promise<string> {
  logger.info(`Compressing PDF with optimization level: ${optimizeLevel}`);

  try {
    validateRequired(pdfFile, "pdfFile");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("optimizeLevel", optimizeLevel);
    formData.append("fastWebView", "false");

    const resultBuffer = await callStirlingAPI("/api/v1/misc/compress-pdf", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully compressed PDF (optimization level: ${optimizeLevel})\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in compressPDF:", error);
    return formatError(error);
  }
}

/**
 * Convert PDF to images
 */
async function convertPDFToImages(
  pdfFile: string = "",
  imageFormat: string = "png",
  dpi: string = "300"
): Promise<string> {
  logger.info(`Converting PDF to ${imageFormat} images at ${dpi} DPI`);

  try {
    validateRequired(pdfFile, "pdfFile");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("imageFormat", imageFormat);
    formData.append("dpi", dpi);
    formData.append("colorType", "color");
    formData.append("singleOrMultiple", "multiple");

    const resultBuffer = await callStirlingAPI("/api/v1/convert/pdf/img", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer, "application/zip");

    return `✅ Successfully converted PDF to ${imageFormat} images\n\n📦 Result (ZIP file as base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in convertPDFToImages:", error);
    return formatError(error);
  }
}

/**
 * Rotate pages in a PDF
 */
async function rotatePDF(
  pdfFile: string = "",
  angle: string = "90",
  pageNumbers: string = "all"
): Promise<string> {
  logger.info(`Rotating PDF pages by ${angle} degrees`);

  try {
    validateRequired(pdfFile, "pdfFile");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("angle", angle);
    formData.append("pageNumbers", pageNumbers);

    const resultBuffer = await callStirlingAPI("/api/v1/general/rotate-pdf", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully rotated PDF pages by ${angle}°\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in rotatePDF:", error);
    return formatError(error);
  }
}

/**
 * Add watermark to PDF
 */
async function addWatermark(
  pdfFile: string = "",
  watermarkText: string = "",
  fontSize: string = "30",
  opacity: string = "0.5",
  rotation: string = "45"
): Promise<string> {
  logger.info(`Adding watermark to PDF: "${watermarkText}"`);

  try {
    validateRequired(pdfFile, "pdfFile");
    validateRequired(watermarkText, "watermarkText");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("watermarkType", "text");
    formData.append("watermarkText", watermarkText);
    formData.append("alphabet", "roman");
    formData.append("fontSize", fontSize);
    formData.append("rotation", rotation);
    formData.append("opacity", opacity);
    formData.append("widthSpacer", "50");
    formData.append("heightSpacer", "50");
    formData.append("customColor", "#000000");

    const resultBuffer = await callStirlingAPI("/api/v1/security/add-watermark", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully added watermark: "${watermarkText}"\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in addWatermark:", error);
    return formatError(error);
  }
}

/**
 * Remove pages from PDF
 */
async function removePages(
  pdfFile: string = "",
  pagesToRemove: string = ""
): Promise<string> {
  logger.info(`Removing pages from PDF: ${pagesToRemove}`);

  try {
    validateRequired(pdfFile, "pdfFile");
    validateRequired(pagesToRemove, "pagesToRemove");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("pagesToDelete", pagesToRemove);

    const resultBuffer = await callStirlingAPI("/api/v1/general/remove-pages", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully removed pages: ${pagesToRemove}\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in removePages:", error);
    return formatError(error);
  }
}

/**
 * Extract images from PDF
 */
async function extractImages(
  pdfFile: string = "",
  format: string = "png"
): Promise<string> {
  logger.info(`Extracting images from PDF in ${format} format`);

  try {
    validateRequired(pdfFile, "pdfFile");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");
    formData.append("format", format);

    const resultBuffer = await callStirlingAPI("/api/v1/general/extract-images", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer, "application/zip");

    return `✅ Successfully extracted images from PDF\n\n📦 Result (ZIP file as base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in extractImages:", error);
    return formatError(error);
  }
}

/**
 * Convert images to PDF
 */
async function convertImagesToPDF(
  imageFiles: string[] = [],
  fitOption: string = "fillPage",
  colorType: string = "color"
): Promise<string> {
  logger.info(`Converting ${imageFiles.length} images to PDF`);

  try {
    if (!imageFiles || imageFiles.length < 1) {
      throw new Error("At least 1 image file is required");
    }

    const formData = new FormData();

    // Add each image file
    imageFiles.forEach((base64Image, index) => {
      const buffer = base64ToBuffer(base64Image);
      // Try to detect image format from data URL
      const formatMatch = base64Image.match(/^data:image\/(\w+);/);
      const ext = formatMatch ? formatMatch[1] : "png";
      formData.append("fileInput", buffer, `image${index + 1}.${ext}`);
    });

    formData.append("fitOption", fitOption);
    formData.append("colorType", colorType);
    formData.append("autoRotate", "false");

    const resultBuffer = await callStirlingAPI("/api/v1/convert/img/pdf", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully converted ${imageFiles.length} images to PDF\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in convertImagesToPDF:", error);
    return formatError(error);
  }
}

/**
 * OCR a PDF to make it searchable
 */
async function ocrPDF(
  pdfFile: string = "",
  languages: string = "eng",
  sidecar: string = "false",
  deskew: string = "false",
  clean: string = "false",
  cleanFinal: string = "false",
  ocrType: string = "skip-text"
): Promise<string> {
  logger.info(`Performing OCR on PDF with languages: ${languages}`);

  try {
    validateRequired(pdfFile, "pdfFile");

    const formData = new FormData();
    const buffer = base64ToBuffer(pdfFile);
    formData.append("fileInput", buffer, "input.pdf");

    // Split comma-separated languages
    const langArray = languages.split(",").map(l => l.trim());
    langArray.forEach(lang => {
      formData.append("languages", lang);
    });

    formData.append("sidecar", sidecar);
    formData.append("deskew", deskew);
    formData.append("clean", clean);
    formData.append("cleanFinal", cleanFinal);
    formData.append("ocrType", ocrType);

    const resultBuffer = await callStirlingAPI("/api/v1/misc/ocr-pdf", formData);
    const resultBase64 = bufferToBase64DataUrl(resultBuffer);

    return `✅ Successfully performed OCR on PDF\nLanguages: ${languages}\n\n📄 Result (base64 data URL):\n${resultBase64}`;
  } catch (error) {
    logger.error("Error in ocrPDF:", error);
    return formatError(error);
  }
}

// === MCP SERVER SETUP ===

const server = new Server(
  {
    name: "stirling-pdf",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
const TOOLS: Tool[] = [
  {
    name: "merge_pdfs",
    description: "Merge multiple PDF files into a single PDF document",
    inputSchema: {
      type: "object",
      properties: {
        pdfFiles: {
          type: "array",
          items: { type: "string" },
          description: "Array of PDF files as base64 data URLs (at least 2 files)",
        },
        sortType: {
          type: "string",
          enum: ["orderProvided", "alphabetical", "reverseAlphabetical"],
          description: "How to sort files before merging (default: orderProvided)",
        },
      },
      required: ["pdfFiles"],
    },
  },
  {
    name: "split_pdf",
    description: "Split a PDF document into multiple files at specified page numbers",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        pageNumbers: {
          type: "string",
          description: "Comma-separated page numbers to split at (e.g., '2,4,6')",
        },
      },
      required: ["pdfFile", "pageNumbers"],
    },
  },
  {
    name: "compress_pdf",
    description: "Compress a PDF file to reduce its size",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        optimizeLevel: {
          type: "string",
          enum: ["0", "1", "2", "3"],
          description: "Optimization level: 0=minimal, 1=low, 2=medium, 3=high (default: 2)",
        },
      },
      required: ["pdfFile"],
    },
  },
  {
    name: "convert_pdf_to_images",
    description: "Convert PDF pages to image files",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        imageFormat: {
          type: "string",
          enum: ["png", "jpg", "gif"],
          description: "Output image format (default: png)",
        },
        dpi: {
          type: "string",
          description: "DPI for output images (default: 300)",
        },
      },
      required: ["pdfFile"],
    },
  },
  {
    name: "rotate_pdf",
    description: "Rotate pages in a PDF document",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        angle: {
          type: "string",
          enum: ["90", "180", "270"],
          description: "Rotation angle in degrees (default: 90)",
        },
        pageNumbers: {
          type: "string",
          description: "Page numbers to rotate (comma-separated) or 'all' (default: all)",
        },
      },
      required: ["pdfFile"],
    },
  },
  {
    name: "add_watermark",
    description: "Add a text watermark to a PDF document",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        watermarkText: {
          type: "string",
          description: "Text to use as watermark",
        },
        fontSize: {
          type: "string",
          description: "Font size for watermark (default: 30)",
        },
        opacity: {
          type: "string",
          description: "Opacity of watermark 0.0-1.0 (default: 0.5)",
        },
        rotation: {
          type: "string",
          description: "Rotation angle of watermark in degrees (default: 45)",
        },
      },
      required: ["pdfFile", "watermarkText"],
    },
  },
  {
    name: "remove_pages",
    description: "Remove specified pages from a PDF document",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        pagesToRemove: {
          type: "string",
          description: "Comma-separated page numbers to remove (e.g., '1,3,5-7')",
        },
      },
      required: ["pdfFile", "pagesToRemove"],
    },
  },
  {
    name: "extract_images",
    description: "Extract all images from a PDF document",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        format: {
          type: "string",
          enum: ["png", "jpg", "gif"],
          description: "Output image format (default: png)",
        },
      },
      required: ["pdfFile"],
    },
  },
  {
    name: "convert_images_to_pdf",
    description: "Convert one or more images to a PDF document",
    inputSchema: {
      type: "object",
      properties: {
        imageFiles: {
          type: "array",
          items: { type: "string" },
          description: "Array of image files as base64 data URLs",
        },
        fitOption: {
          type: "string",
          enum: ["fillPage", "fitDocumentToImage", "maintainAspectRatio"],
          description: "How to fit images on pages (default: fillPage)",
        },
        colorType: {
          type: "string",
          enum: ["color", "greyscale", "blackwhite"],
          description: "Color mode for output (default: color)",
        },
      },
      required: ["imageFiles"],
    },
  },
  {
    name: "ocr_pdf",
    description: "Perform OCR on a PDF to make it searchable",
    inputSchema: {
      type: "object",
      properties: {
        pdfFile: {
          type: "string",
          description: "PDF file as base64 data URL",
        },
        languages: {
          type: "string",
          description: "Comma-separated language codes (e.g., 'eng', 'eng,spa,fra') (default: eng)",
        },
        sidecar: {
          type: "string",
          enum: ["true", "false"],
          description: "Generate sidecar text file (default: false)",
        },
        deskew: {
          type: "string",
          enum: ["true", "false"],
          description: "Deskew pages before OCR (default: false)",
        },
        clean: {
          type: "string",
          enum: ["true", "false"],
          description: "Clean pages before OCR (default: false)",
        },
        cleanFinal: {
          type: "string",
          enum: ["true", "false"],
          description: "Clean final output (default: false)",
        },
        ocrType: {
          type: "string",
          enum: ["skip-text", "force-ocr", "Normal"],
          description: "OCR processing mode (default: skip-text)",
        },
      },
      required: ["pdfFile"],
    },
  },
];

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "merge_pdfs": {
        const pdfFiles = (args?.pdfFiles as string[]) || [];
        const sortType = (args?.sortType as string) || "orderProvided";
        return {
          content: [
            {
              type: "text",
              text: await mergePDFs(pdfFiles, sortType),
            },
          ],
        };
      }

      case "split_pdf": {
        const pdfFile = (args?.pdfFile as string) || "";
        const pageNumbers = (args?.pageNumbers as string) || "";
        return {
          content: [
            {
              type: "text",
              text: await splitPDF(pdfFile, pageNumbers),
            },
          ],
        };
      }

      case "compress_pdf": {
        const pdfFile = (args?.pdfFile as string) || "";
        const optimizeLevel = (args?.optimizeLevel as string) || "2";
        return {
          content: [
            {
              type: "text",
              text: await compressPDF(pdfFile, optimizeLevel),
            },
          ],
        };
      }

      case "convert_pdf_to_images": {
        const pdfFile = (args?.pdfFile as string) || "";
        const imageFormat = (args?.imageFormat as string) || "png";
        const dpi = (args?.dpi as string) || "300";
        return {
          content: [
            {
              type: "text",
              text: await convertPDFToImages(pdfFile, imageFormat, dpi),
            },
          ],
        };
      }

      case "rotate_pdf": {
        const pdfFile = (args?.pdfFile as string) || "";
        const angle = (args?.angle as string) || "90";
        const pageNumbers = (args?.pageNumbers as string) || "all";
        return {
          content: [
            {
              type: "text",
              text: await rotatePDF(pdfFile, angle, pageNumbers),
            },
          ],
        };
      }

      case "add_watermark": {
        const pdfFile = (args?.pdfFile as string) || "";
        const watermarkText = (args?.watermarkText as string) || "";
        const fontSize = (args?.fontSize as string) || "30";
        const opacity = (args?.opacity as string) || "0.5";
        const rotation = (args?.rotation as string) || "45";
        return {
          content: [
            {
              type: "text",
              text: await addWatermark(pdfFile, watermarkText, fontSize, opacity, rotation),
            },
          ],
        };
      }

      case "remove_pages": {
        const pdfFile = (args?.pdfFile as string) || "";
        const pagesToRemove = (args?.pagesToRemove as string) || "";
        return {
          content: [
            {
              type: "text",
              text: await removePages(pdfFile, pagesToRemove),
            },
          ],
        };
      }

      case "extract_images": {
        const pdfFile = (args?.pdfFile as string) || "";
        const format = (args?.format as string) || "png";
        return {
          content: [
            {
              type: "text",
              text: await extractImages(pdfFile, format),
            },
          ],
        };
      }

      case "convert_images_to_pdf": {
        const imageFiles = (args?.imageFiles as string[]) || [];
        const fitOption = (args?.fitOption as string) || "fillPage";
        const colorType = (args?.colorType as string) || "color";
        return {
          content: [
            {
              type: "text",
              text: await convertImagesToPDF(imageFiles, fitOption, colorType),
            },
          ],
        };
      }

      case "ocr_pdf": {
        const pdfFile = (args?.pdfFile as string) || "";
        const languages = (args?.languages as string) || "eng";
        const sidecar = (args?.sidecar as string) || "false";
        const deskew = (args?.deskew as string) || "false";
        const clean = (args?.clean as string) || "false";
        const cleanFinal = (args?.cleanFinal as string) || "false";
        const ocrType = (args?.ocrType as string) || "skip-text";
        return {
          content: [
            {
              type: "text",
              text: await ocrPDF(pdfFile, languages, sidecar, deskew, clean, cleanFinal, ocrType),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    logger.error(`Error executing tool ${name}:`, error);
    return {
      content: [
        {
          type: "text",
          text: formatError(error),
        },
      ],
      isError: true,
    };
  }
});

// === SERVER STARTUP ===

async function main() {
  logger.info("Starting Stirling PDF MCP server...");

  // Validate configuration
  if (!STIRLING_PDF_URL) {
    logger.warn("STIRLING_PDF_URL not set, using default: http://localhost:8080");
  } else {
    logger.info(`Stirling PDF URL: ${STIRLING_PDF_URL}`);
  }

  if (!STIRLING_PDF_API_KEY) {
    logger.warn("STIRLING_PDF_API_KEY not set - API calls may fail if authentication is required");
  } else {
    logger.info("STIRLING_PDF_API_KEY is configured");
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("✅ Stirling PDF MCP server running on stdio");
  logger.info("🚀 Ready to process PDF operations");
}

main().catch((error) => {
  logger.error("Fatal error:", error);
  process.exit(1);
});
