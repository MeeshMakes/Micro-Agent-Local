# README_agent_macros.md
_Per-Agent Macro Workspace (capture ▸ reuse ▸ govern ▸ evolve)_

> **High-contrast UI rule (standing order):** Any surface that renders macro text, logs, or buttons **must** use light text on dark or dark on light—never low contrast. Inline developer comment: _“Text must never share or nearly share the same color/value as its background.”_ :contentReference[oaicite:0]{index=0}

---

## 1) What this folder is

This folder is the **agent-scoped** macro space for the current Agent. It is where the Agent records and reuses the tiny “helper scripts” it invents while working (navigation, file edits, backups, environment checks, etc.). Think of these as **micro-procedures** that make the Agent faster the second time it encounters a similar task. When **Independent Agent Mode** is ON, these macros stay private to this Agent/repo; when OFF (and allowed), they can be surfaced for reuse by other agents. :contentReference[oaicite:1]{index=1}

At the **root** of the repo there is a **single global macro manager** (`system_tools/system_macros/manager.py` in your layout) that knows how to enumerate loaded agents and centralize capture/reuse/cleanup. Agent folders like this one focus on _local macro content_, while the root manager provides consistent TTL + bean-counter retention, authority hooks, and UI surfacing. **We do not duplicate the global manager script here.** :contentReference[oaicite:2]{index=2}

---

## 2) How this relates to the Root Macro Manager

- **One global manager; many agent stores.** The system-level registry/manager lives at root and is the single source of truth for capture, reuse, and GC policies. Agents register their local stores with it. :contentReference[oaicite:3]{index=3}
- **CLI pattern (root manager against this agent store):**
  ```bash
  # add a macro body to THIS agent's local store
  python system_tools/system_macros/manager.py agents/<this_agent>/agent_tools/agent_macros/store.jsonl add "cd src && code ."

  # mark usage (increments beans, updates last_used)
  python system_tools/system_macros/manager.py agents/<this_agent>/agent_tools/agent_macros/store.jsonl use "cd src && code ."
````

The reference manager uses a configurable `STORE` path and writes JSONL entries containing the macro body and usage metadata. 

---

## 3) Folder layout (recommended)

```
agent_tools/
└─ agent_macros/
   ├─ store.jsonl                 # agent-scoped macro registry (JSON Lines)
   ├─ index.md                    # human-readable mini index of curated/pinned macros
   ├─ quarantine.jsonl            # macros held for review (blocked/unsafe/needs fix)
   ├─ blocklist.jsonl             # hard-blocked macros that must never run
   ├─ beans.json                  # usage counters (if you keep them per-agent)
   ├─ lexicons/
   │  ├─ powershell.json          # command verbs & idioms per shell
   │  ├─ cmd.json
   │  └─ bash.json
   ├─ examples/                   # tiny safe samples (open file, list dir, etc.)
   └─ templates/
      └─ macro.schema.yaml        # canonical schema for complex macros
```

> Some repos place the physical store at `tools/macros/store.jsonl`; keep paths consistent and pass the explicit path to the manager when targeting a specific store. 

---

## 4) Authority & Safety model

Macro execution obeys the same approval pipeline as regular “pending commands”: **Allow / Skip / Try Harder / Edit / Always Allow**, recorded in the **authority ledger**. Destructive macros must prompt visibly and require preconditions (e.g., backup path exists) before they run. **Never invent authority.** 

* **Authority ledger location:** `agents/authority/ledger.json` (see `agent.yaml`). 
* **Independent Agent Mode:** isolates approvals + macros to this repo/agent; toggle in the Agent Manager. 

**Quarantine/Block rules**

* **Quarantine** a macro if it fails safety checks, collides with revoked approvals, or needs human revision. Keep the body + metadata in `quarantine.jsonl` with a `reason`, `first_seen_task_id`, and next-attempt notes.
* **Blocklist** a macro when policy requires “never run” (e.g., it deletes large trees). Store its fingerprint and rationale in `blocklist.jsonl`.
* The Agent may propose **repairs** (e.g., add preflight checks); once approved, move from `quarantine` back to `store.jsonl`. Log the action to Implemented/Quarantined/Missing documents for auditability. 

---

## 5) Retention (TTL) & Bean Counter

* Default TTL for **unused** macros: **~24h**.
* Reuse increments **beans** and updates `last_used`.
* **Idle-day exception:** if the user hasn’t opened the tool in >24h and no beans are set yet, **skip cleanup** so yesterday’s macros remain available.
  These knobs are part of the agent/runtime configuration and should be set in `agent.yaml` → `macros: { ttl_hours, bean_keep_if_no_usage_day }`. 

> The Required Updates spec explicitly calls for bean tracking and daily GC. Keep pinned / always-allow macros across GC. 

---

## 6) What goes in a Macro (schema)

**Minimal JSONL record (one per line in `store.jsonl`):**

```json
{
  "macro_id": "nav.open-src-root.v1",
  "body": "cd src && code .",
  "shell": "powershell",
  "tags": ["navigation","editor"],
  "risk": "low",
  "created": "2025-10-29T00:00:00Z",
  "last_used": null,
  "beans": 0,
  "first_seen_task_id": "T-0021"
}
```

**Extended YAML macro (in `templates/macro.schema.yaml`)** might include:

```yaml
macro_id: fs.backup.settings.v1
title: "Backup settings to dated folder"
shell: powershell
requires:
  - repo_root
authority: ask_first      # ask_first | always_allow | blocked
risk: medium
preflight:
  - "Test-Path \"$RepoRoot\\settings\""
steps:
  - "New-Item -ItemType Directory -Force \"$RepoRoot\\backups\\$(Get-Date -Format yyyy-MM-dd)\""
  - "Copy-Item \"$RepoRoot\\settings\\*.json\" \"$RepoRoot\\backups\\$(Get-Date -Format yyyy-MM-dd)\\\" -Force"
success:
  - "Test-Path \"$RepoRoot\\backups\\$(Get-Date -Format yyyy-MM-dd)\\\""
rollback:
  - "Write-Host 'Manual restore from backups folder' # non-destructive macro"
lexicon_tags: ["fs","backup","powershell"]
```

> Destructive macros must route through the pending-command flow with visible confirmation. Record each run (macro_id + task_id) into Implemented/Quarantined/Missing cross-references. 

---

## 7) Lexicons (teach the Agent the language of each shell)

Macos should reference per-shell **lexicons** (`lexicons/powershell.json`, `lexicons/bash.json`) so the Agent can synthesize correct, idiomatic commands for Windows CMD/PowerShell/WSL. Lexicons are simple verb catalogs:

```json
{
  "open_in_editor": ["code \"{path}\"", "notepad \"{path}\""],
  "make_dir": ["mkdir \"{path}\"", "New-Item -ItemType Directory -Force \"{path}\""],
  "copy_glob": ["cp \"{src}\" \"{dst}\"", "Copy-Item \"{src}\" \"{dst}\" -Force"]
}
```

The Agent uses lexicon verbs to compose steps and to auto-port macros between shells when possible. (The global macro spec and base docs already require per-shell tagging + environment detection.) 

---

## 8) Command-style quick reference (do this)

**Capture**

* `add "<command>"` → append macro to `store.jsonl` (dedupe by fingerprint).
* `add --id nav.open-root --shell powershell --tags nav,editor "<body>"`.

**Reuse**

* `use "<body|macro_id>"` → bump beans, set `last_used`.

**Promote**

* `promote --from agents/<this>/agent_tools/agent_macros/store.jsonl --to tools/macros/store.jsonl --id <macro_id>` (requires approval).

**Quarantine / Block**

* `quarantine --id <macro_id> --reason "<why>"`.
* `block --id <macro_id> --reason "<why>"` (update blocklist.jsonl).

**Revive**

* `revise --id <macro_id> --add-preflight "<cmd>" --note "<fix>"` → moves from quarantine to store after approval.

**GC**

* `gc --ttl 24h --keep-pinned true --respect-idle-day true`.

> The root manager exposes these subcommands and takes an explicit `STORE` path so it can operate on this agent’s macro store or the global one. Keep usage consistent with the system macros README. 

---

## 9) Tying macros into the Trifecta (Required ▸ Current ▸ Implemented)

* When a macro is created/used during **Implement Required Updates**, log the `macro_id` + `task_id` in **Implemented-Updates.md**.
* If a macro is blocked, add an entry to **Quarantined-Updates.md** with reason + next attempt.
* If a macro was expected but not found/usable, emit a TODO in **Missing-Updates.md**.
  This keeps audit trails crisp and recoverable. 

---

## 10) Example macros (safe)

* `nav.open-src-root` → `cd src && code .` (non-destructive).
* `fs.list-configs`  → `dir settings/*.json` (PowerShell) or `ls settings/*.json` (bash).

> Keep examples non-destructive. For anything that writes/deletes, force the **pending-command** confirmation flow. 

---

## 11) How the runtime should treat these files

* On startup, **ensure** `store.jsonl`, `quarantine.jsonl`, `blocklist.jsonl`, and `lexicons/` exist; create with sensible defaults if missing.
* Respect `agent.yaml` `macros:` config: `enabled`, `store_path`, `ttl_hours`, `bean_keep_if_no_usage_day`. 
* Surface macros in the **Agent Manager** and **Command Palette** with counts, pins, run buttons, and tooltips from `index.md`. Keep the palette high-contrast. 
* Cross-link macro runs into the operation logs (`logs/session_<date>.md`) and the change log (`docs/changes/CHANGELOG.md`) when they materially modify files. 

---

## 12) When to migrate between Agent and Global

* **Promote up** (agent → global) when a macro proves broadly useful and safe; convert shell specifics into lexicon-backed templates first.
* **Demote down** (global → agent) when a macro is environment-fragile or policy-tight.
* Use the **authority ledger** to record the decision (who/when/why). 

---

## 13) How this grows over time (versioning & archives)

All agents evolve; that’s why we keep **Archived_Agents** with versioned diffs for configs, directives, tools, and macros. Snapshot before major macro migrations, then prune archives that become destructive to future logic. The Agents README explains the broader roster/styles flow and archival expectations. 

---

## 14) Appendix — Minimal Python usage (calling the root manager from code)

```python
# manager_client.py (example)
from subprocess import run

STORE = r"agents\\<this_agent>\\agent_tools\\agent_macros\\store.jsonl"
MANAGER = r"system_tools\\system_macros\\manager.py"

def add_macro(body: str):
    run(["python", MANAGER, STORE, "add", body], check=True)

def use_macro(key: str):
    run(["python", MANAGER, STORE, "use", key], check=True)
```

This delegates logic to the **single** global manager while operating on this agent’s store. (Keep the manager’s interface identical across repos.) 

---

### Bottom line

**This folder is where the Agent becomes faster.** Capture small wins, reuse them safely, keep the registry clean, and wire every run back into the Trifecta so the whole system stays auditable and sharp. 

```

If you want, I can also hand you a `store.jsonl` seed and tiny `lexicons/powershell.json` starter, but this README is ready to ship as-is.
::contentReference[oaicite:24]{index=24}
```
