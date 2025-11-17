/**
 * Shared constants for the Star Atlas MCP Server
 */

// Response size limits
export const CHARACTER_LIMIT = 25000; // Maximum response size in characters
export const MAX_PAGINATION_LIMIT = 100; // Maximum items per page
export const DEFAULT_PAGINATION_LIMIT = 20; // Default items per page

// API configuration
export const API_TIMEOUT = 30000; // 30 seconds timeout for API requests
export const GALAXY_API_BASE_URL = "https://galaxy.staratlas.com";

// Cache configuration
export const CACHE_TTL_SECONDS = 30; // In-memory cache TTL for RPC deduplication
export const S3_CACHE_VERSION = "v1"; // Version for S3 cached snapshots

// Solana configuration
export const SOLANA_NETWORK = process.env.SOLANA_NETWORK || "mainnet-beta";
export const HELIUS_RPC_URL =
  process.env.HELIUS_RPC_URL || "https://api.mainnet-beta.solana.com";

// Token configuration
export const TOKEN_MINTS = {
  ATLAS: "ATLASXmbPQxBUYbxPsV97usA3fPQYEqzQBUHgiFCUsXx",
  POLIS: "poLisWXnNRwC6oBu1vHiuKQzFjGL4XDSu4g9qjz9qVk",
  USDC: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
} as const;

// Server metadata
export const SERVER_NAME = "staratlas-mcp-server";
export const SERVER_VERSION = "0.1.0";
