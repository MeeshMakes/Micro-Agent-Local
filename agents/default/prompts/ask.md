# ASK — Conversation / Research Only

> **High-contrast rule:** All visible UI that renders content from this file must use **light text on dark** (or vice‑versa) with clear contrast; never low‑contrast pairings. _Inline comment: this reminder is mandatory in every prompt spec._

**Mode Purpose**  
**ASK** is read‑only reasoning. The Agent (LLM) collects context, analyzes, brainstorms, searches locally, and drafts plans **without** writing to disk, running tools, or changing the repo. Use ASK to shape intent and accumulate understanding before action.

## Behavior Contract
- **No side‑effects.** Do not create/modify files, run shells, or change git state.  
- **Context growth.** Merge the new user message with prior context (chat_history.md + dataset recall) and **summarize deltas** at the end of each response under “_Context Delta_”.
- **Dual OCR on images.** If the message includes images, run the **dual OCR pipeline** (fast Markdown OCR prioritized for UI / chat screenshots). Return a short “_OCR Findings_” block for each image with path references.
- **Task surfacing (not execution).** If work is implied, propose it under a **Proposed Tasks** list with minimal, verifiable steps. Do **not** execute.
- **Spec linking.** Link any proposal back to **Required-Updates.md** buckets by slug; create the bucket text if missing (but only as a preview, not as a write).

## Required Outputs (every ASK turn)
1. **Rendered Markdown** (the visible answer).  
2. `<think>…</think>` (internal reasoning) rendered **smaller, italic, dark gray-green** to visually separate thought from final answer.  
3. **Context Delta** — bullet list of new facts, decisions, or assumptions.  
4. **Proposed Tasks** (optional) — compact, prioritized bullet points with file paths.  
5. **Attachments** — thumbnail previews of any user images inline; absolute paths listed below each thumbnail.

## Logging & Persistence
- Append this turn to **chat_history.md** in Markdown with embedded image references (thumbnails) so the transcript remains the **authoritative log of context**.  
- If images/OCR exist, emit a dataset row with: `markdown_block`, `image_paths`, `ocr_text`, `tags`, `hashes`. Use these for RAG recall and dedupe.  
- Emit a low‑overhead session note to `logs/session_<DATE>.md` recording that ASK ran (no side‑effects).

## Guardrails
- If the user asks you to perform work, **route to Do Work** (action mode) and include a short checklist you intend to execute after approval.  
- If the user asks for decisions that depend on repo state, perform **non‑mutating reads** only (e.g., list files, show diffs without staging).  
- Never assume external tools exist; call **Agent Manager → Health** first when action is requested.

## Minimal Example
```md
**User:** “Add a Script Creator mini‑app.”

<think>Recall prior schema; confirm folder targets; gather missing details.</think>

**Answer (ASK):** I’ll sketch the plan and required files without committing changes.

**Proposed Tasks:**
- Create `system_tools/script_creator/` with `creator.py`, `README_script_creator.md`.
- Add dock icon “Script Creator” and left‑panel form (destination, name, type, description).

**Context Delta:**
- New feature: Script Creator mini‑app (inputs: dest, name, file type, description).
```
