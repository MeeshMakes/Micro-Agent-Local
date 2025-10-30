# `agents/agent_roster` — Canonical Home of **Named, Deployable Agents**

> **Purpose:** This folder is the roster of *actual* agents you can run. Each subfolder is a fully-specified agent: its `agent.yaml` (behavior), `agent.md` (rules & purpose), prompts, tools/macros, runtime loop, datasets, ledgers, and indexes. These are composed from the **default** agent template plus any **agent_styles** overlays, then tracked, audited, and archived over time.

---

## Why separate **roster** from **default** and **agent_styles**?
- **default** (single source template): Baseline files that always work; the last-resort agent that must not break. We clone from here.
- **agent_styles/** (family overlays): Reusable “style” packs (story, math, game-dev, refactorer, etc.) that *augment* a cloned agent (behavioral overlays, prompt deltas, skill toggles, heuristics).
- **agent_roster/** (this folder): Concrete, named agents born from **default** + optional **agent_styles**. These are the live, evolving, audit-able workers you assign to tasks.

Keeping these separated ensures we can:
1) evolve the **template** without corrupting working agents,
2) iterate **styles** independently,
3) promote *only validated* compositions into this **roster** for daily use and benchmarking.

---

## Directory layout (authoritative)
```
agents/
├─ default/                       # the “must always work” template (golden baseline)
├─ agent_styles/                  # reusable style overlays, categorized
└─ agent_roster/                  # ← THIS FOLDER (deployable agents live here)
   ├─ index.json                  # roster catalog (name → path, style_id, tags, health)
   ├─ archives/                   # checkpoints & diffs for retired/older builds
   ├─ {agent_name}/
   │  ├─ README_{agent_name}.md   # living doc for this agent (what/why/how)
   │  ├─ agent.yaml               # merged behavior: default + styles + local overrides
   │  ├─ agent.md                 # human-readable rules, intent, constraints
   │  ├─ prompts/
   │  │  ├─ ask.md                # “research-only” prompt scaffold
   │  │  ├─ do_work.md            # “plan/execute” scaffold (+ approvals semantics)
   │  │  ├─ try_harder.md         # stronger retry script (escalation knobs)
   │  │  └─ README_prompts.md     # explains how to tune/extend prompts per agent
   │  ├─ tools/
   │  │  ├─ agent_macros/         # agent-scoped macro snippets & compiled macros
   │  │  ├─ lexicons/             # terminal & environment lexicons
   │  │  └─ README_agent_tools.md # how tools plug into this agent
   │  ├─ runtime/
   │  │  ├─ loop.py               # approval-aware autonomous loop (Ask/Plan/Act)
   │  │  ├─ README_runtime.md     # lifecycle, states, safety, telemetry
   │  │  └─ logs/                 # session logs (stdout/stderr/events)
   │  ├─ datasets/
   │  │  ├─ memory.jsonl          # chat memory shards (markdown turns + tags + hashes)
   │  │  ├─ rag/                  # OCR text, thumbnails, embeddings, indexes
   │  │  └─ README_datasets.md    # what is stored; retention & privacy notes
   │  ├─ ledgers/
   │  │  ├─ authority.json        # allowlist decisions, scopes, expirations
   │  │  ├─ macro_usage.json      # per-macro “beans” (use counts, last_used)
   │  │  └─ approvals.json        # pending/approved/denied command records
   │  └─ indices/
   │     ├─ tags.json             # quick lookup by skills, domains, repos
   │     └─ health.json           # last check, error rates, pass/fail tests
   └─ README_agent_roster.md      # ← this document
```

> **Naming:** Use `snake_case` for `{agent_name}` (e.g., `math_agent`, `story_writer_v2`). Keep names descriptive and task-focused.

---

## Lifecycle (Create → Evolve → Retire)
### 1) Create (promote into roster)
- In **Agent Manager**, choose **New Agent from Template**:
  - Base: `agents/default/`
  - Optional style(s): `agents/agent_styles/{family}/{style}` (multi-select allowed)
  - Name: `my_new_agent`
- The system composes a merged `agent.yaml` (default + styles + overrides), scaffolds prompts, tools, runtime, datasets, and ledgers under `agent_roster/my_new_agent/`.
- A roster entry is added to `agent_roster/index.json` with tags, style lineage, and health=“draft”.

### 2) Evolve (learning + governance)
- During work, the agent:
  - appends to `datasets/memory.jsonl` and `chat_history.md` (external log),
  - learns macro opportunities (saves snippets to `tools/agent_macros/snippets/`),
  - increments macro usage “beans” in `ledgers/macro_usage.json`,
  - records approvals in `ledgers/authority.json` (scoped allowlists, expirations),
  - updates `indices/tags.json` as it discovers domain tags.
- Periodically, **checkpoints** are written to `archives/` (diffs of `agent.yaml`, prompts, ledgers), using time‑bucket policy (e.g., 2d, 1d, 6h, 1h).

### 3) Retire (archive or quarantine)
- If an agent becomes obsolete or unsafe, move it to `archives/` with a final health report.
- Macros with low beans (unused ≥24h) may be auto-pruned or quarantined (see **Macro governance** below).

---

## Autonomy & selection
- **Fast selection:** The system consults `agent_roster/index.json` (skills/tags/health) to pick the *best* agent for a task; falls back to **default** if uncertain.
- **Independent Agent Mode:** Agents may run with independent authority ledgers, ignoring global allowlists unless explicitly linked in **Agent Manager**.
- **Style switching:** Agents can hot‑swap styles (overlay deltas) if the task context shifts (e.g., code → story). Style swaps are logged in `health.json` and `archives/`.

---

## Authority model (summary)
- First-time actions **must** prompt for approval (Allow / Skip / Try Harder / Edit).
- “Always Allow” only activates after the *first* explicit Allow for a given capability/signature (recorded in `ledgers/authority.json`).
- Global resets can disable capabilities and auto‑quarantine related macros until re‑approved.

---

## Macro governance (agent scope)
- **Where:** `tools/agent_macros/` contains
  - `snippets/` → small, reusable atomic actions (e.g., open repo, select file, patch line, run tests)
  - `compiled/` → composable, multi-step macros (“recipes”) chaining snippets
  - `blocked/` → macros disabled by policy/authority reset
  - `quarantine/` → macros under investigation (failures, side effects)
  - `README_agent_macros.md` → usage docs & DSL guide
- **Retention:** Macros accrue beans in `ledgers/macro_usage.json`. Unused ≥24h + no session activity ⇒ keep last‑session beans and defer pruning until the next active day; otherwise, prune or quarantine with rationale.
- **Lexicons:** Terminal/OS lexicons live in `tools/lexicons/` and are referenced by macros for portable commands.

---

## Datasets & RAG
- Every message (and every image OCR pass) is appended to `datasets/memory.jsonl` with tags and hashes; thumbnails are saved; embeddings are refreshed asynchronously.
- The agent consults its dataset and **system-level** datasets when answering **Ask** (research) and when planning **Do Work** (execution).

---

## Command palette (macro-aligned verbs)
> These appear in UI menus and as macro invocations. They are also stored as examples for the LLM to follow.

- `agent roster new --name NAME --style STYLE_A,STYLE_B`
- `agent roster activate --name NAME`
- `agent roster audit --name NAME` → writes `indices/health.json`
- `agent roster retire --name NAME --reason` → moves to `archives/`
- `agent macros learn --from Required-Updates.md`
- `agent macros import --from agents/agent_tools/agent_macros/compiled/RECIPE.yaml`
- `agent authority reset --scope NAME|global`
- `agent style swap --name NAME --to STYLE`

*(If not yet implemented as CLI, these exist as runnable macros.)*

---

## Minimal examples

### `agent.yaml` (merged outcome)
```yaml
name: "story_writer_v2"
style_lineage:
  - default@2025-10-27
  - agent_styles/story/writing_v2@2025-10-29
capabilities:
  - code_read
  - code_edit_guarded
  - write_docs_markdown
  - run_tests_with_supervision
approval_policy:
  mode: "ask_first"
  auto_allow_after_first_ok: true
memory:
  dataset: "./datasets/memory.jsonl"
runtime:
  loop: "./runtime/loop.py"
  approvals_ledger: "./ledgers/authority.json"
```

### `agent_macros/compiled/patch_line.yaml` (recipe)
```yaml
name: patch_line
steps:
  - use: snippets/resolve_repo_root.yaml
  - use: snippets/select_file.yaml
  - run: snippets/apply_diff.yaml
  - run: snippets/run_tests.yaml
  - run: snippets/verify_no_errors.yaml
on_failure:
  - quarantine_macro: true
  - log_to: ledgers/approvals.json
```

### `agent_macros/snippets/apply_diff.yaml` (atomic)
```yaml
goal: "Apply a unified diff to a target file and confirm line numbers match."
inputs: [file_path, unified_diff_text]
shell:
  - "git --no-pager diff --no-index --color-words --unified=0"
  - "python - <<'PY'\n# apply diff safely with line guards...\nPY"
safety:
  requires_approval: true
  rollback: true
```

---

## Maintenance
- Keep `index.json` current; stale entries should mark `health: 'stale'` with last_seen timestamp.
- Ensure `archives/` has compressed diffs (space-aware) and redact secrets in ledgers/datasets when archiving.
- Periodically reconcile **roster** with **agent_styles** (record style drift or promote back improvements).

---

## FAQ
**Q:** Should the roster live under `agent_styles/` instead?  
**A:** No. Styles are reusable overlays; the roster are *concrete* agents built from those overlays + default. Separation keeps provenance clean and upgrades manageable.

**Q:** Can a roster agent be style-agnostic?  
**A:** Yes—omit `style_lineage` and rely purely on `default`. Add styles later with `style swap` if needed.

**Q:** How does this link to the rest of the system?  
**A:** Agent selection, approvals, macros, datasets, and archives are all part of the larger “Trifecta”: `Required-Updates.md` (desired), `README.md` (current), `Implemented-Updates.md` (done). The roster is the *actor* that moves items from desired → done.

---

> **Implementer note:** On first run, if this folder is empty, seed a `samples/` agent (e.g., `story_writer_v0`) to demonstrate the structure and allow quick promotion to production.
