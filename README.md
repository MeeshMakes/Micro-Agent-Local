# Micro-Agent — Living README (Canonical “Now” for the Entire System)

> This document is **live state**: it must always reflect what **exists and works right now**—architecture, UI, files, authority policy, styles, datasets, macros, and agent inventory.  
> The Agent (Local Agent or cloud Codex) must treat this README as the single source of truth for **the current reality** of the repo.  
> The backlog/intent and the delivery ledger live alongside it; together they form the **Trifecta** that keeps the project coherent and auditable.

---

## The Trifecta (plan ↔ now ↔ shipped)

```

[ Required-Updates.md ]     → plan of record (backlog / intent / constraints)
[ README.md ]               → current system (this file; must mirror reality precisely)
[ Implemented-Updates.md ]  → shipped ledger (what landed; task ids; diffs/commits)

```

- If an item is **desired** → it belongs in **Required**.  
- If an item is **built** → it must be reflected **here in README** and recorded in **Implemented**.  
- If an item is **blocked/denied/errored** → move it to **Quarantined-Updates.md** with a clear retry plan.  
- After any “Do Work” run, anything that didn’t land is enumerated in **Missing-Updates.md** (auto), so nothing silently drops.

> **Invariant:** the README is the **“now” contract**. The Agent must keep it current or leave explicit “Documentation TODO” stubs *in this file* (template below).

---

## How the Agent must use this README (non-optional loop)

1. **Every run (Ask or Do Work)**  
   - Re-read this README **top-to-bottom**.  
   - Treat it as **ground truth** for: architecture, UI affordances, authority model, current styles, datasets, macro policy, agent inventory.  
   - Perform **drift detection**:  
     - Anything described here that doesn’t exist in code/config → open/fix tasks.  
     - Anything in code/config not captured here → update this README (or add a visible TODO block).

2. **When implementing anything from Required**  
   - Follow: **Plan → Stage → Approve → Apply → Verify → Record**.  
   - After *verify*:  
     - Update **this README** (sections listed below).  
     - Append an entry to **Implemented-Updates.md**: task ids, affected paths, concise rationale, links to diffs/commits.  
     - If partially landed, keep the remainder in **Required** and add a visible **TODO** block *here*.

3. **If docs trail the code**  
   - Insert a **Documentation TODO** block (below) in this README and open a matching task in **Required**.  
   - Never “skip and forget” README updates; make drift visible.

4. **If README vs code disagree**  
   - Prefer **runtime** (code) as factual, then immediately:  
     - Fix this README to match reality **or** file a Required task to align code to the described intent.  
   - Record the reconciliation in **Implemented**.

---

## Execution Modes, Authority & UI Signals

- **Ask** → reason/research/narrate only. **No writes, no shell, no side-effects.**  
- **Do Work** → propose tasks, stage diffs/commands, request approvals, execute approved steps, then update README + ledgers.
- **Context carry-over**: Ask analysis must feed directly into Do Work planning.

**Authority Model (Agent Manager):**
- Profiles: **Ask-First**, **Read-Only**, **Full Auto**, **Independent Agent Mode** (isolated approvals/allow-lists per agent).  
- **Allow / Skip / Try Harder / Edit** flow:
  - Pending command requires approval → **Allow** flashes blue (every ~2s).  
  - **Edit** toggles magenta outline (high-contrast) and lets user revise the pending text before approval.  
  - **Always Allow** persists future approvals for identical actions; first-time actions still prompt and get logged to the allow-list.

**High-Contrast UI (non-negotiable):**
- Never low-contrast pairings. Use **light on dark** or **dark on light** only.  
- Critical affordances: flashing blue **Allow** when needed; magenta **Edit-mode** outline for clarity; state badges readable at a glance.

---

## Core Layout & Current Components (live snapshot)

> This section must always mirror what actually exists, not aspirations. The Agent updates it whenever new capability lands.

- **Mini-App Dock**: Script Creator, Agent Manager, Macros Manager (future: Tools Manager).  
- **Chat Surface**: message input + response pane (vertical), buttons co-located at chat level (**Send / Ask / Do Work / Try Harder / Edit / Allow / Skip**).  
- **Pending Command bar**: appears above chat; shows staged operation, auth state, and the flashing **Allow** when action is required.  
- **Left Slide-Out**: vertical scroller host for Managers (Agent Manager, Extension/Tools Manager, Styles Manager, etc.). Arrow affordance nudges content and auto-slides; panes are movable/dockable; thin grey wireframe + corner handles for resizing.  
- **Staged Changes**: right column under Task Feed; shows file/diff staging with explicit approvals.  
- **Rant Window (top, faint brown-orange)**: speech-to-text stream → converts longform intent into structured entries in **Required-Updates.md** (see ingestion rules below).

> UI geometry follows the **High-Contrast rule** and all panes are movable/dockable; text never overlays similar values.

---

## Files & Folders the Agent must maintain (and auto-seed if missing)

> Current repo uses this README as the only README. As structure is implemented, the Agent will generate per-folder `README_<scope>.md` files using the naming rules below.

```

/Required-Updates.md              # backlog/intent; also receives “Rant” ingestions (structured)
/Implemented-Updates.md           # shipped ledger; links to diffs; task ids
/Quarantined-Updates.md           # blocked/denied w/ reason + retry plan
/Missing-Updates.md               # what didn’t land after a run (auto)

/agents/                          # agents home (default, styles, roster)
/default/
agent.yaml                    # machine config (model/provider/endpoints/limits/authority/style)
Agent.md                      # human-readable system card (loop, safety, datasets, macros, styles)
README_default.md             # local contract for default agent (auto once generated)
/agent_tools/
/agent_macros/              # per-agent macro registry (templates, compiled packs, logs)
/agent_styles/                  # swappable styles (index + folders; auto as implemented)
index.json
README_Styles.md
/agent_roster/                  # cloned, named agents derived from default/style templates (auto)
<agent_name>/
agent.yaml
Agent.md
README_<agent_name>.md

/system_tools/                    # repo-wide tools (non-agent-specific)
/system_tools/system_macros/      # global macro packs (may be imported/compiled into agents)

/datasets/
/chat_history/                  # markdown turns, images, OCR_fast/full, tags & hashes
memory.jsonl                    # consolidated memory rollups (if used)
/indices/                       # semantic indices, allow-lists, style indices

/.logs/                           # session logs, approvals, errors (human-readable)

````

> **Auto-seeding:** if any of the above are missing, the Agent creates sensible defaults and appends the action to **Implemented-Updates.md**.

---

## Styles & Style Packs (agent_styles)

- **Purpose**: change *how* the agent reasons/communicates without breaking the default backbone.  
- **Index**: `agents/agent_styles/index.json` (category, description, guardrails, preferred tasks).  
- **Behavior**: the Agent can switch styles autonomously (fast) based on task semantics; fall back to **default** if style is missing/ambiguous.  
- **Evolution**: styles can be grown over time; descriptions must state differences from default; each style folder will include `README_<style>.md`.

> Rationale for separation: **default** must always work and remain clean. Styles are **additive** overlays tuned for domains (e.g., story, math, code, UI/UX).

---

## Macros (agent_macros + system_macros), Lexicons & GC

- **Macros** are small helper scripts/snippets that the Agent composes to act quickly (navigate FS, open/patch files, apply diffs, run tests, retry with backoff).  
- **Lexicons** enumerate terminal idioms across environments (PowerShell, CMD, bash/WSL/Linux, etc.) so macro generation is precise per shell.  
- **Where**:
  - **Per-agent**: `agents/default/agent_tools/agent_macros/` (templates, compiled macro packs, usage logs).  
  - **Global**: `/system_tools/system_macros/` (can be imported and localized per agent).
- **Bean counter / GC**: unused macros decay after ~24h (usage “beans”); GC does not run if the *entire* session window is idle (to avoid wiping last-used macros).
- **Quarantine / Blocked**: macros with auth collisions or failures are moved to quarantine with a reason; retry logic is recorded; blocked macros are clearly surfaced and can request re-auth.

> The Macros Manager must expose: registry, quarantine, blocked, compiled packs, usage counters, and lexicon links per terminal.

---

## “Rant → Required” Ingestion (speech-to-text intent → structured tasks)

- **Rant Window** continuously streams voice → text into a preprocessing step that:
  - Buckets content, adds semantic tags/hashes, and suggests merges with related Required entries.  
  - Expands existing Required items with new detail **or** creates new ones if distinct.  
  - Preserves raw voice text in datasets and writes clarified task text to **Required-Updates.md**.
- **Buttons** near Rant:
  - **Generate Required** (first pass), **Revise Required** (merge/simplify, never silently delete), **Implement Required** (start autonomous harvest loop).
- **Harvest loop** uses dedicated micro-agent directives to walk Required from top→bottom while cross-linking references across the file; it can partial-land items and open TODOs here.

---

## Default Agent Hygiene (the backbone must stay sharp)

**Path:** `agents/default/` — stable fallback; **must always work**.

- Evolve `Agent.md` by *appending/refining*; do not nuke history.  
- Adjust `agent.yaml` when you have a documented upgrade (model/provider/limits/authority/style).  
- Snapshot to `Archived_Agents/` with short changelog at rolling intervals (2d / 1d / 6h / 1h) and prune as stability holds.  
- To create a new **named agent**:
  1. Clone `agents/default/` to `agents/agent_roster/<agent_name>/`.  
  2. Rename README inside to `README_<agent_name>.md`.  
  3. Tailor `Agent.md` & `agent.yaml`; register optional style in `agent_styles/index.json`.

---

## What this README must always include (sections the Agent maintains)

1. **Overview & Capabilities** (what works right now)  
2. **Architecture Map** (chat → OCR_fast/full → dataset → plan → stage → approve → apply → verify → record)  
3. **Execution Modes & Authority** (Ask/Do Work, allow-list, Independent Agent Mode)  
4. **Models & Providers** (from `agents/default/agent.yaml`, e.g., `ollama:qwen2.5-coder @ http://127.0.0.1:11434`)  
5. **Datasets & RAG** (where markdown/images/OCR live, tags & hashes, indices)  
6. **Macros** (count, latest additions, GC status, quarantine/blocked counts)  
7. **UI & Styles** (active style pack; high-contrast proof points; dock panes)  
8. **Mini-Apps** (Script Creator, Agent Manager, Macros Manager; future Tools Manager)  
9. **Agent Manager** (authority profile, allow/deny lists, pending pipeline states)  
10. **Repo/Script Linking** (how an input path sets active repo; how staged diffs appear)  
11. **Known Limitations / TODOs** (explicit, with task ids tied to Trifecta and `Task-Index.json` if present)

> Any change that touches one of these requires a same-commit README edit or a visible TODO stub.

---

## Documentation TODO (auto-insert template)

```markdown
> 📌 **Documentation TODO (auto)**
> Task: T-YYYY-MM-SEQ
> Affected: <files/paths>
> Status: Implemented in code; README edits pending
> Notes: <screenshots to add, style names to confirm, authority toggle text, etc.>
````

---

## End-of-Run Declarations (the Agent writes these)

* If everything in Required landed:

```
✅ As of <timestamp>, all Required Updates are implemented. README reflects the current system.
```

* Otherwise:

  * Update **Missing-Updates.md** with undelivered items (+ task ids).
  * Update **Quarantined-Updates.md** for blocked items (reason + remediation steps).
  * Leave **Documentation TODO** stubs *here* where code shipped but docs lag.

---

## README Naming, Generation & Read Order (as structure emerges)

> Today, only this root README exists. As features land, the Agent must generate **per-folder READMEs** using these rules.

**Naming (machine-readable scope):**

* `README_<folder_or_scope>.md` (snake-case after `README_` is the scope tag the Agent parses).

  * `agents/` → `README_agents.md`
  * `agents/default/agent_tools/` → `README_agent_tools.md`
  * `system_tools/system_macros/` → `README_system_macros.md`
  * `agents/agent_styles/` → `README_Styles.md`

**Read order before acting:**

1. Root `README.md` (this file).
2. All ancestor READMEs down to the target folder.
3. Target folder’s `README_<scope>.md`.
4. If present: `Agent.md`, `agent.yaml`.
5. Trifecta docs (Required / Implemented / Quarantined / Missing).

If a needed README is missing, the Agent must **create a stub from template**, then proceed once approved.

---

## Practical Examples (how the Agent should behave)

**Example A — Create a macro in `system_tools/system_macros`:**

1. Read: root README → `README_system_tools.md` → `README_system_macros.md` (generate stubs if missing).
2. Ask: propose plan; Do Work: stage file create + doc updates.
3. On **Allow**: write `<macro>.py` with terminal-aware header, update README, append to **Implemented**.
4. If shell/authority unclear: request explicit approval and persist allow-list entry.

**Example B — Add a new style “researcher”:**

1. Update `agents/agent_styles/index.json` with description, category, guardrails.
2. Create folder `agents/agent_styles/researcher/` + `README_researcher.md`.
3. Add style hooks in `Agent.md` (how behavior changes) and ensure **fallback to default** is explicit.
4. Append to **Implemented**; add README TODO here if screenshots pending.

---

## Defaults & Backstops (when in doubt)

* **Default Agent** must always function: switch to it if style resolution fails.
* **Authority**: first-time risky actions always prompt; “Always Allow” is respected thereafter.
* **GC**: macro beans only decay when there was *actual opportunity* to use them; full-day idle means **no** wipe.
* **High-Contrast**: any new visual must assert readable text on background; add a comment note to code where the visual is defined.

---

> This README is the live **system contract**. Keep it accurate, or mark what remains to document—*here*. The Trifecta (Required → README/Now → Implemented) is mandatory. Nothing lands without being reflected in these three views, and nothing described here should be missing in code for long.

```

::contentReference[oaicite:0]{index=0}
```







_____________________


---

# Micro Agent Workbench

## Overview

Micro Agent Workbench is a **local, high-contrast, offline-first** development assistant and IDE shell.

It is a self-contained GUI that:

* Hosts an Agent (LLM) with **repo-scoped memory** and explicit authority gates.
* Lets you converse in **Ask** mode (research/reason only) and authorize execution in **Do Work** mode (plan, stage, apply).
* Captures **chat markdown, screenshots, dual-pass OCR, diffs, approvals, and logs** into a durable knowledge base inside each repo.
* Manages **code editing, version snapshots, diff staging, and safe application** of changes.
* Bootstraps new projects with a **Script Creator** mini-app.
* Exposes an **Agent Manager** for authority mode, safety gates, dataset/memory visibility, and command pipeline control.

All logic runs locally in `micro_agent.py`. The default model path assumes an Ollama-style endpoint (`http://127.0.0.1:11434/api/chat`), but the client is generic and can target any compatible local API.

> **High-contrast rule (non-negotiable):** all text must be readable against its background. We default to **light text on dark** across the entire UI.

---

## Goals

1. Treat the Agent like a **co-developer**, not a chatbot.
2. Keep everything **local, inspectable, and reversible**.
3. Make the Agent **earn permission** before touching disk or running shell.
4. Persist **full context** (reasoning, OCR, images, diffs, approvals, logs).
5. Make starting a new repo **fast** (scaffolding + agent metadata in one click).
6. Enforce **strict visual clarity** with high-contrast UI in every state.

---

## Core Concepts

### 1) RepoSession (per-repo control folder)

When you load a repo, Workbench maintains a hidden control area:

```
<your-repo>/
  .codex_local_agent/
    agent.yaml
    agent.md
    chat_history.md
    patches/
    history/
    dataset/
      memory.jsonl
    logs/
```

* **`agent.yaml`** – machine config (provider, model, endpoint, authority/policies, style).
* **`agent.md`** – human system card describing behavior/safety/loop.
* **`chat_history.md`** – canonical markdown transcript; includes `<think>` and embedded images.
* **`patches/`** – staged unified diffs proposed by the Agent.
* **`history/`** – per-file snapshots for quick rollback.
* **`dataset/memory.jsonl`** – per-turn “RAG seed” entries (message markdown, image paths, **dual-pass OCR** summaries, tags, hashes, timestamps).
* **`logs/`** – session logs with objective, steps, errors, and “next actions.”

> Each repo owns its own `.codex_local_agent` (no cross-repo bleed).

---

### 2) Ask vs Do Work (authority split)

* **Ask** = research/reason/narrate only.
  The Agent may analyze, summarize, brainstorm, reference dataset context, and plan—**but cannot stage diffs or shell**.

* **Do Work** = action pipeline.
  The Agent may **propose tasks**, stage file diffs, and submit shell commands to the **Pending Command** queue. Nothing executes or writes to disk without explicit approval or policy.

Both modes append to `chat_history.md`, so the narrative you build in Ask carries forward into Do Work.

---

### 3) Local LLM Client (Ollama-style)

The client posts to a simple `/api/chat` endpoint:

```json
{
  "model": "gpt-oss:20b",
  "messages": [{ "role": "user", "content": "..." }]
}
```

Responses are parsed; the assistant’s content becomes the Agent reply. The active model/endpoint are declared in `agent.yaml`, allowing offline models (e.g., Ollama) or any compatible local bridge.

---

### 4) Conversation Logging (markdown transcript)

Every turn (user + agent) is appended to `chat_history.md` with timestamps.

Renderer supports headings, lists, code fences, inline code, images, and **`<think>…</think>`** blocks.

Visual semantics:

* `<think>` reasoning → **dim, italic, green-toned**.
* Final answer → **larger, bright white**.

This preserves the distinction between internal reasoning and operator-facing instructions.

---

### 5) Image Intake + Dual OCR

Attaching images to a message:

* Shows **thumbnails** in-feed and injects absolute **file paths** into the message markdown for reference.
* Runs **dual OCR**:

  * `run_ocr_fast(...)` — quick UI/chat text capture.
  * `run_ocr_full(...)` — deeper pass for completeness.
* Logs both OCR outputs alongside the message and image paths into `dataset/memory.jsonl`.

This builds a local, searchable corpus of screenshots and extracted text for later recall.

---

### 6) Task Manager + Task Feed

Do Work plans become tasks:

* Each has **id, title, detail, status** (`pending | running | done | skipped | error`).
* A **Task Feed** lists tasks with **Start / Skip / View**.
* Selecting a task reveals its rationale/details.

Tasks decouple planning from execution while remaining reviewable.

---

### 7) Staged Changes Panel (diff-first writes)

Edit flow:

1. Agent proposes an edit.
2. Workbench computes a unified diff.
3. **Staged Changes** shows colorized `+/-` hunks.
4. You approve; only then does Workbench write to disk and snapshot prior content to `history/`.

All staged diffs are also saved under `.codex_local_agent/patches/`.

---

### 8) Version History Snapshots

On each approved write:

* Prior content is saved in `.codex_local_agent/history/<file>/timestamp.txt`.
* The **Editor Info Bar** lets you step prev/next, copy path, clone, ask for docs, or purge history.

It’s lightweight versioning even before you commit to git.

---

### 9) Pending Command Approval (shell safety)

Agent-proposed shell commands appear in a **Pending Command** bar:

Controls:

* **Allow** (executes) – **flashes blue** every ~2s if approval is needed and “Always Allow” is off.
* **Skip** (reject)
* **Try Harder** (retry same goal with a push/refinement)
* **Edit** (puts the input box into **magenta-outlined purple** edit mode to modify the pending command)
* **Always Allow** (toggle auto-exec for repeated, explicitly permitted classes)

No command runs without approval unless policy explicitly allows it.

---

## UI Layout

### A) Top Banner Mini-App Dock

Row of square icons (right-aligned). Clicking an icon opens its panel; the icon remains highlighted while open.

### B) Left Dock Column

Holds mini-app panels in a collapsible, scrollable stack. Closes entirely when no panels are open.

### C) Project Tree + Editor

File tree rooted at the active repo; tabbed editors; **Info Bar** with file path, prev/next snapshot, Copy Path, Clone, Doc, and Purge Hist.
**High-contrast syntax** is enforced in the editor.

### D) Chat / Agent Panel

* **Ask / Do Work** buttons
* Brain mode dropdown: **Agent (full repo access)** / **LLM (chat only)**
* Transcript (markdown with `<think>` styling + thumbnails)
* Task Feed
* Staged Changes
* Pending Command bar
* Chat box with image attach
* Quick actions: **Plan Tasks**, **Remember**, **Expand Logic**, **Stage File Change**, **Write File To Disk (Approve)**

---

## Mini-Apps (current)

### 1) ScriptCreatorApp

* Choose destination (path or Desktop), filename, and file type (`.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, …).
* Creates folders as needed; previews collisions before overwrite.
* Generates a README for the new folder and seeds `.codex_local_agent` (agent metadata, chat history, dataset base).

Result: an **instant “agent-ready” repo** with a starter script, docs, and control folder.

### 2) AgentManagerApp

* Authority mode: **Full Auto / Ask First / Read Only**
* Policy flags from `agent.yaml`: `require_command_allow`, `safe_write_outside_repo`
* **Always Allow** toggle for repetitive, pre-approved classes
* Dataset summary (row count, tags, known hashes)
* Pending Command pipeline visibility (queued command, waiting state, Always Allow status)

---

## Loading & Linking a Repo

### 1) Clipboard Load

Copy a file or folder path (Ctrl+C in Explorer), then **Load Path From Clipboard**.

* If a **file** path: open it in an editor tab; its parent folder becomes the repo root.
* If a **folder** path: that folder becomes repo root.

### 2) ScriptCreatorApp

Create a new folder + script + README + `.codex_local_agent`. The created folder becomes the active repo automatically.

---

## High-Contrast Accessibility Rules

* **No low-contrast** color pairings—ever.
* Critical states have loud, distinct cues:

  * **Allow** flashes blue if approval is required.
  * **Edit Pending Command** turns the input purple with a magenta outline.
  * `<think>` blocks render dim, italic, green.
  * Final answers render bright white and larger.

These rules apply everywhere: editors, lists, labels, borders, and highlights.

---

## Typical Workflow

1. **Attach a repo** (clipboard) or **create** one (ScriptCreatorApp).
2. **Ask** to align, analyze screenshots, and build narrative. OCR results + images are logged to `dataset/memory.jsonl`.
3. Switch to **Do Work** to propose concrete changes. Tasks appear in the feed; file edits become staged diffs.
4. **Review diffs**; approve to write. Snapshots go to `.codex_local_agent/history/`.
5. **Handle commands** through Pending Command (Allow / Skip / Try Harder / Edit / Always Allow).
6. **Document & iterate**: use Info Bar for docs, clones, or purge; keep cycling. The repo becomes the Agent’s durable working memory.

---

## Security & Control Model

* No silent shell; no silent writes.
* Authority can be downgraded to **Read Only** at any time.
* Sensitive snapshots can be purged.
* `agent.yaml` shows current **model/endpoint/policies**.
* Approval gates and **Always Allow** class toggles ensure transparent, auditable automation.

---

## Companion READMEs (what the Agent must read)

The system treats READMEs as **executable contracts**. Each folder includes a scope-named file the Agent must consult:

* **`Agents.md`** (root, cross-agent contract; Codex Online aware)
* **`README_agents.md`** (home for agent configs/assets and roster guidance)
* **`README_agent_tools.md`**, **`README_agent_macros.md`** (per-agent tools & macro framework; creation, approval, GC)
* **`README_Styles.md`** + `agent_styles/` (style packs for personas/behaviors; includes `index.json`)
* **`README_authority.md`** (authority modes, allow-lists, Always Allow classes)
* **`README_default.md`** (the default agent’s stable baseline contract)
* **`README_runtime.md`** (runtime expectations, loop discipline)
* **`README_prompts.md`**, **`ask.md`**, **`do_work.md`**, **`try_harder.md`** (prompt contracts)
* **`README_system_tools.md`**, **`README_system_macros.md`** (top-level system tools and macros)
* **`archived_agents.md`** (snapshot/rollback policy, aging, and restoration)

> Naming rule: `README_<foldername>.md` (or a clear scope tag). The Agent must parse scope from the filename and apply the right local policy.

---

## Summary

Micro Agent Workbench merges:

* A **repo-aware AI** with persistent memory and explicit authority gates.
* A **diff-first editor** with snapshots and safe writes.
* A **task feed** + **pending command** pipeline for controlled execution.
* A **screenshot/OCR** dataset for local recall.
* A **project bootstrapper** for instant, agent-ready repos.
* An **Agent Manager** that surfaces autonomy, safety, memory, and queues.

Everything is transparent. Everything is high contrast. **Nothing runs without you seeing and approving it.**

