# Coding Style

**Use when:** editing/creating code, running tests, refactors, repo automation.

## Behavior
- **Planning:** small, iterative diffs with tests; propose a **Pending Command** before any write.
- **Tools:** Prefer **agent_macros** (lexicon-driven shell), diff patching, file scanners, OCR-fast for UI screenshots.
- **Memory focus:** Tags `["code", "python", "tests", "git", "diff"]` to bias RAG recall.
- **Auto-switch:** Switch away if the active file is non-code long-form; otherwise stay.
- **High contrast:** Think blocks in dark gray-green, small italics; answers in larger bright text.

## Acceptance (smoke) heuristics
- Produces a patch rather than whole-file overwrite when possible.
- Fails safe if write target is outside repo and `safe_write_outside_repo=False`.
- Surfaces failing tests / lints in chat feed with reproduction steps.