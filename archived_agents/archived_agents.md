```markdown
# Archived_Agents — Purpose, Policy, and Operating Guide

**What is this place?**  
This folder is the **cold storage** for Agent personas and their working bundles. It exists to:  
- **Freeze** a known-good Agent (config + directives + tools + styles + prompts) at a point in time.  
- **Restore** or **diff** against past behavior when debugging, rolling back, or auditing.  
- **Study** growth over time so the system can learn from past successes/failures without dragging old logic into the present.

> Treat everything here as **read-only history**. Active Agents live under `agents/…`; only **snapshots** live here. :contentReference[oaicite:0]{index=0}

---

## How it works (autonomous snapshot loop)

The runtime archives an Agent bundle whenever one of these **triggers** fires:

1. **Stability checkpoint:** N consecutive successful runs (default N=3) with all post-checks passing.
2. **Material change:** `agent.yaml`, `Agent.md`, prompts (`prompts/*.md`), tools, or styles changed and shipped.
3. **Authority shift:** approval mode toggled (AskFirst ↔ AlwaysAllow ↔ Independent).
4. **Style switch:** active style or style pack contents changed.
5. **Version bump:** `version` field increased or semantic change detected.
6. **Manual request:** operator presses “Archive Now” in Agent Manager.

On trigger, the system creates a new archive **folder** with a stable, sortable name and an index entry (see below). It also writes an **Implemented-Updates** entry linking to the archive location and records a short rationale.

---

## What gets saved here?

Each archive is a **self-contained bundle** that can be checked out and re-run (with approvals gated). It includes:

- **Config:** `agent.yaml` (models, endpoints, authority, paths, styles)
- **Directives:** `Agent.md` (system card, rules, loop, safety, Trifecta duties)
- **Prompts:** `prompts/ask.md`, `prompts/do_work.md`, `prompts/try_harder.md`, etc.
- **Local tools:** `agent_tools/` (helpers, runners, schemas, macros with usage notes)
- **Active style(s):** either a referenced style name + exact style JSON(s) copied into the bundle under `styles/`
- **Provenance & metrics:** `provenance.json` (who/when/why), `metrics.json` (run counts, pass/fail, latency)
- **Approvals snapshot:** `approvals.json` (sanitized; secrets & PII stripped)
- **Checksums:** `checksums.sha256` over all files in the bundle
- **Notes:** `notes.md` (human summary: why this was archived, what changed)

> Datasets (large OCR/image caches) are **not** copied wholesale; the archive keeps **references** and verified **hashes** for reproducibility. The Agent can lazily rehydrate from dataset storage if needed.

---

## What an archive looks like (structure spec)

```

Archived_Agents/
└─ 2025-10-29_01-42-17Z_DefaultAgent_v0.3.0_stable-3/
├─ bundle/
│  ├─ agent.yaml
│  ├─ Agent.md
│  ├─ prompts/
│  │  ├─ ask.md
│  │  ├─ do_work.md
│  │  └─ try_harder.md
│  ├─ agent_tools/
│  │  ├─ README_agent_tools.md
│  │  ├─ agent_macros/
│  │  │  ├─ README_agent_macros.md
│  │  │  ├─ macros/              # atomic macros (text or code)
│  │  │  └─ compiled/            # stitched macro chains
│  │  └─ … any other tool dirs …
│  ├─ styles/
│  │  ├─ active_style.json       # exact copy used at archive time
│  │  └─ packs/                   # any additional packs referenced
│  └─ README_default.md           # agent-local readme captured
├─ provenance.json                # who/when/why + git commit(s)
├─ metrics.json                   # run stats around the snapshot
├─ approvals.json                 # sanitized approvals state
├─ checksums.sha256               # integrity list for bundle/**
├─ notes.md                       # human-friendly rationale
└─ DIFFS/
├─ repo.patch                  # diffs vs prior archive (if any)
└─ README_delta.md             # human summary of change set

````

**Naming convention:**  
`<UTC_ISO>_<AgentName>_v<semver>_<reason>` where `<reason>` ∈ { `stable-N`, `style-change`, `authority-change`, `version-bump`, `manual` }.

---

## How the Agent/Codex must use this place

**Before archiving**
- Ensure **README.md** (root) reflects current reality; if not, write a **Documentation TODO** and open a task.
- Ensure **Implemented-Updates.md** has the changes you’re about to freeze.
- Flush pending logs and verify styles/macros referenced actually exist in the repo (no placeholders).

**To create an archive (pseudo-steps)**
1. Build `manifest` of files to capture.
2. Compute hashes; copy to `bundle/`.
3. Write `provenance.json` & `metrics.json`.
4. Generate `checksums.sha256`.
5. Write `notes.md` (short human rationale).
6. If a previous archive exists for the same Agent, emit diffs to `DIFFS/` and summarize in `README_delta.md`.
7. Append an entry to the **archive index** (see below) and to **Implemented-Updates.md**.

**To restore**
- From Agent Manager: pick an entry, **Preview → Rehydrate**.  
- Rehydrate copies **bundle/** back into a new working agent folder under `agents/agent_roster/<name>-<ts>/` (never overwrite the default).  
- Authority resets to **AskFirst** unless the operator explicitly restores approvals.  
- Record the restoration action in **Implemented-Updates.md** with a new task id.

**To diff**
- Use `DIFFS/repo.patch` and `README_delta.md` for a quick view.
- The UI should show file-by-file diffs and a “what changed in Agent behavior” summary (derived from prompts + agent.yaml deltas).

---

## Retention & pruning (keep history without drift)

- Keep **time-window** snapshots by default: `2d / 1d / 6h / 1h`. When a newer snapshot exists for a bucket, **replace** the older one unless **pinned**.
- **Pin** important snapshots (release candidates, big migrations) to bypass pruning.
- Respect **space caps**: when > cap, prune oldest **unpinned** snapshots first.
- Always keep the **most recent** snapshot, even if not pinned.

---

## The Archive Index (machine-readable catalog)

**File:** `Archived_Agents/_index.jsonl` (one JSON object per line)

Each line:

```json
{
  "id": "arch-2025-10-29_01-42-17Z_DefaultAgent_v0.3.0_stable-3",
  "ts": "2025-10-29T01:42:17Z",
  "agent_name": "DefaultAgent",
  "version": "0.3.0",
  "reason": "stable-3",
  "paths": {
    "root": "Archived_Agents/2025-10-29_01-42-17Z_DefaultAgent_v0.3.0_stable-3",
    "bundle": "Archived_Agents/2025-10-29_01-42-17Z_DefaultAgent_v0.3.0_stable-3/bundle"
  },
  "git": { "commit": "<sha>", "branch": "main" },
  "style": { "active": "coding", "packs": ["active_style.json"] },
  "authority": { "mode": "AskFirst", "independent": true },
  "metrics": {
    "runs_ok": 3,
    "tests_ok": true,
    "pending_commands": 0
  },
  "dataset_refs": [
    { "kind": "chat_history", "path": "chat_history.md", "hash": "<sha256>" }
  ],
  "pinned": false
}
````

> The Agent must **append** to `_index.jsonl` on archive, **toggle** `pinned` on operator request, and **never** rewrite history.

---

## Safety, privacy, and integrity

* **Strip secrets**: Remove API keys, tokens, PII from `agent.yaml`, `approvals.json`, and any tool configs before archiving.
* **Verify**: Compute `checksums.sha256` and validate after copy.
* **Immutable**: Archives are write-protected by default. Any change goes through a **new** archive.
* **High-contrast rule**: any UI that renders archive details must ensure strong text/background contrast—no low-contrast ever.

---

## Examples (why & when we archive)

* You tuned prompts and styles for **story-writing** and shipped them—archive under `…_style-change/`.
* You switched authority to **AlwaysAllow** for a long refactor—archive first to preserve the cautious state.
* You detected emergent behavior (macros/lexicon improved execution reliability)—archive a **stable-3** snapshot to preserve the “good groove.”

---

## FAQ (quick answers)

**Q: What is my purpose?**
To **protect, restore, compare, and learn**. This folder captures Agent states so the system can move fast without losing its footing.

**Q: How do I work?**
On triggers, the runtime **freezes** the Agent bundle, records provenance/metrics/checksums, updates the **archive index**, and logs the action to **Implemented-Updates.md**.

**Q: What will be saved here?**
Everything needed to re-run the persona: config, directives, prompts, tools, active style(s), provenance, metrics, approvals snapshot (sanitized), diffs, and checksums.

**Q: What will it look like saved?**
See the **structure spec** above—every archive is a folder named by time, agent, version, and reason, with a `bundle/` and metadata files.

**Q: What is the structure?**
`Archived_Agents/<timestamp>_<agent>_v<semver>_<reason>/…` plus a machine-readable `_index.jsonl` that catalogs all archives.

**Q: What does the Agent/Codex need to know about this place?**
It’s **read-only history**. Use it to restore, to diff, and to teach (patterns), not to run live code from here. Live Agents belong under `agents/…`.

**Q: How are things saved here with code and autonomously—or recalled?**
The runtime executes the **archive recipe** (manifest → copy → checksums → metadata → index), then offers **Restore** in the Agent Manager that rehydrates into a **new working folder** under `agents/agent_roster/<name>-<ts>/` with authority reset to **AskFirst** until explicitly changed.

---

## Operator checklist (fast path)

* [ ] Ship change → update **README.md** (root) to current.
* [ ] Confirm **Implemented-Updates.md** entry exists.
* [ ] Hit **Archive Now** (or wait for stability trigger).
* [ ] Verify the new entry in `Archived_Agents/_index.jsonl`.
* [ ] Optionally **pin** the snapshot.
* [ ] If restoring, select archive → **Preview → Rehydrate** (creates `agents/agent_roster/<name>-<ts>/`).

---

## Machine hint (for LLMs parsing this file)

* Recognize **archive folders** by the naming pattern and presence of `bundle/agent.yaml`.
* Never modify existing archives; propose a **new** archive instead.
* When asked to compare Agent behavior over time, load `DIFFS/README_delta.md` and `provenance.json` first, then open the `bundle/` files for semantic diffs.

```


::contentReference[oaicite:1]{index=1}
```
