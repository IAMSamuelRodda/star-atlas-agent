# Issues & Flagged Items

> **Purpose**: Track items needing attention before/during implementation
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

## Action Items

1. [ ] **Create spike blueprint** for Chatterbox integration
2. [ ] **Decompose task_1_2_3** (prepareTransaction) before implementation
3. [ ] **Decompose task_1_3_3** (subscribeToFleetUpdates) before implementation
4. [ ] **Decompose task_4_3_3** (latency monitoring) before implementation
5. [ ] **Set up monitoring** for external API availability

---

**Note**: Update this file as issues are resolved or new ones discovered.
