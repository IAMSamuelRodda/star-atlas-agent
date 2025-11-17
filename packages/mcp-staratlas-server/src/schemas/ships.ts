/**
 * Zod schemas for ship-related tools
 */

import { z } from "zod";
import { PublicKeySchema, ResponseFormatSchema, PaginationSchema } from "./common.js";

/**
 * Ship class enum for filtering
 */
export const ShipClassSchema = z.enum([
  "xxSmall",
  "xSmall",
  "small",
  "medium",
  "large",
  "capital",
  "commander",
  "titan",
]);

/**
 * Rarity enum for filtering
 */
export const RaritySchema = z.enum([
  "common",
  "uncommon",
  "rare",
  "epic",
  "legendary",
  "anomaly",
]);

/**
 * Input schema for staratlas_get_ship_info tool
 */
export const GetShipInfoInputSchema = z
  .object({
    mint: PublicKeySchema.describe(
      "Ship NFT mint address (Solana public key). Example: 'CRAFTyM9c1zPM4r1h5Aw3jT89oS6LoLb9r3fLqJmU7Y9'"
    ),
    response_format: ResponseFormatSchema,
  })
  .strict();

export type GetShipInfoInput = z.infer<typeof GetShipInfoInputSchema>;

/**
 * Input schema for staratlas_search_ships tool
 */
export const SearchShipsInputSchema = z
  .object({
    class: ShipClassSchema.optional().describe(
      "Filter by ship class. Options: xxSmall, xSmall, small, medium, large, capital, commander, titan"
    ),
    tier: z
      .number()
      .int()
      .min(0)
      .max(5)
      .optional()
      .describe("Filter by ship tier (0-5). Higher tiers are more powerful."),
    rarity: RaritySchema.optional().describe(
      "Filter by rarity. Options: common, uncommon, rare, epic, legendary, anomaly"
    ),
    min_cargo_capacity: z
      .number()
      .min(0)
      .optional()
      .describe("Minimum cargo capacity in m³. Example: 500 for ships with at least 500 m³ cargo."),
    min_fuel_capacity: z
      .number()
      .min(0)
      .optional()
      .describe("Minimum fuel capacity in tons. Example: 1000 for ships with at least 1000 tons fuel."),
    response_format: ResponseFormatSchema,
  })
  .merge(PaginationSchema)
  .strict();

export type SearchShipsInput = z.infer<typeof SearchShipsInputSchema>;
