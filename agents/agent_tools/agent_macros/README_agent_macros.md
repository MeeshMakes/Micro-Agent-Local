# README_agent_macros.md
_Per-Agent Macro Workspace (capture ▸ reuse ▸ govern ▸ evolve)_

> High-contrast UI rule (standing order): any surface that renders macro text, logs, or buttons **must** use light text on dark or dark on light—never low contrast. Inline developer comment: “Text must never share or nearly share the same color/value as its background.”

This folder is the **agent-scoped macro space** for the current Agent. It is where the Agent records and reuses the tiny “helper scripts” it invents while working—navigation, file edits, backups, environment checks, quick tests, etc. When **Independent Agent Mode** is ON, these macros stay private to this Agent/repo; when OFF (and allowed), they can be surfaced for reuse by other agents.

At the **root** of the repo there is one **global macro manager** (`system_tools/system_macros/manager.py`) that lists agents and centralizes capture/reuse/cleanup. This folder focuses on _local content_; the global manager provides TTL + bean-counter retention, authority hooks, and UI surfacing.

---

## What’s included here

```
agent_tools/
└─ agent_macros/
   ├─ README_agent_macros.md
   ├─ index.md
   ├─ store.jsonl                 # agent-scoped macro registry (JSON Lines)
   ├─ quarantine.jsonl            # macros held for repair/review
   ├─ blocklist.jsonl             # macros forbidden to run
   ├─ beans.json                  # usage counters & last_used
   ├─ lexicons/
   │  ├─ README_lexicons.md
   │  ├─ powershell.json
   │  ├─ bash.json
   │  └─ cmd.json
   ├─ examples/
   │  ├─ README_examples.md
   │  ├─ macro_nav_open_src_root.json
   │  ├─ macro_fs_list_configs.json
   │  ├─ macro_code_inline_edit.yaml
   │  └─ macro_git_status_and_branch.yaml
   ├─ templates/
   │  ├─ README_templates.md
   │  └─ macro.schema.yaml
   ├─ compiled/
   │  ├─ README_compiled.md
   │  ├─ code_patch_and_test.v1.yaml
   │  └─ run_compiled_macro.py
   ├─ tools/
   │  ├─ README_tools_bridge.md
   │  └─ manager_client.py
   └─ scripts/
      ├─ apply_text_patch.py
      └─ run_tests_stub.py
```

---

## Store format (JSONL)
Each line is a JSON object with a minimal schema:

{
  "macro_id": "nav.open-src-root.v1",
  "body": "cd src && code .",
  "shell": "powershell",
  "tags": ["navigation","editor"],
  "risk": "low",
  "created": "2025-10-30T02:34:37Z",
  "last_used": null,
  "beans": 0,
  "first_seen_task_id": "T-0000"
}

Additional keys are allowed (e.g., `requires`, `preflight`, `success`, `rollback`). Complex macros live in `*.yaml` files (see **compiled/**).

---

## Authority & Safety
Macro execution obeys the same approval pipeline as regular “pending commands”:
**Allow / Skip / Try Harder / Edit / Always Allow**, recorded in the authority ledger.  
- **Quarantine:** macro fails safety checks or needs human revision → put in `quarantine.jsonl` with `reason` and `next_attempt` notes.  
- **Block:** policy requires “never run” → record fingerprint in `blocklist.jsonl` with rationale.  
- **Repairs:** propose preflight checks or safer variants; on approval move back to `store.jsonl` and update `index.md`.

Destructive macros must prompt visibly and require preconditions (e.g., backup path exists) before they run.

---

## Retention (TTL) & Beans
- Default TTL for **unused** macros: **24h**.  
- Each reuse increments **beans** and updates `last_used`.  
- **Idle-day exception:** if the tool wasn’t used during the last day (no beans set), skip cleanup so the prior session’s macros remain available.

These knobs live in `agent.yaml` → `macros:` config.

---

## Compiled macros (multi-step YAML)
Large operations are defined in YAML (`compiled/*.yaml`) and executed via a thin runner (`run_compiled_macro.py`). Steps can:  
- traverse folders and resolve targets,  
- apply text patches / line edits,  
- run tests (`scripts/run_tests_stub.py` or your real runner),  
- loop with guardrails,  
- use lexicons to port commands across shells,  
- produce **pending commands** for human approval where required.

---

## Quickstart

1. **Add a tiny macro** (safe, non-destructive):
   - Append to `store.jsonl` with macro_id + body (examples provided).
2. **Use a compiled macro**:
   - Read `compiled/code_patch_and_test.v1.yaml`.
   - Dry run: `python compiled/run_compiled_macro.py --macro compiled/code_patch_and_test.v1.yaml --dry-run`.
3. **Promote or quarantine**:
   - Move great, reusable macros into the global manager store (promote).  
   - Quarantine anything that needs fixes; add a `reason` and propose a patch in the YAML notes.
4. **GC and persistence**:
   - Let TTL prune unused, unpinned macros. Pinned/always-allow macros stay.
   - All material changes log into your Implemented/Quarantined/Missing documents as part of the Trifecta (Required ▸ Current ▸ Implemented).
