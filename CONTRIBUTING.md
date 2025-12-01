# Contributing to IRIS

> **Purpose**: Workflow guide for development
> **Lifecycle**: Stable (update when processes change)

---

## Git Workflow: Worktrees (NOT Branch Switching)

**Why worktrees?** Multiple Claude Code agents on the same machine cause conflicts when switching branches. A Git repo has one HEAD - multiple terminals switching branches corrupts state. Worktrees provide isolated directories sharing the same `.git` objects.

### Start Feature Work

```bash
# From main repo directory
cd /home/x-forge/repos/iris

# Create worktree for new feature
git worktree add ../iris--mcp-server feature/mcp-server

# Work in the isolated directory
cd ../iris--mcp-server

# Now you can work without affecting main repo
pnpm install
pnpm dev
```

### During Work

```bash
# Commit as normal (in worktree directory)
git add .
git commit -m "feat: add MCP server foundation

Relates to #42"

git push -u origin feature/mcp-server
```

### Complete Work

```bash
# Create PR from worktree
gh pr create --base main --title "feat: MCP server foundation"

# After PR merged, clean up
cd /home/x-forge/repos/iris
git worktree remove ../iris--mcp-server
git branch -d feature/mcp-server  # if merged
```

### Parallel Agent Work

Multiple Claude Code agents can work simultaneously:

```
Terminal 1: /home/x-forge/repos/iris (main branch)
Terminal 2: /home/x-forge/repos/iris--mcp-server (feature/mcp-server)
Terminal 3: /home/x-forge/repos/iris--voice-service (feature/voice-service)
```

Each worktree is fully isolated - no checkout conflicts.

---

## Quick Reference

```bash
# List active worktrees
git worktree list

# Create worktree
git worktree add ../iris--<feature> feature/<feature>

# Remove worktree (after PR merged)
git worktree remove ../iris--<feature>

# Prune stale worktrees
git worktree prune
```

---

## Branch Strategy (Simple)

```
feature/* --> main (direct PRs)
```

- **main**: Production-ready code
- **feature/***: Development work (via worktrees)
- No dev/staging branch for now (keep it simple)

---

## Commit Format

**Pattern**: `<type>: <description>`

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Issue Linking** (REQUIRED):
- `Closes #42` - Closes on merge
- `Relates to #42` - References only

**Example**:
```
feat: add voice streaming

Implements WebSocket STT with <500ms latency.

Closes #42
```

---

## Progress Tracking

**Tool**: GitHub Issues (simple)

**Labels**:
- Type: `feature`, `bug`, `spike`
- Status: `in-progress`, `blocked` (only when needed)

**Start work**:
```bash
gh issue edit <N> --add-label "in-progress"
```

**Complete work**: Use `Closes #N` in commit message (auto-closes)

---

## Definition of Done

### Feature
- [ ] Implemented
- [ ] Tests passing (when applicable)
- [ ] Issue linked (`Closes #N`)
- [ ] PR merged to main

### Bug Fix
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Issue updated

---

**Last Updated**: 2025-12-01
