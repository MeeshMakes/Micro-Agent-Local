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
