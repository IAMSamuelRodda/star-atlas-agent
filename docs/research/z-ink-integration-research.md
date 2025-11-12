# z.ink Integration Research

**Date**: 2025-11-13
**Status**: Complete
**Related**: Epic #9 Research Spikes, Issue #116 (z.ink Integration Spike)

---

## Executive Summary

**z.ink** is a new Solana Virtual Machine (SVM) Layer 1 blockchain launching in **December 2025**, developed by ATMTA (Star Atlas' development studio). It introduces **zProfile**, a patent-pending zero-knowledge identity system that eliminates transaction friction in blockchain gaming while maintaining security.

### Key Findings

1. **No Public APIs Yet**: z.ink is in alpha testing phase; no public developer documentation or SDKs currently available
2. **Migration Timeline**: Star Atlas will fully migrate to z.ink mainnet in **Q1 2026** (March)
3. **PlayerProfile Primitive**: z.ink's zProfile builds on Star Atlas' existing `@staratlas/player-profile` package (v0.11.0)
4. **Integration Opportunity**: Consider deferring z.ink integration to **Phase 4** (post-MVP) until public APIs are available

---

## What is z.ink?

### Platform Overview

**z.ink** is an SVM Layer 1 blockchain designed specifically for high-performance gaming applications.

**Technical Architecture**:
- **Blockchain Type**: SVM (Solana Virtual Machine) Layer 1
- **Launch Date**: December 2025 (mainnet)
- **Native Token**: $ZINK
- **Transaction Throughput**: ~20 TPS initially
- **Transaction Costs**: **99% lower** than Solana

### Key Technical Features

**Foundation Kit & Starframe**:
- "Add SVM support to your UE5 game" capabilities
- **Starframe**: Upgraded Anchor framework for "more complex programs, less compute, fewer transactions"

**Developer Compatibility**:
- Mirrors Solana architecture for seamless developer migration
- Compatible with existing Solana development tools via SVM standardization

---

## zProfile: Zero-Knowledge Identity System

### Patent-Pending Technology

**zProfile** is ATMTA's patent-pending "player profile primitive" that provides:

1. **Global Permission Settings**: Configure permissions across connected dApps
2. **Automated Transaction Approvals**: Pre-approve transaction categories without manual confirmation
3. **Security Without Friction**: Maintains robust asset protection while eliminating high-frequency approval prompts

### Core Capabilities

**Web3 Single Sign-On**:
- Digital passport for cross-application authentication
- dApp permissioning without repeated transaction signatures

**Privacy Layer**:
- Zero-knowledge proof technology
- Optional KYC verification (binary verification—no data sharing)

**Gamification**:
- **zXP (z.ink Experience Points)**: Tracks player actions and converts them to XP
- Leveling system with progression rewards
- Airdrop allocation based on zXP accumulation

### How It Works

```
User Action (in-game, marketplace, staking)
    ↓
zProfile tracks action via ZK proofs
    ↓
Action converted to zXP
    ↓
zXP determines airdrop allocation + unlocks permissions
```

**Example Use Cases**:
- **Fleet Management**: Pre-approve fuel purchases, repair transactions
- **Marketplace Trading**: Auto-approve buy/sell orders within limits
- **Crafting**: Batch-approve material usage for recipes

---

## Star Atlas Integration with z.ink

### Migration Timeline

| Phase | Date | Description |
|-------|------|-------------|
| **A.LPHA Test** | Oct 30, 2025 - Dec 2025 | Closed alpha testing (access code required) |
| **O.RIGINS Airdrop Season** | Mid-Late Dec 2025 | 10% of $ZINK supply distributed based on user activity |
| **Genesis/Mainnet Launch** | March 2026 (Q1) | Full network launch + token generation event |
| **SAGE C4 Migration** | Q1-Q2 2026 | Star Atlas fully migrates to z.ink mainnet |

### Integration Strategy

**Seamless Migration**:
> "The team's ambition is to adapt the Port of Entry in SAGE Starbased so that when you move your assets out of Starbased, they are seamlessly migrated to C4 on z.ink, without any extra effort."

**Operational Integration**:
- z.ink dashboard fully runs on **StarComm v3** (upgraded middleware)
- All current and future Star Atlas game logic will run on z.ink network starting December

**Cost Benefit**:
- Eliminates deployment costs (ATMTA previously faced ~$40k expenses on Solana)
- Transaction fees "at least 99% lower" than Solana

---

## PlayerProfile Primitive (Current Solana Implementation)

### Package Details

**npm Package**: `@staratlas/player-profile`
**Version**: 0.7.3 (documentation), 0.11.0 (npm)
**Program Address**: `pprofELXjL5Kck7Jn5hCpwAL82DpTkSYBENzahVtbc9`

### Technical Architecture

**Core Concept**: Decentralized identity protocol that "decouples identity from signing keys" using a profile that stores multiple keys with associated permissions.

**Benefits**:
- Key rotation without identity change
- Role-based access control
- Multi-signature authority
- No Cross-Program Invocation (CPI) required for key validation

### Data Structures

#### Profile Account
```typescript
struct Profile {
  version: u8;                    // Version control
  auth_key_count: u8;             // Number of authentication keys
  auth_key_threshold: u8;         // Required signatures
  created_at: i64;                // Creation timestamp
  role_seq: u64;                  // Role sequence ID
  // ... additional fields
}
```

#### ProfileKey Structure
```typescript
struct ProfileKey {
  key: Pubkey;                    // Public key identifier
  scope: KeyScope;                // Operational scope
  expires_at: i64;                // Expiration (-1 = non-expiring)
  permissions: [u8; 8];           // Permission bitflags
}
```

#### Permission System

Bitflag-encoded permissions:
```typescript
const PERMISSIONS = {
  AUTH: 1 << 0,            // Authentication permission
  ADD_KEYS: 1 << 1,        // Can add keys to profile
  REMOVE_KEYS: 1 << 2,     // Can remove keys
  CHANGE_NAME: 1 << 3,     // Can change profile name
  // ... additional permissions
};
```

### Core Instructions (17 Total)

**Profile Management**:
- `createProfile`
- `addKeys`, `removeKeys`
- `adjustAuth`

**Role Operations**:
- `createRole`, `removeRole`
- `setRoleName`, `setRoleAcceptingMembers`
- `setRoleAuthorizer`

**Membership**:
- `inviteMemberToRole`, `acceptRoleInvitation`
- `joinRole`, `leaveRole`
- `addExistingMemberToRole`, `removeMemberFromRole`

**Identity**:
- `setName`

### PDA Derivation Examples

**PlayerName PDA**:
```typescript
const [playerNamePda] = PublicKey.findProgramAddressSync(
  [Buffer.from("player_name"), profilePubkey.toBuffer()],
  programId
);
```

**Role PDA**:
```typescript
const roleSeqIdBuffer = Buffer.alloc(8);
roleSeqIdBuffer.writeBigUInt64LE(BigInt(roleSeqId));

const [rolePda] = PublicKey.findProgramAddressSync(
  [Buffer.from("profile-role"), profilePubkey.toBuffer(), roleSeqIdBuffer],
  programId
);
```

---

## Relationship Between PlayerProfile and zProfile

### Evolution Path

```
Star Atlas PlayerProfile (Solana)
    ↓
Patent-Pending Enhancement (Zero-Knowledge Layer)
    ↓
zProfile (z.ink blockchain)
```

**Key Enhancements in zProfile**:

1. **Zero-Knowledge Proofs**: Privacy layer not present in current PlayerProfile
2. **Transaction Pre-Approval**: Automated transaction categories (gaming-specific)
3. **Cross-App Permissions**: Global permission settings across z.ink ecosystem
4. **Gamification Layer**: zXP tracking and leveling system
5. **Airdrop Integration**: Direct tie to $ZINK token distribution

### Compatibility Assumption

Since zProfile is built on the "player profile primitive," it likely maintains **backward compatibility** with existing PlayerProfile SDK:

```typescript
// Current @staratlas/player-profile usage (Solana)
import { readFromRPC } from '@staratlas/data-source';
import { PlayerProfile } from '@staratlas/player-profile';

const profile = await readFromRPC(connection, PlayerProfile, profilePubkey);

// Expected future usage (z.ink - SPECULATIVE)
import { readFromRPC } from '@z-ink/data-source'; // Hypothetical package
import { zProfile } from '@z-ink/profile'; // Hypothetical package

const zprofile = await readFromRPC(zinkConnection, zProfile, profilePubkey);
// zprofile.zXP, zprofile.level, zprofile.permissions, etc.
```

---

## Developer Resources & APIs

### Current Status (as of Nov 2025)

**No Public APIs Available**:
- z.ink is in **closed alpha testing** (access code required)
- No npm packages published for z.ink or zProfile
- No developer documentation at build.staratlas.com
- No GitHub repositories found for z.ink SDKs

### Expected Package Ecosystem (Speculative)

Based on Star Atlas' existing package structure, we can anticipate:

```typescript
// Existing Solana packages
@staratlas/sage              // v1.8.10 (8 days ago)
@staratlas/data-source       // v0.9.0 (8 days ago)
@staratlas/player-profile    // v0.11.0 (9 months ago)
@staratlas/galactic-marketplace
@staratlas/crafting
@staratlas/cargo
@staratlas/factory
@staratlas/score

// Anticipated z.ink packages (NOT YET PUBLISHED)
@z-ink/profile              // zProfile identity system
@z-ink/data-source          // RPC abstraction for z.ink
@z-ink/sage                 // SAGE game program on z.ink
@z-ink/permissions          // Permission management SDK
@z-ink/zxp                  // zXP tracking and leveling
```

### When Will APIs Be Available?

**Educated Guess**:

| Milestone | Expected Date | Developer Access |
|-----------|---------------|------------------|
| Alpha Testing | Oct 30 - Dec 2025 | Limited (access code) |
| **Mainnet Launch** | **Dec 2025** | **Public beta docs likely** |
| Full Migration | Q1-Q2 2026 | Stable APIs expected |

**Recommendation**: Monitor Star Atlas Discord (#💻┃community-developers) and build.staratlas.com for announcements.

---

## Integration Opportunities for Star Atlas Agent

### Option 1: Defer to Phase 4 (Post-MVP) ⭐ RECOMMENDED

**Rationale**:
- No public APIs currently available
- MVP timeline targets Q1 2026 (coincides with z.ink mainnet)
- Focus on proven Solana integration first (Galaxy API + SAGE SDK)

**Timeline**:
1. **MVP (Dec 2025 - Feb 2026)**: Build on Solana using existing SDKs
2. **Post-MVP (Mar 2026+)**: Integrate z.ink once APIs are stable

**Benefits**:
- ✅ Avoid dependency on unreleased platform
- ✅ Leverage stable, documented APIs (Galaxy API, SAGE SDK)
- ✅ Add z.ink features when they provide clear value

---

### Option 2: Early Adopter Integration (Higher Risk)

**If z.ink APIs become available before MVP launch:**

#### Potential Use Cases for Star Atlas Agent

**1. Seamless Transaction Approval**

**Problem**: Users must manually approve every fleet action (fuel, repair, cargo)

**zProfile Solution**:
```typescript
// Pre-approve transaction categories via zProfile
await zProfile.setPermissions(walletAddress, {
  autoApprove: {
    fuelPurchases: { maxAmount: 1000 }, // Auto-approve up to 1000 ATLAS
    repairCosts: { maxAmount: 500 },
    cargoBuySell: { maxAmount: 5000 },
  },
});

// Agent can now execute transactions without wallet prompts
await agentCore.executeTool('refuelFleet', { fleetId, amount: 800 }); // No prompt!
```

**User Experience**:
- Agent: "Your fleet is low on fuel. Refueling now..."
- *(Transaction executes automatically—no wallet popup)*
- Agent: "Fleet refueled. Resuming mining operations."

---

**2. Voice-First Workflow Automation**

**Scenario**: User gives voice command while driving fleet

**Without zProfile**:
```
User: "Buy 500 food and refuel fleet Alpha-7"
Agent: "Processing... Please approve the food purchase transaction."
*User must switch to wallet, approve*
Agent: "Now please approve the refuel transaction."
*User must approve again*
```

**With zProfile**:
```
User: "Buy 500 food and refuel fleet Alpha-7"
Agent: "Purchasing food and refueling... Done. Ready to depart."
*Zero wallet interactions*
```

---

**3. Trust Progression & Permission Tiers**

Integrate zProfile with our personality progression system:

| Trust Phase | zProfile Permissions |
|-------------|----------------------|
| **Colleague** (Days 1-7) | Manual approval required for all transactions |
| **Partner** (Days 8-30) | Auto-approve low-value transactions (<100 ATLAS) |
| **Friend** (31+ days) | Auto-approve fleet management (<1000 ATLAS), crafting, marketplace |

```typescript
// Update zProfile permissions based on trust score
async function updatePermissionsByTrust(trustScore: number, zProfileId: string) {
  if (trustScore >= 80) { // Friend tier
    await zProfile.setPermissions(zProfileId, {
      autoApprove: {
        fleetManagement: { maxAmount: 1000 },
        crafting: { maxAmount: 500 },
        marketplace: { maxAmount: 5000 },
      },
    });
  } else if (trustScore >= 50) { // Partner tier
    await zProfile.setPermissions(zProfileId, {
      autoApprove: {
        lowValue: { maxAmount: 100 }, // Only small transactions
      },
    });
  }
  // Colleague tier: no auto-approvals
}
```

---

**4. zXP Integration for Gamification**

Track agent usage and reward users:

```typescript
// Agent actions contribute to zXP
await zProfile.trackAction(walletAddress, {
  action: 'agent_assisted_crafting',
  value: 10, // zXP earned
});

// Display zXP progress in UI
const userZXP = await zProfile.getZXP(walletAddress);
console.log(`Your zXP: ${userZXP.current} / ${userZXP.nextLevel}`);
```

**User Benefit**: Agent usage contributes to $ZINK airdrop allocation

---

**5. Cross-App Permissions (Future)**

If z.ink becomes multi-game platform:

```typescript
// Single zProfile used across Star Atlas + other games
await zProfile.setGlobalPermissions(walletAddress, {
  starAtlas: { autoApprove: true, maxAmount: 1000 },
  otherGame: { autoApprove: false }, // Manual approval required
});
```

---

### Integration Architecture (Speculative)

```
┌─────────────────────────────────────────────────┐
│          Star Atlas Agent (MCP Server)          │
├─────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────┐ │
│  │  Solana Layer    │  │   z.ink Layer       │ │
│  │  (Current)       │  │   (Future)          │ │
│  ├──────────────────┤  ├─────────────────────┤ │
│  │ @staratlas/sage  │  │ @z-ink/profile      │ │
│  │ Galaxy API       │  │ @z-ink/sage         │ │
│  │ PlayerProfile    │  │ @z-ink/permissions  │ │
│  └──────────────────┘  └─────────────────────┘ │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Blockchain (Dual-Chain Support)         │
├─────────────────────────────────────────────────┤
│  Solana (current) ←→ z.ink (post-migration)     │
└─────────────────────────────────────────────────┘
```

**Hybrid Approach (During Migration Period)**:
- **Static Data**: Galaxy API (unchanged)
- **Real-Time Data**: Solana RPC → z.ink RPC (gradual migration)
- **Transactions**: PlayerProfile → zProfile (seamless upgrade)

---

## Cost-Benefit Analysis

### Costs of Early z.ink Integration

**Development Costs**:
- ⏱️ **Time**: 1-2 weeks additional development (SDK learning curve)
- 💰 **Risk**: APIs may change during beta period
- 🔧 **Maintenance**: Support both Solana + z.ink during migration

**Infrastructure Costs**:
- 🌐 **RPC Endpoints**: Need z.ink RPC provider (cost TBD)
- 📊 **Testing**: Alpha access codes may be limited

### Benefits of Early z.ink Integration

**User Experience**:
- ✅ **Friction Reduction**: Eliminate transaction approval prompts
- ✅ **Voice-First UX**: Seamless voice commands without wallet interruptions
- ✅ **Competitive Advantage**: First agent to support z.ink

**Airdrop Opportunity**:
- 💰 **zXP Rewards**: Agent usage contributes to $ZINK airdrop allocation
- 📈 **User Acquisition**: Market as "z.ink-native agent" for early adopters

### Recommendation: Defer to Post-MVP

**Rationale**:
1. **No Public APIs Yet**: Cannot build without documentation
2. **MVP Timeline Risk**: Adding z.ink increases scope + delays launch
3. **Migration Timeline Alignment**: z.ink mainnet (Dec 2025) ≈ MVP completion (Q1 2026)
4. **Proven Tech First**: Focus on stable Galaxy API + SAGE SDK for MVP

**Post-MVP Strategy**:
- **Phase 1 (MVP)**: Build on Solana with existing SDKs
- **Phase 2 (Post-MVP)**: Add z.ink integration when APIs are stable (Q1-Q2 2026)
- **Phase 3 (Optimization)**: Migrate fully to z.ink if transaction costs justify it

---

## Open Questions for Star Atlas Team

**If pursuing early integration, clarify:**

1. **API Availability**: When will public developer documentation be released?
2. **SDK Timeline**: Expected release date for `@z-ink/*` npm packages?
3. **Migration Path**: How will existing `@staratlas/*` packages transition to z.ink?
4. **RPC Providers**: Which RPC providers will support z.ink? (Helius, Alchemy, etc.)
5. **Cost Structure**: Exact transaction costs on z.ink vs Solana?
6. **PlayerProfile Compatibility**: Will existing PlayerProfile accounts migrate to zProfile?
7. **Alpha Access**: How to obtain access codes for testing?

**Where to Ask**:
- Star Atlas Discord: `#💻┃community-developers`
- Twitter/X: [@staratlas](https://x.com/staratlas), [@ATMTA_DA](https://x.com/atmta_da)
- Email: developers@staratlas.com (if available)

---

## Tokenomics & Governance (Context)

### $ZINK Token Distribution

| Allocation | Percentage | Purpose |
|-----------|-----------|---------|
| Ecosystem Growth | 65% | Airdrops, partnerships, developer grants |
| ATMTA Team | 20% | Core development team |
| z.ink Operations | 10% | Network operations team |
| Star Atlas DAO | 5% | Governance + validator revenue access |

### Airdrop Structure

**O.RIGINS Campaign** (Dec 2025 - Mar 2026):
- **10% of total supply** distributed based on:
  - SAGE gameplay activity
  - Token staking (ATLAS/POLIS)
  - Galactic Marketplace trading
  - zProfile engagement

**Agent Integration Benefit**: Agent-assisted actions could count toward user's zXP allocation

---

## References

### Official Documentation
- **Star Atlas Build Portal**: https://build.staratlas.com/
- **Player Profile API Docs**: https://build.staratlas.com/dev-resources/apis-and-data/player-profile
- **Star Atlas Discord**: `#💻┃community-developers`

### News & Analysis
- **Aephia z.ink Overview**: https://aephia.com/star-atlas/z-ink-everything-you-should-know/
- **PR Newswire Announcement**: https://www.prnewswire.com/news-releases/atmta-unveils-zink-302529945.html
- **EGamers.io Alpha Testing**: https://egamers.io/z-ink-begins-alpha-testing-ahead-of-zink-airdrop-season/

### npm Packages
- **@staratlas/player-profile**: v0.11.0 (Solana-based PlayerProfile)
- **@staratlas/sage**: v1.8.10 (SAGE game program)
- **@staratlas/data-source**: v0.9.0 (RPC abstraction)

### GitHub
- No public z.ink repositories found (as of Nov 2025)

---

## Conclusion

**z.ink represents a significant evolution** in blockchain gaming infrastructure, with **zProfile** poised to eliminate the transaction friction that currently hampers user experience.

**For Star Atlas Agent MVP**:
- ✅ **Defer z.ink integration to Post-MVP** (Phase 4)
- ✅ **Focus on proven Solana APIs** (Galaxy API + SAGE SDK)
- ✅ **Monitor z.ink mainnet launch** (Dec 2025) for API availability
- ✅ **Design architecture with z.ink compatibility in mind** (abstract blockchain layer)

**Post-MVP Opportunity**:
- Once z.ink APIs are public, add zProfile integration for:
  - Seamless transaction approvals
  - Voice-first workflows without wallet prompts
  - zXP gamification + airdrop rewards
  - Trust-based permission tiers

**Next Steps**:
1. ✅ Complete this research document
2. ⏭️ Update Issue #116 with findings
3. ⏭️ Update BLUEPRINT.yaml: Move z.ink integration to Post-MVP phase
4. ⏭️ Continue with Epic #1 (Foundation & Infrastructure)

---

**Last Updated**: 2025-11-13
**Research Completed By**: Claude Code Agent
**Status**: Research Complete - Ready for Decision
