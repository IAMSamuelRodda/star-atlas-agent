# Star Atlas Agent

> **Purpose**: Project introduction and quick start guide
> **Lifecycle**: Stable (update when fundamentals change)

Voice-first AI agent for Star Atlas fleet monitoring, economic optimization, and gameplay assistance.

**Current Work**: See [`STATUS.md`](./STATUS.md)

---

## Overview

Star Atlas Agent is a voice-first AI assistant for Star Atlas players, evolving from traditional SaaS (Phase 1) to NFT-based agent ownership (Phase 2). Monitor fleets, optimize economics, and get AI-powered gameplay recommendations through natural conversation.

**Unique Value Proposition (Phase 2)**:
- 🎯 **True Ownership** - Mint your agent as an NFT, you own the personality (not rented access)
- 🔄 **Portable Across Infrastructures** - Agent runs on our platform, competitors, or self-hosted (you choose)
- 💎 **Tradeable Asset** - Experienced agents gain value, sell on marketplaces (Magic Eden, Tensor)
- 🧠 **Growing Personality** - On-chain memory (Star Frame) captures key learnings, strategies, trust progression

**Key Features (Phase 1 MVP)**:
- 🎙️ **Voice-First Interface** - Cortana-like experience with <500ms response time
- 🚀 **Fleet Monitoring** - Real-time alerts for fuel, repairs, and resource needs
- 💰 **Economic Optimization** - Crafting ROI analysis and resource allocation
- 🔗 **Blockchain Integration** - WebSocket subscriptions to Solana for real-time data
- 🔐 **Secure Transactions** - Explicit wallet approval required (never auto-sign)


---

## Quick Start

**For Developers:**
```bash
# Clone and setup
git clone https://github.com/IAMSamuelRodda/star-atlas-agent.git
cd star-atlas-agent
pnpm install

# Start all services
pnpm dev
```

**For AI Agents:**
See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for workflow.

---

## Architecture

**Tech Stack:**
- Frontend: React 18 + TypeScript + Vite
- Backend: AWS Lambda + API Gateway (serverless)
- Database: DynamoDB (NoSQL)
- Voice: WebRTC + OpenAI Whisper + ElevenLabs
- Infrastructure: AWS (Free Tier optimized, <$10/month)

**Pattern**: Event-driven microservices with voice service, agent core, MCP server, and web app.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for complete details.

---

## Documentation

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - System architecture, database schema, ADRs
- [`STATUS.md`](./STATUS.md) - Current work, known issues
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) - Workflow, progress tracking
- [`DEVELOPMENT.md`](./DEVELOPMENT.md) - Git workflow, CI/CD, testing
- [`CHANGELOG.md`](./CHANGELOG.md) - Release history
- [`docs/planning-session-2025-11-12.md`](./docs/planning-session-2025-11-12.md) - Vision & constraints

---

## Testing

```bash
# All tests
pnpm test

# Specific package
pnpm --filter mcp-staratlas-server test

# E2E tests (requires test wallet)
pnpm test:e2e
```

See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for complete testing setup.

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for workflow guide and best practices.

**Branch strategy**: `feature/* → dev → main` (three-tier with aggressive branch protection)

---

## License

MIT

---

---

## Roadmap

### Phase 1: MVP (Months 1-6)
- Voice-first AI agent (WebRTC + Whisper + ElevenLabs)
- Fleet monitoring and alerts (Solana WebSocket subscriptions)
- Economic optimization (crafting ROI, resource allocation)
- Cloud-only memory (DynamoDB vector store)
- **Business Model**: $10/month SaaS subscription

### Phase 2: NFT Ownership (Months 7-12)
- Metaplex NFT minting (agent ownership tokens)
- Star Frame on-chain personality program (Rust)
- Memory compression (10 KB → 256 bytes, 97.5% reduction)
- Open-source agent runtime (enable competitor infrastructures)
- **Business Model**: $50 NFT mint + $5/month infrastructure + 5% marketplace royalties

### Phase 3: Decentralized (Months 13-24)
- Fully decentralized agent runtime
- Multi-infrastructure support (ours, competitors, self-hosted)
- Marketplace integrations (Magic Eden, Tensor, Solanart)
- Compete on UX/performance, not lock-in

See: `docs/research/portable-agent-ownership-architecture.md` for complete Phase 2 architecture
See: GitHub Epic #142 for implementation roadmap

---

**Last Updated**: 2025-11-13
