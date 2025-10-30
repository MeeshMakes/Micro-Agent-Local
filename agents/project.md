# Agent Project (Repo Binding)

> Defines how an agent binds to a **project/repository**, honors the **Trifecta**, and executes the Required‑Updates loop with safety, macros, and documentation discipline.

## Project Runtimes (examples)

- `Virtual_Desktop.py`
- `Codex_Terminal.py`

## Update Loop Files

- `Required-Updates.md` — input backlog (desired behaviors and changes).
- `Implemented-Updates.md` — applied items with trace: task IDs, diffs, verification notes.
- `Quarantined-Updates.md` — blocked/needs‑attention items (auth failure, test breakage, ambiguity).
- `Missing-Updates.md` — items that could not be found or were deferred by design.

## Memory Surfaces

- `memory/logic_inbox.jsonl` — task stubs queue (auto‑generated).
- `memory/codex_memory.json` — long‑lived truths (stable facts, directory contracts, invariants).
- `Dev_Logic/` — inspirational (UX/code patterns), not authoritative for behavior decisions.
- **README.md** at repo root is the **“Current”** truth used by the agent to understand the present system and avoid drift.

## Execution Workflow (Human‑in‑the‑Loop)

1. **Ask (thinking only)**
   - Agent reads README (Current), Required (desired), and recent Implemented/Quarantined/Missing.
   - Produces a **task graph** with deps/acceptance criteria. No writes yet.

2. **Stage**
   - Agent proposes **Pending Command** text for each unit of work.
   - UI shows **Allow / Skip / Try Harder / Edit**. “Allow” flashes blue when a decision is needed.

3. **Do Work**
   - On approval, the agent applies **atomic diffs** across one or more files as needed, with rollback notes.
   - Updates **Implemented-Updates.md**. If blocked, logs to **Quarantined-Updates.md**; if spec not found, to **Missing-Updates.md**.
   - If behavior changed, the agent updates **README.md** immediately or creates a doc‑task stub with a deadline.

4. **Reflect & Harvest**
   - Record new **macros** (dedup/TTL) and update **memory/** surfaces.
   - Append the turn to **chat_history.md** with markdown and any thumbnails.

## Diff & Docs Conventions

- Use **split diff** rendering in the UI (left=old, right=new). Include a **diff tally** near the file name.
- Every Implemented entry carries:
  - **Task ID**, **Files touched**, **Rationale**, **Acceptance checks**, **Roll‑forward plan**.
- README is authoritative for “Current”; if it diverges from code, generate and execute a **doc sync** task.

## Roster & Styles

- **agent_roster/** holds named agents cloned from the base. Each contains its `agent.yaml`, `agent.md`, and optional `tools/`, `datasets/`.
- **agent_styles/** holds re‑usable style profiles that can be applied to agents or UI.
- When style detection fails, fall back to **base agent** defaults to ensure progress.

## Example Snippets

**agent.yaml (project override)**
```yaml
name: "project_agent_override"
provider:
  type: "ollama"
  endpoint: "http://localhost:11434/v1/chat"
  model: "gpt-oss:20b"
policy:
  authority_mode: "ask_first"
  always_allow: false
io:
  chat_history: "./chat_history.md"
  macros_store: "./system_tools/system_macros/store.jsonl"
  authority_ledger: "./agents/authority/ledger.json"
```

**agent.md (project notes)**
- This project binds to the Trifecta: keep README as **Current**. Never let Required or Implemented drift without reconciling README.
- Prefer **incremental diffs** with clear acceptance steps over monolithic rewrites.
- Always honor high‑contrast UI rules for any panels this agent renders.
