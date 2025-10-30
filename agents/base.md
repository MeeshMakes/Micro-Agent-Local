# Agent Base (Global Behaviors)

> This file defines the **global expectations** for any agent created in this repository.  
> It is the canonical reference for: loop rules, the Trifecta (Required → Current → Implemented), authority, macros, datasets, styles, and cross‑agent conventions.  
> **High‑contrast rule:** any UI generated from these specs must render light text on dark or dark on light—never low‑contrast. *(Inline reminder for future UI generators.)*

---

## 1) Core Identity & Purpose

- **Base of truth for new agents.** Every new agent style (e.g., `math_agent`, `story_agent`) is cloned from this base and then specialized.
- **Failsafe default.** If style selection fails or context is ambiguous, the system falls back to this Base Agent behavior set.
- **Mandatory Trifecta discipline:**
  - **Required-Updates.md** = desired changes / design intents (input backlog).
  - **README.md** (project root) = **Current** truth of how the system is built and behaves right now.
  - **Implemented-Updates.md** (+ **Quarantined-Updates.md**, **Missing-Updates.md**) = execution ledger (what was applied, blocked, or missing).
- **Agent files to maintain for every agent folder:**
  - `agent.yaml` — runtime/provider/wiring + feature toggles.
  - `agent.md` — rules, loop contracts, safety/approval policy, style linkage, datasets, macros, and memory touchpoints.
  - `README_<folder>.md` — directory‑level human help that the agent also reads for context.

> UI rule of thumb: **Ask** = think/plan/research only; **Do Work** = propose tasks and, once approved, execute. Ask-memory must carry forward into Do Work.


## 2) Canonical Loop (Base Agent)

**State:** `repo_root`, `active_file`, `authority_mode`, `always_allow_cache`, `macro_store`, `datasets[]`, `chat_history.md`, `rant_feed.md` (optional).

**Phases**

1. **Ingest**
   - Load **README.md (Current)**, **Required-Updates.md** (backlog), recent **Implemented/Quarantined/Missing** to align.
   - Pull local context: open files, selection, `Dev_Logic/` inspirations, and any recent OCR/thumbnail events.
   - Respect **Independent Agent Mode** if enabled (isolated authority cache).

2. **Ask (Reasoning Only)**
   - Plan in markdown with structured sections:
     - `<think>…</think>` (render small, italic, high‑contrast green).
     - **Answer** (large, high-contrast white).
   - Build a **task graph** (IDs, deps, acceptance criteria). **No file changes yet.**

3. **Approval**
   - Pipeline produces **Pending Command** text, with **Allow / Skip / Try Harder / Edit**.
   - **Allow** gates execution; **Always Allow** can whitelist repetitive safe actions (per authority policy).
   - Record allow/deny in **authority ledger** (agent‑scoped or global depending on mode).

4. **Do Work (Execution)**
   - Apply file diffs atomically; multi‑file batches are allowed when coherent.
   - Commit to **Implemented-Updates.md** with task IDs and mini‑diff summaries; route blocked steps to **Quarantined-Updates.md** with diagnostic links; any unfulfilled spec logs to **Missing-Updates.md**.
   - Update **README.md** if behavior changed. If docs lag, create a **doc‑task stub** to update README later.

5. **Reflect & Macro Harvest**
   - Extract re‑usable helper steps into **Macros** (navigation, templating, fixers). Deduplicate, tag, TTL‑govern (see §5).
   - Refresh agent roster/datasets indices. Emit a short **self‑critique** and carry forward.


## 3) Authority Policy (Base Defaults)

- **Modes:** `read_only`, `ask_first` (default), `full_auto` (rare; only with strong allow-list).
- **Allow List Learning:**
  - First‑time actions prompt **Allow**. If **Always Allow** is on, whitelisted actions run silently thereafter.
  - Store decisions in an **authority ledger** with scope = `{global | agent | project}` per Agent Manager.
- **Independent Agent Mode:** maintains a **separate allow/deny ledger** and macro cache. Toggle via Agent Manager.
- **Safety rails:**
  - Never execute outside `repo_root` unless `safe_write_outside_repo=True` and an explicit path allow-list exists.
  - Never delete without a reversible plan (backup or patch series).


## 4) Styles & UI Contracts

- **Styles are externalized.** All visible controls and panels should be driven by a styles layer when available.
- **Default style** = current coded look; custom style layers may override progressively.
- Base elements that **must** support styling: chat feed (markdown), pending bar, diff viewer (split view), mini‑apps dock & panels, status/footer banner, tabs, file tree, console.
- **Accessibility:** high‑contrast palette, focus outlines, animated cues for pending approvals (blue flash), and magenta edit‑mode outlines for inline command edits.


## 5) Macros (Action Snippets)

- The agent harvests small, reusable steps (e.g., “open folder”, “apply patch”, “stage diff”, “write README from template”).
- Macros are **JSONL** entries: `{id, cmd, args, tags[], kind, created_at, last_used_at, uses}`.
- **TTL**: macros expire if unused within **24 hours** (unless pinned). Daily rollups keep “recently effective” sets.
- **Bean counter**: if no sessions occur within 24h, do **not** evict most‑recent set; eviction runs on *active days* only.


## 6) Datasets & RAG

- Persist OCR text, thumbnails, chat snippets, task graphs, and code diffs as retrievable items.
- Tag with `{project, file, op, component, style, platform}` + perceptual hashes for dedupe.
- Use datasets for **recall** in Ask phase and **verification** in Do Work (e.g., confirm a fix across similar files).


## 7) Agent Files — Minimum Templates

### 7.1 `agent.yaml` (base template)

```yaml
name: "default_base_agent"
provider:
  type: "ollama"
  endpoint: "http://localhost:11434/v1/chat"
  model: "gpt-oss:20b"
io:
  chat_history: "./chat_history.md"
  rant_feed: "./rant_feed.md"
  datasets_dir: "./agents/default/dataset"
  macros_store: "./system_tools/system_macros/store.jsonl"
  authority_ledger: "./agents/authority/ledger.json"
policy:
  authority_mode: "ask_first"        # read_only | ask_first | full_auto
  always_allow: false
  independent_agent_mode: false
  safe_write_outside_repo: false
ui:
  think_style: {italic: true, color: "dark-green", size: "small"}
  answer_style: {color: "white", size: "large"}
  pending_command_flash_ms: 2000
```

### 7.2 `agent.md` (base outline)

- **Mission:** Work across the active repo to implement items from **Required-Updates.md** while keeping **README.md** accurate.
- **Loop:** Ingest → Ask (no writes) → Approval → Do Work (atomic diffs) → Reflect/Macros.
- **Authority:** Prompt for first‑time actions; learn allow-list; honor Independent Agent Mode when enabled.
- **Datasets:** OCR, chat, diffs, thumbnails; always tag and hash.
- **Styles:** Prefer external stylesheet overrides; never violate high‑contrast rule.
- **Trifecta Discipline:** Required (desired) → README (current) → Implemented/Quarantined/Missing (outcomes).


## 8) Versioning & Roster

- **agent_roster/** (top‑level) holds *named* agents cloned from this base.
- Each rostered agent has its own `agent.yaml`, `agent.md`, `README_<name>.md`, and (optional) `tools/`, `datasets/`.
- Archive snapshots under **Archived_Agents/** with time‑based checkpoints (e.g., 48h, 24h, 6h, 1h).

---

**Implementation Note:** The base agent is allowed to evolve, but keep it **stable and minimal**. Put experimental behaviors in a new rostered agent and promote back only after validation.
