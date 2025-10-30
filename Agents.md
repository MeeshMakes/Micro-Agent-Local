# Micro Agent Local — Operating Policy
Before any planning or edits, reread this file and Required-Updates.md.
Ensure every directory and script has a matching README_<name>.md.
If any are missing, generate them using the templates from the root README and append new paths to the Repository Index.
Keep logs append-only, keep UI high-contrast, and never edit without documentation.


# Agent Operating Procedures — Agent.md

*(Codex Planner / Executor Runtime Policy — local-first, VS-bridge aware, append-only, high-contrast)*

This document defines how you (Codex) must operate in this repository. You must re-read and obey it **every time** you run, plan work, write code, apply diffs, or update documentation.

---

## Required-Updates Sync Loop (MANDATORY)

`Required-Updates.md` (and any files under `Required-Updates/`) is the **active product spec**. It describes behaviors, UI surfaces, data/model flows, integration points, and required capabilities that must exist in the codebase. Your job is to implement **everything** it requires, **nonspecifically** (do not narrow scope to examples). When older and newer logic conflict, **newer logic near the bottom takes precedence**; preserve intent by appending merged notes as **Extended Merged Corrections** to the bottom of `Required-Updates.md`.

### 0) Always load current guidance

Before **any** planning, refactor, file edit, or code generation, you MUST re-read:

* **This `Agent.md`** (process, governance, safety, logging).
* **`Required-Updates.md`** (+ any files in `Required-Updates/`) — treat as the live contract.
* *(If present)* **Implemented-Updates.md** and **Missing-Updates.md** (completion ledger).
* *(If present)* **Dev_Logic/vs_bridge.md** (VS Mode contract: open/diff in VS Code; apply stays local).
* *(If present)* any local policy files under `.codex_local_agent/` (net policy, sandbox profiles, acceptance, impl_check).

Assume `Required-Updates.md` will evolve. You must not ignore new instructions.

### 1) Derive concrete work from the spec (append-only task stubs)

When asked to “start implementing missing changes” (or on each session start):

1. Parse **all** of `Required-Updates.md` (top→bottom). Newest truth is at the bottom; reconcile contradictions via **differential balancer** and record the merged ruling at the end of the file as “Extended Merged Corrections”.
2. For **every** unmet or partially met requirement, **append** a JSON object (“task stub”) to the queue:

   **Primary queue (canonical):**

   ```
   ./.codex_local_agent/memory/logic_inbox.jsonl
   ```

   *(If a legacy `memory/logic_inbox.jsonl` exists, mirror updates to that file as well; never delete either.)*

   **Task stub schema (minimal, testable, non-destructive):**

   ```json
   {
     "timestamp": "<UTC ISO>",
     "area": "<file | module | system area>",
     "need": "<what must exist or change>",
     "why": "Required-Updates.md:<section-or-key>",
     "status": "todo",
     "blocked_on": "",
     "modes": {"ask": true, "do_work": true}
   }
   ```

   * **Append-only.** Never overwrite or remove prior lines.
   * If something is partially complete, the stub must state precisely what remains.

### 2) Mode split — Ask (Plan) vs Do Work (Execute)

* **Ask / Plan mode:** THINK/RESEARCH only. Do **not** modify source. Produce **one** coherent master plan (files/dirs to touch, data schemas, UI hooks, acceptance entries, logs to update, expected diffs). **Stop** after emitting the plan.
* **Do Work / Execute mode:** Implement now. Pick the highest-priority open stub and act. Use guarded apply, reviewable diffs, and append-only logs.

You must **never** silently switch modes.

### 3) Implement incrementally, safely, and locally

For each selected stub:

* Create/modify **real code**, folders, JSON schemas, and UI as required by `Required-Updates.md`.
* Prefer **additive** changes; do not remove or break other flows unless the spec explicitly replaces them.
* **High-contrast UI is mandatory**: readable **light text on dark** backgrounds; **never** low-contrast pairings.
  *Inline code comments in every UI component must note and enforce this rule.*
* **Offline-first**: default deny network. Any online provider/model requires explicit enablement and audit trail (record tokens/costs if applicable).
* **Scope discipline**: operate only on the targeted files/entities declared by the tool or the spec; do not roam the filesystem.

If dependencies are missing:

* Mark the stub **blocked** in the queue (`status: "blocked"` with a short reason).
* Append prerequisite subtasks that will unblock it.

### 4) Log evidence immediately (append-only)

After each implemented change:

* **Changelog:** append a human-readable entry to:

  ```
  ./docs/changes/CHANGELOG.md
  ```

  Include **WHAT** changed (files, classes, data), **WHY** (spec citation), and **WHERE** (paths, UI surfaces).
* **Progress ledger:** append/update status in:

  ```
  ./docs/codex-local/required_updates_progress.md
  ```

  Use:

  * ✅ `<timestamp> <short summary> <Required-Updates.md section>`
  * ⏳ for in-progress
  * 🔒 for blocked
* **Session log:** append to:

  ```
  ./logs/session_<YYYY-MM-DD>.md
  ```

  with Objective, Files touched, Issues, Next steps.
* **Durable truths / architecture:** append newly confirmed rules to:

  ```
  ./.codex_local_agent/memory/bank_core.jsonl
  ```
* **Completion ledgers:** update **Implemented-Updates.md** / **Missing-Updates.md** as appropriate.

All of the above are **append-only**. Never delete or truncate history.

### 5) Acceptance & Implementation Check (final gate)

* For completed work, update simple per-scope acceptance records under:

  ```
  ./.codex_local_agent/acceptance/
  ```
* If changes carry risk, emit notes under:

  ```
  ./.codex_local_agent/diffqa/
  ```
* Before declaring a requirement **complete**, run the orchestrated checks under:

  ```
  ./.codex_local_agent/impl_check/
  ```

  Only when the gate is green may you update **Implemented-Updates.md** and mark the item ✅ in `required_updates_progress.md`.

### 6) Truthfulness of completion

You may **not** mark ✅ unless:

* The code for that behavior exists **in this repository**,
* It is **reachable at runtime** (UI path, callable code path, or invoked on demand),
* It **matches** the requirement described in `Required-Updates.md`,
* Acceptance and implementation checks (where applicable) have passed.

### 7) VS Bridge contract (awareness)

* When **VS Mode** is ON (see `Dev_Logic/vs_bridge.md`), **open files and diffs in VS Code**; rely on its editor/SCM UI.
* **Apply remains local** (inside our tool/Codex); record every operation in logs.
* Copilot/Agent (if present) may be used for **reasoning only** when explicitly invoked; it is **never** granted apply authority.

### 8) Governance & safety

* Never change authority, branching, or safety rules without following governance in `Agent.md` (feature branch if used, archive old policy, update docs).
* Keep **append-only** discipline across all logs and ledgers.
* Keep **high-contrast** accessibility at all times (explicit inline comments in UI code to ensure compliance).

---


## Start every session with this checklist

1. Re-read `Agent.md`, `Required-Updates.md`, and (if present) `Dev_Logic/vs_bridge.md`, `Implemented-Updates.md`, `Missing-Updates.md`.
2. Ensure the following exist (create if missing):

   ```
   ./.codex_local_agent/memory/bank_core.jsonl
   ./.codex_local_agent/memory/logic_inbox.jsonl
   ./docs/codex-local/required_updates_progress.md
   ./docs/changes/CHANGELOG.md
   ./logs/session_<YYYY-MM-DD>.md
   ./.codex_local_agent/acceptance/
   ./.codex_local_agent/diffqa/
   ./.codex_local_agent/impl_check/
   ```

   *(If legacy `memory/` files exist, mirror writes to them as well.)*
3. Rescan `Required-Updates.md` → append task stubs (append-only).
4. If **Ask** mode: emit one master plan and **stop**.
   If **Do Work** mode: implement the top stub now.
5. Log evidence, update ledgers, run acceptance/impl checks as needed.
6. Repeat until **every** requirement in `Required-Updates.md` is implemented and verified.


---


# Agents.md — Root Contract for All Agents (Local, Codex Local, Codex Online, Copilot)

> This file is **authoritative** for how every agent in this repo is expected to read, plan, execute, and document work. It unifies:
> - **Local Micro‑Agent** (this app),
> - **Codex Local** (the `.codex_local_agent` runtime),
> - **Codex Online** (cloud orchestrator),
> - **Copilot/Other IDE Assistants** (when present).
>
> It is optimized to help **Codex Online** consume `Required-Updates.md` and drive reliable delivery across the whole system.

---

## 0) Canon: The Trifecta (stay in lock‑step)

```
[ Required-Updates.md ]   → plan of record (backlog / intent)
[ README.md ]             → current reality (must match code + files)
[ Implemented-Updates.md ]→ shipped ledger (what landed, with links/diffs)
```

Rules of motion:
- If it’s **planned**, it belongs in **Required-Updates.md**.
- If it **exists now**, it must be described in **README.md** and indexed in **Implemented-Updates.md** (or explicitly marked TODO here until docs catch up).
- If blocked/denied: record in **Quarantined-Updates.md**. If still not delivered after a run: list in **Missing-Updates.md** with next steps.

All agents must enforce this loop every time they work. (See “Operating Contract” and the standard loop **Plan → Stage → Approve → Apply → Verify → Report**.) fileciteturn42file2


---


You are now responsible for implementing missing behavior.

1. Update `Agent.md`

   * If the section called **"Required-Updates Sync Loop (MANDATORY)"** is missing, incomplete, or different from policy, you must add/fix it now.
   * That section must say:

     * You MUST re-read both `Agent.md` and `Required-Updates.md` before planning or editing code.
     * You MUST extract missing behaviors from `Required-Updates.md` and append them as task stubs to `memory/logic_inbox.jsonl` (one JSON object per task; append-only).
     * You MUST implement those stubs in code, one by one, safely and incrementally (no reckless rewrites; preserve/extend existing behavior).
     * After each implemented change, you MUST log it in `docs/changes/CHANGELOG.md` and update `docs/codex-local/required_updates_progress.md` using ✅ / ⏳ / 🔒 without deleting history.
     * You MUST maintain high-contrast UI (readable light text on dark backgrounds; never low-contrast pairings).
     * You MUST operate offline-first; any online provider must be explicitly enabled and audited.
     * You MUST treat `Required-Updates.md` as the product contract; when older and newer logic conflict, the newer logic near the bottom takes precedence, while preserving intent via merged notes at the end.

2. Run first pass on `Required-Updates.md`

   * Read `Required-Updates.md` (and, if present, any files under `Required-Updates/`).
   * For every required behavior that is not fully present in this repo (generic: missing components, panels, dialogs, pipelines, capabilities, acceptance checks), generate a concrete task stub and append it to `memory/logic_inbox.jsonl`.
   * Immediately begin working the highest-priority stub in code.
   * Each time you finish a stub:

     * Append a CHANGELOG entry.
     * Update `docs/codex-local/required_updates_progress.md` with status (✅ / ⏳ / 🔒) and timestamp.
     * If you established a durable design rule, merge it into `memory/codex_memory.json`.
     * If applicable, update `Implemented-Updates.md` / `Missing-Updates.md`.

3. Standing rule going forward

   * Before ANY future code edit, you must re-read `Agent.md` and `Required-Updates.md`.
   * You must always:

     * keep `Agent.md` aligned with how you are actually operating (governance, authority, approvals),
     * keep `Required-Updates.md` as the source of truth for what still needs to exist,
     * keep `logic_inbox.jsonl` as the append-only queue of unimplemented work,
     * keep logs and progress append-only (never delete history).

Do not pause or ask for confirmation.
Your next action is: update `Agent.md`, generate task stubs from `Required-Updates.md`, start implementing.

---

1. **Be explicit.**
   Never apply a code or data change without updating the **full trace** in the same session. Every edit must be accompanied by:

   * `logs/session_<YYYY-MM-DD>.md` update (Objective, Files touched, Issues, Next).
   * `docs/changes/CHANGELOG.md` entry (what/why/where).
   * `docs/codex-local/required_updates_progress.md` status mark (✅ / ⏳ / 🔒 with timestamp + spec reference).
   * `./.codex_local_agent/memory/logic_inbox.jsonl` update (close or transition the relevant task stub; append new subtasks if discovered).
   * If a durable rule emerged, append it to `./.codex_local_agent/memory/bank_core.jsonl`.

2. **Be auditable.**
   Each meaningful action must leave a trail humans (and future agents) can reconstruct:

   * **What** changed (files, functions, schemas, UI elements).
   * **Why** it changed (quote or cite the `Required-Updates.md` section/keyword).
   * **Where** the diff lives (paths + Git commit/branch/sha; if a patch artifact was produced, reference its filename and location as noted in the session log).
   * **What’s next** (follow-ups, blocked items, acceptance tests still missing).
     Use **append-only** logs; never delete history.

3. **Be conservative with authority.**
   Expanding Codex’s power (auto-apply, multi-file sweeps, policy edits) requires:

   * A recorded decision in `logs/session_<YYYY-MM-DD>.md` (who/why/when).
   * A governance note in `Agent.md` (what changed in authority).
   * If using branches, move to a feature branch and document merge strategy; if branchless, clearly mark the escalation and add a reversal plan.

4. **Keep humans in the loop.**
   The repository must read like a **self-describing system**. Your trace should let a reviewer understand context, actions, and outcomes **without** asking you. Favor clarity over brevity. Maintain **high-contrast UI** everywhere you touch UI (readable light text on dark background; never low-contrast pairings—add inline comments in UI code to affirm this rule).

If you follow this procedure, the repo remains self-documenting, the project stays coherent, Codex evolves in a controlled way, and future iterations can resume exactly where you stopped—without losing intent, memory, safety, or design clarity.

---

**13. Required-Updates.md (Authoritative Work Queue)**

You MUST treat `Required-Updates.md` at the repo root (and any files in `Required-Updates/`) as the **binding source of truth** for current objectives. It is the **contract** for what must exist. Newer logic near the bottom overrides older guidance; when merging is prudent, record a short **Extended Merged Correction** at the end of `Required-Updates.md`.

**Review First**
Always (re)parse `Required-Updates.md` at the start of a session and **immediately before** you:

* Generate or modify task stubs for Codex execution.
* Edit anything under `AssetsMirror/Scripts/` or equivalent project content.
* Touch Codex-facing UI (e.g., CodexPanelWidget, ChatDockWidget), Diagnosis Bulletin, Plugin/Prompt Manager, or authority/policy logic.
* Change prompt text or templates.
* Toggle **VS Mode** (if applicable) or adjust bridge behavior (consult `Dev_Logic/vs_bridge.md`).

**Sync with Memory / Inbox**
For **each actionable item** in `Required-Updates.md`:

* If it will **not** be completed in this session, **append** a JSON object to `./.codex_local_agent/memory/logic_inbox.jsonl` (append-only) with:

  ```json
  {
    "timestamp": "<UTC ISO>",
    "area": "<file|module|UI|system>",
    "need": "<what must exist or change>",
    "why": "Required-Updates.md:<section-or-keyword>",
    "urgency": "high|med|low",
    "status": "todo",
    "blocked_on": ""
  }
  ```
* If it becomes a **standing rule** or architectural truth, also update `./.codex_local_agent/memory/bank_core.jsonl` so it persists across sessions.

**Trace Closure**
When you complete an item from `Required-Updates.md`, you MUST:

* Add a `docs/changes/CHANGELOG.md` entry (what changed, why, where).
* Mention it in today’s `logs/session_<YYYY-MM-DD>.md` under **Objective / Next Steps** (and list any follow-ups).
* Update `docs/codex-local/required_updates_progress.md` with ✅ and spec citation (keep older lines intact).
* If runtime behavior or UI changed, update the relevant doc(s) under `docs/codex-local/` (and note the **high-contrast** compliance).
* If acceptance or implementation checks exist for that scope, update the records under `./.codex_local_agent/acceptance/` and run the orchestrator under `./.codex_local_agent/impl_check/` before declaring the requirement complete.

**Conflict Resolution**
If `Required-Updates.md` conflicts with older behavior elsewhere:

* Treat `Required-Updates.md` as the **new directive**.
* Do **not** silently discard prior rules—archive or adjust them in `docs/codex-local/` (or `docs/codex-local/archive/` for policy-level deprecations).
* Note the deprecation/adjustment in `CHANGELOG.md`.
* If a merged approach is superior, add a concise **Extended Merged Correction** block at the end of `Required-Updates.md` summarizing the ruling.

**In summary:** `Required-Updates.md` is the live “**do this next**” list. Read it, act on it, **log** what you did, and push all unfinished work into persistent queues:

* Rules → `./.codex_local_agent/memory/bank_core.jsonl`
* Tasks → `./.codex_local_agent/memory/logic_inbox.jsonl`
  Maintain strict append-only discipline and keep the UI accessible (high contrast) at all times.


---


## Global Spec Enforcement and Self-Verification

This agent is responsible for ensuring the **live codebase actually matches the product spec** at all times, using **append-only** evidence and **offline-first** operation with **high-contrast UI** compliance.

### A. `Required-Updates.md` MUST exist (authoritative spec)

If `Required-Updates.md` is missing:

* **Create it immediately** using the most recent, authoritative intent in this order of precedence:

  1. `./.codex_local_agent/memory/bank_core.jsonl` (durable rules/architecture),
  2. `Implemented-Updates.md` / `Missing-Updates.md`,
  3. `docs/codex-local/**` (design/process docs),
  4. `Dev_Logic/**` (bridges, host/runtime notes),
  5. commit history and `CHANGELOG.md`.
* Insert (or update) a **`## Spec Verification Block`** at the end of `Required-Updates.md`. If missing, **add it now** (see D).

When older and newer logic conflict, **newer logic near the bottom overrides**. Preserve intent by appending a concise **Extended Merged Correction** at the bottom (append-only).

### B. Continuous gap hunting (before any change)

Before **any** planning, refactor, prompt update, UI change, or script edit:

1. Re-read **`Agent.md`**.
2. Re-read **`Required-Updates.md`**, including the **Spec Verification Block**.

Then perform a **gap analysis**:

* Compare **spec vs reality** across:

  * Existence of required files/folders/schemas,
  * Reachability of UI surfaces (buttons/dialogs/panels) at runtime,
  * Data/model flows and bridges (e.g., VS Mode routing),
  * Acceptance/impl-check artifacts.
* For **every** missing or partial requirement, **APPEND** a concrete task stub to the canonical queue:

  ```
  ./.codex_local_agent/memory/logic_inbox.jsonl
  ```

  *(If legacy `memory/logic_inbox.jsonl` exists, mirror append there too.)*

**Task stub (example, concrete & testable):**

```json
{"timestamp":"<UTC ISO>","area":"UnityLinker UI","need":"Implement Link Project dialog with Import/Export/Just Link and hierarchy snapshot","why":"Required-Updates.md:<section>","status":"todo","blocked_on":""}
```

Immediately begin work on the highest-priority open stub (unless in Ask/Plan mode).

### C. Implement safely, locally, and log truthfully

For each stub:

* Modify code **in place** to satisfy the spec; prefer **additive** changes.
* Do **not** remove other flows unless the spec **explicitly** replaces them.
* Maintain **offline-first** and **high-contrast UI** (readable **light text on dark**; never low contrast; include inline UI comments noting the rule).

On completion:

* **Progress:** append ✅ with timestamp + spec citation to:

  ```
  ./docs/codex-local/required_updates_progress.md
  ```
* **Changelog:** append a human-readable entry to:

  ```
  ./docs/changes/CHANGELOG.md
  ```

  Include **what/why/where** and any artifacts (paths, temp patch files, commit id).
* **Session:** append to:

  ```
  ./logs/session_<YYYY-MM-DD>.md
  ```

  Objective, Files touched, Issues, Next steps.
* **Durable rule:** if a persistent rule was created/confirmed, append to:

  ```
  ./.codex_local_agent/memory/bank_core.jsonl
  ```
* If the task is not finishable yet, update the stub with `"status":"blocked"` and a brief reason; **append** prerequisite subtasks.

### D. Keep the **Spec Verification Block** synced (at the end of `Required-Updates.md`)

`Required-Updates.md` MUST end with:

```
## Spec Verification Block
STATUS: <IN PROGRESS | ALL SPEC REQUIREMENTS IMPLEMENTED AND VERIFIED>
SNAPSHOT: <UTC ISO>

### Outstanding Requirements (Checklist)
- [ ] <req-id or short title> — <section/keyword> — Acceptance: <brief AC> — Evidence: <paths/links> — Last Checked: <UTC ISO>
- [ ] ...

### Extended Merged Corrections
- <YYYY-MM-DD>: <short ruling that reconciles older vs newer text; why; what changed>

### Evidence Index (recent)
- CHANGELOG: docs/changes/CHANGELOG.md (latest entries with timestamps)
- PROGRESS: docs/codex-local/required_updates_progress.md
- SESSIONS: logs/session_<YYYY-MM-DD>.md
- ACCEPTANCE: ./.codex_local_agent/acceptance/
- IMPL-CHECK: ./.codex_local_agent/impl_check/
```

Your duties:

* **Maintain** this block as a **live ledger** (append-only).
* When a behavior is completed, convert its checklist item to `[x]` and link evidence (progress line, changelog entry, acceptance file, impl-check report).
* If you evolve behavior beyond original wording, record a one-line **evolution note** here (do not silently declare done).

### E. Declaring full satisfaction (hard gate)

Only when **every** requirement in `Required-Updates.md`:

* exists in repo code,
* is **reachable at runtime** (UI path / callable path),
* passes acceptance/impl-check where applicable,

then:

1. Set **STATUS** to `ALL SPEC REQUIREMENTS IMPLEMENTED AND VERIFIED` in the Spec Verification Block and add a one-line rationale (why this is true; point to evidence).
2. Log the event in:

   * `./docs/codex-local/required_updates_progress.md` (✅ full),
   * `./docs/changes/CHANGELOG.md` (summary + evidence pointers).

No assumptions; no “probably fine.” Evidence or it isn’t done.

### F. Recurring duty (every session & before each edit)

* Re-read `Agent.md`.
* Re-read `Required-Updates.md` and the Spec Verification Block.
* Re-open gaps and **append** new task stubs for drift or new requirements.
* Keep `logic_inbox.jsonl` (tasks) and `bank_core.jsonl` (rules) current.
* Honor **VS Bridge** rules when in VS Mode (open/diff in VS; apply remains local; all actions logged).
* Preserve **append-only** discipline and **high-contrast** accessibility across all UI edits.


---

## Codex Local Runtime, Per-Script Agents, and Chat / Editing UX

*(Append this as a new major section in Agent.md and/or Required-Updates.md so Codex implements it.)*

This section defines how **Codex Local** runs, what it’s allowed to touch, how per-script `Agent.md` files work, how new scripts are initialized, and how chat modes must behave in the UI. All behavior must honor **offline-first** operation and **high-contrast** UI (readable light text on dark; never low-contrast).

---

### 1. Codex Local: Scope and Responsibility

**Codex Local is not the same as Codex Online.** They serve different jobs.

* **Codex Online** (remote automation/planner) may shape architecture, author new subsystems, refactor structural code in the repo, and maintain global tooling.
* **Codex Local** is a surgical assistant that runs on the user’s machine and edits **only the currently selected script/asset/config area** for the active project.

  * Allowed scope:

    * gameplay/system scripts,
    * project assets/data files belonging to the **active** project,
    * the project’s mirror inside our tool (e.g., `AssetsMirror/**`).
  * Operates via **linear, targeted diffs** (no repo-wide refactors).
  * Works strictly **inside the selected entity’s boundary** as designated by the tool’s selection state.

**Codex Local does not rewrite the authoring suite itself.** It updates project content (scripts, configs, data) under guardrails; global tool changes remain Codex Online’s responsibility.

---

### 2. Codex Local: Execution Model

We run **one** Codex Local process instance on the machine.

* A single long-lived runtime (hosted by `Dev_Logic/vs_codex_local.py`) serves all local edit requests.
* The app/tool communicates with that runtime through a local bridge (stdin/stdout/pipe or local loopback), mirroring the behavior described in `Dev_Logic/vs_bridge.md`.
* The supervisor GUI marks which project is **active**, which script/entity is **selected**, and the entity’s location in the **project mirror**.
* When invoking Codex Local, the tool provides:

  * the current script/entity source,
  * the entity’s per-script `Agent.md`,
  * relevant summaries/errors/task stubs,
  * the working copy path inside the mirror,
  * the intended diff target(s) to sync back to the real project.

Codex Local then:

1. Reads provided context (`Agent.md`, script text, task stubs, errors, summaries).
2. Proposes diffs or replacements.
3. Returns the new text/diff to the tool.
4. The tool versions it under `AssetsMirror/.../versions` (or equivalent).
5. The tool syncs/exports into the real project as needed (so the IDE/build system recompiles).

**Hard boundary:** Codex Local never roams the filesystem. The tool **must** specify the exact target entity and paths; Codex Local edits **only** that scope.

---

### 3. Per-Script Agent Files (`Agent.md` per script/entity)

Every tracked script/entity has a local `Agent.md` colocated with its dataset, e.g.:

```
AssetsMirror/
  Scripts/
    PlayerController/
      versions/
      chats/
      codex_tasks/
      error_buckets/
      Agent.md
```

The per-script `Agent.md` MUST describe:

* The script’s role and responsibilities.
* Conventions and constraints relevant to that script (lifecycle methods, serialization rules, physics/input/animation expectations, naming conventions).
* Scene wiring expectations and external dependencies (components/game objects, managers).
* Guardrails (e.g., “may patch functions, but may not rename public APIs without review”).
* Any local acceptance checks specific to that script.

Codex Local MUST read this file **before** editing the script and SHOULD update it when responsibilities evolve (append-only notes; do not delete history).

---

### 4. Agent Template Library (category templates)

Ship default **script templates** and **Agent templates** in a central safe-source area:

```
Templates/
  default_scripts/
    MainMenuController.cs
    MainMenuController.Agent.md
    SettingsMenuBootstrap.cs
    SettingsMenuBootstrap.Agent.md
    PlayerController.cs
    PlayerController.Agent.md
    ...
```

When the user creates a new script via Script Builder:

1. Create the script folder under `AssetsMirror/Scripts/<ScriptName>/`.
2. Copy the matching C# (or language) template into `versions/` as v0001.
3. Copy the matching `*.Agent.md` into the script folder as its per-script agent spec.
4. Register it in the project index so selection loads the editor, chat bucket, and capabilities.

---

### 5. Script Builder UI + Category Selection

Provide a **Script Builder** window:

* Inputs: Script Name, Script Category (from templates), Target hierarchy role.
* On confirm:

  * Create folder structure under `AssetsMirror/Scripts/<ScriptName>/...`.
  * Install first version and per-script `Agent.md` template.
  * Update project/hierarchy index so selection activates editor/chat/capabilities for the new script.

The Script Builder must follow high-contrast rules (light text on dark; clear focus outlines).

---

### 6. Per-Script Agent Editor (non-blocking popup)

When a script is selected, show **Edit Agent.md**. Clicking opens a **modeless** popup:

* Editable text view of the script’s `Agent.md`.
* Save writes back atomically to the file (append changes; retain history).
* Main GUI remains usable (hierarchy, code editor, chat, Codex panel). No blocking.
* High-contrast: large, readable fonts; strong contrast against background.

This allows iterative refinement: the user can ask the LLM to improve the Agent.md and paste it in without stopping other work.

---

### 7. Chat Modes (Global / Script / Free)

Support multiple chat presences:

1. **Script-Specific Chat**

   * Context: currently selected script/entity, its `Agent.md`, versions, error buckets, and task stubs.
   * Buttons include (non-exclusive):

     * **Ask (Plan)** — think/research only; produce plans, no edits.
     * **Propose Diff** — generate a candidate patch for the selected script.
     * **Open in VS** — route the current file/diff to VS Code (VS Mode).
     * **Apply Staged Diff** — apply the reviewed patch under local safeguards.
     * **Rollback / Load Version** — pick prior version from `versions/`.
     * **Edit Agent.md** — open the modeless per-script Agent editor.
     * **Log Note** — append a note to the session log and/or script chat bucket.
   * Behavior: All actions must log to `docs/changes/CHANGELOG.md` and `logs/session_<TODAY>.md` as appropriate; acceptance checks update per script.

2. **Global Chat**

   * Scope: repository-level reasoning, non-script-specific planning, and spec Q&A.
   * Buttons: **Ask (Plan)**, **Generate Task Stubs** (append to `memory/logic_inbox.jsonl`), **Open VS Mode**, **Export Plan to Required-Updates.md Extended Corrections**.
   * Guardrails: No direct edits to project content; route implementation through task stubs and Do Work paths.

3. **Free Chat**

   * Unscoped conversation. No automatic application of patches.
   * Can promote notes into `memory/logic_inbox.jsonl` upon user request.

**Ask vs Do Work split:**
*Ask (Plan)* produces one coherent plan and stops. *Do Work* implements under safeguards (diff review, acceptance, logging).

**VS Bridge:**
When **VS Mode** is ON (as per `Dev_Logic/vs_bridge.md`), open files and diffs in VS Code; apply remains in the local tool (Codex Local). Copilot/Agent may be used for **reasoning only** when explicitly invoked; never granted apply authority. All operations must be logged.

---

### 8. Acceptance, Logging, and Safety (always on)

* **Append-only**: `memory/logic_inbox.jsonl`, `docs/codex-local/required_updates_progress.md`, `docs/changes/CHANGELOG.md`, and daily `logs/session_<TODAY>.md` are append-only. Never delete prior history.
* **Acceptance**: for completed work, record/update acceptance items (per script or global). Maintain simple JSON/markdown acceptance records that the tool can surface.
* **Implementation Check**: run implementation checks before claiming completion for any scope; only then update `Implemented-Updates.md`.
* **Offline-first**: default deny network. Any online model/provider requires explicit enablement and an audit entry (token/costs if applicable).
* **High-contrast UI**: all text must remain readable (light on dark). Never render low-contrast pairs. Include inline comments in UI code noting this rule.

---

### 9. Continuous Operation

* Before each edit session: re-read `Agent.md` and `Required-Updates.md`.
* Rescan the spec, append new task stubs for unmet items, implement the next highest-priority stub, and log.
* Never silently change governance/authority; follow `Agent.md`’s rules for any policy updates (branching/approvals/archival).
* Continue until every requirement in `Required-Updates.md` has a ✅ with evidence and the implementation check passes.


---

## 1) Agent Landscape & Intent

### 1.1 Local Micro‑Agent
- Repo‑aware assistant with persistent memory, diff‑first workflow, task feed + approval gates, OCR dataset, and project bootstrapper. Everything is transparent and **high‑contrast**. fileciteturn42file5

### 1.2 Codex Local (`.codex_local_agent/`)
- A runtime with machine config (`agent.yaml`), human system card (`agent.md`), durable task index, macros registry, dataset/memory, logs, and ledgers. These files are **authoritative** and must be kept in sync. fileciteturn42file2

### 1.3 Codex Online (orchestrator)
- Researches, plans, and **lands** improvements directly to `main` (with tests and auditability); coordinates with Local to execute tasks and surface artifacts. fileciteturn42file6

### 1.4 Copilot / Other IDE Assistants
- May be used as auxiliary editors; they must respect the same **Trifecta** and authority gates when invoked via this system (read‑only by default unless routed through our Agent Manager).

---

## 2) Modes, Toggles, and Safety Gates

### 2.1 Plan vs Action (Codex) & Ask vs Do Work (App)
- **Plan / Ask**: analyze and produce tasks/diffs **without** writing or running shell. Prefer fewer, richer tasks (anti‑swarm). fileciteturn42file0
- **Action / Do Work**: perform the approved work **now**, narrate with complete files/diffs/commands and verification. fileciteturn42file0

**Authority gates** (per action): Inline **Allow**, **Always Allow** class, or policy in `agent.yaml`. “Allow” flashes blue only when an approval is required; **Edit** enables magenta edit mode for pending commands. fileciteturn42file2

**Environment/UI toggles** (Codex Online): `CODEX_PLAN_MODE`, `CODEX_AUTHORITY`, `CODEX_TARGET_BRANCH=main`. Show mode, branch, authority in UI. fileciteturn42file7

---

## 3) Required Assets & Directory Contracts

### 3.1 `.codex_local_agent/` (must exist; auto‑seed if missing)
```
agent.yaml                 # machine config (model/provider/endpoint, authority, styles, datasets, paths)
agent.md                   # human system card (rules, policies, safety, loop)
Task-Index.json            # durable task ledger (ids, status, approvals, timestamps)
macros/registry.jsonl      # helper scripts (nav/edit/backup) + usage counters & risk
dataset/memory.jsonl       # per‑turn RAG rows (markdown, image paths, OCR_fast/full, tags, hashes, ts)
logs/session_<DATE>.md     # chronological operation log
```
Keep these in sync with the Trifecta; create sensible defaults if absent. fileciteturn42file2

### 3.2 “Living instructions” workspace (when Codex Online upgrades Local)
Maintain `/docs/codex-local/` with playbooks (runbooks), RFCs (options/choice/tests/rollout/rollback), experiments (gated by tests), and a changelog. fileciteturn42file6

### 3.3 Single‑branch policy
`main` is the working branch of record; use safe push; trigger **Overwrite Guard** if a write would discard newer code already in `main`. fileciteturn42file4

---

## 4) Online ↔ Local Interop (Who does what)

- **Codex Online**: propose tasks (Plan) and land verified changes (Action) into `main`. fileciteturn42file7  
- **Codex Local**: generate artifacts (logs/errors/datasets), apply code changes to `main` only when explicitly instructed and approved. Surface what landed. fileciteturn42file6

**Session loop** (canonical): read memory/logic inbox → Plan (emit tasks; run allowed) → verify → document → Action (apply) → verify → document → update memory + logs → commit. fileciteturn42file6

---

## 5) The “Implement Required Updates” Button (batch execution flow)

When the operator presses **Implement Required Updates**:

1. Scan `Required-Updates.md` from top to bottom.  
2. For each bucket:  
   - Skip if already in **Implemented-Updates.md**.  
   - If quarantined as `blocked_by_user`, queue for re‑ask.  
   - If new, create a **Task Feed** card proposing diffs/commands.  
3. Run tasks sequentially; authority gates apply. Pending commands appear inline with **Allow / Skip / Try Harder / Edit**.  
4. On success: append to **Implemented-Updates.md**, regenerate **Missing-Updates.md**, and clear any quarantine item.  
5. On failure/denial: log in **Quarantined-Updates.md** and list in **Missing-Updates.md**.  
6. Index every task in `.codex_local_agent/Task-Index.json` with id, source bucket id(s), timestamps, final status, last authority decision. fileciteturn42file9

> This batch runner is distinct from normal Ask/Do Work sends and supports **Start All** to walk all staged tasks while pausing for approvals as required. fileciteturn42file11

---

## 6) Multi‑Agent Chain (beyond a single Agent.md)

Load configs in order to form an effective persona for the current repo:  
`agents/base.md → agents/local.md → agents/project.md → agents/*.md (or index.yaml)` with deterministic merge/conflict rules. Feature flag: `CODEX_AGENT_CHAIN=on`. fileciteturn42file6

**Root Agents.md** (this file) sits above that chain and applies to **all** agents; per‑agent READMEs/MDs may refine but **not** contradict this contract.

---

## 7) Macros, Datasets, and Memory

- **Macros**: keep a registry with usage counters; design for navigation/edit/backup; gate risky macros with approvals and authority. Garbage‑collect by usage (“beans”) over 24h. fileciteturn42file2
- **Datasets**: OCR and chat markdown feed `dataset/memory.jsonl` and `chat_history.md` for future recall and RAG. fileciteturn42file5
- **Logs**: every run must write `logs/session_<DATE>.md` with objective, unresolved sub‑goals, file‑scoped snippets, and “Suggested Next Coding Steps.” fileciteturn42file0

---

## 8) UI & High‑Contrast Policy

All surfaces must maintain high color contrast; approval states use strong cues (blue **Allow**, magenta **Edit**). Always declare the active style pack and deviations in README. fileciteturn42file2

---

## 9) Failure & Recovery

- If a change threatens `main` integrity: trigger **Overwrite Guard**, emit status, open reconciliation (Plan) or repair (Action).  
- If partial completion occurs: mark **blocked** with last successful step, error excerpt, and unblocking action. fileciteturn42file7

---

## 10) End‑of‑Run Discipline (what every agent must do)

- Re‑read root **README.md** and reconcile with the code; prefer code for runtime facts, then update docs or open tasks accordingly.  
- Append an **Implementation Check** footer to `Required-Updates.md` summarizing state; if everything shipped, write:  
  `✅ As of <timestamp>, Required Updates are fully implemented. README reflects current system.`  
- Ensure gaps are recorded in **Missing-Updates.md**; blocks in **Quarantined-Updates.md**.  
- Update **Implemented-Updates.md** with task ids, diffs, rationale, and links. fileciteturn42file2

---

## 11) Minimal `agent.yaml` (baseline contract)

```yaml
llm: { provider: ollama, model: qwen2.5-coder:latest, endpoint: http://127.0.0.1:11434 }
modes: { ask_mode: true, do_work_mode: true }
authority: { ask_first: true, always_allow: false, independent_agent_mode: true }
paths:
  repo_root: "."
  agent_root: "./.codex_local_agent"
  dataset_dir: "./.codex_local_agent/dataset"
  logs_dir: "./.codex_local_agent/logs"
style: { active: "default_dark_hicontrast" }
macros: { registry: "./.codex_local_agent/macros/registry.jsonl" }
```

> The machine config above is the starting point; Codex Online may propose upgrades (models, endpoints) via Required‑Updates with tests and rollbacks. fileciteturn42file2

---

## 12) Quick Start for Codex Online (TL;DR)

1. Read: this `Agents.md`, root `README.md`, `.codex_local_agent/agent.md` + `agent.yaml`, and the whole Trifecta.  
2. Plan (Ask/Plan): generate a compact but complete task set for **Required‑Updates.md** buckets.  
3. Action (Do Work/Action): stage diffs, request approvals, run commands; verify with tests.  
4. Document: update **README.md** (current), **Implemented-Updates.md** (ledger), regenerate **Missing‑Updates.md**, and adjust `.codex_local_agent/*` artifacts.  
5. Commit/push to `main` with safe push; log session summary + next steps. fileciteturn42file6

---

### Appendix A — Single‑branch & Context Capture

Before edits: fetch/prune, checkout `main`, rebase/pull; capture `git status`, short log, and diff; record objective and snippets in session log; mirror TODOs to `memory/logic_inbox.jsonl`. fileciteturn42file0

### Appendix B — Implement Button Pseudocode

```
for bucket in walk_required_updates():
    if is_implemented(bucket): continue
    if is_quarantined_by_user(bucket): queue_reask(bucket); continue
    task = stage_task(bucket)
    show_task_card(task)
    if run_authorized(task): apply_and_verify(task); mark_implemented(task, bucket)
    else: mark_quarantined_or_missing(task, bucket)
    index_task(task, bucket)  # Task-Index.json
```
See §5 for semantics and ledgers. fileciteturn42file9

---

## Final Rule

**This file is binding** for all agents operating in this repo. If any behavior here conflicts with a styled agent’s local `Agent.md`, this root **Agents.md** takes precedence unless `Required-Updates.md` explicitly grants an override for that style, with tests and a rollback path. fileciteturn42file2
