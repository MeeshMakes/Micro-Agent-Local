# README — Default Agent (Bedrock) 
> Path: `agents/default/README_default.md`

This folder contains the **Default/Bedrock Agent** used by Micro‑Agent‑Local. It is the **stable baseline** that all other agent “styles” and named agents clone from. When styles are uncertain or a specialized agent is missing, this Default Agent is the **fallback that must always work**.

## What lives here
- **`agent.md`** — natural‑language *working contract* for the agent (identity, goals, authority rules, workflows, memory, macros, datasets, approvals, safety, etc.).  
- **`agent.yaml`** — machine‑readable configuration (paths, authority modes, pipelines, tools, guards, retention, backups).  
- **`tools/`** (optional) — default utilities this agent may call (local scripts, OCR helpers, diff/generative subroutines).  
- **`notes/`** (optional) — scratch notes specific to this agent.

> High‑contrast rule: when rendered in any GUI, this document and all UI related to it **must** use light text on a dark background or dark on light (never low contrast).

## Relationship to the rest of the repo
- **Agent Roster**: new named agents cloned from this default must be stored under `agents/agent_roster/<agent_name>/` with their own `agent.md` + `agent.yaml` (and optional tools).  
- **Agent Styles**: shared patterns live under `agents/agent_styles/` and can be referenced by any roster agent or by the default agent at runtime.  
- **Archived Agents**: time‑boxed or retired variants are zipped or summarized to `Archived_Agents/` with a small metadata index for recall.
- **System Tools**: cross‑cutting utilities live under `system_tools/` (e.g., macros, OCR, diff/patch), and can be enabled/disabled per agent via `agent.yaml` authority and capabilities sections.

## How to create a new named agent (safe clone workflow)
1. **Duplicate** this folder `agents/default/` into `agents/agent_roster/<new_name>/`.
2. **Rename** inside the clone: update `agent.yaml:name`, `agent.md:# Identity`, and any paths pointing to datasets/logs so the new agent does not collide with others.
3. **Tighten** scope: in the clone’s `agent.yaml`, reduce authority/globs to the specific repo or product area.
4. **Register**: add or update the roster index (if present) at `agents/agent_roster/README_agent_roster.md`.
5. **Smoke test**: run **Ask** (read‑only) then **Do Work** with “ask first” authority; verify pending command approvals and the Implemented/Missing/Quarantined indexes update correctly.

## Default Agent responsibilities (summary)
- Obey the **Trifecta**: keep `README.md` (**Current**), `Required-Updates.md` (**Desired**), and the various **Implemented/Missing/Quarantined** indexes always in sync.  
- Maintain **chat_history.md** (markdown), including `<think>…</think>` reasoning blocks (rendered small/italic green) and inline thumbnails for any images attached.  
- Run **Dual OCR** on attached images, prefer the fast **markdown‑oriented** pass when extracting UI/chat or screenshot text. Persist OCR text + image paths + tags + hashes into the dataset.  
- Use and maintain the **Pending Command** gate (**Allow / Skip / Try Harder / Edit**) for any file system, process, terminal, or repo‑mutating actions.  
- Capture and age **Macros** (helper scripts/snippets) with a 24h retention + “bean counter” policy; keep last‑session macros if the user was inactive for >24h.  
- Honor **Independent Agent Mode** when enabled: isolate approvals and authorities from the global allow‑list.  
- Fall back gracefully: if a specialized style/agent is unavailable or uncertain, **this default agent proceeds** using its own rules.

## Backups & checkpoints for the Default Agent
- Keep rolling backups of this folder (config + directives), e.g., **2d / 1d / 6h / 1h**. Store to `Archived_Agents/default_agent_checkpoints/` with a tiny JSON index (timestamp, hash, notes).  
- Only update the default agent’s directives after a **logic quota** (enough usage signals) and a self‑review pass that writes a diff and rationale to `Implemented-DevLogic.md`.

---

### Quick checklist (for any edits to this folder)
- [ ] Renamed `agent.yaml:name` and `agent.md` identity when cloning.  
- [ ] Paths updated to unique datasets/logs/macros bins.  
- [ ] Authority/globs right‑sized for the repo.  
- [ ] Roster index updated.  
- [ ] Smoke tests passed (Ask ➜ Plan ➜ Pending Command ➜ Execute).

