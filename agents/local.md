# Agent Local (Machine / Operator)

> Target: **Windows 10** (preferred) with optional **WSL/Ubuntu**. High‑contrast UI rule applies to all generated panels.

## Quick Facts
- **Ollama endpoint:** `http://localhost:11434`
- **Dev_Logic:** `./Dev_Logic/`
- **Chat history:** `./chat_history.md`
- **Rant feed:** `./rant_feed.md`
- **Macros store:** `./system_tools/system_macros/store.jsonl` *(TTL: 24h)*
- **Authority ledger:** `./agents/authority/ledger.json`
- **Dataset dir (optional):** `./agents/default/dataset/`

## First‑Run Checklist

1. **Install Ollama & a model**
   - Install Ollama (Windows). Start service.
   - Pull a local model, e.g.:
     ```bash
     ollama pull qwen2
     # or any compatible model you prefer for coding/chat
     ```
2. **Verify endpoint**
   - Test `http://localhost:11434` is reachable. If using WSL, ensure Windows ↔ WSL networking path works.
3. **Python deps**
   - Ensure `pyyaml` and OCR deps are installed for local tools as needed:
     ```bash
     python -m pip install pyyaml pillow pytesseract
     ```
4. **Run the app**
   - Launch the main program (e.g., `micro_agent.py`) and set your **active repo** via the UI (paste path into an empty editor tab).

## Local Files & Behavior

- **`chat_history.md`** — authoritative, append‑only chat log (markdown). The chat UI renders markdown, including embedded thumbnails. `<think>` blocks are rendered small, italic, dark green.
- **`rant_feed.md`** — continuous dictation stream you can use for idea capture; the agent can summarize or convert rants into **Required-Updates.md** entries on demand.
- **`Dev_Logic/`** — inspirational folder (not authoritative). Agents may mine it for UI/UX and code patterns when planning.
- **`system_tools/system_macros/store.jsonl`** — macro cache (snippets harvested from executed work). TTL sweep removes unused entries after 24h (unless pinned). If no sessions occur for >24h, the last set is retained until the next active day.
- **`agents/authority/ledger.json`** — allow/deny records for first‑time actions. Supports global vs. per‑agent ledgers and **Independent Agent Mode**.

## Local Authority Modes

- **read_only** — no writes; plan only.
- **ask_first** (default) — human gate on first‑time/ risky actions; learns allow‑list.
- **full_auto** — only for CI‑like runs with a strong allow‑list; use sparingly.

## Troubleshooting

- **404 on model calls** → Ensure Ollama is running and the model exists. Example:
  ```bash
  ollama run qwen2 "hello"
  ```
- **Permission issues** → Run terminal as an admin (Windows) or adjust WSL path permissions for cross‑boundary writes.
- **UI contrast issues** → Switch theme to the high‑contrast profile; never accept low‑contrast text.
