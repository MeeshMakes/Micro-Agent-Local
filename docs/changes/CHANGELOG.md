# Changelog

## 2025-10-29
- Added Required-Updates sync loop scaffolding and tracking artifacts (Required-Updates bucket RU-sync, stub STUB-20251029-00).
## 2025-10-30T11:52:26Z — Control directories initialized
- Created mandatory `.codex_local_agent` subdirectories (memory, acceptance, diffqa, impl_check, config/overrides, chat/sessions) with README guides per Required-Updates.md Global Agent Operations §A.
- Mirrored `memory/logic_inbox.jsonl` into `.codex_local_agent/memory/logic_inbox.jsonl` and appended control-task stub.
- Established daily session logging (`logs/session_2025-10-30.md`) and chat transcript scaffolding satisfying the high-contrast requirements.
- Added README files to new and existing directories to uphold the repository documentation invariant.
- Appended the Spec Verification Block template with live status at the end of Required-Updates.md.

## 2025-10-30T14:07:50.687234+00:00 — Chat panel vertical layout overhaul
- Reorganized the chat interface to use a tall left column combining transcript and input, with Task Feed and staged changes stacked to the right for quick review (micro_agent.py).
- Added Ask/Do Work mode toggles next to a new Send button near the message box so send intent is explicit and high-contrast, as required by Required-Updates.md §1.
- Ensured pending command, brain selector, and attachment controls sit under the chat block while preserving high-contrast styling and shortcut behavior.

## 2025-10-30T15:05:57+0000 — Chat layout splitter + inline mode row refresh
- Added a vertical splitter to keep transcript and input locked as a tall column, matching Required-Updates.md §1 geometry (micro_agent.py).
- Grouped Send, Ask, Do Work, and Attach controls into one row directly under the chat box for compliant intent selection.
- Left pending command, brain selector, and automation buttons stacked below the chat block to maintain high-contrast control flow.

## 2025-10-31T00:06:52+00:00 — Dataset buckets and diff memory
- Introduced an append-only `BucketStore` that versions chat directives, records superseded status, and emits diff artifacts under `.codex_local_agent/memory/buckets`.
- Linked chat logging to the bucket store so dataset entries carry `bucket_id` tags alongside dual OCR hashes for offline RAG (`micro_agent.py`).
- Updated dataset logging to include sanitized, deterministic tags and bucket references, fulfilling Required-Updates.md §2.2–§2.5.
## 2025-10-31T01:02:22+0000 — Mini-app dock arrow and Script Creator bootstrap
- Reworked the mini-app dock with labeled high-contrast buttons, a slide-out arrow handle, and splitter sizing so panels collapse when inactive yet reopen reliably, meeting Required-Updates.md §§3.1–3.3.
- Expanded the Script Creator mini-app to enforce project naming, honor Desktop shortcuts, scaffold `.codex_local_agent` with agent.yaml/agent.md/log/dataset assets, and guard overwrites with previews per Required-Updates.md §4.
