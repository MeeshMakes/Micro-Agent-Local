# System Tools (root-level) — `README_system_tools.md`

> **High-contrast UI rule (accessibility):** Any UI that a tool renders **must** use light text on dark or dark text on light—never low-contrast pairings. Re-state this rule in each tool’s README and, if a tool has a UI, in code comments right where colors are set.

---

## What this folder is

This folder contains **system-wide tools** that any agent or project task can use. Think of them as **global utilities**—repo diagnostics, diff/patch helpers, OCR pipelines, file crawlers, packaging/build helpers, etc.  
They are shared once here and consumed by multiple agents without duplication.

- Repository path: `Micro-Agent-Local/system_tools/`
- README naming follows your rule: the file is named after the folder ⇒ **`README_system_tools.md`**

---

## Naming & scope (decision)

We separate global tools from per-agent tools:

- **Root global tools (final name):** `system_tools/`
- **Per-agent tools (inside each agent):** `agents/<agent_name>/agent_tools/`

If your repo still has an older `tools/` at root, treat it as a **compat alias** to `system_tools/` (see *Migration* below).

**Why this split?**

- Avoids name/behavior collisions with agent-specific helpers.  
- Lets **Agent Manager** enable/disable global tools per agent (authority model).  
- Keeps shared tools updated in one place.

---

## Relationship to per-agent tools

- **`system_tools/`** = global/shared utilities, centrally maintained.  
- **`agents/<agent_name>/agent_tools/`** = tools designed or tuned **for that agent** only (may depend on the agent’s style/persona, private configs, or experimental features).

**Resolution order when an agent calls a tool by name:**

1. If **Independent Agent Mode** is **ON** → search **only** `agent_tools/` (local, sandboxed).  
2. Otherwise → search `agent_tools/` first (agent-specific override), then fall back to `system_tools/`.

> This rule ensures a styled agent can shadow a global tool with a local variant without breaking others.

---

## Authority, isolation & Pending Command pipeline

The **Agent Manager** exposes:

- **Authority mode** per agent: `read_only` | `ask_first` | `full_auto`  
- **Independent Agent Mode** (on/off): if **on**, the agent is confined to `agent_tools/` and **cannot** call `system_tools/`.

When `ask_first` is active, any tool invocation flows through the **Pending Command** bar (Allow / Skip / Try Harder / Edit).  
- **Allow** flashes blue every ~2s when approval is required.  
- **Try Harder** re-prompts the agent with a stronger, built-in “push harder” directive for the same intent.  
- **Always-Allow** entries can be remembered (per-agent or global) so common, safe tool calls don’t keep prompting.  
- The allow-list is reviewable from Agent Manager and can be cleared per agent or globally.

> **Reminder:** even with **Full Auto**, the first time a *new* high-impact capability is attempted, the agent should surface a one-time approval to record it in the allow-list.

---

## Folder layout (template)

```

system_tools/ <tool-name-1>/
README.md          # what/why/how, inputs/outputs, examples, side-effects, safety notes
tool.yaml          # manifest (schema below)
run.py             # or run.ps1 / run.bat; entrypoint must accept --help
src/               # implementation code
tests/             # optional: self-/smoke-tests <tool-name-2>/
...

````

**`tool.yaml` manifest example**
```yaml
name: diff_patch
version: 0.1.0
description: "Create and apply unified diffs to files/folders."
entrypoint: "run.py"          # relative to the tool folder
args_schema:
  - name: mode
    type: enum
    values: [create, apply, check]
  - name: target
    type: path
  - name: patch
    type: path
safety:
  dry_run_supported: true
  requires_network: false
  writes_outside_repo: false
ui:
  needs_high_contrast: true
  presents_diff_split_view: true
````

**Conventions**

* Every tool ships a **mini README** (purpose, args, outputs, side-effects).
* Prefer **idempotent** behavior and `--dry-run`/`--check` flags for anything that mutates files.
* **Logging:** emit structured logs to `./.codex_agent/logs/tools/<tool-name>.log`.
* **Non-zero** exit codes on error; print concise remediation hints.
* **Security:** no network, no writes outside the active repo **unless** the authority policy (and `tool.yaml`) explicitly allow it.
* **Accessibility:** never lower UI contrast; include explicit comments where colors are set.

---

## How agents discover and call tools

Agents read tool roots from `agent.yaml` (or the project’s active config):

```yaml
# agent.yaml (excerpt)
tool_roots:
  - "./system_tools"                     # global utilities
  - "./agents/${AGENT_NAME}/agent_tools" # agent-scoped tools

authority_policy:
  mode: ask_first            # read_only | ask_first | full_auto
  independent_agent_mode: false
  pending_command_timeout_sec: 120
```

At runtime, the agent:

1. Resolves the tool name to a folder under the configured `tool_roots`.
2. Loads `tool.yaml` to validate args and safety flags.
3. If `ask_first`: surfaces a **Pending Command** card and runs only on approval.
4. Executes the entrypoint; captures stdout/stderr/exit code; logs results; updates diffs if applicable.

---

## Integration examples

### 1) `diff_patch` (global)

**Purpose:** Create/apply unified diffs to help the agent propose, review, and stage code changes.

**Quick start**

```bash
# Create a diff between working tree and HEAD into patches/out.diff
python run.py create --target . --patch patches/out.diff --check

# Apply a diff (dry-run first)
python run.py apply --target . --patch patches/out.diff --dry-run
```

**UI:** Show a **split view** (left=original, right=proposed) with added/removed line counts and a **Stage from Editor** action. Keep text high-contrast.

---

### 2) `fast_ocr` (dual OCR)

**Purpose:** Provide a fast, markdown-oriented OCR pass with a fallback “accurate” pass.
**Flags:** `--mode fast|accurate|auto` (default `auto` → fast then cascade on low confidence).
**Output:** raw text + a `*.md` snippet suitable for the chat feed (with image thumbnails when available).

> This tool feeds the RAG dataset: store image path(s), OCR text, markdown block, tags/hashes for semantic recall.

---

### 3) Macros & tool synergy

Global tools can **produce or consume** macros:

* Navigation helpers, staging helpers, “open & patch & verify” sequences, etc.
* Save macros in `system_macros/` (see `README_system_macros.md`) with timestamps/usage counters so the “bean-counter” can prune unused items after 24h (unless the user was inactive; then retain last-used set for the next session).

---

## Migration guide: `tools/` → `system_tools/`

1. **Rename** folder at repo root: `tools/` → `system_tools/`.
2. **Update** paths in:

   * `agent.yaml` (`tool_roots`)
   * Any scripts that previously referenced `tools/`
3. (Optional) Keep a small `tools/README.md` that points here (or a shim that warns and forwards).
4. **Smoke test**: run a sample tool (`--help`, then a dry-run) via the agent to verify discovery.

---

## README policy (folder-level)

Per your repo rule, **every folder contains a README named after the folder**:

* This file: `README_system_tools.md` (lives in `system_tools/`)
* Agent-scoped example: `agents/<agent>/agent_tools/README_agent_tools.md`

Each tool folder also contains its own `README.md` that documents **purpose, arguments, outputs, side-effects, authority requirements, and UI contrast notes**.

---

## Final notes

* Prefer clarity over brevity in tool names and docs.
* Keep tool UX consistent with the rest of the app (split diff view, strong outlines for edit/approval states).
* Log everything critical; avoid silent failures.
* When in doubt, **defer to agent authority policy** and require approval for anything high-impact.

```
```
