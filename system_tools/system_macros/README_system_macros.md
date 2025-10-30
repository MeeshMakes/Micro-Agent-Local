```markdown
# README_system_macros.md
**Location:** `Micro-Agent-Local/system_tools/system_macros/`  
**Scope:** *Root-level, system-wide* macro registry and manager

> **High-contrast UI rule (always):** Wherever macro data is rendered (terminal pane, Macro Manager, popovers), keep text/background contrast high (light text on dark or dark text on light). *Never* ship low-contrast UI.

---

## What this folder is

This directory is the **global macro registry** for the entire workspace. It owns the **single source of truth** for capturing, reusing, and cleaning up small automation snippets (“macros”) that the Agent creates while working (navigation commands, safe file ops, quick backups, common shell routes, etc.).

- **One manager at root:** We keep exactly one macro manager here so retention rules, dedupe, and safety gates stay consistent across all agents.
- **Agent-local helpers allowed:** Agents may maintain agent-scoped helpers under `agents/<agent>/agent_tools/agent_macros/`, but they **register** them with this *root* registry so they show up in the unified Macro UI and benefit from centralized TTL/“bean counter” logic.
- **Authority-aware:** Destructive or sensitive macros always route through the **Pending Command** bar (Allow / Skip / Try Harder / Edit / Always Allow) before execution.

---

## Folder layout

```

system_tools/
└─ system_macros/
├─ README_system_macros.md   ← this file
├─ manager.py                ← global macro manager (capture/reuse/GC)
├─ store.jsonl               ← JSON Lines macro store (global)
├─ registry.md               ← optional human index (curated favorites, notes)
└─ examples/                 ← tiny, safe sample macros

````

> If you move the physical store elsewhere (e.g., `tools/macros/store.jsonl`), set the path in `manager.py` (`STORE = Path(...)`) and keep it consistent across the repo.

---

## Macro record format (JSONL)

Each line in `store.jsonl` is one macro:

```json
{
  "id": "nav:open-src-root",          // unique, human-readable id
  "macro": "cd src && code .",        // the actual command(s)
  "shell": "powershell",               // powershell | cmd | bash | wsl | auto
  "tags": ["navigation","editor"],     // for search & RAG
  "description": "Open VS Code in src/",
  "created": "2025-10-29T02:34:55Z",
  "last_used": "2025-10-29T03:05:12Z",
  "beans": 3,                          // usage counter bumped on reuse
  "pinned": false,                     // true = never GC
  "safety": {
    "destructive": false,
    "requires_approval": false         // force pending-command gate if true
  },
  "origin": {
    "agent": "default",
    "mode": "global"                   // global | independent
  }
}
````

---

## What `manager.py` does

* **Capture** a macro (`add`) with dedupe-by-`id` (or by `macro` text if id absent).
* **Reuse** a macro (`use`) to bump `beans` and update `last_used`.
* **List/Query** the store (`list`, with optional tag/shell filters).
* **Retain/Prune** via TTL + bean counter (see policy below).
* **Migrate** old stores (optional: `migrate` subcommand if format changes).
* **Validate** records (schema checks, fixups for missing keys).
* **Safe Dispatch (optional hook):** emits a “pending command” event rather than executing directly, so UI can gate execution via **Allow / Skip / Try Harder / Edit / Always Allow**.

### CLI (examples)

```bash
# Add a macro (PowerShell example)
python system_tools/system_macros/manager.py add \
  --id nav:open-src-root \
  --shell powershell \
  --macro "Set-Location src; code . " \
  --tags navigation editor \
  --description "Open VS Code in ./src"

# Mark a macro as used (increments beans, touches last_used)
python system_tools/system_macros/manager.py use nav:open-src-root

# List macros tagged 'navigation'
python system_tools/system_macros/manager.py list --tag navigation

# Prune per retention policy (see below)
python system_tools/system_macros/manager.py gc
```

> **Safety:** If `safety.requires_approval = true`, `use` should raise a “pending command” event rather than running, so the UI can blink **Allow** and wait for the user.

---

## Retention policy (TTL + bean counter)

* **Default TTL:** ~**24 hours** idle → candidate for GC.
* **Beans:** Each reuse bumps `beans`. Higher beans = more valuable → protect from GC.
* **Pinned:** `pinned: true` macros are never GC’d.
* **Idle-day exception:** If the system detects a gap where the user was away (>24h) and **no beans** could be set for that period, **skip GC once** so “yesterday’s” macros survive the return session.
* **Always-allow short list:** Approval history converts repeated prompts into “auto-run” if **Always Allow** is on; those macros are effectively protected unless explicitly revoked in **Agent Manager → Authority**.

---

## How agents plug in

* **Agent-local macro sets** live under `agents/<agent>/agent_tools/agent_macros/`.

  * When an agent boots, it can **register** those entries with the root manager (merged, but marked with `origin.agent` and `origin.mode`).
  * **Independent Agent Mode:** registration is still allowed, but flagged `origin.mode = "independent"` so UI scopes them to the active agent/repo only; sharing requires explicit promote-to-global.
* The **Macro UI** (left dock mini-app or terminal pane) queries the *root* store so your catalog remains discoverable and consistent.

---

## Authority & Pending Commands

* Any macro marked **destructive** or **requires_approval** must be routed to the **Pending Command** bar:

  * **Allow** (flashes blue) — run now
  * **Skip** — drop it
  * **Try Harder** — reattempt with a stronger, baked-in self-instruction
  * **Edit** — inline edit before execution (purple input outline)
  * **Always Allow** — whitelist future executions (stored in approval history)
* Approval history is visible/editable under **Agent Manager → Authority** and can be reset per agent or globally.

---

## Naming conventions

* IDs like `nav:open-src-root`, `fs:backup-settings`, `git:stage-from-editor`.
* Use **verbs** and **namespaces**; keep descriptions short and helpful.
* Tag with shell & domain: `["powershell","navigation"]`, `["git","windows"]`, etc.

---

## Examples (safe)

* `nav:open-src-root` → `cd src && code .`
* `backup:settings-json` → copy `config/*.json` to `backups/YYYYMMDD-HHMM/`
* `fs:open-active-repo` → reveal current repo in Explorer/Finder

> Keep examples **non-destructive**. Anything that writes/deletes **must** pass through the pending-command approval flow.

---

## UI integration

* **Macro pane** lists registry entries with:

  * id, shell, tags, short description
  * **beans** count, **last_used**, TTL status (e.g., “will prune in ~18h”)
  * run button (disabled until approved if gated), edit, pin/unpin
* **Search & filter** by text/tag/shell; sort by `beans`, `last_used`, or id.
* **Tooltips** show the full command and safety notes.

---

## Where to keep human notes

Maintain `registry.md` here to **curate favorites**, explain tricky macros, and warn about edge cases. It’s for humans; the JSONL store is for machines.

---

**Bottom line:** One **root** macro registry to capture, reuse, and responsibly prune small automations across all agents; agent-local macro helpers can exist, but this folder is the **hub** that keeps the ecosystem coherent.

```
If you want, I can also add a stricter `gc.py` that enforces the TTL/beans policy and emits a human report (kept/swept/pinned) after each run.
```



```
::contentReference[oaicite:1]{index=1}
```
