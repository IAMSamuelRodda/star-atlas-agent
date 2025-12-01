# IRIS - Issues & Flagged Items

> **Purpose**: Track items needing attention before/during IRIS implementation
> **Generated from**: specs/BLUEPRINT-project-staratlas-20251201.yaml

**Last Updated**: 2025-12-01

---

## High Complexity Items (needs_decomposition)

These tasks have complexity >3.0 and should be broken down further before implementation.

### task_1_2_3: prepareTransaction tool
**Complexity**: 3.2 | **Epic**: MCP Server

**Issue**: High technical complexity (4.0) and risk (4.0) due to transaction construction and security requirements.

**Why flagged**:
- Creating unsigned Solana transactions requires deep blockchain knowledge
- Security-critical: mistakes could cause fund loss
- Must handle various transaction types (SPL transfers, SAGE operations)

**Suggested breakdown**:
1. `subtask_1_2_3_1`: Research Solana transaction structure (spike)
2. `subtask_1_2_3_2`: Implement basic SOL transfer transaction builder
3. `subtask_1_2_3_3`: Add SPL token transfer support
4. `subtask_1_2_3_4`: Add SAGE operation transaction templates
5. `subtask_1_2_3_5`: Implement transaction validation and error handling

**Status**: 🔴 Not started

---

### task_1_3_3: subscribeToFleetUpdates WebSocket
**Complexity**: 3.5 | **Epic**: MCP Server

**Issue**: High technical complexity (4.0), dependencies (4.0), and uncertainty (4.0) due to WebSocket state management and Solana account subscriptions.

**Why flagged**:
- Solana account subscriptions are complex (RPC WebSocket)
- State management across reconnections
- Must handle rate limiting and backpressure

**Suggested breakdown**:
1. `subtask_1_3_3_1`: Implement basic Solana WebSocket connection handler
2. `subtask_1_3_3_2`: Add account subscription management
3. `subtask_1_3_3_3`: Implement reconnection and state recovery
4. `subtask_1_3_3_4`: Add rate limiting and backpressure handling
5. `subtask_1_3_3_5`: Create fleet update event transformation

**Status**: 🔴 Not started

---

### task_4_3_3: Latency monitoring and optimization
**Complexity**: 3.5 | **Epic**: Voice Service

**Issue**: High technical complexity (4.0) and uncertainty (4.0) due to real-time performance requirements.

**Why flagged**:
- <500ms round-trip is aggressive target
- Multiple components in chain (WebRTC → Chatterbox → Agent → Chatterbox → WebRTC)
- Optimization requires profiling across distributed system

**Suggested breakdown**:
1. `subtask_4_3_3_1`: Add timing instrumentation to voice pipeline
2. `subtask_4_3_3_2`: Create latency dashboard/logging
3. `subtask_4_3_3_3`: Identify bottlenecks via profiling
4. `subtask_4_3_3_4`: Implement streaming optimizations (overlap STT/Agent/TTS)
5. `subtask_4_3_3_5`: Add latency alerts and fallback triggers

**Status**: 🔴 Not started

---

## Needs Spike Investigation

These items have high uncertainty (≥4) and need research before implementation.

### SPIKE: Chatterbox Integration
**Feature**: feature_4_1 (Chatterbox Installation & Configuration)
**Uncertainty**: 4.0

**Questions to answer**:
1. What Docker image/setup works best on DO VPS?
2. What are the RAM/CPU requirements?
3. How to configure STT/TTS endpoints?
4. What models are available and their latency characteristics?
5. How to handle concurrent audio streams?

**Suggested spike structure**:
```yaml
BLUEPRINT-spike-chatterbox-integration-20251202.yaml

deliverables:
  - Research report: Chatterbox deployment options
  - POC: Basic STT/TTS working on VPS
  - Decision: Model selection for latency vs quality
  - Documentation: Setup steps for team

duration: 3-5 days
```

**Status**: 🔍 Needs spike before implementation

---

## Risk Register

### High Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Voice latency >500ms | High | Medium | Early Chatterbox spike + fallback to text-only |
| VPS RAM insufficient | High | Low | Load test early, upgrade path ($24/month for 8GB) |
| Solana RPC rate limiting | High | Medium | Aggressive caching (5-min TTL), paid RPC fallback |

### Medium Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| WebSocket stability on mobile | Medium | Medium | Auto-reconnect, polling fallback |
| SQLite concurrent writes | Medium | Low | WAL mode, connection pool, PostgreSQL migration path |
| Star Atlas API changes | Medium | Low | Version lock SAGE SDK, monitor changelog |

---

## Dependencies

### Blocking Dependencies

| Dependency | Blocks | Notes |
|------------|--------|-------|
| Epic 1 (MCP Server) | Epic 3 (Agent Core) | Agent needs MCP tools |
| Epic 2 (Memory Service) | Epic 3 (Agent Core) | Agent needs conversation context |
| Feature 3.4 (Agent API) | Feature 4.4 (Voice API) | Voice needs agent endpoints |

### External Dependencies

| Service | Criticality | Fallback |
|---------|-------------|----------|
| Solana blockchain | High | Cached data, offline mode |
| Star Atlas SAGE API | High | Cached fleet state |
| CoinGecko API | Medium | Stale prices acceptable |
| Chatterbox | High | Text-only fallback |

---

## Assumptions

1. ✅ Digital Ocean VPS has 640MB+ RAM available (verified 2025-12-01)
2. ⚠️ Chatterbox can run alongside other services (needs spike)
3. ⚠️ Star Atlas SAGE API will remain stable (monitor)
4. ✅ SQLite performance adequate for <500 users
5. ✅ WebRTC supported in target browsers

---

## CITADEL Integration (Epic 8)

### task_8_10_2: E2E tests for voice queries
**Complexity**: 3.0 | **Epic**: CITADEL Integration

**Issue**: High technical complexity (4.0) and dependencies (4.0) - requires both IRIS and CITADEL running.

**Why flagged**:
- Playwright tests need to simulate voice input
- Requires CITADEL API running or mocked
- Complex assertion chain: voice → agent → CITADEL API → response

**Suggested breakdown**:
1. Mock CITADEL API responses
2. Test voice input simulation separately
3. Integration test voice → agent flow
4. Full E2E with mock CITADEL

**Status**: 🔴 Not started

---

### CITADEL ↔ IRIS Coordination Notes

**Integration Contract** (defined in blueprint):
```
CITADEL Provides:
├── GET /api/dashboard/prices (30s cache)
├── GET /api/dashboard/fleets/:fleetId (60s cache)
├── GET /api/recommendations/mining (5min cache)
├── GET /api/recommendations/transport/:from/:to (5min cache)
├── WebSocket ws://citadel/ws/prices
└── MCP Tools: citadel_calculate_*, citadel_get_*

IRIS Provides:
├── Voice interface
├── User preferences from knowledge graph
└── Session context
```

**Parallel Development Strategy**:
- IRIS can start immediately with mock APIs (task_8_1_3)
- CITADEL Decision API priority: /api/dashboard/prices first
- Integration testing blocked until both systems have staging

**Risks**:
1. **CITADEL APIs not ready** → Mitigation: Mock responses unblock IRIS
2. **MCP incompatibility** → Mitigation: HTTP API fallback
3. **Voice latency budget** → Mitigation: Aggressive caching (30s-5min TTLs)

---

## Aspirational Features (from CITADEL)

> **Note**: These ML/RL features were originally scoped for CITADEL but moved to IRIS since IRIS is the "intelligent assistant" layer. CITADEL provides reliable data; IRIS provides intelligence.

### ASP-001: Price Prediction Model
**Type**: Machine Learning | **Priority**: Future
**Origin**: CITADEL Epic 6 (removed from scope)

**Concept**: Time-series forecasting (ARIMA, LSTM, Prophet) for Star Atlas resource prices.

**Why IRIS (not CITADEL)**:
- Predictions are recommendations, not raw data
- IRIS provides intelligent insights; CITADEL provides facts
- Can leverage CITADEL's historical data API

**Prerequisites**:
- CITADEL Milestone 2 (TimescaleDB historical data)
- Sufficient price history (~90 days minimum)
- Spike to assess if market has predictable patterns

**Rough scope**:
1. Feature engineering from CITADEL historical API
2. Model training pipeline (Python/scikit-learn)
3. Prediction endpoint for IRIS agent to consume
4. Confidence scoring and fallback to heuristics

**Status**: 🔮 Aspirational (post-MVP)

---

### ASP-002: Automated Strategy Optimizer (RL Agent)
**Type**: Reinforcement Learning | **Priority**: Future
**Origin**: CITADEL Epic 6 (removed from scope)

**Concept**: RL agent that learns optimal fleet allocation and operation strategies.

**Why IRIS (not CITADEL)**:
- Strategy is intelligence, not automation
- IRIS is the "brain"; CITADEL is the "hands"
- Agent can suggest to user; user decides to execute

**Prerequisites**:
- ASP-001 working (price predictions inform rewards)
- CITADEL profitability calculators stable
- Environment simulator for safe training (no real fleets)

**Rough scope**:
1. Design state/action/reward spaces
2. Build simulator using CITADEL APIs
3. Train with Stable-Baselines3 (DQN or PPO)
4. Shadow mode: suggest but don't execute
5. User approval gate before any real actions

**Status**: 🔮 Aspirational (post-MVP, post ASP-001)

---

## Action Items

1. [ ] **Create spike blueprint** for Chatterbox integration
2. [ ] **Decompose task_1_2_3** (prepareTransaction) before implementation
3. [ ] **Decompose task_1_3_3** (subscribeToFleetUpdates) before implementation
4. [ ] **Decompose task_4_3_3** (latency monitoring) before implementation
5. [ ] **Set up monitoring** for external API availability
6. [ ] **Coordinate with CITADEL** on API timeline and contract validation
7. [ ] **Create mock API** responses for CITADEL endpoints (task_8_1_3)
8. [ ] **Spike ASP-001** after CITADEL historical data available (assess prediction feasibility)

---

**Note**: Update this file as issues are resolved or new ones discovered.
