# DO WORK — Autonomous Execution

> **High-contrast rule:** UI controls driven by this spec (Allow / Skip / Try Harder / Edit) must visibly indicate state; **Allow** flashes blue when approval is needed. Inline reminder: _never low-contrast text_.

**Mode Purpose**  
**DO WORK** is action mode. The Agent is allowed to propose, plan, and execute changes **with human gating**. It must keep a clear audit trail and update the “trifecta”: Required‑Updates (desired), README (current truth), Implemented/Quarantined/Missing (status).

## Baseline Pipeline
1. **Parse** `Required-Updates.md` → find relevant, still-missing items (bucket by slug).  
2. **Emit stubs** to `memory/logic_inbox.jsonl` for each item; pop highest-priority stub.  
3. **Plan & seek approval**: render the exact command(s)/edits; wait for **Allow** unless **Always Allow** is active.  
4. **Execute** changes in the repo (batch if multi‑file), creating or updating files atomically.  
5. **Update status docs**:  
   - `Implemented-Updates.md` (success)  
   - `Quarantined-Updates.md` (blocked/denied; include required approval text)  
   - `Missing-Updates.md` (still absent items)  
6. **Roll logs**: `logs/session_<TODAY>.md`, `docs/changes/CHANGELOG.md` (human‑readable summary).  
7. **Maintain macro archive**: `system_tools/system_macros/store.jsonl` — add helpful snippets; enforce TTL/beans; dedupe.  
8. **Spec Verification Block**: regenerate the block at the end of `Required-Updates.md` listing any unimplemented items, or declare:  
   `All implemented, 2025-10-30 01:24:48`  
9. **Promote Rant**: if `rant_feed.md` has new entries, convert coherent items into new Required‑Updates buckets and queue stubs.

## Approval Bar (Pending Command UI)
- **Allow**: execute immediately; record approval source and scope.  
- **Skip**: reject and clear; add a brief note to `Quarantined-Updates.md`.  
- **Try Harder**: regenerate plan with stronger tactics (see `try_harder.md`), then re‑stage.  
- **Edit**: switch input into purple edit mode; the edited text becomes the new pending command.

## Safety & Boundaries
- Respect `safe_write_outside_repo=False` unless user has explicitly granted scope.  
- Show diffs before write; stage commits with precise messages and paths.  
- Never drop context; preserve chat → plan → execution lineage in logs.

## Example Execution (abbrev)
```text
Task: Add Agent Manager mini-app.
Plan: Create agents/manager/{ui.py, README_manager.md}; wire dock icon + left panel; expose authority, datasets, pending pipeline.
Approval: ALLOW
Result: Files written, README updated, Implemented-Updates.md appended, macros saved.
```
