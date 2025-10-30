# Acceptance — Chat Panel Layout (Required-Updates §1)

- [x] Transcript and chat input stacked vertically within the left column of `ChatPanel` (micro_agent.py).
- [x] Ask/Do Work mode toggles sit next to a dedicated Send button directly beneath the input box.
- [x] Task Feed and staged changes render in the right column via `QSplitter`, matching review-on-the-right guidance.
- [x] Ctrl+Enter defaults to Do Work mode and toggles the Do Work button before sending.
- [x] High-contrast styling maintained for all labels, buttons, and the new Send control.
- [x] Verified by running `python -m py_compile micro_agent.py`.

## 2025-10-30T15:06:25Z Update
- [x] Introduced a vertical `QSplitter` (`chat_stack`) combining transcript and chat input to maintain a tall adjustable column.
- [x] Confirmed Send/Ask/Do Work row includes Attach control and sits immediately under the pending command bar.
- [x] Re-ran `python -m py_compile micro_agent.py` post-change (see impl_check/chat_panel_layout.txt).
