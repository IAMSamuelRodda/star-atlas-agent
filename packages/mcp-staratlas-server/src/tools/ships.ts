/**
 * Ship-related MCP tools
 *
 * Provides tools for querying Star Atlas ship data from Galaxy API.
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  GetShipInfoInputSchema,
  SearchShipsInputSchema,
  type GetShipInfoInput,
  type SearchShipsInput,
} from "../schemas/ships.js";
import { ResponseFormat } from "../schemas/common.js";
import { galaxyApi } from "../services/galaxyApi.js";
import {
  formatShipMarkdown,
  formatShipJson,
  formatShipListMarkdown,
  formatShipListJson,
} from "../utils/formatters.js";
import { filterAndPaginate } from "../utils/pagination.js";
import { handleError, notFoundError, emptyResultsMessage } from "../utils/errors.js";
import type { Ship } from "../types.js";

/**
 * Register ship-related tools with the MCP server
 */
export function registerShipTools(server: McpServer) {
  // Tool 1: Get ship info by mint address
  server.registerTool(
    "staratlas_get_ship_info",
    {
      title: "Get Star Atlas Ship Information",
      description: `Retrieve detailed specifications for a Star Atlas ship by its NFT mint address.

This tool fetches complete ship metadata including combat stats, cargo capacity, fuel capacity, movement speeds, and special abilities. Data is sourced from the official Galaxy API with 1-hour caching.

Args:
  - mint (string): Ship NFT mint address (Solana public key, base58 encoded, 32-44 characters)
    Example: "CRAFTyM9c1zPM4r1h5Aw3jT89oS6LoLb9r3fLqJmU7Y9"
  - response_format ('markdown' | 'json'): Output format (default: 'markdown')
    - 'markdown': Human-readable format with headers and bullet points
    - 'json': Structured data for programmatic processing

Returns:
  For markdown format: Human-readable ship specifications with sections for:
    - Basic Information (name, class, tier, rarity)
    - Capacity (crew, components, modules, cargo, fuel)
    - Combat Stats (health, shield, armor)
    - Movement (warp speed, fuel burn rate)
    - Special Abilities (mining, scanning)
    - Market Information (price, supply)

  For JSON format: Structured object with schema:
  {
    "mint": string,
    "name": string,
    "symbol": string,
    "class": "xxSmall" | "xSmall" | "small" | "medium" | "large" | "capital" | "commander" | "titan",
    "tier": number (0-5),
    "rarity": "common" | "uncommon" | "rare" | "epic" | "legendary" | "anomaly",
    "capacity": { crew, components, modules, cargo_m3, fuel_tons },
    "combat": { max_health, max_shield, armor_level },
    "movement": { max_warp_speed, sub_warp_speed, fuel_burn_rate_tons_per_sec },
    "abilities": { mining_rate, scanning_power },
    "market": { price, currency, supply } | null
  }

Examples:
  - Use when: "What are the specs for Pearce X4?" -> Get mint address first, then call this tool
  - Use when: "Show me details for ship CRAFTyM9..." -> params: { mint: "CRAFTyM9..." }
  - Don't use when: Searching for ships by name (use staratlas_search_ships instead)
  - Don't use when: Comparing multiple ships (use staratlas_search_ships with filters)

Error Handling:
  - Returns "Error: Ship not found..." if mint address doesn't exist or isn't a ship
  - Returns "Error: Invalid Solana public key..." if mint format is invalid
  - Returns "Error: Galaxy API is experiencing issues..." if API unavailable`,
      inputSchema: GetShipInfoInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async (params) => {
      try {
        // Fetch ship from Galaxy API
        const ship = await galaxyApi.getShipByMint(params.mint);

        if (!ship) {
          return {
            content: [
              {
                type: "text",
                text: notFoundError("Ship", params.mint),
              },
            ],
          };
        }

        // Format response based on requested format
        const result =
          params.response_format === ResponseFormat.MARKDOWN
            ? formatShipMarkdown(ship)
            : JSON.stringify(formatShipJson(ship), null, 2);

        return {
          content: [
            {
              type: "text",
              text: result,
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: handleError(error, "staratlas_get_ship_info"),
            },
          ],
        };
      }
    }
  );

  // Tool 2: Search ships with filters
  server.registerTool(
    "staratlas_search_ships",
    {
      title: "Search Star Atlas Ships",
      description: `Search and filter Star Atlas ships by class, tier, rarity, cargo capacity, and fuel capacity.

This tool searches across all Star Atlas ships in the Galaxy API, supporting multiple filters and pagination. Use this to find ships matching specific criteria or to compare ships.

Args:
  - class (optional): Filter by ship class
    Options: "xxSmall", "xSmall", "small", "medium", "large", "capital", "commander", "titan"
    Example: "medium" for medium-class ships
  - tier (optional): Filter by tier (0-5)
    Higher tiers are more powerful. Example: 3 for tier-3 ships
  - rarity (optional): Filter by rarity
    Options: "common", "uncommon", "rare", "epic", "legendary", "anomaly"
  - min_cargo_capacity (optional): Minimum cargo in m³
    Example: 500 for ships with at least 500 m³ cargo
  - min_fuel_capacity (optional): Minimum fuel in tons
    Example: 1000 for ships with at least 1000 tons fuel
  - limit (optional): Maximum results to return (1-100, default: 20)
  - offset (optional): Number of results to skip for pagination (default: 0)
  - response_format ('markdown' | 'json'): Output format (default: 'markdown')

Returns:
  For markdown format: Human-readable list with:
    - Summary (total found, showing count)
    - Each ship: name, class, tier, rarity, cargo, fuel, mint

  For JSON format: Structured object with schema:
  {
    "total": number,              // Total matching ships
    "count": number,              // Ships in this response
    "offset": number,             // Current pagination offset
    "has_more": boolean,          // More results available
    "next_offset": number,        // Offset for next page (if has_more)
    "ships": [
      {
        "mint": string,
        "name": string,
        "class": string,
        "tier": number,
        "rarity": string,
        "cargo_capacity_m3": number,
        "fuel_capacity_tons": number
      }
    ]
  }

Examples:
  - Use when: "Find all medium-class combat ships"
    -> params: { class: "medium" }
  - Use when: "Show me tier-3 ships with at least 1000 cargo"
    -> params: { tier: 3, min_cargo_capacity: 1000 }
  - Use when: "List the first 10 capital ships"
    -> params: { class: "capital", limit: 10 }
  - Use when: "What are the best mining ships?"
    -> Search, then use staratlas_get_ship_info on results to check mining_rate
  - Don't use when: You have the exact mint address (use staratlas_get_ship_info)

Error Handling:
  - Returns "No results found..." if no ships match filters
  - Returns "Error: Invalid class..." if invalid enum value provided
  - Automatically truncates if response exceeds 25,000 characters`,
      inputSchema: SearchShipsInputSchema,
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async (params) => {
      try {
        // Fetch all ships from Galaxy API
        const allShips = await galaxyApi.fetchShips();

        // Apply filters
        const filtered = filterAndPaginate(
          allShips,
          (ship: Ship) => {
            // Class filter
            if (params.class && ship.attributes.class !== params.class) {
              return false;
            }

            // Tier filter
            if (params.tier !== undefined && ship.attributes.tier !== params.tier) {
              return false;
            }

            // Rarity filter
            if (params.rarity && ship.attributes.rarity !== params.rarity) {
              return false;
            }

            // Cargo capacity filter
            if (
              params.min_cargo_capacity !== undefined &&
              ship.attributes.cargoCapacity < params.min_cargo_capacity
            ) {
              return false;
            }

            // Fuel capacity filter
            if (
              params.min_fuel_capacity !== undefined &&
              ship.attributes.fuelCapacity < params.min_fuel_capacity
            ) {
              return false;
            }

            return true;
          },
          {
            limit: params.limit ?? 20,
            offset: params.offset ?? 0,
          }
        );

        // Check if no results
        if (filtered.total === 0) {
          const criteria = Object.entries(params)
            .filter(
              ([key, value]) =>
                value !== undefined &&
                key !== "response_format" &&
                key !== "limit" &&
                key !== "offset"
            )
            .map(([key, value]) => `${key}=${value}`)
            .join(", ");

          return {
            content: [
              {
                type: "text",
                text: emptyResultsMessage(criteria || "your search"),
              },
            ],
          };
        }

        // Format response
        const result =
          params.response_format === ResponseFormat.MARKDOWN
            ? formatShipListMarkdown(filtered.items, filtered.total)
            : JSON.stringify(
                formatShipListJson(
                  filtered.items,
                  filtered.total,
                  filtered.offset,
                  filtered.has_more
                ),
                null,
                2
              );

        // Add truncation warning if applicable
        let finalResult = result;
        if (filtered.truncated && filtered.truncation_message) {
          finalResult = `⚠️  ${filtered.truncation_message}\n\n${result}`;
        }

        return {
          content: [
            {
              type: "text",
              text: finalResult,
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: handleError(error, "staratlas_search_ships"),
            },
          ],
        };
      }
    }
  );
}
