# Implemented-Updates.md

(Agent-maintained checklist of completed work.)

## 2025-10-30T11:52:26Z — Global Agent Operations §A
- Task ID: repo-control-bootstrap
- Summary: Established canonical control directories, mirrored task queue, and initialized audit scaffolding required by Required-Updates.md Global Agent Operations §A.
- Evidence: docs/changes/CHANGELOG.md, docs/codex-local/required_updates_progress.md, logs/session_2025-10-30.md

## 2025-10-30T14:08:47.963598+00:00 — Chat Panel Layout (§1)
- Task ID: chat-panel-vertical
- Summary: Refactored ChatPanel to stack transcript and input on the left, moved Ask/Do Work toggles plus Send button under the message box, and relocated Task Feed + staged changes to the right column.
- Evidence: docs/changes/CHANGELOG.md, docs/codex-local/required_updates_progress.md, .codex_local_agent/acceptance/chat_panel_layout.md, .codex_local_agent/impl_check/chat_panel_layout.txt, logs/session_2025-10-30.md

## 2025-10-30T15:06:33+0000 — Chat Panel Layout Refinement (§1)
- Task ID: chat-panel-vertical
- Summary: Added a vertical splitter for transcript/input and grouped Attach, Send, Ask, and Do Work controls directly under the chat block to finalize geometry requirements.
- Evidence: docs/changes/CHANGELOG.md, docs/codex-local/required_updates_progress.md, .codex_local_agent/acceptance/chat_panel_layout.md, .codex_local_agent/impl_check/chat_panel_layout.txt, logs/session_2025-10-30.md

## 2025-10-31T00:06:52+00:00 — Dataset Buckets & OCR (§2)
- Task ID: dataset-bucket-store
- Summary: Added BucketStore versioning with supersession diffs, linked dataset rows to bucket_ids, and persisted dual OCR text/hashes per Required-Updates §2.
- Evidence: micro_agent.py, docs/changes/CHANGELOG.md, docs/codex-local/required_updates_progress.md, .codex_local_agent/acceptance/dataset_buckets.md, logs/session_2025-10-31.md
