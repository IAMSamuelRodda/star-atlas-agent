# Memory Architecture - IRIS

**Date**: 2025-11-12 (Updated: 2025-12-02)
**Status**: Architecture Defined → Ready for Implementation
**Cost Impact**: $0/month incremental (SQLite on existing VPS)

---

## Executive Summary

**Vision**: Build a personalized AI agent with persistent memory and organic relationship development through shared experiences.

**Solution**: SQLite-based knowledge graph (pip-by-arc-forge pattern) with entities, observations, and relations - NOT vector embeddings.

**Cost**: ~$0/month incremental (VPS-hosted SQLite).

**Key Principle**: Relationship develops organically through accumulated observations, NOT XP-based progression systems.

---

## Architecture Decision

### Why Knowledge Graph (Not Vector Embeddings)

| Approach | Cost | Complexity | Retrieval | Chosen? |
|----------|------|------------|-----------|---------|
| **Knowledge Graph** | $0/mo | Simple | Structured queries | ✅ **YES** |
| Vector Embeddings | $20-30/mo | Moderate | Semantic similarity | ❌ No |
| RAG + Embeddings | $30-50/mo | Complex | Hybrid | ❌ No |

### pip-by-arc-forge Pattern

**Reference Implementation**: The pip-by-arc-forge project demonstrates a proven SQLite knowledge graph pattern:

**Core Tables**:
- `entities` - Nodes (users, fleets, starbases, resources)
- `observations` - Facts about entities (preferences, decisions, context)
- `relations` - Connections between entities (owns, stationed_at, prefers)

**Benefits**:
- Zero cost (SQLite file-based)
- Simple queries (SQL, not vector math)
- Human-readable data (easy debugging)
- Structured retrieval (query by entity type, relation)
- No external dependencies (no embedding API calls)

**Performance**:
- Query latency: <50ms (indexed SQLite)
- Storage: ~1KB per observation
- Scale: Handles 100K+ observations easily

---

## Three-Tier Memory Architecture

### 1. Session Memory (In-Memory)
**Purpose**: Current conversation context
**Storage**: Node.js process memory (ephemeral)
**Lifetime**: Duration of voice/chat session
**Size**: Last 10-20 messages (~5-10KB)
**Cost**: $0

**Example**:
```
User: "Check my fleet status"
Agent: "You have 3 fleets..."
User: "Focus on Fleet Alpha"  ← Agent remembers "Fleet Alpha" from context
```

### 2. Recent Conversations (SQLite, TTL)
**Purpose**: Full conversation history for context continuity
**Storage**: SQLite `conversations` table with 48-hour cleanup
**Lifetime**: 48 hours (then observations extracted, conversation deleted)
**Size**: ~50KB per user (recent conversations)
**Cost**: $0

**Example**:
```
Monday 10am: "I'm low on fuel at Starbase X"
Monday 8pm: Agent: "You mentioned fuel issues earlier - want me to check Starbase X again?"
```

### 3. Knowledge Graph (SQLite, Permanent)
**Purpose**: Persistent observations, preferences, relationships
**Storage**: SQLite tables (entities, observations, relations)
**Lifetime**: Permanent
**Size**: ~10KB per user (grows with interactions)
**Cost**: $0

**Tables**:
- `entities`: User, fleets, starbases, resources
- `observations`: Facts learned ("Sam prioritizes fuel efficiency")
- `relations`: Connections ("Sam owns Fleet Alpha")

**Example**:
```sql
-- Query user preferences for route planning
SELECT observation FROM observations
WHERE entity_id = 'user_sam'
AND observation LIKE '%route%' OR observation LIKE '%fuel%';

-- Result: "Prioritizes fuel efficiency over speed"
-- Result: "Prefers scenic routes even if slower"
```

### Game Knowledge (Static JSON)
**Purpose**: Star Atlas game mechanics (not per-user)
**Storage**: JSON files bundled with application
**Lifetime**: Updated with game patches
**Size**: ~100KB (crafting recipes, starbase data)
**Cost**: $0

**Note**: Game knowledge is NOT in the database - it's static reference data loaded at startup.

---

## Trust-Building Visualization Strategy

### Core Principle
**Voice-first, visualizations secondary** - BUT available when user asks "why?"

### Visualization Types

#### 1. Reasoning Transparency (High Priority)
**When**: User asks "why did you recommend X?"

**Show**:
- Decision tree visualization
- Weighted factors (cost, time, risk, user preferences)
- Data sources used (market prices, user history, game mechanics)

**Example**:
```
User: "Why Route A?"
Agent (voice): "Route A saves 20% fuel, which matches your efficiency preference"
Agent (visual): [Bar chart showing fuel cost comparison + user preference weight]
```

#### 2. Fleet Status Dashboard (Medium Priority)
**When**: User asks for fleet status or detailed view

**Show**:
- EvEye-level detail (fuel %, cargo, location, health)
- Historical trends (fuel consumption over time)
- Predictive alerts ("Fuel depletes in 2 hours")

**Not primary UI** - available on request, not pushed

#### 3. Market Context (Low Priority)
**When**: User asks about prices or market conditions

**Show**:
- Price charts (simple, not EvEye-level complexity)
- "Agent's view": What data influenced the recommendation

**Example**:
```
User: "Should I sell titanium now?"
Agent (voice): "Wait 2 days - price trend suggests 15% increase"
Agent (visual): [Simple price trend line + agent's prediction overlay]
```

---

## Knowledge Graph Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interaction                        │
│                  (Voice/Text via Web App)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Agent Core (Node.js on VPS)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Classify query intent                            │  │
│  │  2. Query knowledge graph for relevant context       │  │
│  │  3. Augment prompt with observations & relations     │  │
│  │  4. Generate response (Claude Agent SDK)             │  │
│  │  5. Extract new observations (async)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────┬─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Knowledge Graph (Memory)                 │
│  ┌─────────────────────────┬────────────────────────────┐  │
│  │  conversations          │  entities / observations / │  │
│  │  (48-hour TTL)          │  relations (permanent)     │  │
│  ├─────────────────────────┼────────────────────────────┤  │
│  │ Recent messages         │ User preferences           │  │
│  │ Context threads         │ Fleet configurations       │  │
│  │ Raw transcripts         │ Decision patterns          │  │
│  └─────────────────────────┴────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

No embedding service needed - structured SQL queries only.
```

---

## Relationship Development (Organic, Not XP-Based)

**Core Principle**: IRIS's relationship with the user develops organically through shared experiences and accumulated observations - like a human relationship, NOT an XP/leveling system.

**Inspiration**: Halo's Cortana - Master Chief's intelligent AI companion. The bond grows through adventures together, not through explicit progression mechanics.

**How It Works**:
- Relationship depth emerges naturally from knowledge graph richness
- More observations = deeper understanding = more personalized interactions
- No explicit "trust score" or "friendship level" shown to user
- Agent naturally becomes more helpful as it learns user preferences

**Example**:
```
Early interaction:
Agent: "Would you like me to check your fleet status?"

After many shared experiences:
Agent: "Sam, Fleet Alpha is low on fuel again - I know you hate running
out mid-route. Want me to plot a refuel stop at Starbase 7? It's on the
scenic route through Sector 9 that you like."
```

**Anti-Pattern (What We DON'T Do)**:
- ❌ "Trust Level: 47/100 - Unlock new features at level 50!"
- ❌ "Friendship XP: +10 for completing a trade"
- ❌ Explicit progression tiers (colleague → partner → friend)

---

## Cost Analysis

### VPS Architecture (Current)
- Digital Ocean 4GB droplet: $0 incremental (already provisioned)
- SQLite database: $0 (file-based)
- Chatterbox voice: $0 (self-hosted)
- Caddy reverse proxy: $0 (already running)
- **Total**: $0/month incremental

### Memory Cost Breakdown
- SQLite storage: $0 (included in VPS disk)
- Knowledge graph queries: $0 (local SQL)
- No embedding API calls: $0
- **Total Memory Cost**: $0/month

### Cost Comparison (Why We Chose Knowledge Graph)

| Approach | Monthly Cost | Notes |
|----------|--------------|-------|
| **Knowledge Graph (chosen)** | $0 | SQLite on VPS |
| Vector Embeddings (AWS) | $20-30 | Bedrock + DynamoDB |
| RAG + OpenSearch | $50-100 | Enterprise-grade |

### Scaling Costs (Future)

| Users | Architecture | Cost |
|-------|-------------|------|
| 0-500 | Current VPS | $0 incr |
| 500-2K | Upgrade to 8GB VPS | +$24/mo |
| 2K+ | Dedicated database server | +$50/mo |

---

## Scalability Path

### MVP (0-500 users)
- Single VPS + SQLite
- Knowledge graph queries <50ms
- Cost: $0 incremental

### Growth (500-2K users)
- Upgrade VPS to 8GB RAM
- SQLite with WAL mode for concurrent reads
- Cost: +$24/month

### Scale (2K-10K users)
- PostgreSQL on separate server
- Read replicas if needed
- Cost: +$50-100/month

### Enterprise (10K+ users)
- Managed PostgreSQL (Digital Ocean or AWS RDS)
- Connection pooling (pgBouncer)
- Consider horizontal sharding by user_id
- Cost: $200+/month

**Migration trigger**: When SQLite write contention causes >100ms latency

---

## Implementation Phases

### Phase 1: Knowledge Graph Schema (Week 1-2)
- [ ] SQLite schema (entities, observations, relations)
- [ ] better-sqlite3 integration
- [ ] Basic CRUD operations
- [ ] Session memory (in-memory context)

### Phase 2: Observation Extraction (Week 3-4)
- [ ] Claude Agent SDK + memory augmentation
- [ ] Conversation-to-observation pipeline
- [ ] 48-hour conversation TTL cleanup
- [ ] Basic personalization (name, preferences)

### Phase 3: Context Retrieval (Week 5-6)
- [ ] Query knowledge graph for relevant context
- [ ] Augment prompts with observations
- [ ] Test personalization quality

### Phase 4: Relationship Depth (Week 7-8)
- [ ] Measure observation richness
- [ ] Test organic relationship development
- [ ] User feedback on personalization

---

## Open Technical Questions

1. **Observation granularity**: How specific should observations be? (Test with real conversations)
2. **Context window**: How many observations to include in prompt? (Recommend 5-10 most relevant)
3. **Extraction timing**: Real-time vs batch extraction? (Recommend async after session ends)
4. **Privacy**: Memory retention policy for inactive users? (Recommend 90-day deletion)
5. **User control**: Should users be able to view/edit their observations? (Recommend read-only initially)

---

## Next Steps

1. **Implement knowledge graph schema**: Create SQLite tables (entities, observations, relations)
   - Follow pip-by-arc-forge pattern
   - Use better-sqlite3 for Node.js integration

2. **Build observation extraction**: Pipeline to extract facts from conversations
   - Use Claude to identify important observations
   - Store with entity references

3. **Integrate with agent**: Augment prompts with relevant observations
   - Query by entity type and context
   - Test personalization quality

---

**Status**: Architecture defined. Ready for implementation.

**Approach**: SQLite knowledge graph (pip-by-arc-forge pattern) with organic relationship development through accumulated observations.
