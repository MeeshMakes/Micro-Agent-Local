# Dev_Logic — inspiration, patterns & visual references (non-authoritative)

> Use the **Dev_Logic** folder as a rich knowledge mine: images for UI mood/style, experimental scripts, notes, and prior prototypes. Treat it as **inspiration**, not as the source of truth. When something here is adopted, the change must flow into code and be logged in `Implemented-DevLogic.md` with exact paths and rationale.

## What lives here

- **Images & mockups** (PNGs, JPGs) used to guide **layout and high-contrast visual style**.
- **Prototype scripts/snippets** that demonstrate a behavior or technique.
- **Design notes** and extended READMEs for complex ideas.
- **Experiments**: throw-away spikes, algorithm trials, UI motion drafts.
- **Implemented_logic/**: records and proofs for items that were adopted, plus per-item READMEs.
- **Indexes** (optional): `index.json` or `gallery.md` catalogs to speed discovery.

> Baseline intent (from the original one-liner): *“use all the info inside the Dev_Logic folder as usable reference … use the images and their summaries as visual reference for UI style/layout.”*  :contentReference[oaicite:0]{index=0}

---

## Role in the Trifecta (how Dev_Logic integrates)

- **README.md (root)** = the *current system*.  
- **Required-Updates.md** = *desired* changes.  
- **Implemented-Updates.md** = *shipped* ledger.  
- **Implemented-DevLogic.md** = *this folder’s adoption log*. Each adopt entry should include date, source path in `Dev_Logic/`, destination files touched, and a short rationale.  :contentReference[oaicite:1]{index=1}

When a Dev_Logic idea graduates into the product:
1) implement the code,
2) update root **README.md** to reflect the new reality,
3) append a ledger line to **Implemented-Updates.md**, and
4) append an adoption entry to **Implemented-DevLogic.md**.

> The broader Trifecta (Required → README current → Implemented) is echoed in multiple agent docs; keep them in sync. :contentReference[oaicite:2]{index=2}

---

## How Agents must use this folder

**Ask mode (read/plan only):**
1. Scan Dev_Logic by type (images, scripts, notes). Summarize the top-N most relevant references for the current task.
2. Pull **UI cues** (spacing, contrast, component hierarchy) from images; keep the **High-Contrast rule** (never low-contrast text/background).
3. Cross-reference ideas with `Required-Updates.md`. Propose concrete tasks referencing Dev_Logic paths.

**Do Work mode (with approval gates):**
1. **Never copy blindly.** Draft diffs that *translate* Dev_Logic ideas into maintainable code.
2. Stage changes and run verifications/tests (lint, import, basic run checks).
3. On success, update root **README.md** and both ledgers (**Implemented-Updates.md** and **Implemented-DevLogic.md**).
4. If adoption is partial or blocked, file it under **Quarantined-Updates.md** or **Missing-Updates.md**, and leave a **Documentation TODO** in README if UI changed but docs lag.

---

## Directory conventions (create as needed)

```

Dev_Logic/
├─ images/                    # UI references, mockups, annotated screenshots
│  ├─ README_images.md
│  └─ <any>.png|jpg
├─ prototypes/                # runnable spikes / POCs (console, GUI, algorithms)
│  ├─ README_prototypes.md
│  └─ <topic>/...
├─ snippets/                  # focused code fragments by topic
│  ├─ README_snippets.md
│  └─ *.py|*.md
├─ notes/                     # deep dives, trade-offs, UX copy, flows
│  └─ README_notes.md
├─ implemented_logic/         # proofs and receipts for adopted ideas
│  ├─ README.md               # how to write an adoption record
│  └─ YYYY-MM-DD_<slug>/...
├─ index.json                 # optional searchable catalog (title, tags, path, preview)
└─ README_Dev_Logic.md        # this file

````

**Rule:** Every subfolder should include a `README_<name>.md` describing its scope and how to consume its contents.

---

## Adoption pipeline (from Dev_Logic → product)

1. **Discover**: Find a candidate item (image, script, note). Capture its path and a one-sentence *Why now?*.
2. **Propose**: In **Ask** mode, draft a task block in `Required-Updates.md` with explicit **files, steps, AC, and rollback**.
3. **Stage**: In **Do Work**, generate diffs. Where UI is involved, ensure high-contrast and accessibility are intact.
4. **Verify**: Run lightweight tests (imports, type-checks, smoke run). Capture logs/artifacts.
5. **Record**: Write entries to **Implemented-Updates.md** and **Implemented-DevLogic.md** (include source path + rationale). :contentReference[oaicite:3]{index=3}
6. **Document**: Update root **README.md** sections (Capabilities, UI & Styles, Macros, etc.).
7. **Index**: If images/scripts are generally useful, add them to `index.json` with tags.

---

## Authority & safety for this folder

- Content is **non-authoritative** until adopted; treat any code here as **untrusted**.
- Do not execute binaries from here. Run Python prototypes in a controlled sandbox only.
- Redact keys/PII; if found, quarantine and open a repair task.
- Licenses: if an external snippet is present, include attribution and check license before adoption.

---

## High-contrast & UI guidance (for image-driven work)

- Text must **never** share or nearly share the same color/value as its background. Default to **light text on dark** or **dark text on light** for readability.
- When translating an image to code, explicitly note typography scale, spacing rhythm, and interactive states. Include a comment in code citing the image path that inspired it.

---

## Maintenance & housekeeping

- **Prune** stale experiments quarterly; move any potentially useful dead-ends to `implemented_logic/` with a note *why not adopted*.
- Keep `index.json` tidy: de-duplicate titles, update tags for faster recall.
- Prefer **small, focused** artifacts over monolithic dumps.

---

## Templates

**1) Adoption record (Implemented-DevLogic.md):**
```markdown
- ✅ <YYYY-MM-DD> — <short title>
  - source: Dev_Logic/<relative path>
  - adopted_by: <files changed>
  - rationale: <why this improved the system>
````

*(Mirrors the intended structure.)*  

**2) Documentation TODO (drop into root README if docs lag):**

```markdown
> 📌 **Documentation TODO (auto)**
> Task: <task id>
> Affected: <files>
> Status: Implemented in code; docs pending
> Notes: <what screenshots or sections to add>
```

**3) Image catalog entry (for `index.json`):**

```json
{ "title": "Settings Dock layout", "path": "Dev_Logic/images/settings_dock.png", "tags": ["ui","dock","high-contrast"] }
```

---

## Quick usage examples

* **UI borrow:** “Adopt card spacing from `images/feed_card.png`; implement in `ui/cards.py` and update style tokens.”
* **Algo spike:** “Convert `prototypes/heatmap/` into `tools/heatmap_analyzer.py`; parameterize grid and thresholds.”
* **Copy pass:** “Review `notes/phrasebank.md`; add top 10 tooltips to help overlay.”

---

### Bottom line

Dev_Logic accelerates good ideas into production **without** becoming a second source of truth. Read deeply, adopt deliberately, and always close the loop in the Trifecta + adoption log.

```

**Sources:** baseline intent line from the original file and the adoption-log intent from your Implemented-DevLogic ledger draft were incorporated where noted. :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}
::contentReference[oaicite:8]{index=8}
```
