#!/usr/bin/env node
/**
 * Star Atlas MCP Server
 *
 * Provides tools for Star Atlas game data access, fleet management,
 * market analysis, and Solana blockchain queries.
 *
 * Architecture:
 * - Hybrid data sourcing (Galaxy API + S3 cache for static data, Solana RPC for real-time)
 * - Optimized for context efficiency (response filtering, pagination, dual-response pattern)
 * - Production-ready error handling and validation
 *
 * @see https://build.staratlas.com/ - Official Star Atlas Build Portal
 * @see docs/mcp-server-implementation-plan.md - Implementation details
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SERVER_NAME, SERVER_VERSION } from "./constants.js";
import { registerShipTools } from "./tools/ships.js";

/**
 * Initialize the MCP server instance
 */
const server = new McpServer({
  name: SERVER_NAME,
  version: SERVER_VERSION,
});

/**
 * Register all MCP tools
 */
function registerTools() {
  console.error("[Server] Registering tools...");

  // Ship-related tools (Galaxy API + S3 cache)
  registerShipTools(server);

  console.error("[Server] Tools registered successfully");
}

/**
 * Main server entry point
 */
async function main() {
  // Validate required environment variables
  validateEnvironment();

  // Register all tools with the server
  registerTools();

  // Create stdio transport for MCP communication
  const transport = new StdioServerTransport();

  // Connect server to transport
  await server.connect(transport);

  // Log startup (to stderr to avoid interfering with stdio protocol)
  console.error(`${SERVER_NAME} v${SERVER_VERSION} running on stdio transport`);
  console.error("Waiting for MCP client connection...");
}

/**
 * Validate required environment variables
 */
function validateEnvironment() {
  const warnings: string[] = [];

  // Optional: Helius RPC URL (falls back to public endpoint)
  if (!process.env.HELIUS_RPC_URL) {
    warnings.push(
      "HELIUS_RPC_URL not set - using public Solana RPC (slower, rate-limited)"
    );
  }

  // Optional: S3 bucket for cached data (falls back to Galaxy API direct)
  if (!process.env.S3_BUCKET_NAME) {
    warnings.push(
      "S3_BUCKET_NAME not set - using Galaxy API directly (slower responses)"
    );
  }

  // Log warnings
  if (warnings.length > 0) {
    console.error("\n[Configuration Warnings]");
    warnings.forEach((warning) => console.error(`  - ${warning}`));
    console.error("");
  }
}

/**
 * Handle process termination gracefully
 */
process.on("SIGINT", async () => {
  console.error("\nShutting down gracefully...");
  process.exit(0);
});

process.on("SIGTERM", async () => {
  console.error("\nShutting down gracefully...");
  process.exit(0);
});

/**
 * Run the server
 */
main().catch((error) => {
  console.error("Fatal error starting server:", error);
  process.exit(1);
});
