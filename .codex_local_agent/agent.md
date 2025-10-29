# Local Agent Overview

- Provider: offline-ollama
- Default model: gpt-oss:20b
- Behavior: can draft file edits and propose shell commands.
- Policy: will not run commands or write outside repo without approval.

High contrast rule: display as bright text on a dark background.

## Required-Updates Sync Loop (MANDATORY)

1. Before touching the repo, reread this Agent overview and `Required-Updates.md` so work aligns with the latest directives.
2. Extract any unmet requirements and append structured stubs into `memory/logic_inbox.jsonl` with clear titles, scope, and links back to the relevant Required-Updates bucket IDs.
3. Prioritize outstanding stubs, then implement the highest-impact items during each execution pass.
4. After implementing a stub, update both `docs/changes/CHANGELOG.md` and `docs/codex-local/required_updates_progress.md` with status markers (✅ shipped, ⏳ in-progress, 🔒 blocked).
5. Maintain cross-file traceability: each implementation record must cite the originating Required-Updates bucket and the stub identifier from `memory/logic_inbox.jsonl`.
6. When all stubs tied to a bucket are complete, mark that bucket as satisfied inside the progress tracker and, if needed, update `Required-Updates.md` with a note referencing the closing work.
7. Repeat this loop every session so the repository state, documentation, and planning artifacts remain synchronized.
