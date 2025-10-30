# README_agent_tools.md
> **Scope:** Per‑agent **tools** that the Agent can invoke, extend, or create at runtime. These are not global utilities (see `system_tools/` for those) but *scoped* helpers tied to the **current agent** and its style/persona.  
> **UI rule:** Any UI that surfaces these tools (Tools Manager, Macro Manager) **must use high‑contrast text** (light on dark or dark on light) with clear outlines for critical states.

---

## 1) What this folder is
**`agents/<this_agent>/agent_tools/`** is the private toolbox for one agent. It exists so each agent (default or styled) can carry its own helpers without colliding with other agents or with root‑level `system_tools/`.

- Tools here can **override** similarly named global tools or **extend** them with agent‑specific defaults and constraints.
- “Independent agent mode” (set in Agent Manager) lets an agent **refuse** use of `system_tools/` and rely **only** on `agent_tools/`.
- Conversely, Agent Manager can allow **global tools** while pinning specific agent tools to preferred versions.
- Tools may be **scripts**, **config files**, or **named sub‑tool folders** containing code, manifests, and docs. fileciteturn31file0

> Why separate? Styles/personas often need different behaviors (e.g., *StoryWriter* vs *MathAgent*). Keeping their tools close makes them portable, testable, and easy to audit.

---

## 2) Folder layout (reference)
```
agents/
  default/
    agent.yaml
    agent.md
    agent_tools/
      README_agent_tools.md   <-- this file
      agent_macros/           <-- tiny reusable action snippets (see §6)
        macros.yaml           <-- index/manifest for macros in this folder
        <macro_name>/
          macro.yaml          <-- single-macro manifest
          macro.py            <-- optional executable
          README_macro.md     <-- purpose, inputs/outputs, examples
      <tool_name>/
        tool.yaml             <-- manifest describing the tool
        tool.py               <-- implementation (CLI or importable)
        runner.ps1/.sh        <-- optional shell wrapper (per-OS adapters)
        prompts/              <-- optional prompt snippets for this tool
          ask.md
          do_work.md
          try_harder.md
        tests/                <-- optional self-checks (unit or smoke)
        samples/              <-- example inputs/outputs
        README_tool.md        <-- usage, args, authority notes, diffs policy
      _sandbox/               <-- scratch area; Tools Manager can scaffold here
      _archive/               <-- retired versions (auto-moved by Tools Manager)
```

---

## 3) What is a “tool”?
A **tool** is any callable capability the Agent can invoke with structured arguments and a predictable result. Examples:

- **Repo ops:** create/update files, apply diffs, format, lint, run tests, commit, branchless checkpoints.
- **RAG ops:** ingest docs, snapshot code, tag/rehash datasets, query memory.
- **OCR/vision:** dual‑pass OCR for screenshots, markdown‑first extraction, image hashing.
- **Terminal adapters:** safe wrappers for PowerShell/CMD/WSL/Linux; environment probing; dry‑run simulation.
- **Generators:** code scaffolds, README writers, manifest updaters, prompt composers.
- **Diagnostics:** diff explainers, failure triage, rollback preparation, “Implemented vs Missing vs Quarantined” reconciliation.

> Design intent: tools must be **composable**, **auditable**, and **authority‑aware** (see §7).

---

## 4) Tool manifest (`tool.yaml`) schema
Every tool must ship a manifest so the Tools Manager can index, validate, and present it in the UI.

```yaml
name: snake_case_name           # required, unique within agent_tools
version: 0.1.0                  # semver, bumped on any behavior change
summary: Short, imperative description
entry: tool.py:main             # <module>:<callable> or external CLI path
args:
  - name: path
    type: string
    required: true
    help: "Target file or folder."
  - name: mode
    type: enum
    values: [dry_run, apply]
    default: dry_run
io:
  stdin: false
  stdout: structured_json       # e.g., {"ok": true, "notes": "...", "diff": "..."}
  files_read:
    - "{repo}/**/*.py"
  files_write:
    - "{repo}/**/*"
safety:
  authority_required: write     # none | read | write | network | elevated
  dry_run_supported: true
  allowlist_key: "repo.write.files" # ties into Agent Manager allowlist
ui:
  category: "Repo / Diffs"
  badges: ["safe", "dry-run", "agent-local"]
  needs_high_contrast_note: true
tests:
  - name: smoke
    run: "python tool.py --mode dry_run --path {repo}"
docs: README_tool.md            # relative path
```

> **Note:** The **allowlist_key** integrates with the global **Authority/Approvals** flow so the UI can light up **Allow / Skip / Try Harder / Edit** exactly when needed.

---

## 5) Building & discovering tools (Tools Manager extension)
There is no standalone Tools UI yet. The Agent should **propose** a Tools Manager (left dock mini‑app) and then generate it as an extension window:

**Expected behaviors of Tools Manager:**
1. **Index & search** all `agent_tools/` and `system_tools/` manifests.
2. **Scaffold** new tools into `_sandbox/` with a guided wizard:
   - Choose template (repo‑op, RAG‑op, OCR, generator, adapter).
   - Auto‑create `tool.yaml`, `tool.py`, `README_tool.md`, and `tests/`.
   - Insert high‑contrast UI notes in docs.
3. **Validate** manifests (schema, entrypoint import, required files present).
4. **Run** tools in `dry_run` or `apply` with live logs to the console pane.
5. **Promote** sandbox tools → stable (create stamped version folder; move old into `_archive/`).
6. **Wire** selected tools into **Agent Manager** (enable/disable per agent, set defaults, pin versions).
7. **Expose prompts** for this tool (load `prompts/ask.md`, `do_work.md`, `try_harder.md`) and allow inline edits saved back to disk with diff history.

**Quickstart**  
- Open Tools Manager → **New Tool** → pick template → fill summary → generate.  
- Edit `tool.py`, run **Validate**, then **Dry Run**.  
- If OK, **Promote**. The tool appears under **Agent Manager → Tools** for that agent.  
- Optionally publish a *global* variant in `system_tools/` (see §9).

---

## 6) Agent Macros (`agent_macros/`)
**Macros** are tiny, reusable action snippets the Agent synthesizes during work (e.g., “fast open folder in VSCode,” “prettify then apply staged diff,” “snapshot + hash readme”).

**Structure**
- **`macros.yaml`**: index of known macros (name, tags, triggers, usage counts, TTL).
- **Per‑macro folder** with `macro.yaml`, optional `macro.py`, and `README_macro.md`.

**Retention (“bean counter”)**
- Every macro increments a **usage counter** when invoked.
- Macros not used within 24h **and** with `uses == 0` since last session **expire** (moved to `_archive/`).  
- If you were inactive for >24h (no sessions), last‑session “beans” persist so recently used macros are **not** purged on your return.

**Macro Manager UI (future)**
- Browse, pin, delete, promote ad‑hoc macros to stable tools.  
- Surface **diff previews** for macro‑generated edits before applying.  
- Tag editor & search (by command verbs, file targets, authority class).

**Example `macro.yaml`**
```yaml
name: open_repo_root
summary: "Open current repo root in system file explorer."
command:
  windows: 'explorer "{repo_root}"'
  linux: 'xdg-open "{repo_root}"'
  macos: 'open "{repo_root}"'
tags: ["nav", "os", "file-explorer"]
ttl_hours: 24
```

---

## 7) Authority & approvals (how tools run safely)
Tools participate in the **Pending Command** pipeline:

- When a tool requests an action requiring authority (see `tool.yaml.safety.authority_required`), the UI raises a **pending command** with buttons: **Allow / Skip / Try Harder / Edit**.
- **Allow** flashes blue every 2s when a decision is needed; **Edit** switches the input to purple “edit mode” (magenta outline) for inline command tweaking.
- **Always Allow** whitelists repeated actions via the **allowlist key**. First time still asks; subsequent uses auto‑approve (unless in **Independent Agent Mode**).
- All decisions are logged to the **ledger** and mirrored in `Implemented‑Updates.md` / **Quarantined‑Updates.md** when relevant.

---

## 8) Writing a tool (`tool.py`) – minimal template
```python
def main(path: str, mode: str = "dry_run"):
    """
    High-contrast note: any UI text rendered by this tool MUST remain readable.
    """
    from pathlib import Path
    target = Path(path)
    assert target.exists(), f"Target missing: {target}"

    # ... do analysis, compute a diff, produce a structured result ...
    result = {
        "ok": True,
        "notes": f"Scanned {target}",
        "diff": "",  # unified patch or change summary
        "authority": "write",   # echo what we needed
        "next": "Apply with mode=apply" if mode == "dry_run" else "Applied",
    }
    print(result)
    return 0
```

---

## 9) Relationship to `system_tools/`
- **`system_tools/`** are global, shared utilities (packagers, launchers, indexers).  
- **`agent_tools/`** are private, opinionated per‑agent helpers.  
- Naming collisions: prefer **agent‑local** unless an explicit **use global** flag is set in Agent Manager.
- Promotion path: a polished agent tool may be **published** as a global system tool (with broader docs and tests).

---

## 10) How the Agent creates new tools (self‑service)
When the Agent identifies a repeated pattern, it should **propose** a tool scaffold:
1. Draft `tool.yaml` + `README_tool.md` with clear intent, arguments, and safety.
2. Save into `_sandbox/` and request human **Allow** to proceed.
3. Generate minimal tests and a sample transcript demonstrating use.
4. Run **Validate → Dry Run**, then **Promote** on success.
5. Register the tool in **Agent Manager → Tools** and update this `README_agent_tools.md` with a one‑line catalog entry.

---

## 11) Catalog section (to be maintained by the Agent)
> The Agent should append an entry here per tool with name, version, summary, and last‑verified date.

- _Example_: **repo_apply_diff** `v0.2.1` — Apply unified diff to working tree with staged preview. Last verified: 2025‑10‑29.

---

## 12) Conventions & quality bar
- **Every tool has a README** explaining inputs, outputs, side effects, and authority needs.
- **Manifests are mandatory.** No manifest → tool is hidden in Tools Manager.
- **Dry‑run first.** Tools must support analysis without mutation.
- **High contrast text** in all UIs. Inline doc must include this rule.
- **Version everything**, archive old builds, include change logs in the tool README.
- **Tests** for non‑trivial tools (at least a smoke run).

---

## 13) Future work
- Package tools as signed bundles for sharing between agents.
- Telemetry to the console pane and `ledger.json` for auditable traces.
- Macro → Tool promotion flow with automatic doc and manifest synthesis.
- One‑click “Publish to system_tools/” with conflict checks and migration notes.
