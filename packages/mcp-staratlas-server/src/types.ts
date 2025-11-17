/**
 * TypeScript type definitions for Star Atlas data structures
 * Based on Galaxy API responses and SAGE SDK types
 */

/**
 * Ship class types in Star Atlas
 */
export type ShipClass =
  | "xxSmall"
  | "xSmall"
  | "small"
  | "medium"
  | "large"
  | "capital"
  | "commander"
  | "titan";

/**
 * Rarity levels for Star Atlas items
 */
export type Rarity =
  | "common"
  | "uncommon"
  | "rare"
  | "epic"
  | "legendary"
  | "anomaly";

/**
 * Item types from Galaxy API
 */
export type ItemType =
  | "ship"
  | "resource"
  | "food"
  | "fuel"
  | "ammunition"
  | "component"
  | "collectible";

/**
 * Ship attributes from Galaxy API
 */
export interface ShipAttributes {
  class: ShipClass;
  itemType: "ship";
  tier: number;
  rarity: Rarity;

  // Capacity slots
  crewSlots?: number;
  componentSlots?: number;
  moduleSlots?: number;

  // Combat stats
  maxHealth?: number;
  maxShield?: number;
  armorLevel?: number;

  // Cargo & fuel
  cargoCapacity: number;
  fuelCapacity: number;
  fuelBurnRate?: number;

  // Movement
  maxWarpSpeed?: number;
  subWarpSpeed?: number;
  planetExitFuelAmount?: number;

  // Mining/Scanning
  miningRate?: number;
  scanningPowerLevel?: number;
}

/**
 * Resource/commodity attributes from Galaxy API
 */
export interface ResourceAttributes {
  itemType: ItemType;
  category?: string;
  unitOfMeasure?: "kg" | "m³" | "unit";
  mass?: number;
  volume?: number;
}

/**
 * Market data for an item
 */
export interface Market {
  id: string;
  quotePair: "ATLAS" | "USDC";
  _id: string;
}

/**
 * Primary sales data
 */
export interface PrimarySales {
  listTimestamp: number;
  supply: number;
  price: number;
  currencySymbol: "ATLAS" | "USDC";
}

/**
 * Media assets for an item
 */
export interface Media {
  thumbnailUrl?: string;
  qrInstagramUrl?: string;
  qrFacebookUrl?: string;
  sketchfabUrl?: string;
  audioUrl?: string;
}

/**
 * Ship NFT from Galaxy API
 */
export interface Ship {
  _id: string;
  name: string;
  symbol: string;
  description: string;
  mint: string;
  network: "mainnet-beta";
  attributes: ShipAttributes;
  markets?: Market[];
  primarySales?: PrimarySales[];
  image?: string;
  media?: Media;
}

/**
 * Resource/commodity NFT from Galaxy API
 */
export interface Resource {
  _id: string;
  name: string;
  symbol: string;
  mint: string;
  network: "mainnet-beta";
  attributes: ResourceAttributes;
  markets?: Market[];
  tradeSettings?: {
    msrp?: number;
    vwap?: number;
  };
  image?: string;
}

/**
 * Generic NFT response from Galaxy API (union of Ship and Resource)
 */
export type GalaxyNft = Ship | Resource;

/**
 * Response from Galaxy API /nfts endpoint
 */
export interface GalaxyApiResponse {
  [key: string]: GalaxyNft;
}
