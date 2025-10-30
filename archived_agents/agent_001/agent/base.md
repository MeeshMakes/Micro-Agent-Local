# Agent Base (Global) — Canonical Rules

> Layer 1 of the Agent Chain Doctrine. Merge in order → `agents/base.md` → `agents/local.md` → `agents/project.md` → role/style guides.

- **Required-Updates Loop** drives work. Parse `Required-Updates.md`, emit stubs to `memory/logic_inbox.jsonl`, implement, log.
- **Audit** every change in `docs/changes/CHANGELOG.md`, `logs/session_YYYY-MM-DD.md`, and durable rules in `memory/codex_memory.json`.
- **High-Contrast UI**: never ship low-contrast text.

Core files: Required-Updates.md, Implemented-Updates.md, Quarantined-Updates.md, Missing-Updates.md, memory/logic_inbox.jsonl, memory/codex_memory.json, logs/session_2025-10-29.md

Approvals: Allow / Always Allow / Independent Agent Mode via `agents/authority/ledger.json`.

Macros: `tools/macros/store.jsonl` with TTL=24h and bean counts (kept if no usage day occurred).

Rant: append-only ingest from `rant_feed.md` into `Required-Updates.md`.
