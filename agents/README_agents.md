```markdown
# Agents — Home for Personas, Styles, Tools, and Self-Growth

> This directory is the **authoritative home for Agents**. It contains the default/bedrock template, shared styles, shared tools, and a roster of named, cloned Agents. Treat this README as the Agent’s passport: it tells the Agent (and you) **what lives here, how to read it, and how to evolve it**. :contentReference[oaicite:0]{index=0}

---

## Why every folder here has a README_<name>.md

Agents learn by reading. Clear READMEs at each level prevent guesswork and drift.

- **This file (`README_agents.md`)** explains the entire `agents/` scope: how Agents are defined, loaded, styled, versioned, and archived. :contentReference[oaicite:1]{index=1}
- **Each subfolder** must include a purpose-specific README named after the folder, e.g.,  
  `agent_roster/README_agent_roster.md`, `agent_styles/README_agent_styles.md`,  
  `authority/README_authority.md`, `agent_tools/README_agent_tools.md`, etc.  
  This convention gives the Agent an explicit handle to route logic to the right component. :contentReference[oaicite:2]{index=2}

**High-contrast rule (UI & docs):** Never render low-contrast text; default to light text on dark or dark on light. (Inline reminder for any UI the Agent generates.)

---

## Canon files & merge order (what “base/local/project” do)

These three markdown files form the **configuration canon** the Agent reads in order—use them instead of hardcoding per-machine or per-repo rules:

1. `agents/base.md` — **Global canon / Layer 1.** Defines the Required-Updates Sync Loop, authority & safety, macros archive defaults, styles index, the Trifecta duties, logging lanes. **Always read first.** :contentReference[oaicite:3]{index=3}  
2. `agents/local.md` — **Machine/Operator layer.** Paths/endpoints that vary by workstation (e.g., Ollama URL, local folders like `Dev_Logic/`, chat/rant feeds, macro store path). :contentReference[oaicite:4]{index=4}  
3. `agents/project.md` — **Repo binding.** Runtime entry points, memory file locations, and the statement that **`README.md` is the “Current” truth in the Trifecta**. :contentReference[oaicite:5]{index=5}

> **Merge order:** `base.md → local.md → project.md`. This keeps universal rules stable, then applies machine specifics, then project bindings. :contentReference[oaicite:6]{index=6}

---

## Folder layout (authoritative map)

```

agents/
├─ default/                  # The bedrock Agent you ship with (stable fallback)
│  ├─ agent.yaml             # Model/provider/endpoints, limits, authority+macro+runtime config
│  ├─ Agent.md               # Directives, tone, safety policy, Trifecta duties, self-growth rules
│  ├─ prompts/               # ask.md / do_work.md / try_harder.md (operator-facing loops)
│  ├─ agent_tools/           # Private tools for this Agent (safe helpers, runners, schemas)
│  ├─ agent_styles/          # Style packs local to this Agent (optional)
│  └─ datasets/              # Agent-scoped memories (RAG indexes, tags, hashes)
│
├─ agent_roster/             # ✅ All **named** cloned Agents live here (one folder per Agent)
│  ├─ math_agent/
│  ├─ story_writing_agent/
│  └─ ...                    # Each with its own agent.yaml, Agent.md, tools, styles, README
│
├─ agent_styles/             # Shared style packs reusable by multiple Agents (global)
├─ agent_tools/              # Shared tools callable by Agents (non-destructive preferred)
├─ authority/                # Global authority ledger + policy docs for this repo
├─ Archived_Agents/          # Frozen snapshots of retired personalities (for audit/restore)
├─ base.md                   # Canon Layer 1 (global rules)
├─ local.md                  # Canon Layer 2 (machine/operator specifics)
├─ project.md                # Canon Layer 3 (repo binding)
└─ README_agents.md          # ← you are here

```

> Your repository may also have **root-level `tools/`** (system tools) outside `agents/`. Keep the distinction: **root tools = global**, **`agent_tools/` = local to a persona**. :contentReference[oaicite:7]{index=7}

---

## Default vs. Named Agents (where new Agents live)

- **`agents/default/`** is the **bedrock Agent**: the stable, always-works persona. You **do not** keep additional named Agents here.  
- When you “clone from default” to make a new persona (e.g., *Math Agent*, *Story Agent*), place it in **`agents/agent_roster/<agent_name>/`** with its own `agent.yaml`, `Agent.md`, `agent_tools/`, `agent_styles/`, and a **`README_<agent_name>.md`** describing its role and scope.

> This avoids the fragmentation you noted: default remains canonical; **all named Agents are stored under `agent_roster/`** with clear separation and documentation.

---

## Styles (global vs. per-agent) and the rename to `agent_styles`

- For clarity, **styles within `agents/` are named `agent_styles/`**. There are two places they can live:
  - **Global styles:** `agents/agent_styles/` — reusable packs (e.g., *coding*, *research*, *math*). Index them (e.g., `agent_styles/index.json`).
  - **Per-Agent styles:** `agents/<agent>/agent_styles/` — overrides or additions specific to one Agent.
- A style pack may include: **prompt overlays**, **tool allow-lists**, **UI markdown/render hints**, **memory preferences**. Selection can be static (pinned) or dynamic (Agent Manager chooses per task).

> The prior examples used `styles/`; this README standardizes on `agent_styles/` for the `agents/` tree to avoid ambiguity. (If you still have `styles/` from earlier drafts, migrate and update references.)

---

## Tools vs. Agent Tools vs. Macros

- **Global tools:** `agents/agent_tools/` (and/or root `tools/`) — non-destructive helpers shared across Agents.
- **Per-Agent tools:** `agents/<agent>/agent_tools/` — domain-specific helpers for that persona.
- **Macros:** tiny, reusable action snippets captured during work (navigation, patch, snapshot).  
  Store and dedupe macros; enforce TTL **24h**; retain last-used macros if the user didn’t run the system during a day (bean-keep rule). Surface in UI and Agent Manager. :contentReference[oaicite:8]{index=8}

---

## Authority & Independent Agent Mode

- All risky actions go through **Pending Command** controls: **Allow / Skip / Try Harder / Edit / Always Allow**.  
- **Independent Agent Mode** isolates approvals & macros per Agent; **Global** mode allows reuse where safe.  
- Record approvals in `authority/ledger.json` and keep human-readable notes of why something was approved/denied. :contentReference[oaicite:9]{index=9}

---

## The Trifecta (how Agents stay aligned)

To prevent drift and keep context stable, Agents maintain a three-way sync:

1. **`Required-Updates.md`** — backlog of *desired* changes (human intent).  
2. **`Implemented-Updates.md`** — ledger of what’s *actually done* (with paths/diffs/notes).  
3. **`README.md` (current)** — **the truth** of how the system works now.  

**Agent duties:** read Required; after execution, append Implemented; then update the relevant README to mirror the current state. Blocked items go to **Quarantined**; still-missing items go to **Missing**; inspiration goes into **Dev_Logic** for later harvesting. 

---

## Local vs. Online Codex Agents (both must be aware of each other)

- You may also maintain a **root-level `Agent.md`** for **Codex Online**. The **local** Agents should be aware this file exists and may reference it to align tone & governance, but **local authority & file paths are governed by `agents/base.md → local.md → project.md`** to avoid cross-environment mistakes. :contentReference[oaicite:11]{index=11}

---

## Runtime loop (how an Agent works here)

Two operator modes in the UI:

- **Ask** — context gathering & planning only (no writes/execs).  
- **Do Work** — propose tasks and—once approved—execute, then write Implemented + update READMEs + maintain macro/archive + reflect.

The loop enforces the Trifecta, authority checks, macro capture/TTL, and writes **Spec Verification** at the end of `Required-Updates.md`: either “All implemented” with timestamp or a count of remaining items. :contentReference[oaicite:12]{index=12}

---

## Quick start (for humans and Agents)

1. Read **`agents/base.md → local.md → project.md`** and memoize key paths. :contentReference[oaicite:13]{index=13}  
2. Use **`agents/default/`** as your template. Clone it into `agent_roster/<agent_name>/`.  
3. Populate `<agent_name>/Agent.md` with directives and `<agent_name>/agent.yaml` with model/limits/authority.  
4. Attach styles from `agent_styles/` and tools from `agent_tools/`.  
5. Run **Ask** to build context; run **Do Work** to execute with approvals; update the Trifecta.

---

## Conventions (so Agents don’t get lost)

- **High contrast UI** always.  
- **One purpose per folder**, documented in that folder’s README.  
- **No placeholders**: if a feature isn’t ready, mark it *planned* or *quarantined*.  
- **Keep the Trifecta in sync** at every change: Required ↔ Implemented ↔ README (current). :contentReference[oaicite:14]{index=14}

---

## FAQ

**Q: Where do new Agents live?**  
`agents/agent_roster/<agent_name>/` with its own README and config. Default stays in `agents/default/`.

**Q: Can Agents modify themselves?**  
Yes—under authority. They may propose edits to their own `Agent.md`, `agent.yaml`, tools, or styles; execution still goes through Pending Command (or a prior Always-Allow). :contentReference[oaicite:15]{index=15}

**Q: What are `base.md`, `local.md`, `project.md` again?**  
They’re the canon layers the Agent merges in order (global → machine → repo). They declare the sync loop, authority, macros, styles index, logging, and the rule that **README is the “Current” truth**. :contentReference[oaicite:16]{index=16}
```
