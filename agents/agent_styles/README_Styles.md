# Agent Styles (agent_styles)

**Purpose.** This folder is the **catalog of Agent styles**—named overlays that tune *how* an Agent thinks, plans, renders UI, and chooses tools. A style complements the **default agent** by adding domain‑specific heuristics (e.g., “coding”, “story”, “math”) without forking core logic. Styles can be switched at runtime (manual or auto) and must **always enforce high contrast** (no low‑contrast text on background).

## Why styles are separate from `agents/default/`
- **Backbone vs. overlays:** `agents/default/` stays stable; **styles** carry deltas (prompts, heuristics, UI tokens, tool prefs).
- **Fast specialization:** Ship small, testable changes instead of copying a whole agent.
- **Auto‑selection:** Match style from intent, active files, and RAG tags; fall back to **default** if uncertain or a style is incomplete.
- **UX safety:** Think/Answer separation and critical state cues are declared here and applied consistently.

## Layout
```
agent_styles/
├─ index.json
├─ README_Styles.md
├─ coding/         # seed style for code work
│  ├─ README_coding.md
│  ├─ style.yaml
│  ├─ prompts/
│  │  ├─ ask.md
│  │  ├─ do_work.md
│  │  └─ try_harder.md
│  ├─ ui/
│  │  └─ theme.json
│  └─ tests/
│     └─ smoke.md
├─ story/          # seed style for storytelling/long‑form writing
│  ├─ README_story.md
│  ├─ style.yaml
│  ├─ prompts/...
│  ├─ ui/theme.json
│  └─ tests/smoke.md
└─ math/           # seed style for quantitative/problem solving
   ├─ README_math.md
   ├─ style.yaml
   ├─ prompts/...
   ├─ ui/theme.json
   └─ tests/smoke.md
```

> **High‑contrast rule:** Light text on dark or dark on light only. *Never* low‑contrast pairings. Inline code comments must note this rule.

## `index.json` (source of truth)
A compact registry listing available styles and global UI rules. The runtime reads this first to discover styles and the **contrast policy**.

## Authoring a new style
1. Add entry to `agent_styles/index.json` with `name`, `description`, and `ui_rules`.
2. Create `agent_styles/<name>/` with: `README_<name>.md`, `style.yaml`, `prompts/*.md`, `ui/theme.json`, `tests/smoke.md`.
3. Reload styles in **Agent Manager → Styles**.
4. Validate: run `Ask → Do Work`, verify Pending Command gating, and contrast cues (Allow blinks when required; Edit mode magenta outline).

## Runtime guarantees
- **Non‑destructive:** Styles never bypass authority gates.
- **Fallbacks:** Missing or failing assets ⇒ fall back to **default** and log why.
- **Versioning & archive:** Bump `style.yaml.version` per change; move retired versions to `Archived_Agents/<style>@vN/` and remove from `index.json`.

## Quick checklist
- [ ] Registered in `index.json`
- [ ] `style.yaml` complete (plan/tool/memory/ui)
- [ ] Prompt augments present
- [ ] UI tokens honor high‑contrast
- [ ] Smoke checks added and passing
- [ ] Logged to Implemented‑Updates