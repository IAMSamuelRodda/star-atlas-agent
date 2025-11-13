# Project Status

> **Purpose**: Current work, active bugs, and recent changes (2-week rolling window)
> **Lifecycle**: Living (update daily/weekly during active development)

**Last Updated**: 2025-11-13
**Current Phase**: Active Development
**Version**: 0.1.0 (Pre-MVP)

---

## Quick Overview

| Aspect | Status | Notes |
|--------|--------|-------|
| Planning | =� | Blueprint complete, 133 issues created |
| Architecture Docs | =� | All core docs complete (ARCHITECTURE.md, VISION.md, etc) |
| Infrastructure | =� | Terraform, Lambda, DynamoDB, API Gateway, S3, CloudFront |
| CI/CD Pipeline | =� | 5 workflows (auto-merge, staging/prod deploy, E2E, security) |
| Auth Service | =� | Magic link + wallet auth + profiles complete |
| Test Coverage | =� | Infrastructure in place, tests needed |
| Known Bugs | =� | None yet |

**Status Guide:** =� Good | =� Attention | =4 Critical | =5 In Progress

---

## Current Focus

**Completed Today/This Week:**
-  Vision alignment session (docs/planning-session-2025-11-12.md)
-  Archive mining: galactic-data wisdom extracted
-  Competitive analysis: EvEye feature comparison
-  AWS Free Tier constraints documented (serverless + DynamoDB pattern)
-  Base documentation structure initialized (CLAUDE.md, README.md, STATUS.md)
- ✅ Persistent memory architecture researched (DynamoDB vector store for RAG)
- ✅ Personalization requirements defined (colleague → partner → friend progression)
- ✅ Trust-building visualization strategy documented
- ✅ Complete base documentation (ARCHITECTURE.md, CONTRIBUTING.md, DEVELOPMENT.md, CHANGELOG.md)
- ✅ Generate BLUEPRINT.yaml using `blueprint-planner` subagent
- ✅ Create GitHub issues from blueprint (133 issues: 10 epics, 34 features, 89 tasks)
- ✅ **Star Atlas API Research Spike Complete** (Issue #141)
  - ADR-001: Hybrid data sourcing strategy (Galaxy API + Solana RPC)
  - Data inventory: 10+ data types cataloged with TypeScript interfaces
  - Cost analysis: 91% reduction ($45/month → $4/month)
  - Implementation plan: 4 phases over 2 weeks
- ✅ **Star Atlas Deep Research Phase Complete** (2025-11-13)
  - z.ink Integration: Dec 2025 launch, zProfile eliminates transaction friction
  - Unreal Engine/F-Kit: SAGE AI competitor identified, 1,590 txs/day friction quantified
  - Governance: DAO structure analyzed, Ecosystem Fund grant opportunity ($2.5k-$7.5k)
  - Tokenomics: ATLAS/POLIS/SOL economics documented, $1.37M annual DAO accrual
  - Competitors: ATOM & SLY analysis, market gap identified (no AI/voice/optimization)
  - EvEye Deep Dive: Comprehensive data platform, no public API, self-hosted wins (99.3% cheaper)
  - Historical Backfill Analysis: Live collection wins ($24 vs $124), 6 months sufficient for MVP
  - RPC Provider Analysis: Helius Developer tier selected ($49/month), 19 Star Atlas programs cataloged
  - Star Frame Analysis: Critical for Phase 2+ (on-chain agent NFT ownership, dynamic memory)
  - Portable Agent Architecture: NFT-based ownership model, users own personality (sell/transfer)

**In Progress:**
- 🔧 Auth service improvements (PR #143)
  - Schema migration (userId as primary key)
  - Rate limiting middleware
  - Structured logging
  - Security hardening

**Recently Completed (2025-11-13):**
- ✅ Epic #1 - Foundation & Infrastructure (Issues #1-15)
  - Terraform AWS infrastructure
  - CI/CD pipeline with 5 workflows
  - Monorepo structure with pnpm workspaces
- ✅ Epic #2 - Authentication System (Issues #16-24)
  - Email magic link authentication
  - Wallet signature challenge
  - User profile management (DynamoDB)
  - JWT utilities and auth middleware
- ✅ Web app wallet connection components (partial)
- ✅ IDE crash recovery + codebase audit
- 🚧 Auth service improvements (PR #143 - pending review)

**Next Up:**
- [ ] Add test coverage for auth-service
- [ ] Choose next epic: Memory Service, Agent Core, or MCP Server
- [ ] Continue web-app frontend development

---

## Deployment Status

### Development
- **Status**: Not deployed
- **URL**: N/A
- **Last Deployed**: Never

### Staging
- **Status**: Not deployed
- **URL**: N/A
- **Last Deployed**: Never

### Production
- **Status**: Not deployed
- **URL**: N/A
- **Last Deployed**: Never

---

## Known Issues

### Critical
None

### High Priority
**Workflow Violation**: Recent commits (b347adb, 7c214a8, c90f3b1, a3e16ce, 96cab13) were made directly to `dev` instead of using feature branches and PRs. This violates CONTRIBUTING.md guidelines. All future work must follow the proper workflow:
  1. Branch from dev
  2. Make changes on feature branch
  3. Create PR to dev
  4. Merge after review

### Medium Priority
**Auth Service Issues** (Post-implementation review 2025-11-13, fixes in PR #143):
1. **Missing Tests**: Zero test coverage (no .test.ts or .spec.ts files exist)
   - ⏳ **Status**: Deferred to follow-up task
2. ✅ **Data Model Issue**: Fixed in PR #143
   - Migrated Users table to use `userId` as primary key
   - Added EmailIndex GSI for email lookups
   - Removed placeholder emails (email now optional)
3. ✅ **Security Gaps**: Fixed in PR #143
   - Added rate limiting middleware (3 req/min for magic links)
   - Consistent email normalization (lowercase + trim)
4. ✅ **Missing Observability**: Fixed in PR #143
   - Added structured JSON logging utility
   - CloudWatch Logs Insights compatible

### Low Priority
None

---

## Recent Achievements (Last 2 Weeks)

**Vision & Planning Session** 
- Completed: 2025-11-12
- Established multi-user SaaS scope with voice-first interface
- Defined AWS Free Tier architecture (<$10/month MVP)
- Documented strategic differentiation from EvEye (AI insights vs data viz)
- Extracted wisdom from galactic-data archives (Solana integration patterns)

---

## Next Steps (Priority Order)

1. **Complete Base Documentation**
   - ARCHITECTURE.md with tech stack, database schema, ADRs
   - CONTRIBUTING.md with GitHub workflow
   - DEVELOPMENT.md with git branching, pre-commit checklist
   - CHANGELOG.md with Keep a Changelog format

2. **Generate Project Blueprint**
   - Use `blueprint-planner` subagent to create specs/BLUEPRINT.yaml
   - Validate complexity with `improving-plans` skill
   - Ensure AI-adjusted timeline estimates (20x human speedup)

3. **Set Up GitHub Infrastructure**
   - Create GitHub issues from blueprint
   - Configure project boards
   - Set up branch protection rules (dev � main only)
   - Initialize CI/CD workflows

4. **Begin Implementation**
   - MCP server first (Solana + Star Atlas data access)
   - Agent core (Claude Agent SDK integration)
   - Voice service (WebRTC + Whisper + ElevenLabs)
   - Web app (React + Vite frontend)

---

## Open Questions

**Resolved during planning:**
1. ~~Architecture pattern?~~ � Serverless + DynamoDB (AWS Free Tier)
2. ~~Price monitoring strategy?~~ � Secondary feature (context for AI, not charting)
3. ~~Target users?~~ � Multi-user SaaS

**Still pending:**
1. **Voice UX**: Push-to-talk vs always-listening? (Recommend PTT for MVP - simpler, lower cost)
2. **Authentication**: Wallet-based (Solana) vs traditional (email)? (Recommend both - wallet for on-chain, email for notifications)
3. **Subscription tiers**: Free tier limits? (Recommend: Free = 5 fleets, Pro = unlimited)
4. **Market data frequency**: How often refresh prices? (Recommend: 5-min like EvEye for MVP)
5. **Alert delivery**: Voice-only vs also push notifications/email? (Recommend: Multi-channel for MVP)

**Decision point**: Resolve during blueprint creation or defer to implementation?

---

**Note**: Archive items older than 2 weeks to keep document focused.
