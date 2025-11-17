/**
 * Response formatters for Star Atlas data
 *
 * Provides both Markdown (human-readable) and JSON (machine-readable) formatting
 * for ships, resources, fleets, and other data types.
 */

import type { Ship, Resource } from "../types.js";

/**
 * Format ship data as human-readable Markdown
 */
export function formatShipMarkdown(ship: Ship): string {
  const lines: string[] = [];

  // Header
  lines.push(`# ${ship.name} (${ship.symbol})`);
  lines.push("");

  // Description
  if (ship.description) {
    lines.push(ship.description);
    lines.push("");
  }

  // Basic info
  lines.push("## Basic Information");
  lines.push(`- **Mint Address**: \`${ship.mint}\``);
  lines.push(`- **Class**: ${ship.attributes.class}`);
  lines.push(`- **Tier**: ${ship.attributes.tier}`);
  lines.push(`- **Rarity**: ${ship.attributes.rarity}`);
  lines.push("");

  // Capacity
  lines.push("## Capacity");
  if (ship.attributes.crewSlots !== undefined) {
    lines.push(`- **Crew Slots**: ${ship.attributes.crewSlots}`);
  }
  if (ship.attributes.componentSlots !== undefined) {
    lines.push(`- **Component Slots**: ${ship.attributes.componentSlots}`);
  }
  if (ship.attributes.moduleSlots !== undefined) {
    lines.push(`- **Module Slots**: ${ship.attributes.moduleSlots}`);
  }
  lines.push(`- **Cargo Capacity**: ${ship.attributes.cargoCapacity} m³`);
  lines.push(`- **Fuel Capacity**: ${ship.attributes.fuelCapacity} tons`);
  lines.push("");

  // Combat stats (if available)
  if (
    ship.attributes.maxHealth ||
    ship.attributes.maxShield ||
    ship.attributes.armorLevel
  ) {
    lines.push("## Combat Stats");
    if (ship.attributes.maxHealth !== undefined) {
      lines.push(`- **Max Health**: ${ship.attributes.maxHealth}`);
    }
    if (ship.attributes.maxShield !== undefined) {
      lines.push(`- **Max Shield**: ${ship.attributes.maxShield}`);
    }
    if (ship.attributes.armorLevel !== undefined) {
      lines.push(`- **Armor Level**: ${ship.attributes.armorLevel}`);
    }
    lines.push("");
  }

  // Movement stats
  if (ship.attributes.maxWarpSpeed || ship.attributes.subWarpSpeed) {
    lines.push("## Movement");
    if (ship.attributes.maxWarpSpeed !== undefined) {
      lines.push(`- **Max Warp Speed**: ${ship.attributes.maxWarpSpeed}`);
    }
    if (ship.attributes.subWarpSpeed !== undefined) {
      lines.push(`- **Sub-Warp Speed**: ${ship.attributes.subWarpSpeed}`);
    }
    if (ship.attributes.fuelBurnRate !== undefined) {
      lines.push(`- **Fuel Burn Rate**: ${ship.attributes.fuelBurnRate} tons/sec`);
    }
    if (ship.attributes.planetExitFuelAmount !== undefined) {
      lines.push(
        `- **Planet Exit Fuel**: ${ship.attributes.planetExitFuelAmount} tons`
      );
    }
    lines.push("");
  }

  // Special abilities (mining/scanning)
  if (ship.attributes.miningRate || ship.attributes.scanningPowerLevel) {
    lines.push("## Special Abilities");
    if (ship.attributes.miningRate !== undefined) {
      lines.push(`- **Mining Rate**: ${ship.attributes.miningRate}`);
    }
    if (ship.attributes.scanningPowerLevel !== undefined) {
      lines.push(`- **Scanning Power**: ${ship.attributes.scanningPowerLevel}`);
    }
    lines.push("");
  }

  // Market info (if available)
  if (ship.primarySales && ship.primarySales.length > 0) {
    const sale = ship.primarySales[0];
    lines.push("## Market Information");
    lines.push(`- **Price**: ${sale.price} ${sale.currencySymbol}`);
    lines.push(`- **Supply**: ${sale.supply}`);
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Format ship data as structured JSON
 */
export function formatShipJson(ship: Ship): Record<string, any> {
  return {
    mint: ship.mint,
    name: ship.name,
    symbol: ship.symbol,
    description: ship.description,
    class: ship.attributes.class,
    tier: ship.attributes.tier,
    rarity: ship.attributes.rarity,
    capacity: {
      crew: ship.attributes.crewSlots,
      components: ship.attributes.componentSlots,
      modules: ship.attributes.moduleSlots,
      cargo_m3: ship.attributes.cargoCapacity,
      fuel_tons: ship.attributes.fuelCapacity,
    },
    combat: {
      max_health: ship.attributes.maxHealth,
      max_shield: ship.attributes.maxShield,
      armor_level: ship.attributes.armorLevel,
    },
    movement: {
      max_warp_speed: ship.attributes.maxWarpSpeed,
      sub_warp_speed: ship.attributes.subWarpSpeed,
      fuel_burn_rate_tons_per_sec: ship.attributes.fuelBurnRate,
      planet_exit_fuel_tons: ship.attributes.planetExitFuelAmount,
    },
    abilities: {
      mining_rate: ship.attributes.miningRate,
      scanning_power: ship.attributes.scanningPowerLevel,
    },
    market:
      ship.primarySales && ship.primarySales.length > 0
        ? {
            price: ship.primarySales[0].price,
            currency: ship.primarySales[0].currencySymbol,
            supply: ship.primarySales[0].supply,
          }
        : null,
    image_url: ship.image,
  };
}

/**
 * Format resource data as human-readable Markdown
 */
export function formatResourceMarkdown(resource: Resource): string {
  const lines: string[] = [];

  // Header
  lines.push(`# ${resource.name} (${resource.symbol})`);
  lines.push("");

  // Basic info
  lines.push("## Basic Information");
  lines.push(`- **Mint Address**: \`${resource.mint}\``);
  lines.push(`- **Item Type**: ${resource.attributes.itemType}`);
  if (resource.attributes.category) {
    lines.push(`- **Category**: ${resource.attributes.category}`);
  }
  lines.push("");

  // Physical properties
  if (
    resource.attributes.unitOfMeasure ||
    resource.attributes.mass ||
    resource.attributes.volume
  ) {
    lines.push("## Physical Properties");
    if (resource.attributes.unitOfMeasure) {
      lines.push(`- **Unit of Measure**: ${resource.attributes.unitOfMeasure}`);
    }
    if (resource.attributes.mass !== undefined) {
      lines.push(`- **Mass**: ${resource.attributes.mass} kg`);
    }
    if (resource.attributes.volume !== undefined) {
      lines.push(`- **Volume**: ${resource.attributes.volume} m³`);
    }
    lines.push("");
  }

  // Market info
  if (resource.tradeSettings) {
    lines.push("## Market Information");
    if (resource.tradeSettings.msrp !== undefined) {
      lines.push(`- **MSRP**: ${resource.tradeSettings.msrp}`);
    }
    if (resource.tradeSettings.vwap !== undefined) {
      lines.push(`- **VWAP**: ${resource.tradeSettings.vwap}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Format resource data as structured JSON
 */
export function formatResourceJson(resource: Resource): Record<string, any> {
  return {
    mint: resource.mint,
    name: resource.name,
    symbol: resource.symbol,
    item_type: resource.attributes.itemType,
    category: resource.attributes.category,
    physical_properties: {
      unit_of_measure: resource.attributes.unitOfMeasure,
      mass_kg: resource.attributes.mass,
      volume_m3: resource.attributes.volume,
    },
    market: resource.tradeSettings
      ? {
          msrp: resource.tradeSettings.msrp,
          vwap: resource.tradeSettings.vwap,
        }
      : null,
    image_url: resource.image,
  };
}

/**
 * Format a list of ships as Markdown with summary stats
 */
export function formatShipListMarkdown(ships: Ship[], total: number): string {
  const lines: string[] = [];

  lines.push(`# Ship Search Results`);
  lines.push("");
  lines.push(`Found ${total} ships (showing ${ships.length})`);
  lines.push("");

  for (const ship of ships) {
    lines.push(`## ${ship.name}`);
    lines.push(`- **Class**: ${ship.attributes.class}`);
    lines.push(`- **Tier**: ${ship.attributes.tier}`);
    lines.push(`- **Rarity**: ${ship.attributes.rarity}`);
    lines.push(
      `- **Cargo**: ${ship.attributes.cargoCapacity} m³ | **Fuel**: ${ship.attributes.fuelCapacity} tons`
    );
    lines.push(`- **Mint**: \`${ship.mint}\``);
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Format a list of ships as structured JSON array
 */
export function formatShipListJson(
  ships: Ship[],
  total: number,
  offset: number,
  hasMore: boolean
): Record<string, any> {
  return {
    total,
    count: ships.length,
    offset,
    has_more: hasMore,
    next_offset: hasMore ? offset + ships.length : undefined,
    ships: ships.map((ship) => ({
      mint: ship.mint,
      name: ship.name,
      class: ship.attributes.class,
      tier: ship.attributes.tier,
      rarity: ship.attributes.rarity,
      cargo_capacity_m3: ship.attributes.cargoCapacity,
      fuel_capacity_tons: ship.attributes.fuelCapacity,
    })),
  };
}
