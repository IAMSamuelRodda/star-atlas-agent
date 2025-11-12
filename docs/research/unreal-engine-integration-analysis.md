# Star Atlas Unreal Engine Integration & Current State Analysis

**Date**: 2025-11-13
**Status**: Complete
**Purpose**: Deep analysis of Star Atlas's current technical implementation, game features, and player experience

---

## Executive Summary

**Critical Discovery**: Star Atlas already has a **SAGE AI assistant** in testing (Holosim) that provides gameplay guidance and answers lore questions. Our agent MUST differentiate by focusing on **autonomous fleet management, economic optimization, and voice-first UX**, NOT general Q&A.

**Key Insight**: SAGE Labs generates **~1,590 transactions per player per day** due to fully on-chain gameplay. This creates massive transaction friction that **zProfile (z.ink) is designed to solve**. Our agent's value proposition directly addresses this pain point.

---

## Table of Contents

1. [Unreal Engine Integration (F-Kit)](#unreal-engine-integration-f-kit)
2. [Current SAGE Labs Features](#current-sage-labs-features)
3. [Blockchain Integration Architecture](#blockchain-integration-architecture)
4. [Existing SAGE AI Assistant](#existing-sage-ai-assistant)
5. [Critical Player Pain Points](#critical-player-pain-points)
6. [Implications for Star Atlas Agent Design](#implications-for-star-atlas-agent-design)

---

## 1. Unreal Engine Integration (F-Kit)

### Overview

**F-Kit** (Foundation Kit) is Star Atlas's **free, open-source Unreal Engine plugin** that bridges UE4/UE5 with Solana blockchain.

**Repository**: https://github.com/staratlasmeta/FoundationKit
**License**: Apache-2.0
**Contributors**: Riccardo Torrisi, Jon Sawler
**Code**: 55.2% C, 44.4% C++

### Architecture: Two-Layer Design

```
┌─────────────────────────────────────────────────┐
│         Unreal Engine 5 Game Client             │
├─────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────┐ │
│  │ Wallet & Blueprint│  │  Core SDK Layer     │ │
│  │ Interface Layer   │  │                     │ │
│  ├──────────────────┤  ├─────────────────────┤ │
│  │ - Multi-account  │  │ - Mnemonic/keypair  │ │
│  │   management     │  │   generation        │ │
│  │ - Local encrypted│  │ - Private key import│ │
│  │   keypair storage│  │ - Account queries   │ │
│  │ - Blueprint/C++  │  │ - Transaction       │ │
│  │   UI builders    │  │   creation/signing  │ │
│  │ - SPL token/NFT  │  │ - On-chain program  │ │
│  │   visualization  │  │   interaction       │ │
│  └──────────────────┘  └─────────────────────┘ │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│          Solana Blockchain (RPC)                │
│  - On-chain programs (SAGE, Cargo, Crafting)   │
│  - SPL tokens (ATLAS, resources)                │
│  - NFTs (ships, items)                          │
└─────────────────────────────────────────────────┘
```

### Core Capabilities

**1. Wallet Management**
- In-engine private key generation (no external tools required)
- Mnemonic phrase generation for recovery
- Import existing private keys
- Local encrypted storage of keypairs
- Multi-account support

**2. On-Chain Data Interaction**
- Query Solana account data from within UE5
- Read on-chain program state (SAGE fleet status, cargo holds, etc.)
- Display SPL tokens and NFTs in game UI
- Real-time blockchain state synchronization

**3. Transaction Execution**
- Create transactions targeting Solana programs
- Sign transactions with locally-stored keys
- Send transactions to Solana RPC
- Handle transaction confirmation/failure

**4. Visual Development**
- **Blueprint support**: Visual scripting for blockchain interactions
- UI/UX components for wallet displays
- Asset visualization (ships, resources, tokens)

**5. Program Agnosticity**
- Can integrate with **any Solana program** (not just Star Atlas)
- Flexible architecture for custom game mechanics
- No vendor lock-in to specific blockchain infrastructure

### Example Use Case (Speculative Blueprint)

```
Blueprint: Refuel Fleet
┌─────────────────────────────────────┐
│ 1. Query Fleet Account (SAGE SDK)  │ → On-chain read
│    → Get current fuel level         │
│                                     │
│ 2. Calculate fuel needed            │ → Client-side logic
│    → Target: 100% capacity          │
│                                     │
│ 3. Query Starbase Marketplace       │ → On-chain read
│    → Get fuel price                 │
│                                     │
│ 4. Create Refuel Transaction        │ → Transaction builder
│    → SAGE program instruction       │
│                                     │
│ 5. Sign with Player Wallet          │ → Local keystore
│    → Prompt user approval (UE5 UI)  │
│                                     │
│ 6. Send Transaction                 │ → RPC call
│    → Await confirmation             │
│                                     │
│ 7. Update UI                        │ → Visual feedback
│    → Show new fuel level            │
└─────────────────────────────────────┘
```

### Repository Structure

```
FoundationKit/
├── Content/           # Plugin assets and content
├── Documentation/     # Usage guides and API docs
├── Resources/         # Supporting materials
├── Source/
│   └── Foundation/    # Core C++/C implementation
│       ├── Wallet/    # Wallet management
│       ├── RPC/       # Solana RPC client
│       ├── Programs/  # Program interaction
│       └── UI/        # Blueprint components
└── Foundation.uplugin # Plugin configuration
```

### Limitations & Gaps

**What F-Kit Does NOT Provide**:
- ❌ Pre-built game mechanics (fleet management UI, market analysis)
- ❌ High-level abstractions for Star Atlas-specific logic
- ❌ Automatic transaction batching or optimization
- ❌ Built-in AI/agent capabilities
- ❌ Voice interface integration
- ❌ Real-time price tracking or economic analysis

**Developer Burden**:
- Must implement all game-specific UI from scratch
- Must handle transaction error states manually
- Must manage RPC provider connections
- Must build economic logic (crafting ROI, market arbitrage)

**Implication for Our Agent**:
> F-Kit is a **low-level primitive**. It's the plumbing, not the faucet. Our agent sits **above** F-Kit in the stack, providing high-level intelligence and automation that F-Kit enables but doesn't implement.

---

## 2. Current SAGE Labs Features

### Game Mode: Browser-Based On-Chain Simulation

**Platform**: Web browser (not Unreal Engine - that's for future AAA game)
**Blockchain**: Solana mainnet (every action is an on-chain transaction)
**Game Type**: 2D space economy simulation, menu-driven, no combat (yet)

### Core Gameplay Loop

```
Player Workflow:
┌─────────────────────────────────────────────────┐
│ 1. Faction Selection (Permanent Choice)        │
│    → ONI, MUD, or Ustur                        │
│                                                 │
│ 2. Fleet Assembly (Central Space Station)      │
│    → Deposit ships from wallet                 │
│    → Create fleets (max 145 capacity points)   │
│    → Load R4 resources: Fuel, Ammo, Food,      │
│      Toolkits                                   │
│                                                 │
│ 3. Navigation (51 Star Systems)                │
│    → Subwarp: Slower, cheaper                  │
│    → Warp: Faster, expensive                   │
│                                                 │
│ 4. Economic Activities                         │
│    → Mining: Requires food, ammo, cargo space  │
│    → Scanning: Costs toolkits, finds SDUs      │
│    → Crafting: At starbases, uses resources    │
│    → Trading: Local marketplaces (new!)        │
│                                                 │
│ 5. Resource Management                         │
│    → Monitor fuel levels (fleet stranding risk)│
│    → Manage cargo capacity                     │
│    → Track resource consumption rates          │
│                                                 │
│ 6. Economic Optimization                       │
│    → Find profitable trade routes              │
│    → Optimize crafting ROI                     │
│    → Complete Faction Infrastructure Contracts │
│      (FICs) for guaranteed 2 ATLAS rewards     │
└─────────────────────────────────────────────────┘
```

### Recent Feature Additions (2025)

#### Local Marketplaces

**Problem Solved**: Previously, all trading required withdrawing assets from game to Galactic Marketplace (friction)

**New Mechanic**:
- Each of the **51 starbases** is now an independent market
- **Supply and demand dynamics** vary per location
- Prices fluctuate based on local starbase inventory
- Players buy/sell directly at starbases without leaving game

**Example Scenario**:
```
Starbase Alpha (mining region):
- Fuel: 10 ATLAS (low supply, high demand)
- Iron Ore: 2 ATLAS (high supply, low demand)

Starbase Beta (industrial hub):
- Fuel: 5 ATLAS (high supply, refinery nearby)
- Iron Ore: 8 ATLAS (low supply, high demand)

Arbitrage Opportunity:
1. Buy Iron Ore at Alpha (2 ATLAS)
2. Transport to Beta
3. Sell at Beta (8 ATLAS)
4. Profit: 6 ATLAS minus fuel costs
```

**Implication for Agent**:
> Our agent can analyze all 51 market prices in real-time and identify arbitrage opportunities that humans would miss. This is a **killer feature**.

---

#### Faction Infrastructure Contracts (FICs)

**Mechanic**:
- Players craft contracts at starbases
- Contracts can only be redeemed at **specific starbases** during **designated time windows**
- Redeeming a contract pays **2 ATLAS** (guaranteed income)

**Strategic Depth**:
- Crafting costs materials (must be profitable)
- Time windows create urgency
- Specific redemption locations require logistics planning

**Example**:
```
FIC Recipe:
- Input: 5 Iron Ore + 3 Carbon
- Output: 1 FIC (redeemable for 2 ATLAS)

Cost Analysis:
- Iron Ore: 5 × 1.5 ATLAS = 7.5 ATLAS
- Carbon: 3 × 0.5 ATLAS = 1.5 ATLAS
- Total Cost: 9 ATLAS
- Revenue: 2 ATLAS
- Profit: -7 ATLAS ❌ NOT PROFITABLE

Need to find cheaper materials or alternative recipe!
```

**Implication for Agent**:
> FIC profitability analysis requires real-time material pricing across 51 markets. Our agent can optimize FIC crafting locations and track redemption windows.

---

#### Survey Data Units (SDUs)

**Mechanic**:
- Fleets scan asteroid fields using toolkits
- Find SDUs (random loot drops)
- SDUs used to craft **Golden Tickets** (rare items)
- SDUs exchangeable for rewards

**Resource Cost**:
- **Toolkits**: Consumed per scan action
- **Time**: Scanning takes in-game time

**Implication for Agent**:
> SDU hunting is RNG-based. Agent can track toolkit costs vs SDU market value to determine profitability.

---

### Resource Types (R4 System)

| Resource | Purpose | Consumption Rate | Criticality |
|----------|---------|------------------|-------------|
| **Fuel** | Movement (subwarp/warp) | Per sector traveled | CRITICAL (fleet stranding) |
| **Ammo** | Mining operations | Per mining action | HIGH (no mining without) |
| **Food** | Mining operations | Per mining action | HIGH (no mining without) |
| **Toolkits** | SDU scanning | Per scan action | MEDIUM (optional activity) |

**Fleet Stranding Risk**:
> If a fleet runs out of fuel mid-journey, it becomes **stranded** and cannot move. Players must either:
> 1. Send another fleet with fuel to rescue
> 2. Abandon the stranded fleet (asset loss)

**Implication for Agent**:
> Fuel monitoring is the **#1 priority**. Agent must proactively alert users before fuel reaches critical levels.

---

### World Structure

**51 Star Systems** divided among 3 factions:
- **ONI**: High-tech, aggressive
- **MUD**: Industrial, pragmatic
- **Ustur**: Spiritual, defensive

**Each System Contains**:
- 1 **Starbase**: Resource storage, crafting, fleet management, marketplace
- 1+ **Asteroid Belts**: Mining locations

**Central Space Stations (CSS)**:
- Faction headquarters
- Deposit/withdraw ships and resources from wallet
- Fleet assembly point

---

### Game Modes

#### SAGE Labs (Mainnet)

**Platform**: Solana mainnet
**Cost**: Real ATLAS tokens, real ship NFTs
**Transactions**: ~1,590 per player per day (every action = blockchain tx)
**Audience**: Existing players with invested assets

#### Holosim (Testnet)

**Platform**: Internal Atlasnet blockchain (not Solana)
**Cost**: FREE (no real tokens/NFTs)
**Purpose**: Testing new features before mainnet release
**Features in Testing**:
- Combat system (ship battles, permanent losses)
- SAGE AI assistant (gameplay guide)
- Route Manager (fleet automation tools)
- Tutorial system
- Questing system

**Future Migration**:
> Features proven in Holosim graduate to SAGE Labs mainnet.

---

## 3. Blockchain Integration Architecture

### Fully On-Chain Game State

**Revolutionary Design**: SAGE Labs stores **100% of game logic and game state on-chain**.

**What This Means**:
- Fleet positions: On-chain (Sector PDAs)
- Fuel levels: On-chain (Fleet account data)
- Cargo contents: On-chain (CargoHold account)
- Resource prices: On-chain (Marketplace program)
- Crafting recipes: On-chain (Crafting program)
- Player profiles: On-chain (PlayerProfile program)

**Contrast with Traditional Games**:
```
Traditional MMO:
Game Client ↔ Game Server (Database) ↔ Blockchain (Optional, for NFTs only)
                 ↑
            All state lives here

Star Atlas SAGE Labs:
Game Client ↔ Solana Blockchain (RPC)
                 ↑
            All state lives here
```

### Solana Programs (~20 Programs)

**Core Programs**:
1. **SAGE**: Fleet management, movement, mining, combat
2. **Cargo**: Cargo hold management
3. **Crafting**: Recipe execution, material consumption
4. **Player Profile**: Identity, keys, permissions
5. **Galactic Marketplace**: Buy/sell orders, trading
6. **Profile Faction**: Faction membership, reputation
7. **Score**: Leaderboards, achievements
8. **Factory**: Transaction builders

**Developer Access**:
> All programs have published TypeScript SDKs on npm (`@staratlas/*`)

---

### Transaction Volume & Scale

**Statistics**:
- **2 million transactions per day** (entire SAGE Labs)
- **16 million+ total transactions** since launch
- **15% of all Solana transactions** attributed to SAGE Labs
- **~1,590 transactions per player per day** on average
- **1,442 active players** (Sunday peak)

**Why So Many Transactions?**

Every single gameplay action requires an on-chain transaction:

```
Example: Mining Session
┌─────────────────────────────────────┐
│ 1. Warp to asteroid belt           │ → Transaction 1
│ 2. Start mining                     │ → Transaction 2
│ 3. Mining tick (every 5 min)       │ → Transactions 3-14 (12 ticks)
│ 4. Claim mined resources           │ → Transaction 15
│ 5. Warp back to starbase           │ → Transaction 16
│ 6. Deposit resources to starbase   │ → Transaction 17
│                                     │
│ Total: 17 transactions for 1 hour  │
│ of mining gameplay                  │
└─────────────────────────────────────┘
```

**Wallet Approval Friction**:
> Players must **manually approve ~1,600 transactions per day** with their Solana wallet. This is **unsustainable** for mainstream adoption.

---

### Gas Fees

**Solana Gas Costs**:
- **Per transaction**: ~0.000005 SOL (~$0.0005 at $100/SOL)
- **Daily cost** (1,600 txs): 0.008 SOL (~$0.80/day)
- **Monthly cost**: 0.24 SOL (~$24/month)

**Cost Comparison**:
- Ethereum: $5-50 per tx (impossible)
- Solana: $0.0005 per tx (playable but annoying)
- z.ink (future): $0.000005 per tx (99% cheaper, negligible)

---

### RPC Provider Dependency

**Critical Infrastructure**:
SAGE Labs requires constant RPC access to:
- Read on-chain game state
- Submit player transactions
- Confirm transaction finality

**Providers**:
- Helius
- Alchemy
- QuickNode
- GenesysGo

**Latency Implications**:
- RPC call: 200-500ms
- Fleet status query: Must hit RPC
- Real-time gameplay requires low-latency RPC

**Implication for Agent**:
> Our agent will make frequent RPC calls. We MUST:
> 1. Cache static data aggressively (Galaxy API snapshots)
> 2. Use in-memory caching for recent queries (30s TTL)
> 3. Monitor RPC costs and optimize query patterns

---

## 4. Existing SAGE AI Assistant

### **CRITICAL DISCOVERY**: Star Atlas Already Has an AI Assistant

**Name**: SAGE (same as the game mode - confusing branding)
**Platform**: Holosim (testnet)
**Status**: Testing phase (not yet in mainnet SAGE Labs)
**Technology**: Likely LLM-based (GPT-4 or similar)

### Capabilities

**1. Gameplay Guidance**
- Explains game mechanics (how to mine, craft, trade)
- Answers "how do I..." questions
- Onboarding for new players

**2. Lore & World-Building**
- Provides Star Atlas universe lore
- Character backstories
- Faction information

**3. Interactive Q&A**
- Players can ask questions in natural language
- Trained on Star Atlas knowledge base
- "Full context of how to play the game"

### Example Interactions (Speculative)

```
Player: "How do I start mining?"
SAGE AI: "To start mining, you need:
1. A fleet with cargo capacity
2. Food and Ammo resources
3. Navigate to an asteroid belt
4. Click 'Start Mining'
Your fleet will consume food and ammo while mining."

Player: "What's the lore behind the ONI faction?"
SAGE AI: "The ONI Collective is a technologically advanced
faction focused on innovation and expansion. Founded by..."
```

### What SAGE AI Does NOT Do (Our Opportunity)

**❌ Autonomous Actions**:
- Does NOT execute transactions on player's behalf
- Does NOT manage fleets automatically
- Does NOT monitor fuel levels proactively
- Does NOT optimize trade routes

**❌ Economic Analysis**:
- Does NOT calculate crafting ROI
- Does NOT identify arbitrage opportunities
- Does NOT track market price trends

**❌ Voice Interface**:
- Text-only chat interface
- No voice input/output
- No hands-free operation

**❌ Personalization**:
- No memory of player preferences
- No trust progression system
- Generic responses for all users

**❌ Proactive Alerts**:
- Does NOT warn about low fuel
- Does NOT notify about profitable FIC windows
- Does NOT suggest optimal actions

---

### **Strategic Differentiation for Star Atlas Agent**

```
┌─────────────────────────────────────────────────┐
│         SAGE AI (Star Atlas Official)           │
├─────────────────────────────────────────────────┤
│ Focus: Education & Onboarding                   │
│ - Explains mechanics                            │
│ - Answers lore questions                        │
│ - Guides new players                            │
│                                                 │
│ Type: Reactive Q&A Chatbot                      │
│ Interface: Text chat                            │
│ Capability: Read-only knowledge                 │
└─────────────────────────────────────────────────┘
              vs
┌─────────────────────────────────────────────────┐
│       Star Atlas Agent (Our Product)            │
├─────────────────────────────────────────────────┤
│ Focus: Autonomous Fleet Management & Optimization│
│ - Executes transactions (with permission)       │
│ - Monitors fleet health proactively             │
│ - Optimizes economic strategies                 │
│ - Provides voice-first UX                       │
│                                                 │
│ Type: Autonomous Agent + Economic Advisor       │
│ Interface: Voice + Web Dashboard                │
│ Capability: Read + Write (transaction execution)│
└─────────────────────────────────────────────────┘
```

**Key Insight**:
> SAGE AI is a **teacher**. Our agent is a **co-pilot**. There's no direct competition - they serve different needs.

---

### Route Manager (Also in Holosim)

**Purpose**: Automate fleet logistics

**Capabilities** (based on limited info):
- Streamline operations
- Simplify fleet management
- Make gameplay "quicker, simpler, easier to control"

**What We Don't Know**:
- Exact features (UI screenshots unavailable)
- Does it support multi-hop routes?
- Can it auto-refuel?
- Does it optimize for profit or just convenience?

**Implication**:
> Route Manager is a **competitor feature** if it provides similar automation. We MUST differentiate by:
> 1. Voice-first interface (hands-free)
> 2. AI-driven economic optimization (not just scripted routes)
> 3. Proactive monitoring (alerts before problems occur)
> 4. Cross-platform (works outside browser, via MCP server)

---

## 5. Critical Player Pain Points

### Pain Point #1: Transaction Approval Fatigue

**The Problem**:
- **~1,590 wallet approvals per day per player**
- Every action (move, mine, craft, trade) requires manual approval
- Wallet popup interrupts immersion
- Typing password/clicking approve is tedious

**Player Quote** (from research):
> "The necessity for wallet transactions at various stages of gameplay adds to the complexity of the ecosystem."

**Current Workaround**:
- None (until z.ink zProfile launches)

**Our Solution**:
> **zProfile Integration (Post-MVP)**: Pre-approve transaction categories so agent can act autonomously within limits.

---

### Pain Point #2: Fleet Stranding (Fuel Management)

**The Problem**:
- Fleets consume fuel per sector traveled
- Running out of fuel mid-journey = **stranded fleet**
- Stranded fleets cannot move (asset stuck)
- Recovery requires sending rescue fleet with fuel (more transactions)

**Why It Happens**:
- Players miscalculate fuel requirements
- Unexpected warp detours
- Forgetting to refuel before long journey

**Current Workaround**:
- Manual fuel level monitoring (tedious)
- Conservative fuel buffers (inefficient capital allocation)

**Our Solution**:
> **Proactive Fuel Alerts**: Agent monitors fuel levels in real-time and warns users **before** critical threshold. Voice alert: "Fleet Alpha-7 has 15 minutes of fuel remaining. Nearest refuel station is 3 sectors away. Recommend immediate action."

---

### Pain Point #3: Economic Optimization Complexity

**The Problem**:
- **51 local marketplaces** with independent pricing
- **Hundreds of crafting recipes** with varying profitability
- **FIC redemption windows** (time-limited opportunities)
- **Resource price volatility** across starbases

**Manual Analysis Is Impossible**:
- Checking 51 markets manually: 30+ minutes
- Calculating crafting ROI for 100+ recipes: hours
- Tracking FIC windows across multiple starbases: error-prone

**Current Workaround**:
- Community spreadsheets (static, outdated)
- Trial-and-error (expensive mistakes)
- Gut feel (suboptimal)

**Our Solution**:
> **Real-Time Economic Intelligence**:
> - Agent fetches all 51 market prices via Galaxy API
> - Calculates crafting ROI for all recipes
> - Identifies profitable arbitrage routes
> - Alerts user to FIC redemption windows
>
> Voice interaction: "I found a 40% profit opportunity. Buy Iron Ore at Starbase Theta for 2 ATLAS, transport to Starbase Omega, sell for 3.5 ATLAS. Estimated fuel cost: 0.8 ATLAS. Net profit: 0.7 ATLAS per unit."

---

### Pain Point #4: Menu-Driven UI (Limited Immersion)

**The Problem**:
- SAGE Labs is browser-based, menu-driven (no 3D environment yet)
- Lots of clicking through tabs and panels
- Hard to visualize spatial relationships (sector distances)

**Our Solution**:
> **Voice-First Interface**: Bypass menus entirely. "Warp fleet to Starbase Alpha" → agent executes via MCP tools.

---

### Pain Point #5: Information Overload (51 Systems)

**The Problem**:
- 51 star systems to explore
- Each system has starbases, asteroid belts, markets
- Overwhelming for new players
- Hard to remember which starbase sells what

**Our Solution**:
> **Persistent Memory**: Agent remembers player's preferred trade routes, favorite starbases, fleet compositions. Provides contextual recommendations based on history.

---

## 6. Implications for Star Atlas Agent Design

### Strategic Positioning

**Competitive Landscape**:
```
Existing Tools:
├── SAGE AI (Official)     → Education/onboarding chatbot
├── Route Manager (Official) → Fleet automation (limited scope)
├── Community Spreadsheets  → Static economic data
└── Manual Gameplay         → Default (high friction)

Star Atlas Agent (Our Product):
└── Autonomous Co-Pilot + Economic Optimizer + Voice Interface
    - Differentiators: AI-driven, proactive, voice-first, personalized
```

**Positioning Statement**:
> "Star Atlas Agent is your autonomous co-pilot for fleet management and economic optimization. While SAGE AI teaches you how to play, Star Atlas Agent plays alongside you—monitoring your fleets, identifying profitable opportunities, and executing strategies via voice commands."

---

### Feature Prioritization (Based on Pain Points)

| Feature | Pain Point Addressed | Priority | MVP Phase |
|---------|---------------------|----------|-----------|
| **Fuel monitoring & alerts** | Fleet stranding | CRITICAL | ✅ Phase 1 |
| **Real-time market price tracking** | Economic optimization | HIGH | ✅ Phase 1 |
| **Voice-first interface** | Transaction fatigue | HIGH | ✅ Phase 1 |
| **Crafting ROI calculator** | Economic optimization | HIGH | ✅ Phase 1 |
| **Arbitrage opportunity detection** | Economic optimization | MEDIUM | ⏭️ Phase 2 |
| **FIC window tracking** | Economic optimization | MEDIUM | ⏭️ Phase 2 |
| **Auto-refuel (via zProfile)** | Transaction fatigue + stranding | HIGH | ⏭️ Phase 4 (z.ink) |
| **Route optimization** | Fuel efficiency | MEDIUM | ⏭️ Phase 2 |
| **Persistent memory** | Information overload | HIGH | ✅ Phase 1 |

---

### MCP Tool Design (Informed by Gameplay)

**Critical Tools for MVP**:

#### 1. `getFleetStatus(fleetId)`
**Purpose**: Real-time fuel/cargo/health monitoring
**Pain Point**: Fleet stranding prevention
**Data Source**: SAGE SDK + Solana RPC
**Caching**: 30s in-memory TTL

**Response**:
```typescript
{
  fleetId: "...",
  position: { x: 120, y: 45 }, // Sector coordinates
  fuelCurrent: 850,
  fuelMax: 1000,
  fuelRange: 42, // Sectors remaining before stranded
  cargoUsed: 350,
  cargoMax: 500,
  health: 100,
  status: "mining", // idle, warp, mining, docked
  nearestStarbase: {
    name: "MUD HQ",
    distance: 8, // sectors
  },
}
```

---

#### 2. `getMarketPrices(itemMint?, starbaseId?)`
**Purpose**: Cross-market arbitrage analysis
**Pain Point**: Economic optimization
**Data Source**: Galaxy API (1-hour cache)

**Response**:
```typescript
{
  item: "Iron Ore",
  prices: [
    { starbase: "Alpha", buyPrice: 2.0, sellPrice: 2.5, supply: 1000 },
    { starbase: "Beta", buyPrice: 3.5, sellPrice: 4.0, supply: 50 },
    // ... 49 more markets
  ],
  bestArbitrage: {
    buy: { starbase: "Alpha", price: 2.0 },
    sell: { starbase: "Beta", price: 4.0 },
    profit: 2.0, // ATLAS per unit
    distance: 15, // sectors
    fuelCost: 0.8, // ATLAS
    netProfit: 1.2,
  },
}
```

---

#### 3. `calculateCraftingROI(recipeId)`
**Purpose**: Identify profitable crafting recipes
**Pain Point**: Economic optimization
**Data Source**: Crafting SDK (S3 cache) + Market prices

**Response**:
```typescript
{
  recipe: "Faction Infrastructure Contract",
  ingredients: [
    { item: "Iron Ore", amount: 5, costPer: 2.0, total: 10.0 },
    { item: "Carbon", amount: 3, costPer: 0.5, total: 1.5 },
  ],
  totalCost: 11.5,
  outputs: [
    { item: "FIC", amount: 1, sellPrice: 2.0 }, // Redemption value
  ],
  totalRevenue: 2.0,
  profit: -9.5,
  roi: -82.6%, // Percentage
  profitable: false,
  recommendation: "NOT RECOMMENDED: Find cheaper materials or alternative recipe",
}
```

---

#### 4. `planRoute(fromSector, toSector, optimizeFor?)`
**Purpose**: Fuel-efficient navigation
**Pain Point**: Fleet stranding + fuel costs
**Data Source**: Sector graph (S3 cache) + Fleet specs

**Response**:
```typescript
{
  route: [
    { sector: [120, 45], action: "warp" },
    { sector: [125, 50], action: "subwarp" },
    { sector: [130, 55], action: "warp", refuelAt: "Starbase Gamma" },
    { sector: [135, 60], action: "warp" },
    { sector: [140, 65], action: "arrive" },
  ],
  totalDistance: 25, // sectors
  fuelRequired: 1200,
  fleetFuelCapacity: 1000,
  requiresRefuel: true,
  refuelStops: ["Starbase Gamma"],
  estimatedTime: "45 minutes",
  fuelCost: 18.5, // ATLAS
}
```

---

#### 5. `executeTransaction(toolName, params)`
**Purpose**: Agent-initiated blockchain transactions (with user approval)
**Pain Point**: Transaction fatigue (future: auto-approve via zProfile)
**Data Source**: SAGE SDK transaction builders

**Phase 1 (MVP)**:
- Requires explicit user approval per transaction
- Wallet popup displayed

**Phase 4 (zProfile Integration)**:
- Pre-approved transaction categories
- No wallet popup for common actions
- User sets spending limits

**Example**:
```typescript
// Phase 1: Manual approval
await executeTransaction('refuelFleet', {
  fleetId: '...',
  fuelAmount: 500,
  starbaseId: '...',
});
// → Wallet popup: "Approve refuel transaction (cost: 8.5 ATLAS)"

// Phase 4: Auto-approved (zProfile)
await executeTransaction('refuelFleet', {
  fleetId: '...',
  fuelAmount: 500, // Within pre-approved limit (1000 ATLAS)
  starbaseId: '...',
});
// → No popup, transaction executes immediately
```

---

### Voice Interaction Patterns

#### Proactive Monitoring (Background)

```
Agent (unprompted): "Warning: Fleet Alpha-7 fuel at 20%.
Nearest refuel: Starbase Gamma, 8 sectors away.
Recommend refueling now. Say 'refuel Alpha-7' to proceed."

User: "Refuel Alpha-7"

Agent: "Routing to Starbase Gamma. ETA 12 minutes.
Fuel cost: 8.5 ATLAS. Approving transaction now."
*[Transaction executes]*

Agent: "Refuel complete. Fleet ready to resume operations."
```

---

#### Economic Optimization (Query)

```
User: "What's the most profitable trade right now?"

Agent: "I found 3 profitable opportunities:
1. Iron Ore arbitrage: Buy at Alpha (2 ATLAS), sell at Beta (4 ATLAS).
   Net profit: 1.2 ATLAS per unit after fuel.
2. Crafting Titanium Plates: 15% ROI, 45-minute crafting time.
3. FIC redemption window opens in 30 minutes at Starbase Delta.
   Guaranteed 2 ATLAS per contract.

Which would you like to pursue?"
```

---

#### Fleet Management (Command)

```
User: "Send my mining fleet to the nearest asteroid belt"

Agent: "Nearest asteroid belt: Sector [130, 55], 8 sectors away.
Fleet Bravo-3 selected (cargo capacity: 500m³, fuel: 85%).
Route planned: Subwarp to conserve fuel. ETA 18 minutes.
Initiating warp now."
*[Transaction executes]*

Agent: "Fleet en route. I'll alert you when mining begins."
```

---

### Data Architecture (Hybrid Strategy from ADR-001)

```
┌─────────────────────────────────────────────────┐
│          Star Atlas Agent (MCP Server)          │
├─────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────┐ │
│  │  Static Cache    │  │  Real-Time Layer    │ │
│  │  (S3/CloudFront) │  │  (Solana RPC)       │ │
│  ├──────────────────┤  ├─────────────────────┤ │
│  │ Ship metadata    │  │ Fleet status        │ │
│  │ Crafting recipes │  │ Cargo contents      │ │
│  │ Starbases (51)   │  │ Market prices (1hr) │ │
│  │ Sectors (grid)   │  │ Wallet balances     │ │
│  │                  │  │ Active transactions │ │
│  │ Update: Weekly   │  │ Query: On-demand    │ │
│  │ Cost: $0 (FREE)  │  │ Cost: ~$3/month     │ │
│  └──────────────────┘  └─────────────────────┘ │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│      Voice Service + Agent Core (Bedrock)       │
│  - STT/TTS streaming                            │
│  - LLM reasoning (Claude 3.5)                   │
│  - Memory layer (DynamoDB)                      │
│  - Proactive monitoring loop                    │
└─────────────────────────────────────────────────┘
```

**Cost Optimization**:
- Static data (ships, recipes): **$0/month** (Galaxy API is FREE)
- Real-time RPC queries: **~$3/month** (100 queries/day × $0.001)
- Voice processing: **~$5/month** (ElevenLabs + Whisper)
- LLM inference: **~$10/month** (Bedrock Claude 3.5)
- **Total**: **~$18/month per active user**

---

### Competitive Advantage Summary

| Feature | SAGE AI | Route Manager | Community Tools | **Star Atlas Agent** |
|---------|---------|---------------|----------------|----------------------|
| **Education** | ✅ Excellent | ❌ None | ⚠️ Limited | ✅ Good (via memory) |
| **Autonomous Actions** | ❌ None | ⚠️ Basic | ❌ None | ✅ **Advanced** |
| **Economic Analysis** | ❌ None | ❌ None | ⚠️ Static | ✅ **Real-Time** |
| **Voice Interface** | ❌ Text only | ❌ None | ❌ None | ✅ **Native** |
| **Proactive Monitoring** | ❌ Reactive | ⚠️ Unknown | ❌ None | ✅ **24/7** |
| **Personalization** | ❌ Generic | ❌ None | ❌ None | ✅ **Adaptive** |
| **Transaction Execution** | ❌ No | ⚠️ Limited | ❌ No | ✅ **Full** |
| **zProfile Ready** | ❌ No | ⚠️ Unknown | ❌ No | ✅ **Phase 4** |

**Unique Value Proposition**:
> "The only voice-first autonomous agent that manages your fleets, optimizes your economy, and prevents costly mistakes—all while learning your preferences and getting smarter over time."

---

## Conclusion

### Key Takeaways

1. **F-Kit is Low-Level Plumbing**: It enables blockchain integration but doesn't provide game logic or AI. Our agent sits above it in the stack.

2. **SAGE AI is NOT a Competitor**: It's an educational chatbot. We're an autonomous co-pilot. Different value props.

3. **Transaction Fatigue is Real**: ~1,600 approvals/day is unsustainable. zProfile (z.ink) will solve this, and we'll be ready.

4. **Economic Complexity is Overwhelming**: 51 markets × 100+ recipes × time-limited FICs = impossible for humans to optimize manually. AI excels here.

5. **Fuel Management is Critical**: Fleet stranding is the #1 operational risk. Proactive monitoring is a killer feature.

6. **Voice-First is Unique**: No existing tool offers hands-free fleet management. This is our blue ocean.

---

### Next Steps

1. ✅ Complete research documentation
2. ⏭️ Update BLUEPRINT.yaml with refined features based on gameplay insights
3. ⏭️ Proceed with Epic #1 (Foundation & Infrastructure)
4. ⏭️ Build MVP focusing on fuel monitoring, market analysis, and voice UX
5. ⏭️ Post-MVP: Integrate zProfile when z.ink APIs are available (Q1-Q2 2026)

---

**Research Completed By**: Claude Code Agent
**Date**: 2025-11-13
**Status**: Ready for Implementation Planning
