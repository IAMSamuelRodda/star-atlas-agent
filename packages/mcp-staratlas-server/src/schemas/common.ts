/**
 * Common Zod schemas used across multiple tools
 */

import { z } from "zod";
import { DEFAULT_PAGINATION_LIMIT, MAX_PAGINATION_LIMIT } from "../constants.js";

/**
 * Response format enum - determines output structure
 */
export enum ResponseFormat {
  MARKDOWN = "markdown",
  JSON = "json",
}

/**
 * Response format schema with markdown as default
 */
export const ResponseFormatSchema = z
  .nativeEnum(ResponseFormat)
  .default(ResponseFormat.MARKDOWN)
  .describe(
    "Output format: 'markdown' for human-readable or 'json' for machine-readable"
  );

/**
 * Pagination parameters schema
 */
export const PaginationSchema = z.object({
  limit: z
    .number()
    .int()
    .min(1)
    .max(MAX_PAGINATION_LIMIT)
    .default(DEFAULT_PAGINATION_LIMIT)
    .describe(`Maximum results to return (1-${MAX_PAGINATION_LIMIT})`),
  offset: z
    .number()
    .int()
    .min(0)
    .default(0)
    .describe("Number of results to skip for pagination"),
});

/**
 * Type inference for pagination parameters
 */
export type PaginationParams = z.infer<typeof PaginationSchema>;

/**
 * Solana PublicKey validation schema
 * Validates base58-encoded public keys (32-44 characters)
 */
export const PublicKeySchema = z
  .string()
  .regex(
    /^[1-9A-HJ-NP-Za-km-z]{32,44}$/,
    "Invalid Solana public key format (expected base58 encoded, 32-44 characters)"
  )
  .describe("Solana public key in base58 format");

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  total: number;
  count: number;
  offset: number;
  items: T[];
  has_more: boolean;
  next_offset?: number;
  truncated?: boolean;
  truncation_message?: string;
}
