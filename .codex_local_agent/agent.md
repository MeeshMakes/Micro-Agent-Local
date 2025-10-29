# Local Agent Overview

- Provider: offline-ollama
- Default model: gpt-oss:20b
- Behavior: can draft file edits and propose shell commands.
- Policy: will not run commands or write outside repo without approval.
- High contrast rule: display as bright text on a dark background.

## Required-Updates Sync Loop (MANDATORY)
1. Before editing any file, reread this document and `Required-Updates.md` so the current obligations are fresh.
2. Parse `Required-Updates.md` to enumerate missing features and process gaps.
3. Ensure `memory/logic_inbox.jsonl` includes a task stub for every gap discovered. Create the folder/file if missing.
4. Prioritize the most critical stub, implement the work, and update both `docs/changes/CHANGELOG.md` and `docs/codex-local/required_updates_progress.md` with the outcome (`✅` done, `⏳` in progress, `🔒` blocked).
5. After implementing a stub, re-read `Required-Updates.md` to confirm no new obligations appeared. Repeat the loop until all items are satisfied.
6. Maintain high-contrast UI and document any new environment variables or routes when adding functionality.

## Operational Notes
- Always prefer deterministic, inspectable local operations.
- Document safety policies and approval gates alongside any automation changes.
- Keep OCR and dataset logging paths up to date when new assets are introduced.
