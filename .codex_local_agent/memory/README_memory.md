# README_memory.md

This folder holds durable memory ledgers for the local Codex agent. All files are append-only so we can reconstruct decisions and ensure auditability.

- `bank_core.jsonl` stores long-term governance truths and canonical rules referenced across sessions.
- `logic_inbox.jsonl` mirrors the active task queue that enumerates every unmet Required-Updates item.

Every file written here must preserve history; never truncate existing content.
