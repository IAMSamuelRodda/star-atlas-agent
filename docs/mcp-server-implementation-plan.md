# Star Atlas MCP Server - Implementation Plan

**Date**: 2025-11-17
**Status**: Planning
**Related Issues**: #25 (Epic), #27 (Task - Foundation)
**References**: ADR-001 (Data Sourcing), MCP Best Practices, TypeScript Implementation Guide

---

## Overview

This document outlines the comprehensive implementation plan for the Star Atlas MCP server (`staratlas-mcp-server`). The server will provide tools for fleet management, market analysis, and game data queries, following MCP best practices and the hybrid data sourcing strategy defined in ADR-001.

---

## 1. Tool Selection

### Priority 1: Foundation Tools (Week 1 - MVP)

**Static Data Tools** (Galaxy API + S3 Cache):
1. **`staratlas_get_ship_info`** - Retrieve ship specifications by mint address
   - Input: `mint` (string), `response_format` (markdown|json)
   - Returns: Complete ship specs (stats, capacity, combat, fuel)
   - Use case: "What are the specs for Pearce X4?"

2. **`staratlas_search_ships`** - Search/filter ships by class, tier, rarity
   - Input: `class`, `tier`, `rarity`, `limit`, `offset`, `response_format`
   - Returns: List of matching ships with key stats
   - Use case: "Find all medium-class combat ships"

3. **`staratlas_get_resource_info`** - Get resource/commodity metadata
   - Input: `mint` (string), `response_format`
   - Returns: Resource details (type, category, unit of measure)
   - Use case: "What is Hydrogen used for?"

**Real-Time Tools** (SAGE SDK + Solana RPC):
4. **`staratlas_get_fleet_status`** - Query current fleet state
   - Input: `fleet_id` (PublicKey string), `response_format`
   - Returns: Location, fuel, cargo, health, ship composition
   - Use case: "Check my fleet's fuel level"

5. **`staratlas_get_wallet_balance`** - Query wallet token balances
   - Input: `wallet_address` (PublicKey string), `token_mints` (optional array)
   - Returns: ATLAS, POLIS, SOL, and resource token balances
   - Use case: "How much ATLAS do I have?"

### Priority 2: Market & Economic Tools (Week 2)

6. **`staratlas_get_token_price`** - Real-time token prices
   - Input: `symbols` (array: ["ATLAS", "POLIS", "SOL"]), `quote_currency` ("USD"|"USDC")
   - Source: CoinGecko API (5-min cache)
   - Returns: Current prices with 24h change
   - Use case: "What's the current ATLAS price?"

7. **`staratlas_get_marketplace_orders`** - Active marketplace listings
   - Input: `resource_mint`, `order_type` ("buy"|"sell"|"both"), `limit`
   - Source: Galaxy API markets endpoint (1-hour cache)
   - Returns: Order book with prices and quantities
   - Use case: "Find the cheapest Hydrogen for sale"

### Priority 3: Fleet Management Tools (Week 2)

8. **`staratlas_calculate_fuel_time`** - Estimate fuel duration
   - Input: `fleet_id`, `activity` ("idle"|"warp"|"mine")
   - Returns: Time until fuel depleted (hours)
   - Use case: "How long can my fleet mine before refueling?"

9. **`staratlas_find_nearest_starbase`** - Locate closest starbase
   - Input: `current_sector_coords` (x, y), `starbase_type` (optional)
   - Source: Static starbase locations (S3 cache)
   - Returns: Nearest starbases with distance and coordinates
   - Use case: "Where's the closest refueling station?"

### Priority 4: Crafting & ROI Tools (Week 3 - Deferred)

10. **`staratlas_get_crafting_recipe`** - Recipe requirements
11. **`staratlas_calculate_crafting_roi`** - Profitability analysis

---

## 2. Shared Utilities & Helpers

### 2.1 API Clients

**Galaxy API Client** (`src/services/galaxyApi.ts`):
```typescript
class GalaxyApiClient {
  async fetchAllNfts(): Promise<GalaxyNft[]>
  async fetchMarkets(resourceMint: string): Promise<MarketData>
  // Includes retry logic, timeout handling, rate limiting
}
```

**Solana RPC Client** (`src/services/solanaRpc.ts`):
```typescript
class SolanaRpcClient {
  connection: Connection // Helius RPC endpoint
  async getFleetAccount(fleetId: PublicKey): Promise<FleetAccount>
  async getWalletBalances(wallet: PublicKey, mints: string[]): Promise<TokenBalances>
  // 30s in-memory cache for deduplication
}
```

**S3 Cache Client** (`src/services/s3Cache.ts`):
```typescript
class S3CacheClient {
  async getShipsData(): Promise<Ship[]>
  async getResourcesData(): Promise<Resource[]>
  async getStarbasesData(): Promise<Starbase[]>
  // Fallback to Galaxy API if cache miss
}
```

### 2.2 Response Formatting

**Markdown Formatter** (`src/utils/formatters.ts`):
```typescript
function formatShipMarkdown(ship: Ship): string
function formatFleetMarkdown(fleet: FleetAccount, ships: Ship[]): string
function formatMarketOrdersMarkdown(orders: MarketOrder[]): string
// Human-readable with headers, lists, emojis (⛽ for fuel, 📦 for cargo)
```

**JSON Formatter** (`src/utils/formatters.ts`):
```typescript
function formatShipJson(ship: Ship): Record<string, any>
function formatFleetJson(fleet: FleetAccount): Record<string, any>
// Structured data with complete fields, consistent naming
```

### 2.3 Pagination & Truncation

**Pagination Helper** (`src/utils/pagination.ts`):
```typescript
interface PaginationParams {
  limit: number // 1-100, default 20
  offset: number // default 0
}

interface PaginatedResponse<T> {
  total: number
  count: number
  offset: number
  items: T[]
  has_more: boolean
  next_offset?: number
  truncated?: boolean
  truncation_message?: string
}

function paginate<T>(
  items: T[],
  params: PaginationParams,
  maxCharacters: number = CHARACTER_LIMIT
): PaginatedResponse<T>
```

### 2.4 Error Handling

**API Error Handler** (`src/utils/errors.ts`):
```typescript
function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    switch (error.response?.status) {
      case 404: return "Error: Resource not found. Check the ID/mint address."
      case 429: return "Error: Rate limit exceeded. Try again in 60 seconds."
      case 503: return "Error: Galaxy API unavailable. Using cached data."
      // ... more cases
    }
  }
  if (error instanceof SolanaError) {
    return `Error: Blockchain query failed. ${error.message}`
  }
  return `Error: ${error instanceof Error ? error.message : String(error)}`
}
```

---

## 3. Input/Output Design

### 3.1 Common Zod Schemas

**Response Format** (`src/schemas/common.ts`):
```typescript
enum ResponseFormat {
  MARKDOWN = "markdown",
  JSON = "json"
}

const ResponseFormatSchema = z.nativeEnum(ResponseFormat)
  .default(ResponseFormat.MARKDOWN)
  .describe("Output format: 'markdown' for human-readable or 'json' for machine-readable")
```

**Pagination** (`src/schemas/common.ts`):
```typescript
const PaginationSchema = z.object({
  limit: z.number()
    .int()
    .min(1)
    .max(100)
    .default(20)
    .describe("Maximum results to return (1-100)"),
  offset: z.number()
    .int()
    .min(0)
    .default(0)
    .describe("Number of results to skip for pagination")
}).strict()
```

**Solana PublicKey** (`src/schemas/common.ts`):
```typescript
const PublicKeySchema = z.string()
  .regex(/^[1-9A-HJ-NP-Za-km-z]{32,44}$/, "Invalid Solana public key format")
  .describe("Solana public key (base58 encoded, 32-44 characters)")
```

### 3.2 Tool-Specific Schemas

**Get Ship Info** (`src/schemas/ships.ts`):
```typescript
const GetShipInfoInputSchema = z.object({
  mint: PublicKeySchema.describe("Ship NFT mint address"),
  response_format: ResponseFormatSchema
}).strict()
```

**Search Ships** (`src/schemas/ships.ts`):
```typescript
const SearchShipsInputSchema = z.object({
  class: z.enum(["xxSmall", "xSmall", "small", "medium", "large", "capital", "commander", "titan"])
    .optional()
    .describe("Filter by ship class"),
  tier: z.number()
    .int()
    .min(0)
    .max(5)
    .optional()
    .describe("Filter by ship tier (0-5)"),
  rarity: z.enum(["common", "uncommon", "rare", "epic", "legendary", "anomaly"])
    .optional()
    .describe("Filter by rarity"),
  min_cargo_capacity: z.number()
    .min(0)
    .optional()
    .describe("Minimum cargo capacity in m³"),
  response_format: ResponseFormatSchema
}).merge(PaginationSchema).strict()
```

**Get Fleet Status** (`src/schemas/fleets.ts`):
```typescript
const GetFleetStatusInputSchema = z.object({
  fleet_id: PublicKeySchema.describe("Fleet account public key"),
  response_format: ResponseFormatSchema
}).strict()
```

### 3.3 Character Limits

**Constants** (`src/constants.ts`):
```typescript
export const CHARACTER_LIMIT = 25000 // Maximum response size
export const API_TIMEOUT = 30000 // 30 seconds
export const CACHE_TTL_SECONDS = 30 // In-memory RPC cache
export const S3_CACHE_VERSION = "v1" // Versioned snapshots
```

---

## 4. Error Handling Strategy

### 4.1 Error Categories

**Network Errors**:
- Timeout (30s): "Request timed out. Please try again."
- Connection refused: "Unable to connect to API. Check network status."
- Rate limit (429): "Rate limit exceeded. Wait 60 seconds."

**Validation Errors**:
- Invalid PublicKey: "Invalid Solana address format. Use base58 encoded string (32-44 chars)."
- Invalid enum: "Ship class must be one of: xxSmall, xSmall, small, medium, large, capital, commander, titan"
- Out of range: "Limit must be between 1 and 100"

**Data Errors**:
- Not found (404): "Resource not found. Check mint address or fleet ID."
- Empty results: "No ships match the specified filters. Try broader criteria."
- Cache miss: "Cache unavailable. Fetching from Galaxy API (slower response)."

**Blockchain Errors**:
- Account not found: "Fleet account does not exist. Verify fleet ID."
- RPC error: "Blockchain query failed. Try again or check Solana status."

### 4.2 Error Message Guidelines

All error messages must:
1. Start with "Error: " prefix
2. Explain what went wrong clearly
3. Suggest next steps when possible
4. Avoid technical jargon (use "fleet ID" not "PDA")
5. Be actionable for the LLM agent

---

## 5. Implementation Phases

### Phase 1: Foundation (Task #27 - Week 1, Days 1-2)

**Objectives**:
- Set up TypeScript MCP server package
- Configure build/test infrastructure
- Implement basic stdio transport
- Create project structure

**Deliverables**:
- `packages/mcp-staratlas-server/` package initialized
- `package.json`, `tsconfig.json` configured
- `src/index.ts` with McpServer initialization
- `npm run build` succeeds, produces `dist/index.js`
- Server runs: `node dist/index.js` (stdio transport)

**Files Created**:
```
packages/mcp-staratlas-server/
├── package.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts          # Main entry point
│   ├── constants.ts      # Shared constants
│   └── schemas/
│       └── common.ts     # ResponseFormat, Pagination, PublicKey schemas
└── dist/                 # Built output
```

**Dependencies**:
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.6.1",
    "@solana/web3.js": "^1.95.8",
    "@staratlas/sage": "^1.8.10",
    "@staratlas/data-source": "latest",
    "axios": "^1.7.9",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.10.0",
    "tsx": "^4.19.2",
    "typescript": "^5.7.2"
  }
}
```

### Phase 2: Static Data Tools (Task #28 - Week 1, Days 3-4)

**Objectives**:
- Implement Galaxy API client
- Implement S3 cache client (fallback to API if no S3)
- Create ship/resource data tools
- Add markdown/JSON formatters

**Tools Implemented**:
1. `staratlas_get_ship_info`
2. `staratlas_search_ships`
3. `staratlas_get_resource_info`

**Files Created**:
```
src/
├── services/
│   ├── galaxyApi.ts      # Galaxy API client
│   └── s3Cache.ts        # S3 cache client (optional fallback)
├── tools/
│   └── ships.ts          # Ship-related tools
├── schemas/
│   ├── ships.ts          # Ship schemas
│   └── resources.ts      # Resource schemas
├── utils/
│   ├── formatters.ts     # Markdown/JSON formatters
│   ├── pagination.ts     # Pagination helper
│   └── errors.ts         # Error handling
└── types.ts              # TypeScript interfaces (Ship, Resource, etc.)
```

### Phase 3: Real-Time Tools (Task #29 - Week 1, Day 5 + Week 2, Days 1-2)

**Objectives**:
- Implement Solana RPC client (Helius)
- Integrate SAGE SDK for fleet queries
- Add in-memory caching (30s TTL)
- Implement wallet balance queries

**Tools Implemented**:
4. `staratlas_get_fleet_status`
5. `staratlas_get_wallet_balance`

**Files Created**:
```
src/
├── services/
│   └── solanaRpc.ts      # Solana RPC + SAGE SDK client
├── tools/
│   ├── fleets.ts         # Fleet tools
│   └── wallets.ts        # Wallet tools
└── schemas/
    ├── fleets.ts         # Fleet schemas
    └── wallets.ts        # Wallet schemas
```

**Environment Variables Required**:
```bash
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
SOLANA_NETWORK=mainnet-beta
```

### Phase 4: Market & Economic Tools (Week 2, Days 3-5)

**Objectives**:
- Implement CoinGecko API client
- Add marketplace query tools
- Implement fuel time calculator

**Tools Implemented**:
6. `staratlas_get_token_price`
7. `staratlas_get_marketplace_orders`
8. `staratlas_calculate_fuel_time`
9. `staratlas_find_nearest_starbase`

**Files Created**:
```
src/
├── services/
│   └── coinGecko.ts      # CoinGecko API client
├── tools/
│   ├── markets.ts        # Market tools
│   └── navigation.ts     # Navigation/fleet management
└── schemas/
    ├── markets.ts        # Market schemas
    └── navigation.ts     # Navigation schemas
```

---

## 6. Testing Strategy

### 6.1 Manual Testing

**Ship Tools**:
```bash
# Get ship info
echo '{"mint":"<PearceX4_mint>","response_format":"markdown"}' | \
  node dist/index.js staratlas_get_ship_info

# Search ships
echo '{"class":"medium","tier":3,"limit":5}' | \
  node dist/index.js staratlas_search_ships
```

**Fleet Tools** (requires real fleet ID):
```bash
# Get fleet status
echo '{"fleet_id":"<your_fleet_pubkey>","response_format":"json"}' | \
  node dist/index.js staratlas_get_fleet_status
```

### 6.2 Evaluation Questions (Phase 4 - Week 3)

Following MCP best practices, create 10 complex evaluation questions:

1. "Find all medium-class ships with cargo capacity over 500 m³ and recommend the best one for mining operations based on fuel efficiency."

2. "Check my fleet at `<fleet_id>`. How much fuel do I have? Based on current fuel burn rate, how many hours can I mine asteroids before needing to refuel?"

3. "What's the current market price for Hydrogen on the marketplace? Compare it to the MSRP. Is it a good time to buy?"

4. "I have 10,000 ATLAS tokens. How many Pearce X4 ships can I buy at current market prices?"

5. "Find the nearest starbase to sector coordinates (50, -30). What resources are available there?"

*(... 5 more complex questions)*

---

## 7. Success Criteria

### Phase 1 (Foundation)
- [ ] Package builds successfully (`npm run build`)
- [ ] Server runs without errors (`node dist/index.js`)
- [ ] Stdio transport accepts connections
- [ ] Common schemas defined (ResponseFormat, Pagination, PublicKey)

### Phase 2 (Static Data)
- [ ] Galaxy API client fetches ships/resources
- [ ] S3 cache client works (or graceful fallback to API)
- [ ] 3 ship/resource tools registered and functional
- [ ] Markdown and JSON formatters produce correct output
- [ ] Pagination works correctly with truncation

### Phase 3 (Real-Time Data)
- [ ] Solana RPC connection established (Helius)
- [ ] SAGE SDK integrated, fleet queries work
- [ ] In-memory cache prevents duplicate RPC calls (30s TTL)
- [ ] 2 real-time tools registered and functional
- [ ] Error handling graceful (404, timeout, invalid address)

### Phase 4 (Market Tools)
- [ ] 4 additional tools implemented
- [ ] All 9 tools functional and tested manually
- [ ] Character limit enforcement working (<25K chars)
- [ ] Evaluation questions created (10 complex questions)

---

## 8. Future Enhancements (Deferred)

### Crafting Tools (Week 3+)
- `staratlas_get_crafting_recipe`
- `staratlas_calculate_crafting_roi`
- Requires crafting SDK integration (documentation incomplete as of 2025-11-12)

### Transaction Tools (Week 4+)
- `staratlas_prepare_transaction` - Prepare unsigned transactions
- `staratlas_get_transaction_history` - Query past transactions
- Requires wallet integration and transaction signing

### Advanced Navigation (Week 4+)
- `staratlas_calculate_warp_time` - Estimate travel duration
- `staratlas_optimize_route` - Multi-stop routing optimization

---

## 9. Notes & Risks

### Known Risks

1. **Crafting SDK Documentation Incomplete**
   - **Mitigation**: Defer crafting tools to Phase 5, prioritize Galaxy API + SAGE SDK tools first

2. **S3 Cache Not Available in Local Development**
   - **Mitigation**: Graceful fallback to Galaxy API direct calls (slower but functional)

3. **Helius RPC Rate Limits**
   - **Mitigation**: 30s in-memory cache, request deduplication, monitor usage

4. **Galaxy API Schema Changes**
   - **Mitigation**: Version S3 snapshots (`v1`, `v2`), add schema validation

### Development Notes

- **Naming**: All tools prefixed with `staratlas_` to avoid conflicts
- **Annotations**: Use `readOnlyHint: true` for all query tools (no mutations yet)
- **Documentation**: Comprehensive descriptions with examples in every tool
- **Type Safety**: Strict TypeScript, no `any` types, Zod validation everywhere

---

## 10. References

- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Star Atlas Build Portal](https://build.staratlas.com/)
- [Galaxy API](https://galaxy.staratlas.com/nfts)
- [SAGE SDK](https://www.npmjs.com/package/@staratlas/sage)
- [ADR-001: Data Sourcing Strategy](./adr/001-star-atlas-data-sourcing.md)
- [Star Atlas Data Inventory](./star-atlas-data-inventory.md)
- Issue #25: MCP Server Epic
- Issue #27: MCP Server Bootstrap

---

**Next Step**: Implement Phase 1 (Foundation) - Create package structure, configure TypeScript, set up stdio transport
