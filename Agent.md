# Local Codex Agent Contract

## Sync Loop
1. Re-read `Agents.md`, `Required-Updates.md`, and ledger files (`Implemented-Updates.md`, `Missing-Updates.md`).
2. Select the next unmet requirement from `Required-Updates.md` only.
3. Begin work immediately; no parallel scopes. Capture a start entry in `.codex_local_agent/memory/logic_inbox.jsonl`.
4. Implement the requirement with additive, high-contrast, offline-first code.
5. Append completion entry to the logic inbox, update changelog, progress ledger, session log, and persistent memory.
6. Run acceptance and implementation checks for the scope; remediate until green.
7. Loop back to step 1 until all requirements are ✅, then update `Required-Updates.md` Implementation Check footer.

## Append-only Logging
- Never delete or rewrite historical lines in ledgers or logs.
- Record worklog entries in both `.codex_local_agent/memory/logic_inbox.jsonl` and `memory/logic_inbox.jsonl`.
- Maintain chronological append-only files: `docs/codex-local/required_updates_progress.md`, `docs/changes/CHANGELOG.md`, `logs/session_<DATE>.md`, and `chat/sessions/<DATE>/chat.md`.
- Use UTC ISO timestamps for all new entries.

## Acceptance Tracking
- For each completed requirement, create or refresh a file under `.codex_local_agent/acceptance/` summarizing verification steps and results.
- Mark blocked items with rationale inside the acceptance note and in the progress ledger.
- Store durable truths or constraints related to acceptance in `.codex_local_agent/memory/bank_core.jsonl`.

## Implementation Check Discipline
- House scope-specific validations in `.codex_local_agent/impl_check/` (scripts, configs, reports).
- After running validation, update `Implemented-Updates.md` with evidence links and status.
- If checks fail, remain on the same requirement until all tests are passing; log the failure in `docs/codex-local/required_updates_progress.md` as ⏳ with context.
