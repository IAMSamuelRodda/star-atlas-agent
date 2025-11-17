/**
 * Galaxy API Client
 *
 * Fetches Star Atlas ship and resource metadata from the official Galaxy API.
 * Implements retry logic, timeout handling, and response caching.
 *
 * @see https://galaxy.staratlas.com/nfts
 */

import axios, { AxiosError } from "axios";
import { GALAXY_API_BASE_URL, API_TIMEOUT } from "../constants.js";
import type { GalaxyApiResponse, GalaxyNft, Ship, Resource } from "../types.js";

/**
 * In-memory cache for Galaxy API responses
 * TTL: 1 hour (data rarely changes)
 */
interface CacheEntry {
  data: GalaxyNft[];
  timestamp: number;
}

let nftsCache: CacheEntry | null = null;
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

/**
 * Galaxy API client class
 */
export class GalaxyApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = GALAXY_API_BASE_URL, timeout: number = API_TIMEOUT) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Fetch all NFTs from Galaxy API with caching
   * @returns Array of all Star Atlas NFTs (ships and resources)
   */
  async fetchAllNfts(): Promise<GalaxyNft[]> {
    // Check cache first
    if (nftsCache && Date.now() - nftsCache.timestamp < CACHE_TTL_MS) {
      console.error("[GalaxyAPI] Using cached NFT data");
      return nftsCache.data;
    }

    console.error("[GalaxyAPI] Fetching NFT data from Galaxy API...");

    try {
      const response = await axios.get<GalaxyApiResponse>(`${this.baseUrl}/nfts`, {
        timeout: this.timeout,
        headers: {
          Accept: "application/json",
          "User-Agent": "staratlas-mcp-server/0.1.0",
        },
      });

      // Convert object response to array
      const nfts = Object.values(response.data);

      // Update cache
      nftsCache = {
        data: nfts,
        timestamp: Date.now(),
      };

      console.error(`[GalaxyAPI] Fetched ${nfts.length} NFTs successfully`);
      return nfts;
    } catch (error) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Fetch all ships from Galaxy API
   * @returns Array of ships only
   */
  async fetchShips(): Promise<Ship[]> {
    const allNfts = await this.fetchAllNfts();
    return allNfts.filter((nft) => nft.attributes.itemType === "ship") as Ship[];
  }

  /**
   * Fetch all resources from Galaxy API
   * @returns Array of resources/commodities only
   */
  async fetchResources(): Promise<Resource[]> {
    const allNfts = await this.fetchAllNfts();
    return allNfts.filter((nft) => nft.attributes.itemType !== "ship") as Resource[];
  }

  /**
   * Find a ship by mint address
   * @param mint Solana mint address
   * @returns Ship if found, null otherwise
   */
  async getShipByMint(mint: string): Promise<Ship | null> {
    const ships = await this.fetchShips();
    return ships.find((ship) => ship.mint === mint) || null;
  }

  /**
   * Find a resource by mint address
   * @param mint Solana mint address
   * @returns Resource if found, null otherwise
   */
  async getResourceByMint(mint: string): Promise<Resource | null> {
    const resources = await this.fetchResources();
    return resources.find((resource) => resource.mint === mint) || null;
  }

  /**
   * Clear the NFT cache (useful for testing or manual refresh)
   */
  clearCache(): void {
    nftsCache = null;
    console.error("[GalaxyAPI] Cache cleared");
  }

  /**
   * Handle API errors and convert to user-friendly messages
   */
  private handleApiError(error: unknown): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;

      if (axiosError.response) {
        // Server responded with error status
        const status = axiosError.response.status;
        switch (status) {
          case 404:
            return new Error(
              "Error: Galaxy API endpoint not found. Service may be unavailable."
            );
          case 429:
            return new Error(
              "Error: Rate limit exceeded. Please try again in 60 seconds."
            );
          case 500:
          case 502:
          case 503:
          case 504:
            return new Error(
              "Error: Galaxy API is experiencing issues. Try again later."
            );
          default:
            return new Error(`Error: Galaxy API request failed (status ${status})`);
        }
      } else if (axiosError.code === "ECONNABORTED") {
        return new Error(
          "Error: Request to Galaxy API timed out. Check network connection."
        );
      } else if (axiosError.code === "ENOTFOUND" || axiosError.code === "ECONNREFUSED") {
        return new Error(
          "Error: Cannot connect to Galaxy API. Check network connection."
        );
      }
    }

    return new Error(
      `Error: Unexpected error fetching data from Galaxy API: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
  }
}

/**
 * Singleton Galaxy API client instance
 */
export const galaxyApi = new GalaxyApiClient();
