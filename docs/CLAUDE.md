# Star Atlas Agent - Claude Code Instructions

## Project Overview

Star Atlas Agent is a Cortana-like AI assistant for the Star Atlas on-chain economy ecosystem. Built with Claude Agent SDK, it monitors blockchain activities, tracks material pricing, provides game control through natural language, and features voice-to-voice interaction. The agent integrates with Star Atlas APIs, Solana blockchain, and game systems to create an immersive assistant experience.

## Architecture

### Technology Stack

- **Agent Framework**: Claude Agent SDK (TypeScript)
- **MCP Server**: @modelcontextprotocol/sdk + @staratlas/sage + @solana/web3.js
- **Voice Service**: Whisper (STT) + ElevenLabs (TTS) + WebRTC
- **Frontend**: React + Vite + Three.js (for visualizations)
- **Backend**: Firebase Functions (serverless)
- **Database**: Firestore (existing from galactic-data)
- **Blockchain**: Solana (migrating to z.ink Layer 1)
- **Hosting**: Firebase Hosting

### Project Structure

```
star-atlas-agent/
├── packages/
│   ├── galactic-data/         # Existing price monitoring (refactored)
│   ├── mcp-staratlas-server/  # MCP server for Star Atlas + Solana
│   ├── agent-core/            # Claude Agent SDK wrapper
│   ├── voice-service/         # Voice interaction pipeline
│   └── web-app/               # Web interface
├── backend/functions/         # Serverless + blockchain webhooks
├── infrastructure/            # Firebase configuration
└── docs/                      # Project documentation
```

## Development Workflow

### Package Management

**ALWAYS use `pnpm` for package management:**
- Install: `pnpm install`
- Add dependency: `pnpm add <package>`
- Run scripts: `pnpm run <script>`

### Environment Setup

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Configure Firebase (existing setup from galactic-data):**
   ```bash
   firebase login
   firebase use <project-id>
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Configure Solana RPC:**
   - Use Helius, QuickNode, or public RPC endpoints
   - Add RPC_URL to environment

5. **Configure Voice Services:**
   - Whisper API key (OpenAI) or local Whisper
   - ElevenLabs API key for TTS
   - Alternative: Deepgram (STT) + Coqui TTS (local)

### Running the Project

**Development mode:**
```bash
pnpm dev
```

**Build for production:**
```bash
pnpm build
```

**Run tests:**
```bash
pnpm test
```

## Star Atlas Integration

### Blockchain Infrastructure

**Current State:**
- Star Atlas built on Solana blockchain
- Migrating to **z.ink** (Custom SVM Layer 1) - December 2025 launch
- All game logic and state stored on-chain

**z.ink Key Features:**
- zProfiles: Identity-linked accounts with zero-knowledge proofs
- dApp Permissioning: Set automatic transaction limits
- Token airdrop campaigns

### Tokens

**ATLAS** (Utility Token):
- Primary in-game currency
- Earned through gameplay
- Used for transactions and purchases

**POLIS** (Governance Token):
- Voting power for game direction
- Staking opportunities
- Faction governance

### Available APIs

**Game APIs (build.staratlas.com):**
1. **SAGE API** (`@staratlas/sage`)
   - Core game mechanics
   - Fleet management
   - Ship operations
   - Player state

2. **Galactic Marketplace API**
   - Asset trading
   - Price discovery

3. **Galaxy API**
   - Items, tokens, showroom

4. **Cargo API**
   - Inventory management
   - Logistics

5. **Crafting API**
   - Item creation
   - Upgrades

6. **Player Profile API**
   - Progression tracking
   - Reputation

7. **Fleet Rentals API**
   - Ship leasing

### Blockchain Monitoring

**WebSocket Subscriptions (Recommended):**
```typescript
import { Connection } from '@solana/web3.js';

const connection = new Connection(RPC_URL, {
  wsEndpoint: WS_URL,
  commitment: 'confirmed'
});

// Monitor account changes
const subscriptionId = connection.onAccountChange(
  publicKey,
  (accountInfo) => {
    // Handle state update
  }
);

// Monitor program logs
const logSubscription = connection.onLogs(
  programId,
  (logs) => {
    // Handle program events
  }
);
```

**Price Tracking:**
- Chainlink Data Feeds for market prices
- Moralis Price APIs for token data
- Custom aggregation from DEX data

## MCP Server Design

### Tool Categories

**Marketplace Tools:**
```typescript
- get_asset_price(assetId: string): Price
- track_price_history(assetId: string, timeRange: TimeRange): PriceHistory[]
- get_trending_assets(): Asset[]
- search_marketplace(query: string): Asset[]
```

**Fleet Management Tools:**
```typescript
- get_fleet_status(fleetId: string): FleetStatus
- move_fleet(fleetId: string, destination: Coordinates): void
- get_fleet_inventory(fleetId: string): Inventory
- repair_fleet(fleetId: string): RepairStatus
```

**Crafting Tools:**
```typescript
- get_crafting_recipes(): Recipe[]
- calculate_crafting_cost(recipeId: string): Cost
- optimize_crafting(targetItem: string): CraftingPlan
```

**Blockchain Query Tools:**
```typescript
- get_wallet_balance(address: string): Balance
- get_token_holdings(address: string): Token[]
- get_transaction_history(address: string): Transaction[]
- monitor_address(address: string): Subscription
```

**News & Events Tools:**
```typescript
- get_latest_news(): NewsArticle[]
- get_faction_events(faction: string): Event[]
- track_economic_indicators(): EconomicData
```

## Agent Architecture

### Orchestrator Pattern

- **Main Agent**: Coordinates tasks, maintains context
- **Market Analyst**: Price analysis, trading insights
- **Fleet Commander**: Fleet management, game control
- **Craft Optimizer**: Crafting optimization
- **Voice Handler**: Voice command processing

### Specialization

**Market Analyst Agent** (`/.claude/agents/market-analyst.md`):
- Real-time price monitoring
- Trend analysis
- Trading recommendations
- Alert management

**Fleet Commander Agent** (`/.claude/agents/fleet-commander.md`):
- Fleet status monitoring
- Natural language ship commands
- Resource management
- Mission planning

**Craft Optimizer Agent** (`/.claude/agents/craft-optimizer.md`):
- Recipe analysis
- Cost optimization
- Resource allocation
- Production planning

**Voice Handler Agent** (`/.claude/agents/voice-handler.md`):
- Voice command recognition
- Context-aware responses
- Conversation flow management
- Voice-optimized formatting

## Voice Interaction Architecture

### Voice Pipeline

```
User Speech → WebRTC → Voice Service
                         ↓
                    Whisper STT
                         ↓
                      Text Input
                         ↓
                    Agent Processing
                         ↓
                    Text Response
                         ↓
                  ElevenLabs TTS
                         ↓
                     Audio Output
                         ↓
                   WebRTC → User
```

### Voice Service Implementation

**Speech-to-Text Options:**

1. **Whisper API (OpenAI)** - Recommended for MVP
   - High accuracy
   - Multi-language support
   - Cloud-based (requires API key)

2. **Deepgram** - Alternative
   - Real-time streaming
   - Low latency
   - Cost-effective

**Text-to-Speech Options:**

1. **ElevenLabs** - Recommended for quality
   - Natural voices
   - Emotion and tone control
   - Custom voice cloning

2. **Coqui TTS** - Local alternative
   - Open source
   - Self-hosted
   - No API costs

### WebRTC Integration

**Browser Client:**
```typescript
// Capture audio
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

// Create peer connection
const pc = new RTCPeerConnection(config);
pc.addTrack(stream.getAudioTracks()[0], stream);

// Handle incoming audio
pc.ontrack = (event) => {
  audioElement.srcObject = event.streams[0];
};
```

**Signaling Server:**
- WebSocket for offer/answer exchange
- STUN/TURN servers for NAT traversal
- Session management

### Voice Command Patterns

**Push-to-Talk:**
- User holds button/key to speak
- Release to process
- Visual feedback during recording

**Wake Word:**
- Always listening for "Hey Cortana" (or custom phrase)
- Activate on detection
- Privacy considerations

**Continuous Conversation:**
- VAD (Voice Activity Detection)
- Natural turn-taking
- Context maintenance across turns

## Balanced MVP Features

### On-Chain Monitoring (35%)

**Core Capabilities:**
- Real-time price tracking for materials (leverage galactic-data)
- Material availability monitoring
- Fleet status via SAGE API
- Transaction notifications
- Economic indicator tracking

**Implementation Priority:**
1. Extend galactic-data price monitoring
2. Add SAGE API integration for fleet status
3. Implement WebSocket subscriptions for real-time updates
4. Create alert system for price thresholds

### Natural Language Game Control (35%)

**Core Capabilities:**
- Text-based fleet commands
- Crafting optimization queries
- Market analysis questions
- Game state queries
- Resource management

**Implementation Priority:**
1. Define command vocabulary
2. Create fleet management tools
3. Implement crafting calculator
4. Add market analysis tools

### Voice Interaction Foundation (30%)

**Core Capabilities:**
- Speech-to-text for command input
- Text-to-speech for responses
- Push-to-talk interface
- Basic voice command library
- Error handling and clarification

**Implementation Priority:**
1. Set up WebRTC signaling server
2. Integrate Whisper for STT
3. Integrate ElevenLabs for TTS
4. Create voice-optimized response formatting
5. Build push-to-talk UI

## Refactoring galactic-data

### Preserve

- Firebase + Firestore architecture (proven scalable)
- Docker containerization
- TypeScript codebase
- Cloud Build CI/CD

### Extend

1. **Add Agent SDK Integration**
   - Wrap existing price monitoring in MCP tools
   - Create agent layer for natural language queries

2. **Expand Data Sources**
   - Integrate SAGE API
   - Add Galaxy API for items/tokens
   - Include blockchain monitoring

3. **Add Voice Interface**
   - Voice service package
   - WebRTC communication layer

4. **Enhance Real-Time Capabilities**
   - WebSocket subscriptions for Solana
   - Push notifications for alerts

## Security Considerations

### Wallet Integration

- Read-only wallet connections by default
- Explicit user approval for transactions
- Transaction simulation before signing
- Spending limits and safeguards

### Voice Privacy

- Local processing options for sensitive commands
- Clear recording indicators
- User consent for voice storage
- Encrypted transmission

### API Keys

- Never commit API keys
- Use environment variables
- Firebase secret management for functions
- Key rotation policies

## Testing Strategy

### Unit Tests
- MCP tool handlers
- API client wrappers
- Agent logic
- Voice pipeline components

### Integration Tests
- SAGE API integration
- Solana RPC interactions
- Voice service end-to-end
- Agent + MCP integration

### E2E Tests
- Fleet command workflows
- Price alert system
- Voice interaction flows
- Crafting optimization

## Deployment

### Firebase Deployment

```bash
firebase deploy
```

### Voice Service Deployment

- Deploy as separate Cloud Run service (lower latency)
- WebRTC signaling on Cloud Functions
- STT/TTS API calls from voice service

## Troubleshooting

### Common Issues

**Solana RPC Connection Issues:**
- Verify RPC endpoint health
- Check rate limits
- Use fallback RPC providers
- Monitor WebSocket connection stability

**SAGE API Errors:**
- Verify program IDs match mainnet
- Check account ownership
- Validate transaction formats

**Voice Service Latency:**
- Target < 500ms end-to-end
- Use streaming STT/TTS
- Optimize audio codec
- Deploy voice service closer to users

**Token Refresh for Voice:**
- Maintain WebSocket connection
- Implement reconnection logic
- Handle network interruptions gracefully

## References

- [Star Atlas Documentation](https://build.staratlas.com/)
- [SAGE API Reference](https://www.npmjs.com/package/@staratlas/sage)
- [Solana Web3.js](https://solana-labs.github.io/solana-web3.js/)
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [ElevenLabs API](https://elevenlabs.io/docs/api-reference/overview)
- [WebRTC API](https://webrtc.org/)
- [z.ink Documentation](https://z.ink/) (coming December 2025)
