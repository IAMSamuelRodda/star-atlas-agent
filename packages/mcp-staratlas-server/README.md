# Star Atlas MCP Server

MCP (Model Context Protocol) server for Star Atlas game data and fleet management.

## Overview

This server provides AI agents with access to Star Atlas game data, fleet management tools, market analysis, and Solana blockchain queries through the Model Context Protocol.

### Features

- **Fleet Management**: Query fleet status, fuel levels, cargo, and ship composition
- **Market Data**: Real-time token prices, marketplace orders, and crafting ROI analysis
- **Ship & Resource Data**: Complete Star Atlas item metadata with specs and attributes
- **Wallet Queries**: Token balances and transaction history
- **Optimized for Context**: Response filtering, pagination, and dual-response patterns

### Architecture

**Hybrid Data Sourcing Strategy** (see `docs/adr/001-star-atlas-data-sourcing.md`):
- **Static Data**: Galaxy API + S3 cache (ship specs, resources, recipes) - Updated weekly
- **Real-Time Data**: Solana RPC via SAGE SDK (fleet status, wallet balances) - On-demand queries
- **Cost Optimized**: 91% reduction from full real-time approach ($45/month → $4/month)

## Installation

```bash
# Install dependencies
pnpm install

# Build the server
pnpm build

# Run the server
pnpm start
```

## Development

```bash
# Watch mode with auto-reload
pnpm dev

# Type checking
pnpm typecheck

# Linting
pnpm lint
```

## Configuration

### Environment Variables

**Optional** (graceful fallback to public endpoints):

```bash
# Helius RPC for faster Solana queries (recommended for production)
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY

# S3 bucket for cached static data (recommended for production)
S3_BUCKET_NAME=staratlas-static-data-prod
AWS_REGION=us-west-2

# Solana network (defaults to mainnet-beta)
SOLANA_NETWORK=mainnet-beta
```

## Tools

### Phase 1: Foundation (Current)

**Static Data Tools**:
- `staratlas_get_ship_info` - Retrieve ship specifications by mint address
- `staratlas_search_ships` - Search/filter ships by class, tier, rarity
- `staratlas_get_resource_info` - Get resource/commodity metadata

**Real-Time Tools**:
- `staratlas_get_fleet_status` - Query current fleet state
- `staratlas_get_wallet_balance` - Query wallet token balances

### Phase 2: Market & Economic Tools (Upcoming)

- `staratlas_get_token_price` - Real-time ATLAS/POLIS/SOL prices
- `staratlas_get_marketplace_orders` - Active marketplace listings
- `staratlas_calculate_fuel_time` - Estimate fuel duration
- `staratlas_find_nearest_starbase` - Locate closest starbase

### Phase 3: Crafting Tools (Future)

- `staratlas_get_crafting_recipe` - Recipe requirements
- `staratlas_calculate_crafting_roi` - Profitability analysis

## Documentation

- **Implementation Plan**: `docs/mcp-server-implementation-plan.md`
- **Data Sourcing ADR**: `docs/adr/001-star-atlas-data-sourcing.md`
- **Data Inventory**: `docs/star-atlas-data-inventory.md`
- **MCP Protocol**: https://modelcontextprotocol.io

## References

- [Star Atlas Build Portal](https://build.staratlas.com/)
- [Galaxy API](https://galaxy.staratlas.com/nfts)
- [SAGE SDK](https://www.npmjs.com/package/@staratlas/sage)
- [Model Context Protocol](https://modelcontextprotocol.io)

## License

MIT
