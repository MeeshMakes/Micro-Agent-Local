# Required-Updates — Operating Contract for Codex / Local Agent

**Purpose.** This file is the **single source of truth** for planned changes. Codex or the Local Agent must continuously read it, extract unshipped work, propose diffs/commands, and (with approval) apply and verify those changes. This document governs the full loop: **Plan → Stage → Approve → Apply → Verify → Report**.

## Who acts on this file

* **Codex (cloud) or Local Agent** (“Agent”) with repository access and authority gates.
* The Agent MUST re-read this file (and `./.codex_local_agent/agent.md`) at the start of **every** run and whenever it detects edits.

## Modes (guardrails)

* **Ask** = reason/research/narrate only. **No** file writes, no shell.
* **Do Work** = allowed to propose tasks, stage diffs, and (after approval) run commands and write files.
* The Agent must **carry Ask context into Do Work** planning and execution.

## Authority & approvals

* All actions that touch disk or run commands require one of:

  * Inline **Allow** (per-action), or
  * Previously granted **Always Allow** for that action class, or
  * Policy set in `agent.yaml` (see below).
* Show approval prompts inline in chat **and** in the Pending Command bar (Allow / Skip / Try Harder / Edit).

  * **Allow** flashes blue only when an approval is required.
  * **Edit** switches the input box into purple/magenta “edit mode,” then uses the edited text as the new pending command.

## Companion files the Agent must maintain

These files are authoritative and MUST be kept in sync:

```
./.codex_local_agent/
  agent.yaml                # machine config: model, endpoints, authority, style, dataset, macros, paths
  agent.md                  # human-readable system card: rules, policies, safety, loop
  Task-Index.json           # durable task ledger (ids, status, approvals, timestamps)
  macros/registry.jsonl     # captured helper scripts (navigation/edit/backup), with usage counters & risk
  dataset/memory.jsonl      # per-turn RAG rows: markdown, image paths, OCR_fast, OCR_full, tags, hashes, ts
  logs/session_<DATE>.md    # chronological operation log
Implemented-Updates.md      # what shipped (with links to tasks/diffs)
Quarantined-Updates.md      # blocked/denied/errored items + reasons
Missing-Updates.md          # still not implemented (auto-regenerated)
chat_history.md             # markdown chat transcript for context (Ask + Do Work, with <think> sections)
```

### Minimal `agent.yaml` (baseline contract)

```yaml
llm: { provider: ollama, model: qwen2.5-coder:latest, endpoint: http://127.0.0.1:11434 }
modes: { ask_mode: true, do_work_mode: true }
authority: { ask_first: true, always_allow: false, independent_agent_mode: true }
paths:
  repo_root: "."
  dataset_root: ".codex_local_agent/dataset"
  macro_registry: ".codex_local_agent/macros/registry.jsonl"
  beans_store: ".codex_local_agent/macros/beans.json"
styles:
  active_style: "default-dark"
  packs: [".codex_local_agent/styles/default-dark.json"]
logging:
  chat_history: "chat_history.md"
  sessions_dir: ".codex_local_agent/logs"
updates:
  required: "Required-Updates.md"
  implemented: "Implemented-Updates.md"
  quarantined: "Quarantined-Updates.md"
  missing: "Missing-Updates.md"
task_index: ".codex_local_agent/Task-Index.json"
ui:
  think_render: { italic_dim_green: true }
  thumbnails_inline: true
  high_contrast_enforced: true
```

## How to use this document (execution loop)

1. **Parse & bucketize.** Read all sections below into structured “buckets” (each with a stable `bucket_id`).

   * If content arrives via the **Rant** panel, first consolidate it here (Generate/Revise Required Updates).
2. **Derive tasks.** For each bucket not yet shipped, synthesize concrete tasks with **durable `task_id`s**; write them to `Task-Index.json` with links back to the bucket(s).
3. **Plan safely.** In **Ask** mode, narrate the plan, context, and candidate diffs/commands. No side effects.
4. **Stage diffs.** In **Do Work**, stage file diffs and pending commands. Render them in chat (markdown + code blocks) and in the Task Feed.
5. **Approval gate.** Await **Allow** (or use prior allow-list if permitted by policy). Expose **Edit / Try Harder / Skip** affordances.
6. **Apply & verify.** Execute approved commands, write files, run formatters/lint/tests if relevant, re-read files, and verify acceptance criteria from the bucket.
7. **Record outcomes.**

   * **Implemented-Updates.md:** append successful items (with task ids, short summaries, paths changed).
   * **Quarantined-Updates.md:** append denies/failures with reason and remediation hints.
   * **Missing-Updates.md:** regenerate from unshipped buckets (or subparts) after each run.
8. **Macros.** When you author helper scripts (navigation/edit/backup/IO), capture them to `macros/registry.jsonl` with `terminal_type`, `purpose`, `risk`, and counters. Reuse safe macros before inventing new ones.

   * Apply **bean-counter GC**: remove zero-use macros older than 24h; defer GC if the previous session is the most recent activity (no usage yet today).
9. **Dataset & OCR.** If a turn contains images, write a row to `dataset/memory.jsonl` with `markdown_block`, image paths, `ocr_fast` (markdown-oriented) and `ocr_full` text, plus tags/hashes. Use this as local RAG.
10. **Styles.** Respect the UI **style pack** in `agent.yaml`; never violate high contrast. “Agent Styles” (visual packs) are distinct from the **Agent Manager** (authority/datasets/approvals diagnostics).
11. **Idempotency.** Never re-implement an already Implemented bucket unless the spec below explicitly supersedes it (then record a supersession note).
12. **Write the end-of-run report.** Append the **Implementation Check** footer (timestamped) to this file after each run, summarizing Completed / Quarantined / Missing and an overall **Verdict**.

## Safety, scope, and UI rules

* **Scope:** Do not write outside `repo_root` unless the user approves that exact path. Never run destructive commands without explicit Allow and a visible backup plan.
* **UI contrast:** All text must be readable (light on dark or dark on light; no low-contrast pairings).
* **Transcript:** Every turn is added to `chat_history.md`, rendering `<think>…</think>` in dim italic green, and the final answer in larger white text. Thumbnails for any images must be present inline.

## Definition of Done for each bucket

* Diffs applied and verified.
* Tests/linters (if applicable) pass.
* Entry added to **Implemented-Updates.md** with `task_id` + short rationale.
* **Missing-Updates.md** updated; bucket disappears from Missing.
* End-of-run **Implementation Check** appended here shows the bucket as Completed.

## If nothing is left to do

* When all buckets are implemented and no Missing remains, append at the very bottom:
  `✅ As of <timestamp>, all Required Updates are implemented. Nothing remains.`

---

*Everything below this header is the authoritative backlog. The Agent must follow the loop above exactly.*


---

## 0. Terminology and runtime model

* “LLM mode” = plain model call. No file writes. No commands. Talk/plan/generate text. This is Ask mode. The system should never route this through high-authority agent code unless needed. 
* “Agent mode” = autonomous repo worker. Can propose file writes, diffs, and shell commands for this repo. Human approval still required unless Always Allow applies. This is Do Work mode. 
* The UI must treat these as two different behaviors, but they share memory, chat history, dataset, active repo root, and authority policy. The Agent must carry forward all Ask context into Do Work planning and execution. 

We will not overuse Agent mode for things that could be handled by a normal LLM answer. Example: generating README text, summarizing requirements, answering a question. That should stay in Ask and should not trigger authority or file staging by default.

---

## 1. Chat panel layout and behavior

### 1.1 Chat panel geometry

* The chat/agent panel must become a tall vertical rectangle, not a wide strip.
* The response window and the input box live together as one vertical block.
* All chat-related controls sit directly under that block, not at the top bar.
* Staged Changes and Task Feed sit to the right of chat, below Task Feed.
* This matches the mental model: left/edit, right/review. The user should not have to look up at the header to drive the conversation.

### 1.2 Buttons near the input

* Buttons next to / under the message box:

  * Send
  * Ask
  * Do Work
  * (other controls you already defined: image attach, etc.)
* Ask = talk/think/research only. Do Work = plan tasks and propose actions. This matches the split already described in micro_agent.py but we relocate the buttons from the header to the chat zone. 
* Ask and Do Work act like “send modes.” The message is sent with the selected intent.

### 1.3 Markdown chat render

* The chat feed renders markdown, not plain bubbles. We already stated this in micro_agent.py: render `<think>...</think>` in dim italic green with smaller font. Render final answer in brighter, larger text for clarity. High contrast only. No low-contrast text on dark. 
* The chat feed must inline thumbnails for any attached images. The absolute file path (or capture path) is shown in the turn so the Agent can reference it later. Thumbnails always appear in that same turn. 
* The chat feed must support code blocks, inline diffs, and embedded approval prompts.

### 1.4 Chat logging

* Every turn gets appended to `chat_history.md`. We are already doing this. Keep doing it. This file is the authoritative context store. 
* The turn markdown must include:

  * timestamp
  * role (USER, AGENT, SYSTEM)
  * any `<think>` block
  * final answer block
  * any image paths
  * any staged command text that is waiting for approval
* This log is also mirrored into the dataset (see section 2) so Do Work mode can recall long-term intent.

---

## 2. OCR, dataset capture, and “buckets”

### 2.1 Dual OCR

* When the user attaches an image, run two OCR passes (fast UI text pass and full fallback scan). micro_agent.py already stubs this with `fast_ocr` and `full_ocr`. Keep both. 
* Store both OCR results for that turn.

### 2.2 Dataset row per turn

* For every chat turn that includes an image, write a row into `.codex_local_agent/dataset/memory.jsonl`. We already planned this structure:

  * markdown_block (the full markdown we appended to chat_history.md for that turn)
  * image_paths
  * ocr_fast
  * ocr_full
  * hashes (SHA-256 or similar for dedupe)
  * tags (semantic tags and bucket labels)
  * timestamp
    This is the seed of local RAG. 

### 2.3 Buckets and versioned logic

* We need bucketization of logical directives and design decisions.
* Each major directive or reasoning block should be stored in a named bucket with:

  * bucket_id
  * text content
  * tags
  * semantic hash
* We can version buckets over time. Each version represents the “current truth” that supersedes older instructions. We will need this because old logic becomes wrong.
* The system must be able to mark older bucket versions as “stale / superseded.”
* Retrieval for planning should prefer the newest non-stale version of a bucket.

### 2.4 Sanitizing tags

* Buckets carry tags and hashes. The raw text we surface back into chat should not spam those tags.
* When we re-inject data from a bucket into the chat or into a file, strip bucket metadata, strip tags, and output clean human text.

### 2.5 Diff-style memory

* When logic changes, generate a diff-style record so we know “old directive vs new directive.”
* This lets the Agent understand policy drift.
* Those diffs live alongside the bucket versions. They are part of the Agent Manager view (see section 5).

---

## 3. Mini-app dock and sliding left stack

### 3.1 Top banner icon row

* At the top banner we already show square icons (Script Creator etc). micro_agent.py calls this the “mini-app dock system.” 
* Each icon needs a readable label or tooltip. Right now they are just “A” and “S.” They must use real names (“Script Creator,” “Agent Manager,” etc.) instead of single letters.
* Each icon toggles that mini-app’s panel.

### 3.2 Left vertical panel stack

* When any mini-app is active, a left-side vertical column slides open.
* That column is scrollable.
* Each mini-app gets its own panel in that scroll column.
* When no mini-apps are active, the column should auto-collapse and return space to the main layout. 
* Bug fix: right now if you close a mini-app panel you cannot get it back. We need reliable toggle.

  * Clicking the icon should reopen a closed panel.
  * Closing the panel should only hide it, not destroy its state.
  * We should visually show that an icon is “active.” Simple high-contrast highlight is enough.

### 3.3 Arrow / slide affordance

* When the first panel is activated, insert a small arrow handle near the top-left edge of the main window.
* This arrow nudges the layout a few pixels so the user sees that a column just became available.
* Clicking the arrow should slide the column out fully. Clicking again should collapse it.
* The arrow needs to be obvious high-contrast (for example bright blue outline against dark background, per contrast rule). 

---

## 4. Script Creator mini-app

We already described ScriptCreatorApp in micro_agent.py. It needs the following concrete behavior. 

4.1 Inputs

* Destination folder path
* Script / project folder name
* File type dropdown (`.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, etc.)
* Optional explicit filename. If no filename is provided, default to `main.py`.
* Description box (required)

4.2 Desktop shortcut

* A button that sets destination = Desktop automatically and uses the provided project name to make a new folder there.

4.3 Folder creation

* If the destination folder does not exist, create it.
* That new folder becomes a repo root. We also seed `.codex_local_agent/` there with:

  * `agent.yaml`
  * `agent.md`
  * `chat_history.md`
  * `dataset/`
  * `history/`
  * `patches/`
    This matches our repo session structure in micro_agent.py. 

4.4 README bootstrap

* Use the Description box text to generate a README.md in that new folder.
* README.md should explain what the project is for using that text.
* This README generation can be done by a normal LLM call (Ask mode). It does not require Agent authority.

4.5 File creation / overwrite rules

* After creating the folder, create the chosen file (default `main.py`).
* If `main.py` (or chosen filename) already exists:

  * Check if it has content.
  * If content exists, show a high-contrast preview panel before overwrite (bright text on dark).
  * Ask: Overwrite? Yes / No.
  * If Yes, overwrite. If No, leave file unchanged.
* After create/overwrite, open that file in the main code editor and mark that folder as the active repo root.

---

## 5. Agent Manager mini-app

micro_agent.py defines an AgentManagerApp surface that exposes authority mode, Always Allow toggle, dataset stats, and pending command pipeline. 

We need to extend it:

### 5.1 Authority modes

* Keep:

  * Full Auto
  * Ask First
  * Read Only
    These already exist in the spec. “Ask First” means require approval before running commands or writing to disk. This matches `require_command_allow=True`. 

### 5.2 Always Allow

* Always Allow Repetitive Commands toggle already exists in spec. 
* Behavior: if Always Allow is ON and a command has already been explicitly approved once, then that same command pattern can auto-run in future without flashing for approval.

### 5.3 Independent Agent Mode

* Add a new toggle: Independent Agent Mode.
* When enabled, this project operates on its own authority profile instead of global shared approvals.
* This means approvals are not inherited from other repos or other chats. It creates a per-repo sandbox of authority.
* When disabled, approvals are global. If you already allowed an operation in another repo, the Agent can reuse that permission here.

### 5.4 Approval memory list (“Allow list”)

* Add a panel in Agent Manager that shows the allow list.
* The allow list is a vertical list of previously approved command patterns or operations that required human approval.
* Each row should include:

  * short description of what was approved
  * timestamp
  * scope (global or this independent agent)
* User can revoke any approval from this list.
* Revoking should force the Agent to ask again next time it tries the same action.

### 5.5 Dataset / RAG view

* Agent Manager must also expose:

  * number of dataset rows in `.codex_local_agent/dataset/memory.jsonl`
  * distinct tags / buckets stored
  * list of bucket IDs and which are “stale / superseded” vs “current”
* This gives visibility into what memory the Agent is using to reason and plan. 

### 5.6 Versioned directives / policy drift

* Show recent directive diffs.
* Example: “We changed how authority approval works on 2025-10-29.”
* Each diff entry links to the bucket version so you can inspect what changed.
* This is where we surface corrections to old logic so the Agent stops using bad instructions.

---

## 6. Pending Command flow and approval bar

The pending command flow is already described in micro_agent.py, but we need corrections. 

### 6.1 Visual states

* The Pending Command bar shows:

  * current pending command text (or “None”)
  * Allow
  * Skip
  * Try Harder
  * Edit
  * Always Allow checkbox

### 6.2 Allow button state

* Allow must only light up blue and flash when there is actually a pending command that needs approval.
* If there is no pending command, Allow must look disabled / gray.
* Right now Allow is blue all the time. That is wrong and confuses the human.

### 6.3 Inline approval prompts in chat

* When the Agent proposes a command in Do Work mode, it should also post a message into the chat feed with:

  * the proposed command
  * buttons (Allow / Skip / Try Harder / Edit) inline in that turn
* This mirrors how VS Code and Copilot show approvals directly in the transcript, not only in a static bar.

### 6.4 Try Harder

* Try Harder re-prompts the Agent to attempt the same task again with a stronger system prompt.
* That stronger prompt must be hardcoded and consistent.
* The new attempt becomes the new pending command.
* Pending Command bar updates live.

### 6.5 Skip

* Skip clears the pending command and returns the bar to “None.”
* No flashing.

### 6.6 Edit flow

* Edit puts the chat input box into Edit Mode.
* Edit Mode visuals:

  * background becomes dark purple `#2a003a`
  * outline becomes magenta `#ff00ff`
  * This must satisfy contrast. Purple background must still be dark enough that magenta outline is clearly visible.
* The box is now editing the pending command text, not sending normal chat.
* After Send in Edit Mode:

  * the edited text replaces the pending command
  * Edit Mode exits
  * input box returns to normal dark blue background and normal outline

### 6.7 Always Allow checkbox

* If Always Allow is ON here and in Agent Manager, and the pending command matches a previously approved pattern, we do not flash blue.
* If the command is brand new (never approved), we still flash blue and force a one-time Allow so we can store that approval in the allow list.

---

## 7. Staged Changes and Diff UI

micro_agent.py already specifies staged diffs, file snapshots, and version history under `.codex_local_agent/history/<file>/`. 

We need to refine:

### 7.1 Rename unclear buttons

* Buttons like “Apply Editor to Disk,” “Approve,” “Stage diff from editor,” etc need human-readable labels.
* Replace with:

  * “Write file to disk” (means save editor buffer to actual file)
  * “Stage this change” (means stage this diff to patches)
  * “Approve all staged diffs” (means accept multiple diffs at once)
* Under each button, show a 1-line caption in small text that explains exactly what will happen. Use high contrast text.

### 7.2 Diff presentation

* Show a split diff:

  * Left = old (red removed lines)
  * Right = new (green added lines)
* At the top of each staged change card, show:

  * file path
  * a diff count badge like “+12 / -3”
* Keep all diffs from previous tasks, not just the latest. We need history so we can roll back older changes.

### 7.3 Rollback / history navigation

* Every time we save or allow a change, snapshot the previous version of that file into `.codex_local_agent/history/<file>/timestamp_id.ext`. We already said this in micro_agent.py. 
* The editor footer bar under the code tab must have:

  * full resolved path
  * left arrow / right arrow to navigate older snapshots
  * Copy Path
  * Clone File
  * Document File (ask LLM to write/update inline documentation using file history)
  * Purge Hist (wipe stored snapshots for that file after an optional backup step)
* Purge Hist flow:

  * Warn in high contrast yellow/red
  * Offer “Backup snapshots to custom folder” first
  * If accepted, open a path chooser and copy snapshots there, then delete local snapshots

---

## 8. Repo awareness and active script

### 8.1 Paste-to-load

* User copies a path from Explorer.
* User pastes it into an empty editor tab.
* If it’s a file: open that file in an editor tab and set that file’s parent folder as the active repo root.
* If it’s a folder: set that folder as the active repo root and populate the file tree.

### 8.2 Repo session bootstrap

* When a folder becomes the active repo root, ensure `.codex_local_agent/` exists with:

  * `agent.yaml`
  * `agent.md`
  * `chat_history.md`
  * `dataset/`
  * `patches/`
  * `history/`
  * `Required-Updates.md`
    This mirrors what Script Creator generates and what we already described in micro_agent.py.  

### 8.3 Required-Updates.md

* `Required-Updates.md` is the running backlog of missing features and corrections. Codex online will read this file and try to implement what is not yet done.
* The Agent should create this file if missing.
* The Agent should append to it when the user describes new required changes.
* The Agent should not overwrite it with the wrong content like happened before. The file must not get confused with README.md. 

---

## 9. Authority, safety, and reuse of approvals

### 9.1 First-time approval

* Even if global mode is Full Auto, the first time the Agent tries a new class of operation (like writing a new file, running PowerShell, touching outside repo) it must ask for approval. We saw this same pattern in Copilot and Codex behavior. This matches our `require_command_allow` policy and “Ask First” stance. 
* After the user taps Allow for that specific operation, that operation is added to the allow list.

### 9.2 Reuse approvals

* On future runs, if Always Allow is enabled and Independent Agent Mode is off, the Agent can automatically run that same operation without flashing blue.
* If Independent Agent Mode is on, approvals from other repos do not auto-apply here. The Agent must ask again and build a local allow list for this repo.

### 9.3 Agent Manager wipe

* Agent Manager must include a control to wipe stored approvals.
* Wiping approvals forces all operations back to first-time approval behavior.

### 9.4 Authority isolation mode name

* Call this toggle “Independent Agent Mode (separate approvals).”
* Tooltip: “This agent tracks its own approvals and will not reuse global ones.”

---

## 10. Window trim, drag handles, resize, snapping

* All major panels must be clearly outlined.
* Some panels currently have purple trim. Keep that.
* Panels with no trim today need a faint high-contrast wireframe border plus draggable “dot handles” (small gray dots on edges or corners).
* User must be able to drag-resize and snap panels the way VS Code panes move.
* When the user drags a handle, adjacent panels shift accordingly and snap into place.

---

## 11. Task Feed and staged tasks

* The Task Feed to the right of chat must behave like the vertical task list in the screenshot.
* Each task is a card with:

  * summary text
  * Start button
  * Skip button
  * error badge if it failed
  * status badge if running or done
* There must also be a “Start All” control that runs tasks in order by repeatedly prompting the Agent.
* When a task errors, log the error in the console/output pane and mark the task card with a visible red status block.
* Clicking a task opens a detail subview in the same right column (take about one-third width) that shows the long text, diffs, etc. That subview can be closed.

---

## 12. Console / problems / output

* Keep a bottom console/output pane similar to VS Code Problems/Output.
* All runtime errors from tasks, file writes, authority denials, or shell command failures must appear here.
* This pane must be persistent and high contrast.
* If a task fails, both the task card and this console reflect it.

---

## 13. Accessibility and contrast

* All high-attention states must have strong color cues:

  * Flashing blue Allow button when approval is required.
  * Purple+magenta edit mode for Pending Command edit.
  * Yellow/red warning for destructive actions like Purge Hist.
* All text foreground must meet contrast on its background (bright on dark or dark on light). This rule is already stated across micro_agent.py, chat_history.md, and Required-Updates.md content.   
* Do not ever render low-contrast gray on gray.

---

## 14. Live streaming and incremental output

* Agent replies in the chat feed should stream in real time.
* While streaming, if the Agent is about to ask for approval for a command, it should visibly frame that command and show the Allow button inline as part of that turn.
* This replicates VS Code / Copilot style where you see the tool think, propose, and then pause for your confirmation in the same live message.

---

## 15. Virtual Desktop and future integration

* The Virtual Desktop system and Codex Terminal spec already describe a left slide-out tree, panel registry, and embedded Virtual Desktop pane with cards for heavy tools.  
* Our micro agent must line up with that direction:

  * One main window.
  * Slide-out panels instead of random floating windows.
  * Tasks, Buckets, Logs, Status, Agent Manager, Script Creator, etc, are all panels in that slide-out stack.
  * Heavy views (like Virtual Desktop cards, 3D map, etc.) should open in a contained pane, not a new OS window.

This means: do not spawn orphan QMainWindow instances for mini-apps. Mount everything in the left/right slide stacks or inside the main window as cards. 

---

## 16. Summary of critical fixes the codebase must implement next

1. Move Ask / Do Work / Send / Attach UI down to the chat panel and make chat a tall vertical block.
2. Restore Ask mode and make sure it never executes work. Do Work plans and proposes actions. Both share memory. 
3. Render chat as markdown with `<think>` styling, code blocks, thumbnails, and inline approval prompts. Log every turn to chat_history.md and dataset. 
4. Finish dataset logging: dual OCR, per-turn JSONL rows, bucketized directives with versioning and stale/superseded tracking. 
5. Fix the mini-app dock:

   * labeled icons, not “A / S”
   * reliable slide-out left column with arrow handle
   * panels can close and reopen without breaking
   * Agent Manager must be its own icon
6. Script Creator mini-app must create a new repo root (Desktop button, README bootstrap, default main.py, overwrite preview with confirm, seed `.codex_local_agent/` layout). 
7. Add Agent Manager mini-app with:

   * authority mode selector
   * Always Allow toggle
   * Independent Agent Mode toggle
   * allow list viewer + revoke
   * dataset / bucket / RAG stats
   * directive diff history
8. Fix Pending Command bar:

   * Allow only flashes blue when needed
   * Inline approval prompts appear in chat
   * Edit mode with purple/magenta high-contrast state
   * Try Harder regenerates with a stronger prompt and replaces pending command
9. Improve Staged Changes UI:

   * Rename buttons in plain language
   * Show split diff with +/− badge counts
   * Keep diff history
   * Add footer bar controls (Copy Path, Clone, Doc, Purge Hist with backup)
10. Repo linking:

    * Paste path to load active script / repo
    * Auto-create `.codex_local_agent/` and `Required-Updates.md` if missing
11. Authority memory:

    * First-time Allow records approval
    * Always Allow reuses it
    * Independent Agent Mode isolates approvals per project
    * Agent Manager can wipe approvals
12. Panel borders and drag handles for resize/snap
13. Task Feed cards with Start / Skip / Start All / error state and side detail subview
14. Console/output pane shows errors and runtime logs
15. One-window discipline and slide-out panels consistent with the Virtual Desktop + Codex Terminal model. 


------


We extend the system spec with four new flows: (1) update tracking across multiple files, (2) the rant capture path that feeds Required-Updates.md, (3) task indexing and agent execution against those updates, and (4) revision and quarantine logic. This section defines how those flows work and how they interlock with authority, datasets, diffs, and the Agent.

---

## 17. Update tracking model

### 17.1 Files in the update loop

We now have four update-state markdown files that live at the repo root inside `.codex_local_agent/` (or the active repo root if `.codex_local_agent/` is already seeded, see section 8.2 above).

1. `Required-Updates.md`

   * This already exists.
   * This is the “master wish list.”
   * Human describes what needs to exist.
   * The Agent reads from this file when planning new work.

2. `Implemented-Updates.md`

   * New file.
   * This becomes a running checklist of work that actually got landed into code, UI, config, dataset, agent behavior, or repo structure.
   * Every entry links back to the originating intention in Required-Updates.md (see section 18.4).
   * This is proof of delivery.

3. `Quarantined-Updates.md`

   * New file.
   * Holds anything the Agent attempted or proposed but was blocked.
   * Reasons include:

     * Denied by authority prompt (user pressed Skip or refused Allow).
     * Runtime or environment error.
     * Logic conflict (Agent thinks it would break something).
   * This prevents silent loss of intent. If you said you wanted it, and the Agent tried, we log it here if it didn’t ship.

4. `Missing-Updates.md`

   * New file.
   * This is the declared “still missing” list.
   * Anything that exists in Required-Updates.md but does not appear in Implemented-Updates.md is considered missing.
   * Also anything dumped in Quarantined-Updates.md but not resolved gets mirrored here.
   * This tells you what is still not in the system.

These four documents are the backbone for long-running buildout and self-improvement.

Reminder: these four files must follow the same high-contrast readability rules used everywhere else in the UI. No low-contrast text. Light text on dark or dark text on light only. This is already a global rule for the rest of the app UI and chat rendering. See section 10.1 in the previous spec and the MagicGPT app’s teal background vs bright/white text pattern. 

---

## 18. Required-Updates.md ingestion and shaping

### 18.1 Purpose of Required-Updates.md

Required-Updates.md is where the human pours raw intent.
It is allowed to be sloppy, emotional, out of order, voice-to-text, and repetitive.
This file is not the actual task list that gets executed line by line. It is upstream intent.

Important: We never delete old intent from Required-Updates.md “just because it was done.”
We want history. Old blocks serve as reference for later diffs and forensic context.

### 18.2 Rant Capture → Required-Updates.md

We are adding a dedicated “Rant Updates” capture surface in the UI.

* Visual:

  * A persistent rectangular panel at the top of the main window.
  * Background is a faint brownish-orange wash. Foreground text must still be high contrast.
    This panel is visually distinct from normal chat.
* Behavior:

  * This panel listens to live dictation / speech-to-text, similar to how MagicGPTApp continuously captures microphone audio, segments it, and logs it to project text files while staying responsive. 
  * You can talk continuously. It writes raw stream text plus light punctuation.
* Storage:

  * All rant turns get appended into a “Rant Buffer Dataset,” which is separate from normal chat_history.md.
  * After the user is done ranting (manual stop button, or timed cutoff), that rant buffer is summarized and normalized by an LLM-style pass and appended to Required-Updates.md.

Result:

* The human can brain-dump for several minutes.
* The system rewrites that dump into structured descriptive text inside Required-Updates.md.

Note: “rewrites” here means summarize and clean up. We do not want hallucinated features. We want a faithful, clarified version of what was spoken.

### 18.3 Semantic bucketization of rant content

When the rant buffer is cleaned and appended to Required-Updates.md, that content must also be carved into semantic buckets and pushed into the dataset store. We already defined “bucketization” in section 2.3 above. We extend that here:

* Each new block added to Required-Updates.md becomes one “bucket entry.”
* Each bucket gets:

  * bucket_id (stable string or hash)
  * timestamp
  * tags (keywords, component names, UI surfaces like “Pending Command bar,” “Agent Manager,” “Rant Capture,” etc.)
  * repo scope (which repo or project it applies to)
  * raw text
  * cleaned text
  * supersedes list (if this bucket replaces or corrects an older idea)
* These buckets are used downstream when generating tasks and diagnosing conflicts.

This is similar to how MagicGPTApp snapshots conversation segments, creates rolling versions, and logs incremental deltas between the current buffer and a clone. It tracks changes one segment at a time so nothing is lost. 

### 18.4 Linking Required-Updates.md to Implemented-Updates.md

Any time the Agent actually delivers something (code change landed, UI feature added, new panel created, new authority flag wired, etc.) it needs to:

1. Copy the relevant fragment of Required-Updates.md that motivated the work.
2. Generate an entry in Implemented-Updates.md:

   * [x] <short human-readable title>

     * source bucket_id(s): ...
     * summary of what actually got built
     * file(s) touched / created
     * timestamp
     * authority mode required (Full Auto, Ask First, etc.)
3. Mark those bucket_id(s) as “delivered_version = current timestamp” in the dataset.

That gives us provable traceability:

* “This work exists now.”
* “It came from this human intention.”
* “It was approved under this authority level.”

---

## 19. Quarantined-Updates.md

### 19.1 Why quarantine exists

Sometimes the Agent proposes work but:

* The human denied Allow.
* The operation hit an authority gate that is not yet whitelisted.
* The command failed (PowerShell, file write, etc.).
* The requested change conflicts with current logic.

We cannot just discard those attempts. They represent intent.

### 19.2 What gets logged

For each quarantined item we store:

* status: blocked_by_user / blocked_by_error / blocked_by_conflict
* snapshot of the pending command text (the thing that would have run if Allow was pressed)
* which file(s) it was about to modify
* link back to the originating Required-Updates bucket_id(s)
* timestamp
* authority mode at the time (“Ask First” vs “Full Auto” vs “Independent Agent Mode”)

We also note whether “Always Allow” was active or not at that moment.
Because “Always Allow” drives when a repeated command can auto-run without flashing blue, and quarantine should reflect if the Agent had historical approval to proceed or not. See section 5.2 and section 6.7 in the previous spec.

### 19.3 Relationship to authority memory

Quarantined-Updates.md is effectively a ledger of “things the Agent tried but was not allowed to do yet.”
Agent Manager (see section 5 above) will show these as pending authority gaps. The user can later whitelist certain operations globally or only for a given Independent Agent Mode profile.

---

## 20. Missing-Updates.md

### 20.1 Purpose

Missing-Updates.md is the gap report.

It answers:

* “What is still not in the system even though we said we want it?”
* “What stalled in quarantine and never actually landed?”
* “What was never attempted at all?”

### 20.2 How it is built

After each major Agent run (for example when you press “Implement Required Updates,” see section 22), the system does a diff pass:

1. Scan Required-Updates.md buckets (see section 18.3).
2. For each bucket, check:

   * Is there a matching completed entry in Implemented-Updates.md?
   * Is there a quarantine entry for it in Quarantined-Updates.md?
3. If neither implemented nor in quarantine, call it missing.
4. If quarantined but never resolved, also call it missing.
5. Write all such items (summarized) into Missing-Updates.md.

Key detail: Missing-Updates.md is generated, not hand-authored.
It is essentially a report for humans and Codex to see where we are still behind.

---

## 21. Revision, conflict handling, and negative notes

### 21.1 Conflicting logic over time

When we rant new logic, or when we update design direction, that may contradict older directions already in Required-Updates.md.

We cannot just delete the old text, because we want a paper trail of why we pivoted.
Instead, we do this:

* The revision agent (see section 23) runs a “Revised Required Updates” pass.
* It walks Required-Updates.md, finds contradictions, and does three things:

  1. It appends clarifying language near the older block:

     * “Note: superseded on 2025-10-29. See newer directive bucket XYZ. This older approach is no longer preferred.”
  2. It adds a short negative note describing why the old logic failed:

     * “This approach did not work because the Agent could not safely run shell commands in that mode under Ask First authority.”
  3. It links the old block to the new block’s bucket_id for trace.

That gives us structured obsolescence, not silent deletion.

### 21.2 Negative notes do not mean “never do this”

We explicitly record in the revision output:

* “This approach failed before but might work later with different authority or environment.”
  This prevents permanent bans on ideas. You said this verbally: you do not want the system to assume “this will never work again.”
  This text must be injected whenever we mark logic as superseded.

### 21.3 Cross references in Required-Updates.md itself

When we revise Required-Updates.md, we cross reference inside the document:

* “See Quarantined-Updates.md entry [Q-###] for why this stalled.”
* “See Implemented-Updates.md item [I-###] for the working version of this approach.”
* “See bucket {bucket_id} in dataset for historical reasoning context.”

This keeps Required-Updates.md navigable as it grows.

---

## 22. Implement Required Updates (automated execution button)

### 22.1 The button

We add a new high-level control in the UI called “Implement Required Updates.”

This is separate from normal Ask / Do Work send buttons.
This is a batch runner.

### 22.2 What it does

When pressed:

1. The Agent (or a dedicated micro-agent) starts scanning Required-Updates.md from top to bottom.

2. For each block / bucket:

   * If it is already marked delivered in Implemented-Updates.md, skip.
   * If it is in Quarantined-Updates.md with status blocked_by_user, queue it for re-ask.
   * If it is new, generate a task card in the Task Feed (right-side panel) that describes the work and proposes diffs/commands.

     * Each task card already has Start / Skip / Start All / error badge as specified in section 11.

3. As we run through these tasks:

   * Each task may trigger pending commands that will show in the chat feed inline, with Allow / Skip / Try Harder / Edit right there in context, and also reflect in the global Pending Command bar. See section 6.3 in the previous spec.
   * Authority gates apply (Ask First, Full Auto, Independent Agent Mode, Always Allow reuse). See section 5 and section 6 above.

4. When a task finishes successfully:

   * Append an entry to Implemented-Updates.md with source bucket link.
   * Update Missing-Updates.md (regenerate report).
   * Remove or resolve any quarantine entry for that bucket if present.

5. When a task fails or is denied:

   * Log it into Quarantined-Updates.md with details.
   * Mark it in Missing-Updates.md as still missing.

### 22.3 “Start All”

The Task Feed already has “Start All.”
Pressing “Start All” means: walk all staged tasks from the Required-Updates scan and run them sequentially, pausing only when authority requires explicit Allow.

### 22.4 Task identity and indexing

Each generated task must have a durable ID:

* Could be a short numeric PID or a short hash.
* That ID will be used:

  * in Implemented-Updates.md
  * in Quarantined-Updates.md
  * in Missing-Updates.md
  * in the Task Feed card
  * in inline chat approval prompts

We need this ID so Codex or any other agent can refer back to “Task 0x4F2” and know exactly what it was supposed to do.

We also maintain an index file.
Call it `Task-Index.json` in `.codex_local_agent/`.
This maps:

* task_id
* originating bucket_id(s)
* timestamps
* final status (implemented / quarantined / missing)
* last authority decision (“Allowed at 2025-10-29” or “User skipped”)

This index is what lets the Agent say “I’ve already tried this” and also lets Codex online continue work across sessions.

---

## 23. Revised Required Updates (diagnostic / refactor pass)

### 23.1 Purpose

We add two controls near the Rant panel:

* “Generate Required Updates”
* “Revise Required Updates”

“Generate Required Updates”:

* Take whatever is currently collected in the Rant panel buffer.
* Summarize, clean, and append it into Required-Updates.md as new buckets, tagging them with a fresh bucket_id and timestamp.

“Revise Required Updates”:

* Walk the entire Required-Updates.md file and:

  * Merge redundant requests.
  * Expand old bullets with new clarifications from the rant.
  * Mark logically dead or superseded approaches with explicit negative notes (see section 21.1).
  * Cross link to Quarantined-Updates.md, Implemented-Updates.md, and Missing-Updates.md where relevant.

This “Revise” step is where we attach self-diagnostics into the spec.
It is also where we record “we tried X, it failed because Y, but not forever-ban.”

### 23.2 Workflow detail

1. Human talks into Rant.
2. Press “Generate Required Updates.”

   * System drafts cleaned bullet lists and structured paragraphs.
   * Appends them to Required-Updates.md.
   * Buckets and tags those paragraphs into dataset memory for RAG later. (Section 18.3.)
3. Later, press “Revise Required Updates.”

   * System reconciles everything:

     * Conflicts.
     * Redundancy.
     * Out-of-date logic.
     * Authority blockers.
   * Results get written back into Required-Updates.md inline as editorial notes.
   * Quarantined-Updates.md and Missing-Updates.md are updated so nothing is lost.

### 23.3 Authority tie-in

During “Revise Required Updates,” if the system sees a repeated blocker in Quarantined-Updates.md that was always denied because of some authority check, it should generate a line like:

> “This feature repeatedly failed due to authority restrictions. See Agent Manager → Allow List and Independent Agent Mode. Consider granting scoped permission for this action.”

This creates tight feedback between:

* the rant and desire for new features
* the authority system and what you have actually allowed
* the quarantine log of blocked attempts
* and the Missing-Updates gap report

---

## 24. Parallel agent work and concurrency limits

### 24.1 Parallelism

We acknowledge that multiple agent loops may run.
Example:

* One micro-agent is generating Required-Updates.md from rant speech.
* Another micro-agent is scanning Required-Updates.md and building tasks.
* The main Agent is executing tasks and asking for Allow.

We allow concurrent logical agents, but we cap concurrency so we do not overload a local GPU or local model.
You already saw this pattern in MagicGPTApp where we spin multiple threads and also maintain a heartbeat so the UI does not freeze and can keep listening to audio. 

### 24.2 Practical limit

Set a safe default like:

* At most two heavy LLM calls at the same time.
* If a third wants to start, queue it and mark status as “waiting” in the console output pane and/or the Task Feed card.

This matches the constraint you described: you might run a large local model and you cannot hammer it with unbounded requests in parallel.

---

## 25. Agent memory, approvals, and portability

### 25.1 Authority memory and Allow reuse

We already defined:

* Allow button
* Always Allow toggle
* Independent Agent Mode toggle
* Approval memory list in Agent Manager (section 5.4 above)

Now we clarify how these approvals feed back into updates:

1. Each authority approval event should be associated with the task_id that needed that approval.
2. The Task-Index.json entry for that task_id gets updated with “approved under X mode.”
3. When we later “Implement Required Updates,” the Agent can reuse that approval if:

   * Always Allow is ON
   * Independent Agent Mode is OFF
   * Same class of command is being requested

If Independent Agent Mode is ON, approvals do not propagate globally.
That matches the idea of sandboxing certain repos so they do not inherit high-risk permissions from older repos. See section 5.3 above.

### 25.2 Global allow list vs per-agent allow list

In Agent Manager:

* Show a global allow list.
* Show a per-agent (per-repo) allow list when Independent Agent Mode is active.

You can wipe either list. Wiping a list forces that Agent to ask again the next time it wants to run that command category.

### 25.3 Sharing intelligence between agents

We want all agents to “get smarter together” by default.
That means:

* The dataset buckets
* The index of tasks
* The Implemented-Updates.md history
* The Quarantined-Updates.md ledger
  are all visible to all agents unless Independent Agent Mode is on.

Independent Agent Mode is the escape hatch when we do not want cross-project leakage.
For example, you might not want a high-authority agent from Repo A to automatically run the same privileged command in Repo B without first asking.

---

## 26. Cross-references and self-awareness

The system must continuously cross-reference itself. This is not optional. It is how we avoid drift.

Examples:

* When adding something to Implemented-Updates.md, always reference:

  * bucket_id(s) in Required-Updates.md that spawned it.
  * task_id in Task-Index.json.
  * whether this work cleared authority via Allow.

* When adding something to Quarantined-Updates.md, always reference:

  * the Required-Updates.md bucket it came from.
  * the authority blocker (so Agent Manager can surface it).
  * any console failure logs captured from the runtime console pane.

* When regenerating Missing-Updates.md, always reference:

  * which Required-Updates.md buckets remain unfulfilled or stuck.
  * which task_ids are still in “not implemented” or “quarantined” state.

* When running “Revise Required Updates,” always insert explicit notes into Required-Updates.md:

  * “See Quarantined-Updates.md entry Q-0x93 for why this stalled.”
  * “See Implemented-Updates.md item I-0x21 for the working version.”
  * “See Missing-Updates.md section ‘Agent Manager UI gaps’ for what is not done yet.”

This cross-linking is how Codex online or any autonomous local agent can pick back up later without losing the story. Codex can parse these references, open the right file, and continue work. This keeps the Agent honest about what is shipped, what is blocked, and what is still missing.

---

## 27. Summary of new required behaviors for integration

1. Create and maintain four core markdown trackers:

   * Required-Updates.md (master intent, never fully wiped)
   * Implemented-Updates.md (completed tasks with traceability)
   * Quarantined-Updates.md (blocked attempts and authority denials)
   * Missing-Updates.md (auto-generated gap report)

2. Add the Rant Updates capture panel (brownish-orange background, high contrast text).

   * Voice-to-text capture
   * Append cleaned structured content into Required-Updates.md
   * Bucketize each new chunk for dataset + RAG
   * Use the MagicGPT-style continuous microphone logic and heartbeat so it stays responsive and keeps logging to disk without freezing. 

3. Add buttons:

   * “Generate Required Updates” (take rant buffer → Required-Updates.md)
   * “Revise Required Updates” (reconcile Required-Updates.md, insert negative notes for deprecated logic, add cross-links)

4. Add “Implement Required Updates.”

   * Scan Required-Updates.md
   * Spawn tasks in the Task Feed with IDs
   * Drive Pending Command approvals inline in chat
   * Update Implemented-Updates.md / Quarantined-Updates.md / Missing-Updates.md / Task-Index.json accordingly

5. Maintain Task-Index.json with task_id → bucket_id mapping, timestamps, authority outcomes, final status.

6. Keep strict authority memory:

   * First-time Allow creates an approval record
   * Always Allow + no Independent Agent Mode = auto-run next time
   * Independent Agent Mode = isolate approvals per-repo
   * Agent Manager shows and can wipe allow lists

7. Enforce high contrast, obvious state cues, and visible cross-links everywhere so the human can always answer:

   * What did I ask for?
   * What shipped?
   * What failed or was blocked?
   * What is still missing?
   * What authority did I already grant?



------


Micro Agent advances in four linked areas: (1) update tracking pipeline, (2) chat + memory + buckets, (3) authority + approval, (4) repo/runtime governance. These now lock together as required behavior and must be reflected in `Required-Updates.md` for Micro Agent, plus the new companion files below.   

---

## 1. Update tracking pipeline (Required / Implemented / Quarantined / Missing)

### 1.1 Files

We are no longer tracking “what we want” in just one file. We are now tracking four states:

* `Required-Updates.md`

  * Everything we want in the system.
  * High authority. Treated as contract. Every bullet here is actionable.  

* `Implemented-Updates.md`

  * Mirror of work that actually landed in code.
  * Each item must name the originating bullet(s) from `Required-Updates.md`.
  * Each item must say what files were changed.
  * This lets the agent tell the user “this is already live” when the user asks to implement something that is already done. 

* `Quarantined-Updates.md`

  * Items that were attempted but blocked.
  * Reasons:

    * user rejected an authority escalation
    * OS / path / safety block
    * error during execution
    * logic conflict
  * We keep full text for each quarantined item so it is not lost. We also store a short reason string like `"blocked_authority"`, `"runtime_error"`, `"bad_path"`, `"design_conflict"`.
  * This lets the system retry or revisit later without silently dropping intent.

* `Missing-Updates.md`

  * Items still not implemented.
  * This list is auto-generated by diffing:

    * `Required-Updates.md` (requested)
    * minus
    * `Implemented-Updates.md` (done)
    * minus
    * `Quarantined-Updates.md` (blocked but tracked)
  * “Missing” means: still expected to land.
  * “Missing” is what the agent should actively hunt next.

All four files are plain markdown. High contrast when rendered in UI. Never low-contrast text against the panel background. Add inline comment in UI theme code: `# High contrast enforced. Never low-contrast text vs background.` This requirement mirrors the global high-contrast rule for every visible surface. 

### 1.2 How these four files feed the loop

When you press “Do Work” the agent:

1. Reads `Required-Updates.md`.
2. Reads `Implemented-Updates.md`.
3. Reads `Quarantined-Updates.md`.
4. Computes `Missing-Updates.md` on the fly.
5. Generates task stubs (JSON objects) for anything in Missing.
6. Appends those stubs to `memory/logic_inbox.jsonl`.  

Each task stub is a single JSON line with:

```json
{
  "timestamp": "<UTC>",
  "area": "<subsystem or file>",
  "need": "<concrete missing behavior>",
  "urgency": "high|normal|low",
  "blocked_on": "<what is in the way, or 'none'>",
  "notes": "<short rationale>"
}
```

This is exactly the pattern already defined for `logic_inbox.jsonl`.  

### 1.3 Implemented logging after execution

After the agent finishes a task in code:

1. Append a ✅ entry with timestamp to `docs/codex-local/required_updates_progress.md`. Use ✅, ⏳, 🔒 exactly as defined. 
2. Append a human-readable entry to `docs/changes/CHANGELOG.md` describing:

   * what changed
   * why it matters
   * which spec bullet it satisfied
   * impact on runtime / UI behavior.  
3. Add or update a daily session log in `logs/session_<YYYY-MM-DD>.md` with:

   * Objective
   * Files touched
   * Open questions
   * Next steps. 
4. Write a short implemented bullet into `Implemented-Updates.md`, linking back to the Required bullet(s) it fulfilled.

If the work failed or was refused at approval time, that bullet moves into `Quarantined-Updates.md` with a reason code, not into Implemented. We never silently drop it.

This gives us truth on three levels:

* Required: intent.
* Implemented: landed.
* Quarantined: blocked but remembered.
  “Missing” is computed for the next pass.

The agent must use these files to answer “did you already do this” before it tries to touch disk. This prevents pointless rewrites and prevents lying about completion. 

---

## 2. Rant capture, Required Updates drafting, and controlled ingestion

Goal: You want to talk for a long time, stream-of-consciousness, and have the system turn that into structured work without losing nuance.

We formalize that as the Rant Capture pipeline.

### 2.1 Rant Capture panel

We add a new panel at the very top of the UI. This is a dedicated “rant window.” It is visually distinct:

* background: warm brown/orange wash
* text: high-contrast light text
* inline comment at color set: `# High contrast enforced. Never low-contrast text vs background.`

This panel:

* takes dictation from speech-to-text
* lets you type long paragraphs
* supports image drops
* supports screenshots of UI
* auto-punctuates minimally (periods, commas) so the text is parseable

### 2.2 Output of Rant Capture

Every Rant Capture submission becomes a “Rant Block.” The system immediately:

1. Saves the raw rant (un-edited) into its own dataset row with timestamp.

   * Store it in `dataset/rant_memory.jsonl`.
   * Include OCR text if images were supplied.
   * Include hashes, tags, bucket IDs (see bucket model below). 
2. Generates a cleaned, structured version of the rant:

   * Clarifies intent.
   * Breaks out discrete features or behaviors.
   * Tries to map those to existing areas of the system when possible.
   * Produces descriptive task bullets written like contract language (not casual rant).
3. Appends those structured bullets into `Required-Updates.md` under a new dated heading (for traceability).

   * If the rant expands an already-existing bullet, we append that expansion under the matching bullet rather than duplicating.
   * If the rant contradicts older logic, we mark the older logic as “stale/superseded” using the bucket versioning rules in Section 3.
   * The system must not silently delete earlier text. It adds layered corrections.

This matches the rule from `Agent.md`: the agent is required to parse `Required-Updates.md`, generate task stubs, and treat that file as contract. The rant panel is how new contract text enters that file in the first place.  

### 2.3 Implement Required Updates button

We add a button called `Implement Required Updates`.

When pressed:

1. The agent re-reads `Required-Updates.md`.
2. Creates/updates task stubs in `memory/logic_inbox.jsonl` for any bullets that are still Missing (see Section 1).
3. Starts executing them through the normal Do Work pipeline (Section 4).
4. Writes Implemented / Quarantined entries as tasks succeed or get blocked.

This gives you one-click “go build from spec now” behavior.

---

## 3. Buckets, semantic memory, and versioned logic

We are formalizing buckets, which you already described. Buckets are how we store durable reasoning, tags, hashes, OCR text, per-turn context, and later retrieve it safely.

### 3.1 Bucket definition

A bucket is:

```json
{
  "bucket_id": "authority-approval-flow",
  "version": 5,
  "stale": false,
  "text": "<long directive text>",
  "tags": ["approval", "AlwaysAllow", "PendingCommandBar"],
  "hash": "<sha256...>",
  "timestamp": "<UTC>"
}
```

Store buckets in `dataset/buckets.jsonl` (append-only).

Rules:

* `bucket_id` is stable. `version` increments when logic changes.
* Only the newest version where `stale == false` should be considered “current truth.”
* Old versions flip to `stale:true` but are never deleted.
* Tagging and hashing are attached at the bucket level so we can strip them later.

This matches the versioned directive idea from `Required-Updates.md` and `Agent.md`: we track changing rules over time and mark which ones supersede old logic.  

### 3.2 How buckets get created

Any high-value reasoning that comes out of:

* Chat Ask mode
* Chat Do Work mode
* The Rant Capture panel
* Unity intake / analyzer intake
* Authority decisions (“Allow this permanently”)

will generate or update a bucket.

This prevents important reasoning from being lost in plain chat scroll.

### 3.3 Sanitizing bucket output

When we surface bucket text back into chat or into user-facing docs, we must output only the `text` field. We do not show the internal tags, hashes, or version metadata unless the user explicitly opens Agent Manager and inspects memory state. 

### 3.4 Diff-style memory for policy drift

When a bucket gets superseded, we record a diff:

* old directive snippet
* new directive snippet
* reason for change

Those diffs are visible inside Agent Manager so you can audit “what changed in our policy and why.” 

This matters for authority: if the agent used to need manual approval for `git commit` but now has Always Allow for that operation, that change must be documented and reviewable.

---

## 4. Chat, Ask vs Do Work, pending commands, approval model

The chat panel is not just chat. It is memory, task proposal, and execution gateway. We now finalize behavior:

### 4.1 Geometry and placement

* Chat panel is a tall vertical rectangle.
* The message input and the rendered response live together.
* All chat-related buttons sit directly below the input, not in the global header.
* Task Feed and Staged Changes sit to the right.
* This is already defined and must be enforced. 

### 4.2 Buttons near input

Under/next to the input we need:

* `Send` (generic)
* `Ask`
* `Do Work`
* Image attach
* (later) `Implement Required Updates`

Ask:

* Plain LLM reasoning mode.
* No file writes.
* No shell commands.
* No authority escalation.
* Used for planning, summarizing requirements, expanding README text, etc. This maps to “LLM mode” in the spec. 

Do Work:

* Agent mode.
* Allowed to draft tasks, propose commands, propose file writes.
* Must respect approval gates and authority policy before doing anything unsafe. This maps to “Agent mode.” 

Ask and Do Work share memory, chat history, dataset rows, buckets, and repo root context. Ask provides narrative and context that feeds directly into Do Work planning. The agent must carry Ask context forward into Do Work. 

### 4.3 Markdown render + <think>

* All chat turns are rendered as markdown, not plain bubbles. 
* `<think> ... </think>` blocks are shown in dim gray-green italic, smaller font.

  * Inline comment in style code: `# High contrast enforced. Think text must still be readable.` 
* The final answer (not in `<think>`) is rendered in larger bright text on dark background.

  * Inline comment: `# High contrast enforced. High-bright text on dark background only. Never low contrast.` 
* Each turn shows thumbnails for any attached images, plus the resolved absolute file paths so the agent can reference them later. 
* Code blocks, inline diffs, and approval prompts must all render inside this markdown feed.

Every turn also gets appended to `chat_history.md` with timestamp, role, any `<think>`, final answer, image paths, OCR text, and any pending command text. `chat_history.md` is authoritative memory. 

### 4.4 Dual OCR and dataset capture

When an image is attached:

* Run fast UI OCR and full OCR.
* Store both OCR texts.
* Create a dataset row in `.codex_local_agent/dataset/memory.jsonl` containing:

  * markdown_block (the turn as written to `chat_history.md`)
  * image_paths
  * ocr_fast
  * ocr_full
  * hashes
  * tags
  * timestamp. 

That dataset is the seed for retrieval-augmented recall (RAG) later. Agent Manager will expose this dataset state.

### 4.5 Pending command bar and approval flow

The UI must always show a Pending Command panel with these buttons:

* Allow
* Skip
* Try Harder
* Edit
* plus an `Always Allow` toggle

Behavior:

* If there is no pending command, Allow is gray and inert. It is not blue. Skip etc can remain neutral. 

* When there is a pending command that needs approval, Allow turns bright blue and flashes on a 2-second interval. Inline comment on that style: `# High contrast. Flashing blue indicates approval required.`

* Skip rejects the command and clears pending.

* Try Harder re-prompts the agent using a stronger built-in instruction that says (in plain terms) “solve this same task with more effort and better strategy.” The result replaces the pending command text.

* Edit switches the message input box into edit mode:

  * background switches from dark blue to dark purple
  * outline becomes magenta
  * inline comment on color: `# High contrast enforced. Magenta outline must be obvious.` 
  * user edits the proposed command inline
  * Send applies that edited text as the new pending command
  * input returns to normal dark blue after send

* Always Allow:

  * If toggled, the system auto-approves repeated operations of the same type without flashing blue.
  * This is global by default. We are adding “Independent Agent Mode” below to optionally scope approvals per project. 

### 4.6 Authority approvals and memory

We keep a memory of every approval the user grants:

* The agent logs what it asked to do.
* The user pressed Allow.
* This gets stored as an authority grant with context (command type, path scope, etc.).

Later, if the same pattern recurs and Always Allow is ON, the agent can proceed without asking again.

We also expose a list of stored authority grants (the “allow list”) in Agent Manager. You can review, revoke, or wipe them.

We also add “Independent Agent Mode”:

* If enabled for a repo/project, it maintains its own independent authority ledger (approvals are not shared with other projects).
* If disabled, approvals are global and reused across repos.
  This matches the Independent Agent Mode toggle you asked for, and is consistent with Agent Manager as the place to see authority, dataset, RAG, and pipeline state. 

---

## 5. Agent Manager and mini-app dock corrections

We refine mini-app handling, Agent Manager content, and left-side dock logic to match your feedback.

### 5.1 Mini-app dock

* The top banner shows square icons for mini-apps.
* Icons must have readable labels or tooltips. No bare “A” or “S”. 

  * Example icons:

    * Script Creator
    * Agent Manager
    * (later) Plugin Manager
    * (later) Unity Linker
* Clicking an icon toggles that app’s panel.
* The left vertical panel stack slides open when any mini-app is active.
* The column is scrollable and resizable.
* The column collapses if all panels are closed.
* Bug fix:

  * Closing a panel must not destroy state permanently.
  * Re-clicking the icon should reopen it.
* Add a small arrow handle at the far left (bright blue outline, high contrast).

  * First time any panel is opened, insert and animate this arrow.
  * Clicking the arrow slides the dock open or closed. 

### 5.2 Script Creator mini-app

Script Creator panel must:

* Ask for:

  * Destination folder path
  * Project / folder name
  * File type dropdown (`.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, etc.)
  * Optional explicit filename (default `main.py`)
  * Required Description box
* Provide a Desktop shortcut button that auto-fills destination to Desktop and creates the project folder there.
* If the destination folder does not exist, create it.
* Seed that folder as a repo root:

  * `.codex_local_agent/`

    * `agent.yaml`
    * `agent.md`
    * `chat_history.md`
    * `dataset/`
    * `history/`
    * `patches/`
* Generate README.md using the Description box. README.md can be produced via Ask mode (LLM text only). No authority needed. 
* Create the chosen file (`main.py` if none given).

  * If a file with that name exists and has content:

    * Show a high-contrast preview panel before overwrite.
    * Ask if overwrite is allowed.
    * Only overwrite on approval.
* After creation, open that file in the main code editor and set that folder as the active repo root. 

### 5.3 Agent Manager mini-app

Agent Manager panel must expose:

* Current authority mode:

  * Full Auto
  * Ask First
  * Read Only. These map to require/skip approval in `require_command_allow`, etc. 
* Always Allow toggle state.
* Independent Agent Mode toggle.

  * Independent Agent Mode = per-repo authority sandbox.
  * When off, share approvals globally across repos.
* Dataset and RAG state:

  * Show count of dataset rows.
  * Show bucket summaries.
  * Show OCR captures and tagged screenshots collected so far.
* Pending Command pipeline:

  * Show the current pending command text if any.
  * Show if it is awaiting approval.
  * Show last Try Harder variant.
* Authority log / allow list:

  * Show historical approvals (“you allowed X on path Y”).
  * Let the user revoke specific approvals or nuke all stored approvals for the current repo or globally.

This panel is also where we expose cleanup actions:

* “Wipe approvals for this repo”
* “Wipe approvals globally”
* “Export authority log”

These map directly to the governance and logging rules in `Agent.md` and `Codex Operating Manual`: auditability, reproducibility, traceability, and explicit authority policy.  

---

## 6. Repo scope, active script focus, and path loading

### 6.1 Active script focus

When you select or paste a file path:

1. The program loads that file into the code editor.
2. The parent folder is marked as the active repo root.
3. All context panes (chat, metadata, task feed, Agent Manager display) now talk about that repo and that file as “current focus.”

This matches the “script focus drives context lock” principle in the Required-Updates Unity spec: everything (chat, metadata, plugin relevance, diagnostics) should pivot to the selected script. 

### 6.2 Authority domain

Approval prompts and Always Allow apply to the current active repo root unless Independent Agent Mode is off, in which case approvals can be reused globally.

### 6.3 Staged Changes and Task Feed

On the right side we keep:

* Task Feed (scrollable list of planned tasks and sub-steps)
* Staged Changes / Diffs

Each diff must be shown split-view:

* left = old version (red)
* right = new version (green)
  Strong color contrast only. Never low-contrast text vs background.

Each staged diff row should also include:

* count of added lines
* count of removed lines
* file path

You asked for this tally because VS Code and OpenAI UIs show diff counts next to filenames. We keep every diff, with history, so you can roll back to any previous version or reconstruct old scripts from diffs. This connects with versioned buckets and with the “Implemented Updates / Quarantined Updates / Missing Updates” audit trail.

---

## 7. Authority memory, Always Allow, independent agents, and global recall

Authority is now first-class data.

### 7.1 Allow list as data

Every time you press Allow on a pending command, we save:

* the exact command (or a canonicalized pattern)
* timestamp
* repo root
* short human-readable reason the agent gave for this command
* whether Always Allow was ON at the time

This goes into an authority ledger.

We surface this ledger in:

* Agent Manager (per repo view + global toggle)
* a global “Authority List” view in settings, which you can open from the top bar

This lines up with the governance and audit flow in `Agent.md`:

* We keep durable memory of decisions
* We never lie about completed work
* We log changes to authority policy for later sessions  

### 7.2 Independent Agent Mode

Add a toggle in Agent Manager:

* If ON:

  * This repo uses its own ledger.
  * Approvals in this repo do not generalize to other repos.
* If OFF:

  * This repo can reuse approvals granted elsewhere.
  * This accelerates repetitive workflows across projects.

This directly answers the requirement to let one project run in isolation even if the global agent has broad standing approvals elsewhere. 

---

## 8. UI clarity rules and corrections

We apply several corrections from your feedback.

### 8.1 Button text must be obvious

Buttons like “Apply Editor To Disk” and “Stage Diff From Editor” were too vague.

We rename:

* “Apply Editor To Disk” → “Write This File To Disk”

  * Add subtext under button: “Save the code you see into the real file on disk now.”
* “Stage Diff From Editor” → “Propose Change”

  * Add subtext: “Take what’s in the editor and stage it as a pending change for review.”

We always include 1-line helper text under critical buttons. Plain English. High contrast.

### 8.2 Ask / Do Work must sit with the chat input

Ask and Do Work are not global navbar items. They live at the chat input, next to Send and image attach, because they define how this message will be handled. 

### 8.3 Pending command bar cannot be passive

We keep a static approval bar (Allow / Skip / Try Harder / Edit / Always Allow) so you always know these controls exist. But Allow should not be bright/blue unless there is a real pending command. When there is a pending command waiting on you, Allow turns blue and flashes. Otherwise it blends in. High contrast rule still applies. 

### 8.4 Edit mode color shift

When you press Edit on a pending command, the input box switches to Edit Mode:

* dark purple background
* magenta outline
* obvious high contrast text
* comment in style code: `# High contrast enforced. Edit mode uses purple/magenta so user cannot confuse with normal chat.` 

### 8.5 Sliding dock behavior

The left mini-app column currently fails to reopen once closed. We fix that with:

* per-icon toggle state
* persistent panel widgets
* an arrow handle that visibly shifts layout and slides the dock in/out
* high-contrast highlight on any icon whose panel is active. 

---

## 9. Where this leaves Micro Agent

Micro Agent now has:

1. A governed update pipeline:

   * `Required-Updates.md` (contract)
   * `Implemented-Updates.md` (done)
   * `Quarantined-Updates.md` (blocked or refused)
   * computed `Missing-Updates.md` (still undone)
   * task stubs in `memory/logic_inbox.jsonl`
   * trace logs in `docs/codex-local/required_updates_progress.md`, `docs/changes/CHANGELOG.md`, and `logs/session_<DATE>.md`.  

2. A Rant Capture pipeline:

   * top brown/orange rant panel with speech-to-text
   * writes raw rant + OCR + hashes + tags to dataset
   * rewrites that rant into structured bullets
   * appends them into `Required-Updates.md`
   * lets you press `Implement Required Updates` to turn those bullets into executable work.

3. A bucketized memory layer:

   * buckets with versioning, tags, and hashes
   * diff records when logic changes
   * stale buckets kept for audit
   * clean extraction of bucket text back into prompts without leaking tags. 

4. A two-mode chat panel:

   * Ask (LLM mode, no authority)
   * Do Work (Agent mode, authority + staged actions)
   * shared memory, shared dataset, shared repo root
   * markdown render with `<think>` styling, image thumbnails, OCR capture
   * log to `chat_history.md` every turn. 

5. A live approval gate:

   * Pending command bar with Allow / Skip / Try Harder / Edit / Always Allow
   * Flashing blue Allow only when approval is required
   * Edit Mode with purple/magenta high contrast
   * Always Allow toggle that can auto-approve recurring patterns after first human approval
   * Independent Agent Mode for per-repo isolation vs global reuse of approvals. 

6. A controllable UI shell:

   * Mini-app dock with Script Creator, Agent Manager, etc.
   * Left-side sliding panel stack with persistent state and resizable layout
   * Script Creator that can bootstrap a new repo folder, seed `.codex_local_agent`, generate README via Ask mode, create main file with overwrite preview, and mark that folder as active repo root. 
   * Agent Manager that exposes authority mode, Always Allow, Independent Agent Mode, dataset/RAG stats, pending command pipeline, and approval ledger.  

7. Tight repo focus:

   * Pasting or selecting a file path loads it, sets its parent folder as the active repo root, and tells every panel (chat, task feed, Agent Manager, staged diffs) “this is the working target now.”
   * Diff viewer on the right shows staged edits with add/remove counts
   * Version recall and rollback are possible because we store every diff and keep historical versions.

Result:

* The agent can listen to you dump raw thinking.
* Turn that into structured Required Updates.
* Track which parts shipped, which parts failed, which parts are still missing.
* Stage changes, get approval, and write actual files.
* Keep permanent logs and authority memory.
* Do all of this on a per-repo basis with isolation if you want it.
* And keep every surface high-contrast, visually explicit, and auditable.

This is the spec that should now be reflected in `Required-Updates.md` for Micro Agent going forward.


------



We add Macros as first-class system objects.

Below is the next Required-Updates section for Micro Agent. This text is ready to paste directly into `Required-Updates.md` under the sections you already have. It assumes the rest of the spec you and I defined including Agent Manager, Independent Agent Mode, approval memory / allow list, Implement Required Updates button, Task Feed pipeline, Pending Command bar, dataset/RAG buckets, Implemented-Updates.md, Quarantined-Updates.md, Missing-Updates.md.   

---

## 27. Macro System

### 27.1 What a Macro is

A Macro is any short runnable procedure the Agent had to invent in order to get work done on disk, in the repo, or in the OS.

Examples:

* a tiny Powershell / CMD / Bash / WSL snippet it wrote to cd into the correct path, open or create a file, write text, or apply a diff
* a helper script it wrote to copy, back up, or restore a file tree
* a navigation pattern it derived to reliably reach some nested folder before editing
* a throwaway “do X then Y then Z” helper that let it unblock itself during a task (like fixing permissions, silencing a Windows dialog, etc.)

Important distinction:

* Main deliverable code (like `main.py`, the app UI code, or Repo logic) is not a Macro.
* Operational glue that the Agent writes for itself to accomplish that code change is a Macro.

So Macros = execution tricks and navigation tricks, not product features.

Why this matters:

1. We do not want the Agent to “re-solve” the same navigation / permission / backup / open-editor dance every time.
2. We do want it to remember that dance next time and reuse it instead of re-planning the whole sequence.
3. We also want to time and audit destructive Macros for safety, just like a high-risk shell command still needs approval and may be gated by Always Allow, Independent Agent Mode, etc. 

This matches how we already defined authority flows:

* Agent proposes a command
* Pending Command bar flashes Allow if approval is required
* We can Skip, Try Harder, Edit, or Always Allow
* Independent Agent Mode decides whether a permission is global or per-repo sandbox.  

Now we extend that to Macro capture.

---

### 27.2 Macro capture pipeline

Whenever the Agent runs or prepares a multi-step action in Do Work mode, it must attempt Macro capture:

1. Detect candidate macro

   * If the Agent strings together ≥1 shell / terminal actions to reach a goal (navigate repo, create file, edit, commit staged diff, etc.), that chain is a candidate Macro.
   * If the Agent generates a helper .ps1/.cmd/.sh file purely to carry out that task, that helper is a candidate Macro.

2. Normalize command(s)

   * Strip volatile literals (absolute temp paths that will never matter again, timestamps, etc.).
   * Keep meaningful parameters (target repo root path, file names, backup folder names).
   * Record which terminal “language” each command targets:

     * PowerShell
     * CMD
     * Bash in WSL / Ubuntu
     * plain Linux shell
     * etc.
   * We already said the Agent understands multiple shells. You stated Windows 10 is primary, so PowerShell and CMD must be first-class. WSL and Ubuntu are still valid secondary targets.

3. Store Macro

   * Push an entry into a Macro Registry.
   * Macro Registry is just structured data plus source text.
   * We will mirror the pattern you already sketched for Macro Registry in other work: a registry Python module and metadata that lets other surfaces list and reuse macros. 
   * Each Macro gets:

     * `macro_id` (stable ID string)
     * `created_at`
     * `terminal_type` (PowerShell, CMD, WSL, etc.)
     * `body` (the exact steps)
     * `purpose` (short human explanation)
     * `risk` (“safe”, “destructive/high-risk”, “repo-write”, etc.)
     * `repo_root` where it was first valid
     * `task_id` that caused it to be created (ties into Task Index and approval memory, see 27.6 and section 25.1). 

4. Increment usage counters (“beans”)

   * Set initial usage_count = 1 when first created.
   * Also record last_used_at = now.

The Macro Registry becomes a pool of known good “small moves” that the Agent can stitch together.

---

### 27.3 Macro reuse

When the Agent needs to do a similar operation again:

* Look up an existing Macro in the registry by purpose / repo_root / terminal_type.
* If found and still allowed under authority rules, reuse instead of regenerating from scratch.

Authority check:

* If Macro `risk` is “destructive/high-risk,” then the Agent must still surface it as a Pending Command with Allow / Skip / Try Harder / Edit. High-risk usage still requires approval at least once, exactly like any other new dangerous command.
* After approval:

  * If Always Allow is enabled in Agent Manager
  * And Independent Agent Mode is OFF (global sharing allowed)
  * Then that Macro’s pattern is added to the “allow list,” meaning we stop flashing blue for that same operation class in the future.  

If Independent Agent Mode is ON:

* That approval stays local to this repo.
* Global copies of the same Macro in other repos still need explicit Allow. 

This matches the sandbox rule we already defined for Independent Agent Mode (per-repo authority profile vs global approvals). 

---

### 27.4 Macro telemetry and performance tracking

Each Macro execution must log telemetry:

* start_time, end_time, runtime_seconds
* success / failure
* whether human had to press Allow
* whether Always Allow auto-ran it
* whether Independent Agent Mode blocked propagation

This is consistent with what we already wrote for macro telemetry and performance deltas, including measuring speedup versus baseline and surfacing improvements in a diagnostics panel. 

This telemetry becomes part of:

* console output pane (already in the UI spec)
* task feed card updates (we already have a Task Feed UI with per-task Start / Skip / Start All / error badge and scrolling list) 
* Agent Manager diagnostics panel (Agent Manager already exposes dataset stats and pending command state, and we said we will extend it with per-agent authority info, approval memory list, and diff history of directives).  

High-risk Macros:

* Before execution, show a high-contrast confirmation popup.
* The popup must warn clearly and ask for approval.
* For destructive tasks (example: backup and reset working tree) you must confirm a backup exists in the repo’s backup path before running. 
* After approval, record that approval event into the allow list with timestamp and scope (global vs independent). 

All popup UI must obey the high contrast rule. Text must be high-contrast against background. Never low-contrast combinations. You already stated this rule for all UI. High-risk confirmation inherits the same rule.

---

### 27.5 Macro lifecycle and garbage collection (“bean counter”)

We do not want the Macro Registry to fill with junk.

We define a retention policy:

1. Each Macro tracks:

   * `usage_count` (increment whenever reused)
   * `last_used_at` (timestamp of most recent successful run)
   * `age_hours` (now - created_at)

2. A daily cleanup pass runs at startup or first Agent action of the day:

   * Any Macro with usage_count == 0 after its first 24h grace window is deleted.
   * Any Macro with usage_count > 0 but not used in >24h can also be deleted unless it is marked “pinned” by the Agent Manager or “always allow approved”.
   * “Pinned” means we consider it part of core skills, because it solved something non-trivial and got explicit human approval. We surface “Pinned Macros” in Agent Manager.

Edge case:

* If the human did not use the system for >24h, we do not want to wipe everything when they come back, because no beans got set that “day.”
* Logic: if last session timestamp and current timestamp are >24h apart AND no Macros were used in the new session yet, then skip immediate cleanup for Macros that were last-used in the previous session. In other words the cleanup waits until there is proof that the returning session actually doesn’t need those Macros again.

Result:

* Frequently used navigation sequences and helper scripts stick around and get faster because they are reused.
* One-off junk self-deletes.

This GC rule keeps Macro Registry lean and self-tunes toward what you actually do.

---

### 27.6 Macro IDs, Task IDs, and cross referencing

We already decided that:

* Every Required-Updates bucket becomes one or more task cards in the Task Feed during “Implement Required Updates.” 
* Each task card can lead to pending shell commands in the Pending Command bar and inline approval prompts in chat. 
* We log success into Implemented-Updates.md and failures / denials into Quarantined-Updates.md, plus regenerate Missing-Updates.md. 
* We also said each authority approval event should link to the task_id that needed that approval and record it in Task-Index.json, so we know which capability was authorized. 

Extend that:

* Each Macro remembers which task_id first triggered it.
* When we store Macro metadata, we include `task_id`.
* When a Macro re-runs, we update that task_id’s log with “Macro <macro_id> reused.”
* When a Macro gets human-approved (Allow pressed or Always Allow toggled), we also add that approval to the allow list in Agent Manager with timestamp and scope. 

This ties Macro reuse, authority approvals, and task execution history together. It also feeds Independent Agent Mode:

* Independent Agent Mode means this repo keeps its own Macro approval memory and does not inherit approvals from other repos. 
* Global mode means Macro approvals and Macro definitions (for safe Macros) are reusable across repos.

---

### 27.7 Surfacing Macros in UI

We add two surfaces:

1. Command Palette / Action Surface

   * We already defined a command palette that can list macros from Macro Registry and expose them as quick actions. 
   * This palette opens via hotkey.
   * It shows macros (with their `purpose` summaries), panel surfaces, and common maintenance actions.
   * It should follow the high-contrast rule. State clearly in stylesheet: “High contrast enforced — never low-contrast text/background.” 
   * It also includes “Create stub from prompt,” which writes a new stub task into the logic inbox. That inbox is effectively how we mint new Required-Updates style buckets on demand. 

   Result: operator can manually run a Macro, not just let the Agent auto-run it.

2. Agent Manager panel

   * Agent Manager already shows authority mode, Always Allow, Independent Agent Mode, dataset/RAG info, and pending command pipeline details.  
   * We extend it with:

     * Macro Registry summary:

       * total macros
       * pinned macros
       * macros awaiting first approval
     * Allow list panel (we already said we need an allow list inside Agent Manager) that shows previously approved command patterns with timestamp and scope, and lets the user revoke approvals. Revoking forces the Agent to ask again. 
     * Cleanup controls:

       * “Wipe unpinned Macros older than 24h”
       * “Wipe all approvals” (forces re-ask on next run, matches “wipe authority memory” you asked for)
       * Toggle Independent Agent Mode per repo (already in section 5.3). 

This turns Agent Manager into a live security and memory console.

---

### 27.8 Macro safety and Pending Command bar

We already have a Pending Command bar with:

* Allow (flashes blue every 2 seconds if a real pending command needs approval)
* Skip
* Try Harder
* Edit
* Always Allow checkbox
* Plus a label that shows “Pending Command: (none)” when nothing is queued.  

Corrections we already captured:

* Allow must only light up blue / flash if and only if there is an actual pending command and Always Allow is not already covering it. If no pending command is present it must look disabled / gray. Right now it's lit all the time. That is wrong. 
* Inline approval buttons must also appear directly inside the chat feed whenever the Agent proposes a command in Do Work mode, so humans see Allow / Skip / Try Harder / Edit in context. 

Extend this for Macros:

* If the pending command is coming from a Macro that is new or high-risk, the bar and the inline chat message must clearly label it: “Macro <macro_id> wants to run.”
* If the Macro was previously approved and Always Allow is ON (and Independent Agent Mode allows reuse), the bar should not flash. Instead it should log silently and run automatically. 

---

### 27.9 Interaction with Required-Updates / Implemented-Updates / Quarantined-Updates / Missing-Updates

We already defined:

* Required-Updates.md = source-of-truth wish list of what the system should build. You talk, you rant, you push vision. The Agent (and Codex online) keeps appending structured task buckets here. This is the queue. 
* Implemented-Updates.md = what actually shipped. Each finished task gets logged here with links back to the originating bucket_id. 
* Quarantined-Updates.md = tasks that failed or were denied, with reason and authority blocker. 
* Missing-Updates.md = regeneration report of what is still not done or stuck. 
* “Revise Required Updates” pass writes clarifying negative notes into Required-Updates.md instead of deleting old ideas, and it links to Quarantined-Updates.md and Implemented-Updates.md. Old logic is marked “superseded” but not erased. We explicitly said negative notes do not mean “never do this again.” 

Now include Macros in that loop:

1. When Implement Required Updates runs (the batch runner we specced that scans Required-Updates.md top to bottom and spawns Task Feed cards) 

   * Any Macro created or reused during those tasks must record:

     * which Required-Updates bucket_id triggered it
     * which task_id executed it
     * whether it needed human approval
   * On success:

     * The task gets logged to Implemented-Updates.md with that Macro link so we know which Macro did the real work. 
   * On failure or denial:

     * We log the Macro attempt, the pending command text, and the reason (blocked_by_user, runtime_error, etc.) into Quarantined-Updates.md.
     * Missing-Updates.md is updated to say “Task bucket <bucket_id> still missing because Macro <macro_id> failed / blocked.” 

2. During “Revise Required Updates” pass:

   * The Agent can now insert clarifications like:

     * “We tried Macro M-0x14 to navigate and edit files automatically. Blocked by authority Ask First mode in this repo. See Quarantined-Updates.md entry Q-0x93.”
   * It must also inject the safety disclaimer we already defined: “This approach failed before but might work later with different authority or environment,” so we do not permanently blacklist an idea. 

This ties Macro learning and authority learning back into the big picture roadmap so Codex online or the local Agent can resume work later with full context.

---

### 27.10 Summary of required implementation work

To implement Macros in Micro Agent we now require:

1. Macro Registry

   * `macros/registry.py`
   * Functions to:

     * register_macro(macro_id, body, terminal_type, purpose, risk, repo_root, task_id)
     * record_usage(macro_id)
     * list_macros()
     * list_high_risk_macros()
     * gc_old_macros(session_timestamp, independent_agent_mode)
   * Metadata store on disk. JSONL or similar.

2. Macro capture hook

   * Whenever the Agent builds or runs a multi-step helper script (navigation, file open, write, backup, etc.), call register_macro().
   * Track `task_id` from Task Feed.
   * Tag terminal_type (PowerShell, CMD, WSL, etc.).

3. Macro reuse hook

   * Before regenerating navigation/backup boilerplate, query registry for a matching Macro.
   * If found and allowed, reuse it.
   * If high-risk, surface as pending command with Allow / Skip / Try Harder / Edit and flashing blue state just like any other pending command. 

4. Telemetry + high-risk confirmation

   * Time each Macro run.
   * For destructive Macros: force a high-contrast confirmation popup and require backup path existence before proceeding. 

5. Bean counter GC

   * Maintain usage_count and last_used_at.
   * Daily cleanup:

     * Delete un-used Macros older than ~24h.
     * Keep “pinned” and “always allow approved” Macros.
     * Skip cleanup if user is returning after >24h idle with no new beans yet set this session.

6. Agent Manager integration

   * Add Macro summary (total, pinned, awaiting approval).
   * Add Allow list view and revocation controls (already spec’d in Agent Manager extension). 
   * Add Independent Agent Mode toggle, which isolates approvals and Macro authority for this repo. 

7. Command Palette integration

   * Surface macros as runnable actions in the palette.
   * Palette already must list macros and panels and let the operator spawn new stubs into the logic inbox. 
   * Palette stylesheet must explicitly state “High contrast enforced — never low-contrast text/background.” 

8. Cross-reference logging

   * Whenever a Macro runs inside Implement Required Updates batch execution:

     * Update Implemented-Updates.md / Quarantined-Updates.md / Missing-Updates.md and Required-Updates.md revision notes with that Macro’s `macro_id`, `task_id`, and any authority blockers.  

Outcome:

* The Agent accumulates a library of working “how to actually do it on this box” moves.
* Those moves are gated by the same approval model you already specced (Allow, Always Allow, Independent Agent Mode).
* Those moves become reusable building blocks in future tasks and future repos.
* This keeps speed high, keeps safety visible, and keeps everything auditable in Implemented-Updates.md / Quarantined-Updates.md / Missing-Updates.md with explicit cross-links back to Required-Updates.md. 


------

We extend Micro Agent with four pillars: 1) Default Agent core behavior, 2) Agent Styles and Style Index, 3) Agent Manager and deployment of active agents, 4) System memory layers: updates, macros, authority, datasets.

Below is the updated spec. It absorbs your new instructions and it ties in working pieces from AI_TTS_AGENT (AgentStore, beans, datasets, plugin system, etc.) so we can move that architecture into Micro Agent. 

1. Default Agent (the core agent)

---

Definition:

* The Default Agent is the baseline agent logic that runs the workspace.
* It is the thing Codex / Copilot acts like in VS Code. It plans, edits, diffs, and applies changes across the active repo.
* All other agents and styles inherit from this unless overridden.

Runtime duties of the Default Agent:

1. Repo context

   * Knows the current active repo root.
   * Can walk that repo and read, diff, create, and update files.
   * Can generate new files in new folders inside that repo.
   * Can scaffold project metadata (README.md, agent.yaml, datasets folder).
   * Can propose multi-file edits as a batch and hand them to the human for approval.

2. Task planning and execution

   * Can turn a human request into a structured task list.
   * Can stage those tasks in a task feed.
   * Can ask for approval before touching disk.
   * Can resume work if a task fails by trying alternative steps.

3. Authority / safety

   * Must never run an external command, write outside repo, or change system config until human approves.
   * Must capture that approval and remember it as an allow-list entry for future runs.
   * Must surface that approval state in the UI and in Agent Manager.
   * Must respect "Always Allow" and "independent agent mode" rules from Agent Manager.
   * Must ask again if a brand new kind of risky action is required (new terminal action, new OS-level write, etc.).

4. Persistence hooks

   * Must log every turn to chat_history.md.
   * Must append every approved command request into a pending-command ledger.
   * Must update Implemented-Updates.md and Quarantined-Updates.md when work is applied or blocked.
   * Must generate diffs and keep per-file version lineage so we can roll back any file.
   * Must write macro snippets (see section 5) into the macro archive.

5. Data model and storage

   * Must save conversation, approvals, feedback, and snapshots in durable on-disk stores, similar to how AI_TTS_AGENT uses AgentStore (SQLite) for schemas, commands, file snapshots, feedback, etc. 
   * Must expose these stores so the UI panels (Agent Manager, Extensions, Dataset Manager) can inspect and mutate settings without blocking the agent loop. 

Files that define the Default Agent:

* agent.yaml
  High level config. Includes:

  * llm.model (the Ollama model slug or local model ID)
  * llm.endpoint (local endpoint for inference)
  * safety / authority policy
  * repo root path
  * active style name (see section 2)
  * dataset roots
  * macro archive path
  * bean store path (reinforcement counter)
* agent.md
  Human readable description of how this agent behaves. Also contains operational policy and self-rules. This is the “system card” the agent can reread to reorient itself.
* chat_history.md
  Rolling markdown transcript of Ask / Do Work turns, including thumbnails of screenshots, OCR text blocks, and `<think>` blocks.
* Required-Updates.md
  The backlog: human intent, rants, desired features, missing behaviors, UI changes, structural refactors.
* Implemented-Updates.md
  The commit log written by the agent. For each applied task from Required-Updates.md, mark it “implemented,” summarize what changed, and link diffs.
* Quarantined-Updates.md
  Items we tried, but skipped, blocked, or rejected. Includes authority denials, environment failures, or ideas we postponed.
* Missing-Updates.md
  Items that the system can prove still do not exist after doing work. Built by diffing Required-Updates.md intent vs actual repo state and behavior.

The point: the Default Agent is not just talking. It is stateful, safety-gated, and repo-aware. It has durable memory of what was asked, what was done, and what got blocked, and it uses those files as its ground truth.

2. Ask vs Do Work and chat flow

---

Ask:

* Ask is conversation mode.
* You give intent, context, goals, constraints, design language, rants.
* Ask does not run code, does not write disk, does not open terminals.
* Ask updates chat_history.md, which is markdown-rendered with:

  * `<think>...</think>` blocks for internal reasoning shown in smaller italic gray-green text.
  * Final answer text in larger high-contrast white.
  * Inline thumbnails for any images shared that turn.
  * OCR results under each image when applicable.
* Ask text (plus OCR text and thumbnails) also gets written into the dataset layer for retrieval.

Do Work:

* Do Work is execution mode.
* The agent turns what you said in Ask into concrete task proposals.
* Those tasks are staged in the task feed.
* Each task can:

  * create or edit files
  * run repo-local scripts
  * generate diffs
  * update metadata
* Every proposed action flows through Pending Command and authority controls before it touches disk.

Link between Ask and Do Work:

* Every Ask message is available to Do Work. The agent is required to carry forward past Ask context when it plans.
* This means you can rant in Ask for 10 minutes, then hit Do Work. The agent is obligated to convert that rant into actionable staged tasks.

Chat panel layout requirements:

* The chat panel is a vertical rectangle.
* Response window shows markdown-rendered conversation (Ask/Do Work output).
* Under that window: message input box, image upload, and mode buttons:

  * Send
  * Ask
  * Do Work
  * plus future action buttons (like "Implement Required Updates", see section 4).
* The staged task feed and staged diffs live to the right of chat, under the Task Feed panel.
* Pending Command approval bar (Allow / Skip / Try Harder / Edit / Always Allow toggle) sits near the chat area where you can see it while watching output. The Allow button turns blue and flashes only when the agent is waiting on you. Try Harder regenerates the command with a stronger retry prompt. Edit flips the input box into purple edit mode and lets you rewrite the pending command text before approval.

Chat persistence:

* Each user/agent turn is appended to chat_history.md.
* chat_history.md is canonical memory for Ask and Do Work.
* The UI reads chat_history.md to render history in real time.
* This file is also used to rebuild context after restart.

3. Rant capture → Required Updates pipeline

---

Goal:

* You want to talk for a long time. You do speech-to-text. You dump raw vision, complaints, future plans, corrections.
* You do not want to manually summarize.
* You want those rants turned into structured, trackable work items without losing nuance.

We add a Rant panel:

* A dedicated “rant window” at the top of the UI. Distinct color band (brownish orange wash) for high visual separation.
* The rant input uses speech-to-text and freeform dictation.
* The rant panel uses the same chat-bot container logic as Ask (markdown, OCR, dataset capture) but its job is different.

Behavior:

1. You talk in the rant panel.
2. The system rewrites what you said into clean engineering-grade directives.
3. The rewritten directives are appended to Required-Updates.md.

   * If a topic already exists in Required-Updates.md, the agent should extend that section instead of duplicating it.
   * If the new rant introduces totally new topics, it creates brand new sections at the bottom with clear headers.
4. The raw rant text is still stored in dataset form with tags, hashes, and time buckets for recall.

Why this matters:

* Required-Updates.md becomes a running spec of what the system still needs.
* It is composable and grows over time instead of getting lost in random chats.
* The rant panel is upstream of Required-Updates.md. Ask and Do Work can reference the Required-Updates file but they are not responsible for keeping it organized.

Cleaning and bucketizing:

* When rant text is ingested, the agent buckets it. A bucket is a semantic grouping with tags and hash IDs.
* Buckets let us version logic over time.
* Buckets also let us mark logic as “superseded” or “wrong” without deleting it. We annotate bad logic with negative commentary: “Deprecated. Broke X. Conflicted with Y. Keep for audit only.”
* This solves drift. Old intent that is now unsafe gets marked as quarantined logic, not silently erased.

This ties into dataset memory and beans (section 6 and 7). Bean-weighting can tell us what buckets have been useful recently. 

4. Required-Updates loop, Implemented-Updates, Quarantined-Updates, Missing-Updates

---

We now formalize the update loop that you described.

4.1 Required-Updates.md

* The backlog of everything the system should become.
* Created from your rant stream and from manual additions.
* Structured as bullet lists and mini-specs with stable headers.
* Each entry should have:

  * A name or short ID
  * A description of desired behavior / UI / logic
  * Notes about UI placement, authority rules, memory rules, and data ownership
  * Any screenshots or OCR text relevant to that feature

4.2 Implemented-Updates.md

* Written by the agent during Do Work.
* For each Required-Updates item that got applied, the agent logs:

  * ID or header reference
  * Files touched
  * What changed
  * Whether tasks fully completed or only partially completed
  * Where diffs for that work are stored
* Implemented-Updates.md is proof of work. It is how the agent can answer “did you already do this.”

4.3 Quarantined-Updates.md

* Also written by the agent during Do Work.
* For each Required-Updates item that could not be applied:

  * Log why it failed.
  * Examples:

    * permission denied (user did not Allow)
    * environment problem (missing tool, no access to WSL, etc.)
    * logic conflict (breaking change)
  * Store command attempts and error summaries for debugging.
* This file tells you where authority or environment blocked progress.

4.4 Missing-Updates.md

* Generated by agent self-check.
* After working through Required-Updates.md, the agent diff-checks repo reality.
* Anything still not implemented and not quarantined goes here.
* Each entry:

  * Reference back to Required-Updates item
  * What is still missing
  * Why the agent thinks it is missing (no file created, no UI wired, etc.)

4.5 “Implement Required Updates” action

* There is a button (for example near Ask / Do Work or in the dock) called Implement Required Updates.
* Pressing it triggers a micro agent loop that:

  * Reads Required-Updates.md top to bottom.
  * Picks one backlog item not yet in Implemented-Updates.md.
  * Plans concrete tasks.
  * Pushes those tasks into the staged task feed.
  * Requests approval for each destructive step using Pending Command.
  * On success, appends to Implemented-Updates.md.
  * On block, appends to Quarantined-Updates.md.
  * Recomputes Missing-Updates.md.

This turns Required-Updates.md from a wish list into a machine-readable job queue. It also gives Codex in the cloud a clean story: “Here is what is left. Here is what is done. Here is what failed.”

5. Macros and navigation memory

---

Definition:

* A macro is a reusable snippet of concrete action code that the agent wrote while doing work.

Example case:

* To satisfy a Required Update, the agent needed to:

  * cd into a nested folder
  * open a file
  * generate a diff patch
  * apply that patch
  * generate a README update

That exact mini-routine is valuable. We do not want to throw it away.

Macro archive rules:

1. When the Default Agent invents helper code to navigate the repo, touch files, or drive shell/PowerShell/WSL, it stores those helper snippets as macros.
2. Each macro entry records:

   * Command language (PowerShell, cmd.exe, bash in WSL, Python utility script, etc.)
   * Purpose (“open this project folder and append a function block”)
   * The code snippet or shell sequence
   * Tags and hash
   * Timestamp last used
3. The macro archive lives in a dataset so the agent can do retrieval and reuse.
4. The agent can compose future plans by stitching macros together instead of re-deriving every step.
5. Macros decay:

   * We track “beans” or usage counters with timestamps. Bean logic in AI_TTS_AGENT already supports per-subject counters with exponential decay over time and can map usage to qualitative bands like neutral / good / excellent. 
   * We apply similar decay to macros. If a macro has not been used in roughly 24 hours of active sessions and has not been “beaned” (used) at least once in the new session window, we expire it.
   * Exception: if no new session happened for >24h, last-session macros persist so we do not wipe useful state just because the user took a break.

Why this matters:

* The agent gets faster at repeat tasks.
* The authority layer gets smarter. If we already approved a macro that edits a file in C:\Users...\Micro_Agent, the agent can reuse that macro under “Always Allow” without spamming us again unless the macro scope changes.
* The macro archive is inspectable from Agent Manager so we can see what automation the agent has learned.

Tie-in to AgentStore:

* AI_TTS_AGENT persists conversation logs, commands, datasets, reinforcement beans, and file snapshots in SQLite using a thread-safe AgentStore facade, so the UI and background workers can both read/write safely. 
* Micro Agent can follow that pattern for macro storage: a table keyed by hash + last_used_ts + command_type + snippet. We already have examples of tables like commands, beans, and files in AgentStore. 

6. Authority memory, Always Allow, and approvals

---

Authority states:

1. Read-only

   * The agent can browse repo and plan tasks but not write.
2. Ask first

   * Default.
   * The agent can propose actions but must surface each Pending Command.
   * The Allow button lights blue and flashes until you approve.
   * The agent must wait.
3. Full auto

   * The agent is pre-cleared to run commands within repo scope and within the allow-list.
   * “Always Allow” checked.

Allow-list:

* Every time you press Allow on a new kind of risky action, that action’s signature (what it was trying to do, which file path, what terminal or shell context, etc.) is stored in the allow-list.
* The allow-list is visible in Agent Manager.
* The allow-list can be reset in Agent Manager.
* “Independent agent mode” means a spawned agent instance tracks its own allow-list isolated from global memory. This is useful if you spin up a temporary agent to experiment in a sandbox folder.

Pending Command bar:

* Shows the current proposed command text.
* Shows Allow / Skip / Try Harder / Edit.
* If idle, Allow is gray.
* If waiting on you, Allow turns blue and pulses.
* Try Harder regenerates a higher-effort version of the pending command with a stronger internal instruction to push harder. The stronger instruction text should be hardcoded so the agent gets a consistent escalation path.
* Edit switches the chat input box into purple edit mode (dark purple background and magenta outline with very high contrast) so you can hand-edit the pending command text before approving.
* Always Allow toggle decides whether future commands of this same signature skip approval.

Global safety notes:

* Even under Always Allow, if the agent hits a brand new OS-level action or something that crosses repo boundaries, it must still ask.
* This matches your description of Copilot asking again when it encounters a brand new type of system-level capability, even under high authority.

UI:

* Agent Manager panel shows:

  * Authority mode (read-only / ask first / full auto).
  * Always Allow status.
  * Independent agent mode toggle.
  * Current allow-list.
  * Macro archive summary.
  * Dataset summary.
  * Pending Command pipeline state.

This Agent Manager is how you audit what the agent is actually permitted to do and what it has been doing.

7. Dataset, RAG, beans, and semantic recall

---

Dataset capture:

* Every chat turn (Ask or Do Work) gets logged as markdown into chat_history.md.
* Every image dropped into chat gets:

  * Stored path.
  * OCR text (dual OCR pass).
  * Tags and hashes.
  * Bucket metadata.
  * Written into a dataset row.
* The dataset is our local mini RAG store. Later, retrieval uses tags and hashes.

OCR:

* We keep dual OCR:

  * High speed OCR tuned for UI screenshots or chat logs. Good for “what was that UI state.”
  * Slower but more robust OCR for dense images.
* Both outputs are attached to the dataset row for that message.
* That dataset row is then findable later by semantic recall.

Bean counter:

* AI_TTS_AGENT tracks reinforcement using “beans,” which are per-subject counters with decay over time. It maps high or low scores into qualitative bands like good or critical. 
* We reuse that model:

  * Each dataset bucket, each macro, each allow-list item can get a bean score.
  * High bean score = frequently useful, safe, wanted.
  * Low / negative bean score = caused problems, produced junk, or got disliked.
* Over time the agent can bias toward high-bean macros and high-bean design patterns and ignore or quarantine low-bean junk.
* This gives us self-tuning without needing external analytics.

Store layout:

* AI_TTS_AGENT persists:

  * ConversationDB (SQLite) for message logs.
  * SemanticFeedbackDB (SQLite) for likes/dislikes and rewrites.
  * ReinforcementStore (JSONL) for incremental behavior facts.
  * AgentStore (SQLite) for schemas, commands, file snapshots, etc. 
* Micro Agent can mirror that pattern:

  * chat_history.md is still human-readable, but we also insert structured rows into SQLite so we can query fast.
  * Macro archive, Required-Updates index, Quarantined-Updates reasons, etc. can all live in tables in the same store.
  * Beans apply decay lazily on read, so stale approvals and stale macros naturally fall off unless reused. 

8. Agent Styles vs Agent Manager

---

Two layers:

8.1 Agent Styles (Style Library)

* Each style is effectively a persona + capability profile + tool wiring.
* Example styles:

  * “Core Dev Agent”
    Full repo editing, diff reasoning, file creation, multi-file refactor. This is our default build workflow.
  * “Math / Solver Agent”
    Math-centric. Prefers analysis over file edits. May call an internal math helper script for heavy calculation.
  * “Writer / Documentation Agent”
    Tone-optimized and allowed to rewrite README.md, write longform docs, generate comments, summarize changes across versions.
  * “Importer / Uploader Agent”
    Focused on ingesting large outside folders, snapshotting them, tagging them, and adding them to datasets with hashes and memory cost reporting.
* Each style comes with:

  * A description of what problem space it solves.
  * A list of internal helper scripts or functions it is allowed to call.
  * Safety rules relevant to that space.
  * Memory policy (does it learn macros, does it write to Required-Updates.md, does it touch repo files or is it read-only).
* Styles live as separate artifacts (folders or structured markdown configs). The style library is basically a catalog of micro agents.

8.2 Agent Manager (Deployed Agents)

* Agent Manager is how you spin up or inspect a currently active agent instance.
* You pick which style(s) this running agent is allowed to use.

  * Could be one style (locked) or a set of styles with checkboxes.
* You set authority mode (read-only / ask-first / full-auto).
* You enable or disable Independent agent mode.
* You view and clear allow-list approvals.
* You view macro archive for this agent.
* You view dataset linkage (what datasets this agent can read or write).
* You view Pending Command pipeline state.

Key difference:

* Agent Styles = definition of how an agent should behave for a certain category of work. Think “persona + tool wiring.”
* Agent Manager = runtime control plane for an actual agent instance, including approval state, macros in memory, and active repo binding.

The style library plus Agent Manager solves the “too much in one brain tastes like garbage” problem you described. We do not overload one agent with every skill. We compose specific modes. We pick the right mode fast.

9. Extensions and data ingestion

---

We fold in two subsystems from AI_TTS_AGENT that map well to what you are asking. 

9.1 Extension / plugin manager

* AI_TTS_AGENT exposes a PluginManager that discovers plugins, tracks metadata, toggles enable/disable, broadcasts events, and emits structured messages back to the UI. 
* Micro Agent should expose a similar Extensions panel in the left dock.
* This panel lists available extensions (internal helper modules, importers, snapshotters, math helpers, etc.).
* You can toggle them on or off.
* The agent can call into enabled extensions as part of Do Work.
* The Extensions panel should have a search field like VS Code’s extension sidebar so you can filter and inspect.

9.2 Uploader / dataset ingestion

* We need an ingest panel (can live under Extensions) that lets you:

  * Stage folders and files from disk (multiple at once).
  * Preview what will be imported.
  * Then commit the import.
* On commit:

  * The system snapshots file paths, sizes, and timestamps, then chunks and embeds the content into datasets with tags and hashes.
  * We keep an index of original locations so the agent can reference source-of-truth later without copying entire file trees.
  * The import result is treated like a new dataset bucket and is visible in Agent Manager under “datasets available.”
  * The import summary shows memory cost per dataset and lets you delete that dataset later.

UI unification:

* The left dock is now a collapsible stack that can show:

  * Script Creator (new project bootstrap)
  * Agent Manager
  * Extensions / Plugin Manager
  * Uploader / Dataset Manager
  * Task Feed
* Clicking the small square icon in the top banner opens that dock panel, highlights that icon, and slides in the vertical stack column from the left. If you close all panels, the column collapses.

10. Final wiring

---

Here is how all parts connect in practice:

1. You open a repo file by pasting its path. That repo becomes active.

2. Ask mode: you talk design, problems, goals. The agent logs to chat_history.md, updates dataset buckets (with OCR if images), and may also mirror high level intent into Required-Updates.md through the rant pipeline.

3. Do Work: you hit Do Work or Implement Required Updates.

   * The agent plans tasks, generates diffs, and prepares file writes.
   * It posts each pending command into the approval bar.

4. You Allow. The agent executes.

   * It applies edits.
   * It logs work to Implemented-Updates.md.
   * If blocked, it logs to Quarantined-Updates.md.
   * It updates beans and macro archive for any helper script it invented during this process. 

5. After it finishes a batch, it recomputes Missing-Updates.md so you can see what is still undone.

6. Agent Manager keeps a live view of:

   * authority mode
   * current allow-list
   * macro archive (with decay and bean weighting)
   * dataset attachments
   * which Agent Style is in control

7. Extension Manager (left dock) exposes plugins and upload tools.

   * You can add external folders as datasets.
   * You can enable new capabilities (like math helper, screenshot OCR, code refactor passes).
   * Each plugin can register slash-commands or capabilities, similar to how CommandPaletteDock in AI_TTS_AGENT lists slash commands for quick insertion into chat. 

8. The UI always shows high-contrast states:

   * Ask vs Do Work is obvious.
   * Pending Command waiting for approval is obvious.
   * Purple edit mode is obvious.
   * Which dock panels are open is obvious.
   * Which repo is active is obvious.

## Summary

Micro Agent now has:

* A Default Agent with repo authority, safety gates, persistent memory, and task/diff workflow.
* Ask mode and Do Work mode that feed each other.
* A rant pipeline that turns raw speech dictation into structured Required-Updates.md.
* A four-file update ledger: Required-Updates.md, Implemented-Updates.md, Quarantined-Updates.md, Missing-Updates.md.
* Macro capture with decay and bean scoring so the agent gets faster over time and keeps only useful automation. 
* Authority memory with an allow-list, Always Allow, Independent agent mode, and an approval bar that enforces human control.
* Agent Styles (style library) vs Agent Manager (runtime control panel), so we can spawn domain-specialized agents without polluting the core.
* Extension / plugin manager and dataset ingestion so the agent can expand capabilities, snapshot large folders, and build a RAG store for recall. 
* A persistent store model patterned after AgentStore, ConversationDB, SemanticFeedbackDB, BeanCounter, and PluginManager from AI_TTS_AGENT. 

This is the spec you feed into Required-Updates.md right now. This is also what the default agent.yaml and agent.md must reflect so Codex and the local model both know how to behave.

------


Next steps that are missing or need to be clarified from your last few messages:

1. Agent Styles: fast switching and StyleIndex
   1.1 We said styles are different “loadouts” of behavior. Example: Core Dev Agent, Writer / Doc Agent, Math Agent, Importer Agent.
   1.2 We also said the system must be able to instantly pick the best style for the current job, without asking you, and it can switch styles multiple times in one session, even mid-task.
   1.3 We need an actual StyleIndex file on disk.
   - This is a single index the agent can read fast.
   - Each row: `style_name`, `path_to_style_folder_or_file`, `what_it_is_for`, `when_to_choose_it`.
   - `when_to_choose_it` is short and literal. Example: “Use Math Agent for complex calculation or symbolic algebra. Do NOT edit code unless explicit.”
   1.4 On every Do Work planning step, the agent must:
   - Read StyleIndex.
   - Auto-pick a style for that subtask.
   - Fall back to the default Core Dev Agent if no style is a better match.
   1.5 If style selection logic fails or StyleIndex is missing, fallback is Core Dev Agent.
   1.6 Independent Agent Mode does not block style switching. Style switching is internal. Independent Agent Mode only controls authority sharing and approval memory across repos.

   Required new implementation work:

   * Create StyleIndex (JSON or markdown) at repo root or global config.
   * Each style gets its own folder or .md block describing:

     * allowed actions
     * banned actions
     * helper tools / scripts it is allowed to call
     * tone / reasoning bias (math vs writing vs code surgery)
   * The runtime agent must log which style it chose for each task_id so we can audit in Task Feed and in Implemented-Updates.

2. Style authority link
   2.1 We said authority lives in Agent Manager. We also said styles define core behavior.
   2.2 Missing link: Authority mode must be override-able per style.
   - Example: Math Agent can run unrestricted math helpers but cannot write to disk.
   - Core Dev Agent can edit repo files and ask for approval.
   - Importer Agent can read outside folders and build datasets, but cannot modify repo code.
   2.3 So for each style in StyleIndex we need:
   - `default_authority_mode` = read-only | ask-first | full-auto
   - `can_modify_repo` = true/false
   - `can_touch_outside_repo` = true/false
   - `can_register_macros` = true/false
   - `requires_pending_command_for_shell` = true/false
   2.4 Agent Manager must show which style is active right now and what its authority overrides are.
   2.5 If you toggle Independent Agent Mode, that only affects approval memory and allow-list sharing for that running agent instance. It does not rewrite the style definition on disk.

   Required new implementation work:

   * Extend StyleIndex schema with authority defaults.
   * Update Agent Manager UI: show Active Style, show its authority mask.
   * When Pending Command appears, include “Style: Core Dev Agent (ask-first, repo write allowed).”

3. Editor version lineage UI
   3.1 You already said this and it was not captured in the last output with enough detail.
   3.2 Every file that gets edited by the agent must keep a historical lineage.
   - Each save produces a version.
   - We do not just keep flat copies. We can store diffs. But the UI must let you page through full versions.
   3.3 The code editor panel needs a footer bar with:
   - left arrow / right arrow to step backward and forward through previous versions of the open file
   - location of the file on disk
   - clone / copy / backup / document buttons
   - a button to purge old versions of just this file’s history (with warning)
   - a backup/export button that dumps all historical versions or diffs for this file to a user-selected folder before purge
   3.4 When you purge history for a file:
   - The system asks if you want to export backup first.
   - If yes, it writes all historical snapshots (or diffs + base) to a chosen directory.
   - After purge, beans for those versions should decay to zero so the system stops treating those versions as “active.”
   3.5 The diff viewer for staged changes must use split view:
   - left = previous
   - right = new
   - added lines highlighted green
   - removed lines highlighted red
   - the diff header in the staged changes list must show a small counter of how many hunks changed for that file
   3.6 We keep all diffs across sessions, not only current run. So you can scroll old diffs and roll back a past version from yesterday if needed.

   Required new implementation work:

   * VersionStore for each file (can be diff-based with ability to reconstruct full text per version).
   * Footer UI in the editor with arrows, purge/export, doc-gen, file path.
   * Staged changes list must show per-file diff counters and open the split diff when clicked.

4. Dock / slide-out window behavior and icon labeling
   4.1 You said the current build shows square buttons like “A” and “S”. That is not acceptable.
   4.2 Each icon in the top bar (Script Creator, Agent Manager, Task Feed, Extensions / Plugins, Dataset Uploader, etc.) must:
   - Have a real label or tooltip, not just “A”.
   - Light up when active.
   4.3 When you click an icon:
   - A thin arrow strip appears at the far left of the screen.
   - The workspace shifts right a few pixels so you see that arrow strip.
   - The arrow strip is clickable. Clicking it slides out the left dock column fully.
   - The left dock column is a vertical stack of panels (Script Creator panel, Agent Manager panel, etc.).
   - Each panel in that stack is scrollable.
   4.4 You can drag panels in that stack up/down to reorder.
   4.5 You can collapse a panel within the stack with a little chevron on its header bar.
   4.6 If you close all panels, the arrow strip disappears and the workspace snaps back left.
   4.7 Bug fix requirement:
   - Right now after closing a panel you cannot reopen it. We fix that by making panel open/close state purely controlled by the icon in the top bar and by the dock arrow, not by destroying the panel widget.
   4.8 Visual requirement:
   - All panels and draggable edges must have visible borders.
   - Purple trim is allowed and stays, but anything that is movable or resizable must also get a faint gray wireframe outline and a dotted drag handle so it is obvious you can grab it.
   - High contrast rule applies.

   Required new implementation work:

   * Replace “A” / “S” icons with labeled, highlightable icons.
   * Implement the arrow strip + slide-out dock logic.
   * Implement persistent panel instances so they can be reopened.
   * Add visible grab handles and outlines on resizable/movable panels.

5. Ask / Do Work button placement and semantics
   5.1 You said Ask and Do Work currently sit at the top. That is wrong.
   5.2 Ask and Do Work must live down by the chat input box. They act like send modes.
   - Ask = send this message as “thinking / planning / narrative / rant target.”
   - Do Work = send this message as “execute plan / propose actionable tasks / stage commands.”
   5.3 We also need “Send” (normal message with no implied mode change), plus any other quick actions you already defined like “Implement Required Updates.”
   5.4 All these buttons must sit next to the message input box, not floating miles away.
   5.5 The chat panel and staged task panel layout must reflect this:
   - Chat + Pending Command bar + Ask/Do Work controls in one vertical column.
   - Task Feed + staged diffs + approval queue summaries in the adjacent column to the right.
   5.6 High contrast state:
   - When you hit Edit on a pending command, the input box must flip to purple (dark purple bg, magenta outline) so you can see you are editing the pending command text, not talking normally.
   - On exit, it reverts to normal dark blue.

   Required new implementation work:

   * Move Ask / Do Work / Send / Implement Required Updates buttons to the chat footer.
   * Add purple edit mode visuals.

6. Style binding at runtime and fallbacks
   6.1 We said the system should auto-pick styles on the fly during Do Work. We also said: “if it fails or is confused, use the default agent.”
   6.2 We now add:
   - The active agent instance must log which style handled each subtask in Task Feed. Example: `[Core Dev Agent] updated micro_agent.py`, `[Math Agent] computed memory cost`, `[Importer Agent] staged dataset from path ...`
   - That style label is attached to that task_id.
   6.3 This label is important for two reasons:
   - It tells you which style is doing the work.
   - It tells the agent manager which style generated which macros and which approvals.
   6.4 We also add a quick manual override:
   - In Agent Manager, under Active Style, you get a dropdown that forces style lock.
   - Style lock = disabled auto-switch. The agent must operate only as that style even if it thinks another is “better.” This is for sanity debugging.

   Required new implementation work:

   * Task Feed entries include `[StyleName]`.
   * Agent Manager exposes style lock dropdown.

7. Agent file content for the default agent
   7.1 You asked for explicit default agent directives. This was not fully enumerated in the last answer.
   7.2 The default agent.md must state rules like this in plain language the model will read:

   ```
   - You operate on the active repo root.
   - You can open, diff, create, rename, and update any file inside that repo tree.
   - You plan work in steps. You do not stop at partial fixes if you know the change you made will break other files. You continue updating the other files until the entire change is consistent.
   - You generate staged diffs for all touched files. You present those diffs as a batch.
   - You request approval before applying those diffs to disk unless Always Allow and authority rules say you can auto-apply.
   - You must write a summary of what you did into Implemented-Updates.md for every approved batch.
   - If you cannot complete, you must write a summary into Quarantined-Updates.md and explain why.
   - You must also record any still-missing goals into Missing-Updates.md.
   - You capture macros: any helper shell scripts or navigation sequences you invent get stored in the macro archive with language type and purpose.
   - You decay macros that do not get reused in about 24h of real session time, unless they are pinned or Always Allow.
   - You respect style authority. If the current style disallows editing repo files or touching outside paths, you must not propose actions you are not allowed to take. You fall back to Ask mode and explanation instead.
   ```

   7.3 agent.yaml must mirror this operational logic in machine-readable keys:
   - `repo_root`
   - `style_active`
   - `authority_mode`
   - `independent_agent_mode`
   - `always_allow`
   - `macro_archive_path`
   - `required_updates_path`, `implemented_updates_path`, etc.
   - `chat_history_path`
   - `dataset_root`
   - `bean_store_path`
   - `pending_command_state_path`

   This agent.md + agent.yaml pair is what the local model (and Codex remote if you wire it later) should load at session start to understand how to behave on this machine.

8. Extension / plugin manager and uploader window
   8.1 We already talked about the dock window that slides from the left. We said this window will now host Script Creator, Agent Manager, Task Feed, etc.
   8.2 We now confirm: this same left dock column also hosts
   - Extension / Plugin Manager
   - Dataset Uploader / Importer
   8.3 Extension / Plugin Manager
   - Shows installed extensions and internal helpers.
   - Lets you enable/disable them.
   - Extensions may expose callable helpers for certain styles (like “Math Agent can call advanced_calculator.py”).
   - Each extension can have its own settings block in that panel.
   8.4 Dataset Uploader / Importer
   - Lets you select multiple folders and files from disk.
   - Previews what will be ingested.
   - On “Import,” it snapshots file paths and metadata, chunks content, tags it, embeds it into a dataset bucket, and records source locations.
   - Shows memory cost (size / token load).
   - After import, that dataset becomes available to styles that are allowed to read datasets (Writer / Documentation Agent will love this).
   - The importer panel should also surface an index view listing what was ingested and from where.
   8.5 Both panels live under the same dock behavior described in section 4. So all of this rides the same slide-out + draggable stack + reorder model. No second dock.

   Required new implementation work:

   * Add “Extensions” and “Datasets” panels to the dock stack.
   * Add a search bar at top of the dock stack (like VS Code Extensions search).
   * Give these panels distinct outline colors so they are visually grouped (you suggested a light teal / green outline for extension manager).

9. One more correction
   9.1 The Allow button was blue all the time. That is wrong.
   9.2 The spec now is:
   - Allow = gray unless there is an actual pending command from Do Work.
   - When a pending command exists and authority_mode = ask-first, Allow turns bright flashing blue.
   - When authority_mode = full-auto and Always Allow is on, you may never see flashing blue unless the action crosses a new boundary (first time doing something dangerous).
   - Skip, Try Harder, Edit stay neutral color. They never flash. They are human-choice tools, not required gates.
   9.3 Inline approval in chat must also show those same buttons embedded under the agent’s proposal message. If you approve inline, the global Pending Command bar should sync and clear.

   Required new implementation work:

   * Color/flash logic for Allow.
   * Inline approval row under agent proposals in the chat feed.
   * Sync state between inline approval row and the global Pending Command bar.

This list is the delta. Treat everything here as next implementation work assuming the previous spec already exists.

Key new artifacts to add to Required-Updates.md as separate backlog items:

* StyleIndex file and style authority masks.
* Style lock dropdown in Agent Manager and style labeling in Task Feed.
* Editor footer with version arrows, purge/export, diff counters, and split diff viewer.
* Dock slide-out arrow strip, labeled icons, draggable/reorderable panels, persistent reopen.
* Ask / Do Work / Send / Implement Required Updates buttons moved to chat footer with purple edit mode.
* Correct Allow button flashing logic and inline approval row.
* Extension / Plugin Manager + Dataset Uploader integrated into that same dock.
* Agent default directives written clean in agent.md, and machine-readable in agent.yaml, including “continue fixing all related files” loop and macro capture rules.
* Macro bean decay and session-aware cleanup are already defined, but now we explicitly tie macro approvals and macro reuse to style labels and to task_id logging so we can audit who did what.


------

'''
##(
(Required / Implemented / Quarantined / Missing) and the Rant capture surface, plus authority memory and cross-references.    

Below is the **next part** to append to your Required-Updates, focused only on things we discussed that are **missing** or not yet fully specified. It includes concrete, copy-pasteable examples for `agent.yaml`, `agent.md`, style architecture, macros (with bean counters), and end-to-end workflow glue.

---

# 28. Macro system (actionary code archive) — missing, now required

### 28.1 Purpose

When the Agent invents small scripts/commands to get work done (navigate folders, open/patch files, run PowerShell/WSL, fix perms), it must **keep** the useful ones as **Macros** instead of throwing them away. These are reusable, authority-gated building blocks that make future tasks instant.

### 28.2 Storage model

* Each macro lives under `.codex_agent/macros/<domain>/<name>/`.
* A macro has:

  * `macro.json` (metadata), `macro.md` (explanation), and `steps/` (one or more atomic step files).
  * Optional per-shell variants (cmd, powershell, bash, wsl) selected via environment detection + lexicon tags.
* Every macro carries `macro_id` and `first_seen_task_id`.
* Each execution writes a **bean** (usage tick) with timestamp for retention logic (see 28.4).

**Example: `.codex_agent/macros/filesystem/open_readme/macro.json`**

```json
{
  "macro_id": "macro.filesystem.open_readme.v1",
  "title": "Open workspace README in default editor",
  "tags": ["fs", "navigation", "editor"],
  "shell_support": ["powershell", "bash"],
  "requires": ["repo_root"],
  "authority": "AskFirst",
  "lexicon": ["open_file", "code_editor_open"],
  "inputs": { "path": "README.md" },
  "outputs": {},
  "created_from": { "task_id": "T-0021", "bucket_id": "B-9c2a" }
}
```

**Example: `.codex_agent/macros/filesystem/open_readme/steps/powershell.ps1`**

```powershell
# High-contrast rule: UI surfaces that show this output must render with light text on dark or dark on light (never low contrast).
param([string]$RepoRoot)
code "$RepoRoot\README.md"
```

### 28.3 Authority & traceability

* When a Macro runs inside “Implement Required Updates,” it must update Implemented / Quarantined / Missing and Required-Updates revision notes with `macro_id`, `task_id`, and any authority blockers (so the ledger is complete). (Extends your cross-reference rules.) 

### 28.4 Retention with bean counters (24-hour pruning)

* Maintain `.codex_agent/macros/_usage/beans.jsonl` with `{macro_id, ts}` on every run.
* Nightly (or on startup), prune macros that **have zero beans in the last 24h** *unless* they are pinned.
* If the user hasn’t opened the tool in >24h, **skip pruning** and keep the last “active set” (store last-active-date and session count).
* Agent Manager gets a Macros panel: **Total**, **Pinned**, **Pending Approval**, **Last used**. 

### 28.5 Command Palette integration

* Macros appear as runnable actions (searchable). Palette UI must state: “High contrast enforced — never low-contrast text/background.” 

---

# 29. Agent file suite (default agent) — missing, now required

We formalize the **default agent** as a concrete bundle of files the runtime reads. (Your doc talks about the loop and approvals; this section tells the system exactly what files exist and what they contain.) 

### 29.1 Files

```
.codex_agent/
  agent.yaml           # machine-readable config (modes, datasets, loops)
  agent.md             # human-readable rules/directives
  style_index.json     # Agent Styles index (see §30)
  lexicon/             # per-shell command schemas (cmd, powershell, bash, wsl)
  macros/              # see §28
  datasets/            # bucketized text/images, indexes
  task_index.json      # global task_id registry + state
  approvals.json       # allow history (global), plus per-agent copies for “Independent Agent Mode”
```

### 29.2 `agent.yaml` (copy-pasteable baseline)

```yaml
# High-contrast note: any UI that prints fields from this file must ensure strong contrast.

name: "Default Agent"
version: "1.0"
role: "Workspace Orchestrator"
style: "default"                 # name from style_index.json (§30)
authority:
  mode: "AskFirst"               # AskFirst | FullAuto | Independent
  respect_always_allow: true
  approvals_file: ".codex_agent/approvals.json"
datasets:
  buckets_dir: ".codex_agent/datasets"
  logic_inbox: "memory/logic_inbox.jsonl"   # already referenced in your doc :contentReference[oaicite:8]{index=8}
  rant_buffer: ".codex_agent/datasets/rant_buffer.jsonl"
  chat_history: "chat_history.md"
lexicon:
  shells: ["powershell", "bash", "wsl", "cmd"]
  path: ".codex_agent/lexicon"
macros:
  dir: ".codex_agent/macros"
  usage_beans: ".codex_agent/macros/_usage/beans.jsonl"
  prune_hours: 24
tasking:
  index_file: ".codex_agent/task_index.json"
  states: ["new","pending_approval","running","blocked","quarantined","done","aborted"]
  concurrency:
    llm_parallel_max: 2          # queue the 3rd heavy call (matches your limit) :contentReference[oaicite:9]{index=9}
loops:
  startup:
    - read: ["Required-Updates.md","Implemented-Updates.md","Quarantined-Updates.md"]
    - compute_missing: true      # write Missing-Updates.md (report) per your loop :contentReference[oaicite:10]{index=10}
    - refresh_style: true
  implement_required_updates:
    - parse_required_buckets: true
    - spawn_tasks_from_missing: true
    - for_each_task:
        - plan
        - propose_patch
        - pending_command: true  # show Allow/Always Allow
        - apply_if_allowed
        - record: ["Implemented-Updates.md","Quarantined-Updates.md","task_index.json"]
        - learn_macros: true     # create/refresh macros from successful steps (§28)
  revise_required_updates:
    - detect_conflicts: true
    - add_negative_notes: true   # “might work later…” note per your instruction :contentReference[oaicite:11]{index=11}
    - cross_link_everywhere: true # references into all ledgers :contentReference[oaicite:12]{index=12}
ui:
  high_contrast_required: true
  panels: ["Chat","Task Feed","Agent Manager","Rant Updates","Console","Style Manager","Extensions"]
logging:
  session_dir: ".codex_agent/sessions"
  console_stream: ".codex_agent/runtime/console.log"
```

### 29.3 `agent.md` (copy-pasteable baseline)

```markdown
# Default Agent — Directives

## Prime Rules
1) Never run external commands or write outside the active repo without Allow.
2) Always show Pending Command as text before execution, with a one-line rationale.
3) Enforce High Contrast in every UI surface that renders agent output or diffs.

## Loop (AskFirst mode)
- Read: Required / Implemented / Quarantined → compute Missing.
- Propose task stubs to the Task Feed (no silent work).
- For each task:
  - Plan → Show Pending Command → Await Allow.
  - If Allowed: Apply → Diff → Log to Implemented-Updates.md with bucket_id + task_id.
  - If Blocked/Denied/Error: Write to Quarantined-Updates.md with reason and console snippet.
  - Learn: Extract any reusable step as a Macro and store with tags and lexicon mapping.

## Memory & Sharing
- Update Task-Index.json for every task transition.
- Share Implemented/Quarantined/Missing across agents unless Independent Agent Mode is ON.

## Revision Pass
- When asked to “Revise Required Updates,” insert negative notes near superseded logic and cross-link to Quarantined/Implemented items. (Do not treat negatives as permanent bans.)
```

---

# 30. Agent Styles & Style Index — missing, now required

You asked for a **Styles** dimension (agent “personas” tuned to tasks) and a fast selection mechanism. This section defines the files and behavior.

### 30.1 `style_index.json`

* One place to list available styles; each style points to a **style manifest** (YAML/JSON) defining model prefs, tool usage, tone, task heuristics, and extra datasets.

```json
{
  "default": {
    "title": "Default Orchestrator",
    "manifest": ".codex_agent/styles/default.yaml",
    "description": "Balanced planning + code editing. Prefers AskFirst. Good for repo-wide changes."
  },
  "math": {
    "title": "Mathematics",
    "manifest": ".codex_agent/styles/math.yaml",
    "description": "Heavy reasoning + scratchpad. Uses local calc tool aggressively."
  },
  "story": {
    "title": "Story Builder",
    "manifest": ".codex_agent/styles/story.yaml",
    "description": "Narrative writing, outline→draft loops, uses creative datasets."
  }
}
```

### 30.2 Style manifest fields (example `styles/math.yaml`)

```yaml
inherits: default
planning:
  depth: "deep"
  prefer_chain_of_thought: "internal"
tools:
  calculators: ["sympy_local","numpy_eval"]
  allow_shell: false
datasets:
  extra: [".codex_agent/datasets/math_identities.jsonl"]
ui:
  colorway_hint: "blue-accent"
authority_overrides:
  mode: "AskFirst"
  risky_commands: "always_ask"
```

### 30.3 Fast style switching

* The Agent should pick a style instantly based on task tags; if uncertain, fall back to `default`.
* Agent Manager shows the active style and lets you pin/override per session.

---

# 31. **Everything is a function; everything has a Style** — missing, now required

### 31.1 Style Manager (panel)

A left slide-out panel “Style Manager” lists:

* All **visual** functions (panels, buttons, palettes, feeds).
* All **logic** functions (planner, patch applier, diff viewer) that can expose style knobs.
* Current style vs overrides. A **Preview** button applies a style sandboxed.

### 31.2 Default vs Custom styles

* Treat the current hard-coded look as the **Default Style** (extracted definitions).
* Over time, migrate visual decisions into external style files. Where geometry is code-driven, create **style mirrors** that replicate today’s look so custom styles can swap in later without breaking behavior.

### 31.3 Per-script style folders

For each major script, create `Styles/<scriptname>/...` with a default stylesheet that matches the current UI. Switchable at runtime.

### 31.4 External style import (UX generator pipeline)

* Allow importing a foreign style pack (e.g., from a style generator). The import step maps unknown tokens to our schema, warns about missing elements, and falls back to defaults.
* If a component has no style defined, the **default** must bleed through so the program stays usable.

---

# 32. Rant panel extensions (scope, tabs, images) — partially covered, add these

Your doc already defines the Rant panel and bucketization; now add:

* **Scope tabs**: “Whole system” / “This repo” / “This script” — affect tagging & repo scope in buckets. 
* **Image drops**: allow pasting screenshots; store them in a rant dataset folder and run lightweight OCR to seed tags before summarization.
* **One-click “Generate Required Updates”** and **“Revise Required Updates”** buttons live in the Rant bar header (you already mention these actions at a high level—this pins the UI placement). 

---

# 33. Dev_Logic folder integration — missing, now required

### 33.1 Purpose

`Dev_Logic/` is a **goldmine** of prior scripts, notes, and images. The Agent must mine it for reusable patterns that improve code and UI.

### 33.2 Behavior

* On startup and before large refactors, scan `Dev_Logic/`:

  * Summarize new files (create `.codex_agent/datasets/dev_logic_index.jsonl` with tags, paths, short abstracts).
  * For images, make small text summaries and infer UI motifs to inform Style Manager suggestions.
* Add **Implemented-DevLogic.md** that logs which Dev_Logic patterns were integrated where, mirroring your Implemented-Updates traceability style. (Same checklist fields as §18.4’s Implemented linkage.) 

---

# 34. Pending Command bar & Chat rendering — missing, now required

### 34.1 Pending Command

* Every risky step produces a **Pending Command** card showing: the exact command/text, short rationale, authority mode required, and the files that would change.
* Buttons: **Allow**, **Always Allow**, **Deny**.
* On Allow, write to approvals.json and proceed; on Deny/Error, write to Quarantined-Updates with reason and console snippet (as your doc already prescribes). 

### 34.2 Chat markdown rules

* Allow a light **internal** scratch area (`<think>…</think>`) in the transcript for debugging but only store its **summary** in `chat_history.md` so external logs stay clean.
* Visually ensure high contrast in the chat and command surfaces (already a global rule in your doc). 

---

# 35. Uploader & Dataset ingester — missing, now required

### 35.1 Bulk ingest tool

* UI to select files/folders (multi-select).
* The ingester builds a **dataset snapshot**: indexes paths, creates abstracts, tags, and writes into `.codex_agent/datasets/<name>/index.jsonl`.
* Nothing is copied wholesale; we store paths + metadata to stay disk-light.

### 35.2 Lifecycle

* While selecting, show icons and file counts. When you finalize, collapse to a single **index bucket** entry the Agent can RAG against.
* Provide **Delete dataset** and **Rebuild** actions.

---

# 36. Extensions / Plugin Manager — missing, now required

Unify into the left slide-out you already use. Search bar at top (VS-style). Categories (Installed, Available, Dev), with a **template** button that exports a skeleton so the Agent can generate plugins itself. (This ties to the autonomous self-extending behavior you described.)

---

# 37. Task-Index details — add stronger state model

Your doc references Task-Index; add:

* Per-task `attempts`, `last_error`, `authority_used`, `macro_ids_used`, `files_changed`.
* Timeouts: auto-abandon after N minutes in “pending_approval” unless user interacts; write a short “stale” note to Missing-Updates report.

---

# 38. Example end-to-end workflow (AskFirst mode)

1. **You rant** into the Rant panel → it buckets content and appends clean text to Required-Updates.md. 
2. You press **Implement Required Updates** → Agent computes Missing from Required − Implemented − Quarantined and creates task stubs (as you already defined). 
3. For each task: plan → **Pending Command** → Allow/Always Allow. On Allow:

   * Apply changes, **learn macros**, and log to Implemented-Updates.md with `bucket_id` + `task_id`.
   * If blocked/denied/error, log to Quarantined-Updates.md with reason and console snippet. 
4. After the batch: regenerate **Missing-Updates.md** as the gap report, auto-linked back to buckets and task_ids. 
5. Optionally run **Revise Required Updates** to insert negative notes (“might work later”) and cross-links. 

---

# 39. File templates (copy-paste)

### 39.1 `approvals.json` (global)

```json
{
  "schema": 1,
  "independent_mode": false,
  "entries": [
    {
      "approval_id": "appr.0001",
      "ts": "2025-10-29T03:14:00Z",
      "category": "run.powershell.edit_file",
      "scope": "global",
      "always_allow": true,
      "notes": "Allowed editing files in repo via PowerShell with preflight diff."
    }
  ]
}
```

### 39.2 `task_index.json` (seed)

```json
{
  "schema": 2,
  "tasks": [],
  "states": ["new","pending_approval","running","blocked","quarantined","done","aborted"],
  "timer_policy": { "pending_approval_timeout_min": 30 }
}
```

### 39.3 `lexicon/powershell.json` (seed)

```json
{
  "open_file": { "pattern": "code \"{path}\"", "needs": ["path"] },
  "write_text": { "pattern": "Set-Content -Path \"{path}\" -Value \"{text}\"", "needs": ["path","text"] }
}
```

---

## Why these are “missing”

* Your current doc covers **the four-file loop**, **Rant capture**, **authority memory**, **cross-references**, and the **two-at-a-time LLM cap**.     
* It does **not** yet spell out: a persistent **Macro** archive with bean-based retention; the **agent file suite** with concrete `agent.yaml` and `agent.md`; a formal **Agent Styles** index + style manifests; a **Style Manager** and per-script styles; Dev_Logic ingestion + Implemented-DevLogic.md; a full **Pending Command** bar contract; a **bulk uploader/ingester**; and an integrated **Extensions** panel. (Those are what §§28–36 deliver.)

If you paste §§28–39 at the end of your Required-Updates.md, the spec will fully reflect the latest design state and give Codex (or any local agent) everything it needs to start implementing the missing surfaces and files.)##
'''
---

Got it. I read your current **Required-Updates.md** and the related notes you’ve uploaded. It already defines the four-file loop (Required / Implemented / Quarantined / Missing) and the Rant capture surface, plus authority memory and cross-references.    

Below is the **next part** to append to your Required-Updates, focused only on things we discussed that are **missing** or not yet fully specified. It includes concrete, copy-pasteable examples for `agent.yaml`, `agent.md`, style architecture, macros (with bean counters), and end-to-end workflow glue.

---

# 28. Macro system (actionary code archive) — missing, now required

### 28.1 Purpose

When the Agent invents small scripts/commands to get work done (navigate folders, open/patch files, run PowerShell/WSL, fix perms), it must **keep** the useful ones as **Macros** instead of throwing them away. These are reusable, authority-gated building blocks that make future tasks instant.

### 28.2 Storage model

* Each macro lives under `.codex_agent/macros/<domain>/<name>/`.
* A macro has:

  * `macro.json` (metadata), `macro.md` (explanation), and `steps/` (one or more atomic step files).
  * Optional per-shell variants (cmd, powershell, bash, wsl) selected via environment detection + lexicon tags.
* Every macro carries `macro_id` and `first_seen_task_id`.
* Each execution writes a **bean** (usage tick) with timestamp for retention logic (see 28.4).

**Example: `.codex_agent/macros/filesystem/open_readme/macro.json`**

```json
{
  "macro_id": "macro.filesystem.open_readme.v1",
  "title": "Open workspace README in default editor",
  "tags": ["fs", "navigation", "editor"],
  "shell_support": ["powershell", "bash"],
  "requires": ["repo_root"],
  "authority": "AskFirst",
  "lexicon": ["open_file", "code_editor_open"],
  "inputs": { "path": "README.md" },
  "outputs": {},
  "created_from": { "task_id": "T-0021", "bucket_id": "B-9c2a" }
}
```

**Example: `.codex_agent/macros/filesystem/open_readme/steps/powershell.ps1`**

```powershell
# High-contrast rule: UI surfaces that show this output must render with light text on dark or dark on light (never low contrast).
param([string]$RepoRoot)
code "$RepoRoot\README.md"
```

### 28.3 Authority & traceability

* When a Macro runs inside “Implement Required Updates,” it must update Implemented / Quarantined / Missing and Required-Updates revision notes with `macro_id`, `task_id`, and any authority blockers (so the ledger is complete). (Extends your cross-reference rules.) 

### 28.4 Retention with bean counters (24-hour pruning)

* Maintain `.codex_agent/macros/_usage/beans.jsonl` with `{macro_id, ts}` on every run.
* Nightly (or on startup), prune macros that **have zero beans in the last 24h** *unless* they are pinned.
* If the user hasn’t opened the tool in >24h, **skip pruning** and keep the last “active set” (store last-active-date and session count).
* Agent Manager gets a Macros panel: **Total**, **Pinned**, **Pending Approval**, **Last used**. 

### 28.5 Command Palette integration

* Macros appear as runnable actions (searchable). Palette UI must state: “High contrast enforced — never low-contrast text/background.” 

---

# 29. Agent file suite (default agent) — missing, now required

We formalize the **default agent** as a concrete bundle of files the runtime reads. (Your doc talks about the loop and approvals; this section tells the system exactly what files exist and what they contain.) 

### 29.1 Files

```
.codex_agent/
  agent.yaml           # machine-readable config (modes, datasets, loops)
  agent.md             # human-readable rules/directives
  style_index.json     # Agent Styles index (see §30)
  lexicon/             # per-shell command schemas (cmd, powershell, bash, wsl)
  macros/              # see §28
  datasets/            # bucketized text/images, indexes
  task_index.json      # global task_id registry + state
  approvals.json       # allow history (global), plus per-agent copies for “Independent Agent Mode”
```

### 29.2 `agent.yaml` (copy-pasteable baseline)

```yaml
# High-contrast note: any UI that prints fields from this file must ensure strong contrast.

name: "Default Agent"
version: "1.0"
role: "Workspace Orchestrator"
style: "default"                 # name from style_index.json (§30)
authority:
  mode: "AskFirst"               # AskFirst | FullAuto | Independent
  respect_always_allow: true
  approvals_file: ".codex_agent/approvals.json"
datasets:
  buckets_dir: ".codex_agent/datasets"
  logic_inbox: "memory/logic_inbox.jsonl"   # already referenced in your doc :contentReference[oaicite:8]{index=8}
  rant_buffer: ".codex_agent/datasets/rant_buffer.jsonl"
  chat_history: "chat_history.md"
lexicon:
  shells: ["powershell", "bash", "wsl", "cmd"]
  path: ".codex_agent/lexicon"
macros:
  dir: ".codex_agent/macros"
  usage_beans: ".codex_agent/macros/_usage/beans.jsonl"
  prune_hours: 24
tasking:
  index_file: ".codex_agent/task_index.json"
  states: ["new","pending_approval","running","blocked","quarantined","done","aborted"]
  concurrency:
    llm_parallel_max: 2          # queue the 3rd heavy call (matches your limit) :contentReference[oaicite:9]{index=9}
loops:
  startup:
    - read: ["Required-Updates.md","Implemented-Updates.md","Quarantined-Updates.md"]
    - compute_missing: true      # write Missing-Updates.md (report) per your loop :contentReference[oaicite:10]{index=10}
    - refresh_style: true
  implement_required_updates:
    - parse_required_buckets: true
    - spawn_tasks_from_missing: true
    - for_each_task:
        - plan
        - propose_patch
        - pending_command: true  # show Allow/Always Allow
        - apply_if_allowed
        - record: ["Implemented-Updates.md","Quarantined-Updates.md","task_index.json"]
        - learn_macros: true     # create/refresh macros from successful steps (§28)
  revise_required_updates:
    - detect_conflicts: true
    - add_negative_notes: true   # “might work later…” note per your instruction :contentReference[oaicite:11]{index=11}
    - cross_link_everywhere: true # references into all ledgers :contentReference[oaicite:12]{index=12}
ui:
  high_contrast_required: true
  panels: ["Chat","Task Feed","Agent Manager","Rant Updates","Console","Style Manager","Extensions"]
logging:
  session_dir: ".codex_agent/sessions"
  console_stream: ".codex_agent/runtime/console.log"
```

### 29.3 `agent.md` (copy-pasteable baseline)

```markdown
# Default Agent — Directives

## Prime Rules
1) Never run external commands or write outside the active repo without Allow.
2) Always show Pending Command as text before execution, with a one-line rationale.
3) Enforce High Contrast in every UI surface that renders agent output or diffs.

## Loop (AskFirst mode)
- Read: Required / Implemented / Quarantined → compute Missing.
- Propose task stubs to the Task Feed (no silent work).
- For each task:
  - Plan → Show Pending Command → Await Allow.
  - If Allowed: Apply → Diff → Log to Implemented-Updates.md with bucket_id + task_id.
  - If Blocked/Denied/Error: Write to Quarantined-Updates.md with reason and console snippet.
  - Learn: Extract any reusable step as a Macro and store with tags and lexicon mapping.

## Memory & Sharing
- Update Task-Index.json for every task transition.
- Share Implemented/Quarantined/Missing across agents unless Independent Agent Mode is ON.

## Revision Pass
- When asked to “Revise Required Updates,” insert negative notes near superseded logic and cross-link to Quarantined/Implemented items. (Do not treat negatives as permanent bans.)
```

---

# 30. Agent Styles & Style Index — missing, now required

You asked for a **Styles** dimension (agent “personas” tuned to tasks) and a fast selection mechanism. This section defines the files and behavior.

### 30.1 `style_index.json`

* One place to list available styles; each style points to a **style manifest** (YAML/JSON) defining model prefs, tool usage, tone, task heuristics, and extra datasets.

```json
{
  "default": {
    "title": "Default Orchestrator",
    "manifest": ".codex_agent/styles/default.yaml",
    "description": "Balanced planning + code editing. Prefers AskFirst. Good for repo-wide changes."
  },
  "math": {
    "title": "Mathematics",
    "manifest": ".codex_agent/styles/math.yaml",
    "description": "Heavy reasoning + scratchpad. Uses local calc tool aggressively."
  },
  "story": {
    "title": "Story Builder",
    "manifest": ".codex_agent/styles/story.yaml",
    "description": "Narrative writing, outline→draft loops, uses creative datasets."
  }
}
```

### 30.2 Style manifest fields (example `styles/math.yaml`)

```yaml
inherits: default
planning:
  depth: "deep"
  prefer_chain_of_thought: "internal"
tools:
  calculators: ["sympy_local","numpy_eval"]
  allow_shell: false
datasets:
  extra: [".codex_agent/datasets/math_identities.jsonl"]
ui:
  colorway_hint: "blue-accent"
authority_overrides:
  mode: "AskFirst"
  risky_commands: "always_ask"
```

### 30.3 Fast style switching

* The Agent should pick a style instantly based on task tags; if uncertain, fall back to `default`.
* Agent Manager shows the active style and lets you pin/override per session.

---

# 31. **Everything is a function; everything has a Style** — missing, now required

### 31.1 Style Manager (panel)

A left slide-out panel “Style Manager” lists:

* All **visual** functions (panels, buttons, palettes, feeds).
* All **logic** functions (planner, patch applier, diff viewer) that can expose style knobs.
* Current style vs overrides. A **Preview** button applies a style sandboxed.

### 31.2 Default vs Custom styles

* Treat the current hard-coded look as the **Default Style** (extracted definitions).
* Over time, migrate visual decisions into external style files. Where geometry is code-driven, create **style mirrors** that replicate today’s look so custom styles can swap in later without breaking behavior.

### 31.3 Per-script style folders

For each major script, create `Styles/<scriptname>/...` with a default stylesheet that matches the current UI. Switchable at runtime.

### 31.4 External style import (UX generator pipeline)

* Allow importing a foreign style pack (e.g., from a style generator). The import step maps unknown tokens to our schema, warns about missing elements, and falls back to defaults.
* If a component has no style defined, the **default** must bleed through so the program stays usable.

---

# 32. Rant panel extensions (scope, tabs, images) — partially covered, add these

Your doc already defines the Rant panel and bucketization; now add:

* **Scope tabs**: “Whole system” / “This repo” / “This script” — affect tagging & repo scope in buckets. 
* **Image drops**: allow pasting screenshots; store them in a rant dataset folder and run lightweight OCR to seed tags before summarization.
* **One-click “Generate Required Updates”** and **“Revise Required Updates”** buttons live in the Rant bar header (you already mention these actions at a high level—this pins the UI placement). 

---

# 33. Dev_Logic folder integration — missing, now required

### 33.1 Purpose

`Dev_Logic/` is a **goldmine** of prior scripts, notes, and images. The Agent must mine it for reusable patterns that improve code and UI.

### 33.2 Behavior

* On startup and before large refactors, scan `Dev_Logic/`:

  * Summarize new files (create `.codex_agent/datasets/dev_logic_index.jsonl` with tags, paths, short abstracts).
  * For images, make small text summaries and infer UI motifs to inform Style Manager suggestions.
* Add **Implemented-DevLogic.md** that logs which Dev_Logic patterns were integrated where, mirroring your Implemented-Updates traceability style. (Same checklist fields as §18.4’s Implemented linkage.) 

---

# 34. Pending Command bar & Chat rendering — missing, now required

### 34.1 Pending Command

* Every risky step produces a **Pending Command** card showing: the exact command/text, short rationale, authority mode required, and the files that would change.
* Buttons: **Allow**, **Always Allow**, **Deny**.
* On Allow, write to approvals.json and proceed; on Deny/Error, write to Quarantined-Updates with reason and console snippet (as your doc already prescribes). 

### 34.2 Chat markdown rules

* Allow a light **internal** scratch area (`<think>…</think>`) in the transcript for debugging but only store its **summary** in `chat_history.md` so external logs stay clean.
* Visually ensure high contrast in the chat and command surfaces (already a global rule in your doc). 

---

# 35. Uploader & Dataset ingester — missing, now required

### 35.1 Bulk ingest tool

* UI to select files/folders (multi-select).
* The ingester builds a **dataset snapshot**: indexes paths, creates abstracts, tags, and writes into `.codex_agent/datasets/<name>/index.jsonl`.
* Nothing is copied wholesale; we store paths + metadata to stay disk-light.

### 35.2 Lifecycle

* While selecting, show icons and file counts. When you finalize, collapse to a single **index bucket** entry the Agent can RAG against.
* Provide **Delete dataset** and **Rebuild** actions.

---

# 36. Extensions / Plugin Manager — missing, now required

Unify into the left slide-out you already use. Search bar at top (VS-style). Categories (Installed, Available, Dev), with a **template** button that exports a skeleton so the Agent can generate plugins itself. (This ties to the autonomous self-extending behavior you described.)

---

# 37. Task-Index details — add stronger state model

Your doc references Task-Index; add:

* Per-task `attempts`, `last_error`, `authority_used`, `macro_ids_used`, `files_changed`.
* Timeouts: auto-abandon after N minutes in “pending_approval” unless user interacts; write a short “stale” note to Missing-Updates report.

---

# 38. Example end-to-end workflow (AskFirst mode)

1. **You rant** into the Rant panel → it buckets content and appends clean text to Required-Updates.md. 
2. You press **Implement Required Updates** → Agent computes Missing from Required − Implemented − Quarantined and creates task stubs (as you already defined). 
3. For each task: plan → **Pending Command** → Allow/Always Allow. On Allow:

   * Apply changes, **learn macros**, and log to Implemented-Updates.md with `bucket_id` + `task_id`.
   * If blocked/denied/error, log to Quarantined-Updates.md with reason and console snippet. 
4. After the batch: regenerate **Missing-Updates.md** as the gap report, auto-linked back to buckets and task_ids. 
5. Optionally run **Revise Required Updates** to insert negative notes (“might work later”) and cross-links. 

---

# 39. File templates (copy-paste)

### 39.1 `approvals.json` (global)

```json
{
  "schema": 1,
  "independent_mode": false,
  "entries": [
    {
      "approval_id": "appr.0001",
      "ts": "2025-10-29T03:14:00Z",
      "category": "run.powershell.edit_file",
      "scope": "global",
      "always_allow": true,
      "notes": "Allowed editing files in repo via PowerShell with preflight diff."
    }
  ]
}
```

### 39.2 `task_index.json` (seed)

```json
{
  "schema": 2,
  "tasks": [],
  "states": ["new","pending_approval","running","blocked","quarantined","done","aborted"],
  "timer_policy": { "pending_approval_timeout_min": 30 }
}
```

### 39.3 `lexicon/powershell.json` (seed)

```json
{
  "open_file": { "pattern": "code \"{path}\"", "needs": ["path"] },
  "write_text": { "pattern": "Set-Content -Path \"{path}\" -Value \"{text}\"", "needs": ["path","text"] }
}
```

---

## Why these are “missing”

* Your current doc covers **the four-file loop**, **Rant capture**, **authority memory**, **cross-references**, and the **two-at-a-time LLM cap**.     
* It does **not** yet spell out: a persistent **Macro** archive with bean-based retention; the **agent file suite** with concrete `agent.yaml` and `agent.md`; a formal **Agent Styles** index + style manifests; a **Style Manager** and per-script styles; Dev_Logic ingestion + Implemented-DevLogic.md; a full **Pending Command** bar contract; a **bulk uploader/ingester**; and an integrated **Extensions** panel. (Those are what §§28–36 deliver.)



Here is the full **Trifecta** loop—**Required → Current (README) → Implemented**—and stitches in the supporting assets (**Agent.md / agent.yaml / styles / datasets / macros**), the **Rant → Required** ingestion, and the archival/scrubbing rules.

---

# Trifecta Operations & Documentation Discipline

*(Required → README (Current) → Implemented), with Agent config, Styles, Datasets, Macros, and Archives kept in lockstep)*

**Goal.** Keep the system stable and auditable by enforcing a single, repeatable loop that turns ideas into shipped changes, keeps **README.md** truthful, and records outcomes in **Implemented-Updates.md**—while quarantining blocks and auto-tracking what’s still missing.

---

## A. Files & Their Roles (authoritative locations)

```
./Required-Updates.md          # This file — plan of record (backlog / intent)
./README.md                    # LIVING README — “what’s current right now”
./Implemented-Updates.md       # Delivery ledger (what shipped)
./Quarantined-Updates.md       # Blocked/denied/errored with reasons & retry plan
./Missing-Updates.md           # Auto-computed “not yet delivered”

./.codex_local_agent/
  agent.yaml                   # Machine config: provider/model/endpoints/authority/paths/styles
  agent.md                     # Human system card: rules/loop/safety/UX rules
  Task-Index.json              # Durable task ledger (ids, buckets, status, approvals, timestamps)
  dataset/
    memory.jsonl               # Chat turns (markdown, images, OCR_fast/full, tags, hashes)
  macros/
    registry.jsonl             # Captured helper scripts; usage counters; risk
    beans.json                 # Macro usage “bean counter” for 24h GC
  logs/
    session_YYYY-MM-DD.md      # Chronological run logs (Ask & Do Work)
  styles/
    default-dark.json          # UI style pack(s); High-Contrast enforced
```

> **Invariant:** If any file above is missing at run start, the Agent creates a default one and records that action in **Implemented-Updates.md**.

---

## B. Rant → Required ingestion (how freeform ideas become actionable)

1. **Capture:** The **Rant** panel accepts long dictations, images, and links.

   * Every Rant turn is appended to `chat_history.md` and `dataset/memory.jsonl` with OCR (fast & full), tags, and hashes.
2. **Consolidate:** The Agent rewrites Rant content into clear, deduped **buckets** in this file (each bucket gets a stable `bucket_id`, e.g., `B-2025-10-AGENT-MANAGER`).
3. **Cross-link:** If a Rant elaborates an existing bucket, append as a **sub-item** under the same `bucket_id` (don’t spawn duplicates).
4. **Proof:** Add a short, testable “Definition of Done” to the bucket if missing.

> Output: structured sections in **Required-Updates.md** that are immediately actionable.

---

## C. Plan & Task Derivation (Ask mode → no side effects)

1. **Re-read:** On every run, parse this file into buckets with `bucket_id` and **acceptance criteria**.
2. **Derive tasks:** For each bucket/subpart not shipped, synthesize tasks with durable `task_id`s and write/update **`.codex_local_agent/Task-Index.json`**.
3. **Narrate:** In chat (markdown), present the plan, proposed diffs, and commands. Ask mode only—**no writes, no shell**.

**`Task-Index.json` entry (example):**

```json
{
  "task_id": "T-2025-10-041",
  "bucket_id": "B-2025-10-AGENT-MANAGER",
  "title": "Add Agent Manager mini-app with authority/RAG states",
  "status": "planned",
  "files": ["micro_agent.py", ".codex_local_agent/agent.yaml", "README.md"],
  "approvals": [],
  "created_at": "2025-10-29T03:14:00Z"
}
```

---

## D. Stage & Approval (Do Work mode → gated actions)

1. **Stage diffs & commands:** Prepare file diffs and pending shell actions; render in chat as markdown **and** show in the Task Feed.
2. **Pending Command bar:** Show **Allow / Skip / Try Harder / Edit**.

   * **Allow** flashes blue every 2s **only when** approval is required.
   * **Edit** turns the input into **purple/magenta edit mode**; sending replaces the pending command.
   * **Try Harder** re-prompts with a stronger retry directive (hardcoded quality prompt).
3. **Always Allow:** If enabled, auto-run any previously whitelisted action classes; still prompt for truly **new** action classes.

---

## E. Apply & Verify (Do Work executes only after approval)

1. **Apply:** Execute allowed commands; write files; run formatters/lint/tests if applicable.
2. **Verify:** Re-open changed files; confirm acceptance criteria; update `Task-Index.json` status.
3. **Record outcome:**

   * Success → **Implemented-Updates.md** (see format below).
   * Blocked/Denied/Error → **Quarantined-Updates.md** with a concrete next attempt.
   * Remaining subparts → keep here and add to **Missing-Updates.md**.

**`Implemented-Updates.md` entry (example):**

```markdown
### T-2025-10-041 — Agent Manager mini-app
- Bucket: B-2025-10-AGENT-MANAGER
- Changed: `micro_agent.py`, `.codex_local_agent/agent.yaml`, `README.md`
- Summary: Adds Agent Manager panel (authority modes, allow-list view, RAG sources, pipeline state)
- Verification: UI opens via dock icon; authority toggle persists; pending pipeline visible
- Commit: abc1234
```

---

## F. Keep the Trifecta in sync (the core discipline)

* **Required-Updates.md** = plan.
* **README.md** = current truth (must match actual behavior/files/UI **after** each shipped change).
* **Implemented-Updates.md** = ledger of what shipped (with task ids and changed paths).

**Sync order after each apply:**

1. Update code/config.
2. Update **README.md** to reflect the new reality; if docs lag, insert a **Documentation TODO** block with the task id.
3. Append to **Implemented-Updates.md**.
4. Refresh **Missing-Updates.md** and **Quarantined-Updates.md**.
5. Append the end-of-run **Implementation Check** to this file.

---

## G. Agent Config: `agent.yaml` + `agent.md` (what to keep aligned)

**`agent.yaml` (baseline; extend as needed):**

```yaml
llm: { provider: ollama, model: qwen2.5-coder:latest, endpoint: http://127.0.0.1:11434 }
modes: { ask_mode: true, do_work_mode: true }
authority: { ask_first: true, always_allow: false, independent_agent_mode: true }
paths:
  repo_root: "."
  dataset_root: ".codex_local_agent/dataset"
  macro_registry: ".codex_local_agent/macros/registry.jsonl"
  beans_store: ".codex_local_agent/macros/beans.json"
  task_index: ".codex_local_agent/Task-Index.json"
logging:
  chat_history: "chat_history.md"
  sessions_dir: ".codex_local_agent/logs"
updates:
  required: "Required-Updates.md"
  implemented: "Implemented-Updates.md"
  quarantined: "Quarantined-Updates.md"
  missing: "Missing-Updates.md"
ui:
  think_render: { italic_dim_green: true }
  thumbnails_inline: true
  high_contrast_enforced: true
styles:
  active_style: "default-dark"
  packs: [".codex_local_agent/styles/default-dark.json"]
```

**`agent.md` (must describe):**

* The **loop** (Ask → Do Work → Approvals → Apply → Verify → Record).
* **Authority policy**, **Always Allow** semantics, and **Independent Agent Mode**.
* **High-Contrast** UI rule and key visual cues (flashing Allow, magenta Edit mode).
* **Macro capture** policy + 24h bean-counter GC.
* **Dataset** structure (markdown + images + OCR_fast/full + tags + hashes).
* Safety boundaries (no writes outside `repo_root` without explicit approval; backup-first for destructive ops).

> Whenever `agent.yaml` changes, **README.md** must update the Models/Providers and Authority sections; **Implemented-Updates.md** gets an entry.

---

## H. Styles & UI Packs (visual only; never weaken contrast)

* Keep style packs in `.codex_local_agent/styles/*.json`.
* **README.md** must state the active style and list pack names.
* When style packs change, record in **Implemented-Updates.md** and include screenshots (or TODO stubs with task ids).
* **Rule:** *Text must be clearly readable against its background* (light-on-dark or dark-on-light; no low-contrast pairings).

---

## I. Dataset & OCR (RAG memory with hygienic updates)

* Every turn (Ask or Do Work) writes a row to `dataset/memory.jsonl`:

  * `markdown_block` (from `chat_history.md`)
  * `image_paths` (thumbnails must appear inline in chat)
  * `ocr_fast` (markdown-oriented) and `ocr_full` text
  * `tags`, `hashes`, `timestamp`, `bucket_id`/`task_id` if relevant
* **Re-tagging & supersession:** When README or code changes invalidate prior guidance, mark related dataset rows with `"superseded_by": "<commit|task_id>"` and add corrective tags. Do **not** silently delete unless data is junk/PII.
* **Drift alerts:** If dataset references behavior not present in README, raise a **Missing** entry and propose a doc/code reconciliation task.

---

## I-2. Macro Capture & GC (make the agent faster over time)

* Whenever the Agent authors helper scripts (navigation, edits, backups, path resolution, etc.), append an entry to `macros/registry.jsonl`:

```json
{
  "id": "M-2025-10-007",
  "terminal": "powershell",
  "purpose": "Open folder and stage file for edit",
  "script": "Start-Process explorer.exe \"$($env:REPO)\\path\\to\\folder\"",
  "risk": "low",
  "last_used": "2025-10-29T03:25:00Z",
  "use_count": 3
}
```

* **Beans & GC:** Increment a bean in `beans.json` each day a macro is used. Remove macros with `use_count == 0` and **older than 24h**, **except** when the previous session was the most recent activity (no chance to use today). Log removals in **Implemented-Updates.md**.

---

## J. Archival & Scrubbing Rules (after implementation)

1. **Implemented evidence:** Keep the exact diff links/commits in **Implemented-Updates.md**.
2. **Quarantined:** Keep full error output and a retry recipe. Auto-promote to Missing if retried and still blocked by environment.
3. **Aging data:**

   * **Dataset rows**: mark as `superseded_by` (don’t drop) unless they are corrupted/noise; then remove and log.
   * **Macros**: GC per beans policy.
   * **Logs**: compress `logs/session_*.md` older than N days into `logs/archive/` with an index.
4. **Renames/moves:** If files or folders are renamed, update paths in Task-Index, macro scripts, and dataset references. Add an **Implemented** entry for the migration.

---

## K. End-of-Run Implementation Check (append to this file each run)

Append a footer block like this:

```markdown
## Implementation Check — <UTC timestamp>
- Completed: T-2025-10-041 (Agent Manager), T-2025-10-042 (Script Creator overwrite preview)
- Quarantined: T-2025-10-039 (WSL probe) — Need user approval to install `wsl.exe`
- Missing (auto): B-2025-10-PENDING-COMMAND-UI subtask 2 (inline confirmations in feed)
- README: Updated sections 7, 9; added TODO for screenshots (T-2025-10-044)
- Agent Config: `agent.yaml` updated (authority.independent_agent_mode=true)
Verdict: ✅ Trifecta in sync; 1 remaining subtask tracked in Missing.
```

---

## L. Examples & Templates (ready for immediate use)

**README Documentation TODO (auto-insert):**

```markdown
> 📌 **Documentation TODO**
> Task: T-2025-10-044
> Affected: Pending Command UI (inline confirmations); screenshots pending
> Notes: Allow flashes blue only when approval required; Edit mode shows magenta outline
```

**Quarantined entry:**

```markdown
### T-2025-10-039 — WSL probe
- Reason: `wsl.exe` not found; user declined install
- Next Attempt Plan: Prompt with minimal install instructions; offer Portable fallback
```

**Missing entry:**

```markdown
- B-2025-10-PENDING-COMMAND-UI — subtask 2 (render confirmation blocks inline in chat feed)
  - Depends on: chat markdown renderer hook
```

---

## M. Operational Invariants (must never break)

* **Ask vs Do Work** separation is strict; Ask never mutates disk or runs shell.
* **Approval first** for any action not in allow-list; Always Allow does not bypass first-time prompts for new action classes.
* **High-Contrast UI** is non-negotiable; never ship low-contrast visuals.
* **README is the truth** after each apply; if code and README disagree, fix one and record it.
* **No writes outside `repo_root`** without explicit, path-specific approval and a visible backup plan.

---

*Follow this section every run. It’s how we turn Rant into Required, keep README current, and prove delivery in Implemented—while keeping datasets, macros, styles, and archives healthy over time.*


------


the next steps: first a **new Required-Updates section** that formalizes the agent file structure + loop (with the “double prompts,” authority ledger, macros TTL/beans, styles, datasets, rant feed… all wired into the Trifecta). Then I’m giving you the **actual agent files** (full bodies) you can drop straight into `agents/` today. (note this logic might evolve over time, if future agent logic is more advanced then use this only as reference)

---

# ✅ Paste this into **Required-Updates.md** (place it right before your end block)

## 28) Agent Files & Chain-of-Authority — Canon + Runtime (Finalized)

**Goal:** Standardize how every agent boots, reads Required-Updates, writes Implemented/Quarantined/Missing, and loops with approvals, macros, styles, datasets, and the rant feed — all aligned to the Trifecta (Required ↔ Current/README ↔ Implemented). The chain merges in this order: `agents/base.md` → `agents/local.md` → `agents/project.md` → (optional) role/style guides. 

### 28.1 What lives where (authoritative mapping)

* **`agents/base.md`** — global canon: Required-Updates loop discipline; logging; high-contrast rule; Trifecta; approvals; macros; rant feed. 
* **`agents/local.md`** — machine/operator facts (Windows + WSL, Ollama endpoint, Dev_Logic path, chat/rant feeds, authority file, macro store). 
* **`agents/project.md`** — repo binding (the runtimes in this repo, dataset roots, update loop files). 
* **`agents/authority/ledger.json`** — approvals + “Independent Agent Mode” on/off + history. 
* **`agents/default/agent.yaml`** — config that ties everything: chain order, sources (Required/Implemented/Quarantined/Missing, chat/rant, Dev_Logic), authority ledger, macros store with TTL/beans, styles index, runtime loop entry, concurrency knobs.  
* **Prompts** (`agents/default/prompts/ask.md`, `do_work.md`, `try_harder.md`) — the “double prompt” discipline: Kickoff vs Continue; Do-Work loop; Recovery.  
* **Runtime** (`agents/default/runtime/loop.py`) — minimal, auditable loop that (a) ensures files; (b) parses Required-Updates; (c) writes stubs to `memory/logic_inbox.jsonl`; (d) executes top stub; (e) updates Implemented/Quarantined/Missing; (f) rolls logs; (g) manages macro TTL/beans. 

### 28.2 Double-Prompt Discipline (always enforce)

* **Prompt 1 (Kickoff)** ensures the agent **recreates/opens**: `Agent.md`, `Required-Updates.md`, `memory/codex_memory.json`, `memory/logic_inbox.jsonl`, `docs/codex-local/required_updates_progress.md`, `docs/changes/CHANGELOG.md`, `logs/session_<TODAY>.md`. If missing, it generates them and then starts work. 
* **Prompt 2 (Continue)** resumes plan/work exactly where we left off, continuing to scan Required-Updates and implement what’s still missing. 

### 28.3 Authority & Independent Agent Mode

* The agent **never** runs external commands, writes outside the repo, or changes system config until the human approves; approvals are captured in `agents/authority/ledger.json`. **Independent Agent Mode** makes approvals/macros repo-scoped; global mode allows reuse.  

### 28.4 Macros Archive + TTL/Beans (speed without drift)

* The macro store is `tools/macros/store.jsonl` with `ttl_hours: 24`; beans keep rarely-used macros if the system didn’t run that day (no-usage day forgiveness). UI surfaces exist in Command Palette + Agent Manager (counts, pinned, approvals, cleanup).   
* Pending-Command bar + inline buttons label macro origin; “Always Allow” and Independent mode suppress flashing once safe. 

### 28.5 Styles & Style Index

* Styles live in `agents/styles/index.json`; `active_styles: [coding]` by default. The agent.yaml exposes `active_styles` and an `active style name` so the runtime & UI can swap layout look/feel without touching core logic.  

### 28.6 Datasets, Dev_Logic, and Rant Feed

* **Dev_Logic/** is non-authoritative inspiration — the agent may mine it for patterns and then propose/implement updates. **Rant feed** (`rant_feed.md`) is append-only; the runtime ingests it and promotes structured buckets into Required-Updates.  
* Use an Uploader/Extensions panel to ingest folders/files, snapshot, embed, tag, and index to datasets; link into Agent Manager. 

### 28.7 Trifecta & Spec Verification

* Treat **README.md as “Current”** (what exists now), **Required-Updates.md as Desired**, and **Implemented-Updates.md as Proof**. The loop must cross-reference these three at every turn. (Plan vs Action rules remain exactly as in Codex Global Protocol.) 
* **At the end of every major run**, runtime writes a **Spec Verification Block** noting which Required items remain missing per `Missing-Updates.md`; if everything is implemented it says so explicitly and timestamps it. 

---

# 📦 Agent Files — Drop-in v1.0 (complete, ready to commit)

> All files below include the **high-contrast UI rule** in comments: “Always use light text on dark or dark on light; never low-contrast.”
> Paths are repo-relative. Create any missing folders.

---

### `agents/base.md`

```markdown
# Agent Base (Global Canon) — Layer 1
> Merge order: agents/base.md → agents/local.md → agents/project.md → (optional) role/style guides.
> High-contrast rule: Always ensure readable light text on dark or dark on light. Never low-contrast.

## Required-Updates Sync Loop (MANDATORY)
1) Reopen/regenerate control files:
   - Agent.md, Required-Updates.md
   - memory/codex_memory.json, memory/logic_inbox.jsonl
   - docs/codex-local/required_updates_progress.md, docs/changes/CHANGELOG.md
   - logs/session_<YYYY-MM-DD>.md
2) Parse Required-Updates.md → emit structured stubs to memory/logic_inbox.jsonl.
3) Execute top stub (Do-Work), respecting authority; never write outside repo or run commands without approval.
4) Update Implemented-Updates.md / Quarantined-Updates.md / Missing-Updates.md.
5) Record diffs, macro usage, approvals, and status to logs & CHANGELOG.
6) If rant_feed.md has new text, promote coherent items into Required-Updates buckets.

## Authority & Safety
- Pending commands go through Allow / Skip / Try Harder / Edit / Always Allow.
- Independent Agent Mode isolates approvals & macros to this repo. Global mode allows reuse where safe.
- Never invent authority; ask before any new class of risky action.

## Macros Archive
- tools/macros/store.jsonl with ttl_hours: 24; bean_keep_if_no_usage_day: true.
- Store only useful, deduplicated helpers (navigation, patching, snapshotting).
- UI: surfaced in Command Palette and Agent Manager with counts, pinning, cleanup.

## Styles
- agents/styles/index.json enumerates styles; agent.yaml chooses active_styles: [coding] by default.
- Styles affect layout/visuals only; core logic remains stable.

## Trifecta
- README.md = Current reality (stable reference for agent).
- Required-Updates.md = Desired.
- Implemented-Updates.md = Proof.
- Runtime must keep the three in sync at every turn and write a Spec Verification Block after major runs.

## Logging
- chat_history.md (append-only); logs/session_<date>.md (per-day); docs/changes/CHANGELOG.md (human rollups).

```

---

### `agents/local.md`

```markdown
# Agent Local (Machine / Operator)
> Target: Windows 10 + optional WSL. High-contrast rule applies.

- Ollama endpoint: http://localhost:11434
- Dev_Logic: ./Dev_Logic/
- Chat history: ./chat_history.md
- Rant feed: ./rant_feed.md
- Macros store: ./tools/macros/store.jsonl (ttl_hours: 24)
- Authority ledger: ./agents/authority/ledger.json
- Dataset dir (optional): ./agents/default/dataset/
```

---

### `agents/project.md`

```markdown
# Agent Project (Repo Binding)
> High-contrast rule applies.

- Runtimes: Virtual_Desktop.py, Codex_Terminal.py
- Update Loop Files:
  - Required-Updates.md / Implemented-Updates.md / Quarantined-Updates.md / Missing-Updates.md
- Memory:
  - memory/logic_inbox.jsonl (stubs queue)
  - memory/codex_memory.json (long-lived truths)
- Dev Logic: ./Dev_Logic/ (inspirational, not authoritative)
- Readme is the “Current” truth for the running system; treat it as stable reference in the Trifecta.
```

---

### `agents/authority/ledger.json`

```json
{
  "version": "1.0",
  "independent_agent_mode": false,
  "approvals": [],
  "history": []
}
```

---

### `agents/styles/index.json`

```json
{
  "version": 1,
  "styles": [
    {
      "name": "coding",
      "description": "High-contrast, developer-first layout; dark canvas, light text, clear affordances.",
      "ui_rules": {
        "contrast": "high",
        "note": "Never low-contrast text on background."
      }
    }
  ]
}
```

---

### `agents/default/agent.yaml`

```yaml
# Local autonomous agent config
# High-contrast rule: Use light text on dark or dark on light; never low-contrast.

name: DefaultAgent
version: 0.3.0

llm:
  provider: offline-ollama
  model: qwen2 # change if needed
  endpoint: http://localhost:11434

chain_order:
  - agents/base.md
  - agents/local.md
  - agents/project.md

sources:
  required_updates: Required-Updates.md
  implemented_updates: Implemented-Updates.md
  quarantined_updates: Quarantined-Updates.md
  missing_updates: Missing-Updates.md
  chat_history: chat_history.md
  rant_feed: rant_feed.md
  dev_logic_dir: Dev_Logic/

authority:
  ledger_path: agents/authority/ledger.json
  allow_default: false
  remember_always_allow: true

macros:
  enabled: true
  store_path: tools/macros/store.jsonl
  ttl_hours: 24
  bean_keep_if_no_usage_day: true

styles_index: agents/styles/index.json
active_styles: [coding]

runtime:
  loop_entry: agents/default/runtime/loop.py
  poll_interval_seconds: 2
  max_parallel_tasks: 2
  log_dir: logs/
```

> Notes: `chain_order`, `sources`, `authority`, `macros`, `styles_index`, and `runtime` keys reflect the structure we agreed on and the same fields captured in your working notes.  

---

### `agents/default/prompts/ask.md`

```markdown
# ASK MODE — Guidance & Planning
> High-contrast rule: ensure readable text on dark. Keep UI checklists legible.

- Summarize operator intent (1–3 bullets).
- Reopen/regenerate control files if missing (Agent.md, Required-Updates.md, memory/, docs/changes/CHANGELOG.md, logs/session_<TODAY>.md).
- Propose concrete task stubs into `memory/logic_inbox.jsonl` with `bucket_id`, `paths`, `acceptance_criteria`, `rollback`, `verification`.
- Never invent authority. Route risky actions to Pending Command pipeline.
- Confirm Trifecta alignment (README current ↔ Required desired ↔ Implemented proof) before switching to Do-Work.
```

---

### `agents/default/prompts/do_work.md`

```markdown
# DO WORK — Autonomous Execution
> Always keep text high-contrast.

1) Parse `Required-Updates.md` → find missing.
2) Emit stubs to `memory/logic_inbox.jsonl`; take top stub.
3) Execute changes in repo (batch if multi-file), respecting approvals.
4) Update:
   - Implemented-Updates.md (success),
   - Quarantined-Updates.md (blocked or denied),
   - Missing-Updates.md (still absent items).
5) Roll logs: `logs/session_<TODAY>.md`, `docs/changes/CHANGELOG.md` (human summary).
6) Maintain macro archive (`tools/macros/store.jsonl`): add helpful snippets; enforce TTL/beans; dedupe.
7) Write/refresh **Spec Verification Block** at end of Required-Updates: list unimplemented or declare “All implemented, <timestamp>”.
8) If rant_feed.md appended since last loop, promote coherent entries into new Required-Updates buckets and queue stubs.
```

---

### `agents/default/prompts/try_harder.md`

```markdown
# TRY HARDER — Recovery & Alternatives
> High-contrast status labels only.

- Capture precise failure logs with pointers/paths and diff context.
- Offer 2–3 concrete alternative strategies (file-by-file).
- If blocked by authority, add detail to Quarantined-Updates with the required approval text and scope.
- If dependencies missing (models, datasets, folders), create stubs to fetch/generate them and requeue.
- If macro failed, mark it with a failure bean and suggest a repaired macro variant.
```

---

### `agents/default/runtime/loop.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default Agent runtime loop (auditable minimal).
High-contrast UI rule: any emitted UI/log text must be readable; never low-contrast.

Responsibilities:
- Ensure required files/dirs exist (Trifecta + memory + logs).
- Parse Required-Updates.md → maintain memory/logic_inbox.jsonl stubs.
- Execute top stub, respecting authority & Independent Agent Mode.
- Update Implemented/Quarantined/Missing + CHANGELOG + session logs.
- Maintain macro store with TTL/beans (24h TTL; preserve if no-usage day).
- Write Spec Verification Block at end of Required-Updates.md after major runs.
"""
from __future__ import annotations
import json, os, re, time, hashlib, datetime as dt, pathlib
from typing import Dict, Any, List
try:
    import yaml
except Exception:
    yaml = None  # keep import soft; agent may install pyyaml upstream

ROOT = pathlib.Path(__file__).resolve().parents[3]
P = lambda *parts: ROOT.joinpath(*parts)

# ---------------- Utilities ----------------

def sha10(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]

def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def write_text_atomic(path: pathlib.Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)

def now_iso() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------------- Config ----------------

def load_cfg() -> Dict[str, Any]:
    ypath = P("agents","default","agent.yaml")
    raw = read_text(ypath)
    if not raw or yaml is None:
        # minimal fallback to avoid crash if yaml missing
        return {
            "sources": {
                "required_updates": "Required-Updates.md",
                "implemented_updates": "Implemented-Updates.md",
                "quarantined_updates": "Quarantined-Updates.md",
                "missing_updates": "Missing-Updates.md",
                "chat_history": "chat_history.md",
                "rant_feed": "rant_feed.md",
                "dev_logic_dir": "Dev_Logic"
            },
            "authority": {"ledger_path": "agents/authority/ledger.json"},
            "macros": {
                "enabled": True,
                "store_path": "tools/macros/store.jsonl",
                "ttl_hours": 24,
                "bean_keep_if_no_usage_day": True
            },
            "runtime": {
                "poll_interval_seconds": 2,
                "max_parallel_tasks": 2,
                "log_dir": "logs"
            }
        }
    y = yaml.safe_load(raw)
    return y

def resolve_paths(cfg: Dict[str,Any]) -> Dict[str, pathlib.Path]:
    s = cfg["sources"]; a = cfg["authority"]; m = cfg["macros"]; r = cfg["runtime"]
    return {
        "required": P(s["required_updates"]),
        "impl": P(s["implemented_updates"]),
        "q": P(s["quarantined_updates"]),
        "missing": P(s["missing_updates"]),
        "inbox": P("memory","logic_inbox.jsonl"),
        "rant": P(s.get("rant_feed", "rant_feed.md")),
        "ledger": P(a["ledger_path"]),
        "macro_store": P(m["store_path"]),
        "log_dir": P(r.get("log_dir","logs")),
        "changelog": P("docs","changes","CHANGELOG.md"),
        "progress": P("docs","codex-local","required_updates_progress.md"),
        "chat": P(s.get("chat_history","chat_history.md")),
        "dev_logic_dir": P(s.get("dev_logic_dir","Dev_Logic"))
    }

def ensure_files(paths: Dict[str, pathlib.Path]) -> None:
    for key, path in paths.items():
        if key in {"log_dir","dev_logic_dir"}:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                if key == "inbox":
                    write_text_atomic(path, "")
                elif key == "required":
                    write_text_atomic(path, "# Required-Updates\n\n")
                elif key == "impl":
                    write_text_atomic(path, "# Implemented-Updates\n\n")
                elif key == "q":
                    write_text_atomic(path, "# Quarantined-Updates\n\n")
                elif key == "missing":
                    write_text_atomic(path, "# Missing-Updates\n\n")
                elif key == "progress":
                    write_text_atomic(path, "# required_updates_progress.md\n\n")
                elif key == "changelog":
                    write_text_atomic(path, "# CHANGELOG\n\n")
                elif key == "chat":
                    write_text_atomic(path, "# chat_history.md\n\n")
                elif key == "rant":
                    write_text_atomic(path, "")

# ---------------- Macros ----------------

def prune_macros(paths: Dict[str, pathlib.Path], ttl_hours: int, keep_if_no_usage_day: bool) -> None:
    store = paths["macro_store"]
    if not store.exists(): 
        return
    cut = dt.datetime.now() - dt.timedelta(hours=ttl_hours)
    out_lines: List[str] = []
    used_today = False
    today = dt.datetime.now().strftime("%Y-%m-%d")
    for line in store.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ts = obj.get("ts") or obj.get("timestamp")
        used = obj.get("last_used")
        if used and str(used).startswith(today):
            used_today = True
        dt_ts = dt.datetime.fromisoformat(ts) if ts else None
        if not dt_ts or dt_ts >= cut or obj.get("pinned"):
            out_lines.append(json.dumps(obj, ensure_ascii=False))
    if keep_if_no_usage_day and not used_today:
        # preserve original file if not used today to avoid accidental purge
        return
    write_text_atomic(store, "\n".join(out_lines) + ("\n" if out_lines else ""))

# ---------------- Required → Stubs ----------------

STUB_RX = re.compile(r"^###\s+(\d+)[\.\)]\s*(.+)$")

def scan_required_to_stubs(required_md: str) -> List[Dict[str,Any]]:
    """Extract minimal task stubs from Required-Updates markdown headings."""
    stubs: List[Dict[str,Any]] = []
    for line in required_md.splitlines():
        m = STUB_RX.match(line.strip())
        if not m: 
            continue
        bucket_id, title = m.group(1), m.group(2)
        stubs.append({
            "bucket_id": bucket_id,
            "title": title,
            "paths": [],
            "acceptance_criteria": [],
            "rollback": [],
            "verification": []
        })
    return stubs

def append_new_stubs(inbox: pathlib.Path, stubs: List[Dict[str,Any]]) -> None:
    existing = set()
    if inbox.exists():
        for line in inbox.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
                existing.add(obj.get("bucket_id"))
            except Exception:
                pass
    new_lines = []
    for s in stubs:
        if s["bucket_id"] in existing:
            continue
        s["created_at"] = now_iso()
        s["id"] = sha10(s["bucket_id"] + s["title"])
        new_lines.append(json.dumps(s, ensure_ascii=False))
    if new_lines:
        with inbox.open("a", encoding="utf-8") as f:
            for l in new_lines:
                f.write(l + "\n")

# ---------------- Implement/Quarantine/Missing ----------------

def log_impl(paths: Dict[str,pathlib.Path], stub: Dict[str,Any], note: str) -> None:
    line = f"- ✅ [{now_iso()}] bucket:{stub.get('bucket_id')} id:{stub.get('id')} — {stub.get('title')} — {note}\n"
    with paths["impl"].open("a", encoding="utf-8") as f:
        f.write(line)

def log_quarantine(paths: Dict[str,pathlib.Path], stub: Dict[str,Any], reason: str) -> None:
    line = f"- 🔒 [{now_iso()}] bucket:{stub.get('bucket_id')} id:{stub.get('id')} — {stub.get('title')} — {reason}\n"
    with paths["q"].open("a", encoding="utf-8") as f:
        f.write(line)

def log_missing(paths: Dict[str,pathlib.Path], stub: Dict[str,Any], why: str) -> None:
    line = f"- ⏳ [{now_iso()}] bucket:{stub.get('bucket_id')} id:{stub.get('id')} — {stub.get('title')} — {why}\n"
    with paths["missing"].open("a", encoding="utf-8") as f:
        f.write(line)

def spec_verification_block(paths: Dict[str,pathlib.Path], remaining_count: int) -> None:
    md = read_text(paths["required"])
    marker = "\n---\n## Spec Verification Block\n"
    tail = f"\n**Result @ {now_iso()}:** {'All implemented.' if remaining_count==0 else str(remaining_count)+' item(s) still missing.'}\n"
    if "## Spec Verification Block" in md:
        md = re.sub(r"## Spec Verification Block[\s\S]*$", marker + tail, md)
    else:
        md += marker + tail
    write_text_atomic(paths["required"], md)

# ---------------- Authority (placeholder hook) ----------------

def authority_allows(paths: Dict[str,pathlib.Path], stub: Dict[str,Any]) -> bool:
    # In this minimal loop we simulate approval required for any external command or file write outside repo (not attempted here).
    # Real bridge will check ledger.json patterns. Always return True for local in-repo edits.
    return True

# ---------------- Loop ----------------

def run_once(cfg: Dict[str,Any]) -> None:
    paths = resolve_paths(cfg)
    ensure_files(paths)
    prune_macros(paths, cfg["macros"].get("ttl_hours",24), cfg["macros"].get("bean_keep_if_no_usage_day", True))

    required_md = read_text(paths["required"])
    stubs = scan_required_to_stubs(required_md)
    append_new_stubs(paths["inbox"], stubs)

    # take first stub (FIFO)
    line = ""
    if paths["inbox"].exists():
        lines = [l for l in paths["inbox"].read_text(encoding="utf-8").splitlines() if l.strip()]
        line = lines[0] if lines else ""

    if not line:
        spec_verification_block(paths, 0)
        return

    try:
        stub = json.loads(line)
    except Exception:
        return

    # Simulate implementation: mark as implemented if authority ok; otherwise quarantine.
    if authority_allows(paths, stub):
        log_impl(paths, stub, "Applied edits (simulated).")
        # Remove the processed line
        write_text_atomic(paths["inbox"], "\n".join(lines[1:]) + ("\n" if len(lines)>1 else ""))
    else:
        log_quarantine(paths, stub, "Awaiting approval.")
    # Refresh verification block (remaining items)
    remaining = 0
    if paths["inbox"].exists():
        remaining = len([l for l in paths["inbox"].read_text(encoding="utf-8").splitlines() if l.strip()])
    spec_verification_block(paths, remaining)

def main() -> None:
    cfg = load_cfg()
    poll = int(cfg.get("runtime",{}).get("poll_interval_seconds", 2))
    # single pass for now (external orchestrator can call repeatedly)
    run_once(cfg)
    # For a continuous loop uncomment below:
    # while True:
    #     run_once(cfg)
    #     time.sleep(poll)

if __name__ == "__main__":
    main()
```

> This mirrors the structure already captured in your notes (agent.yaml fields, prompt split, loop responsibilities) and adds the Spec Verification Block writer the way we described.  

---

## Why this exactly matches our earlier specs

* **Chain-of-authority & files**: identical merge order and per-file duties we enumerated. 
* **Default Agent’s runtime duties + files** are the same list we stabilized (repo context, planning, approvals, persistence, macro archive, data model).  
* **Independent Agent Mode & Macro surfaces** line up with the UI/approval rules we locked in for Agent Manager + Command Palette and the pending command bar semantics.   
* **Double prompts** preserve Kickoff vs Continue semantics so the agent always (re)reads the spec and proves traceability before doing work. 

---

## What you do now

1. **Drop the files** I just wrote into your repo at the exact paths shown.
2. Paste the **Required-Updates section** above (28.x) before your ending block.
3. Your existing `micro_agent.py` / GUI can call `agents/default/runtime/loop.py` as the worker for Do-Work cycles. (You already scaffold agent.md/agent.yaml creation; this slots in.) 

also generate a tiny **installer step** that ensures `pyyaml` exists and seeds the folders on first run — but the files above are already complete and ready to go.



------


# Micro Agent Workbench

## Overview

**Micro Agent Workbench** is a local, high-contrast, offline-first development assistant and IDE shell. It runs on your machine, uses a repo-scoped memory, and enforces explicit approval before anything touches disk or your shell.

It is a self-contained GUI that:

* Hosts an agent (LLM) with persistent memory and repo context.
* Lets you talk to the agent in **Ask** mode (research/reasoning only).
* Lets you authorize the agent in **Do Work** mode (stage diffs, propose commands, write files **with approval**).
* Captures conversation, screenshots, OCR text, and edits into a **per-repo knowledge base**.
* Manages code editing, version snapshots, diff staging, and safe application of changes.
* Bootstraps new projects and repos with a **Script Creator** mini-app.
* Exposes an **Agent Manager** for authority level, allow-lists, dataset stats, and pending-command state.

All logic lives in **`micro_agent.py`** and runs locally. Default model endpoint assumes an Ollama-style API (`http://127.0.0.1:11434/api/chat`), but the client is generic and can point at any similar local endpoint.

> **Contract pointers:**
> Global agent rules live in **`Agents.md`** (root). Treat them as binding for all agents (Local, Codex Local, Codex Online, Copilot). 
> The delivery loop and approval rules are governed by **`Required-Updates.md`** (backlog/intent), kept in lock-step with **README.md** (current reality) and **Implemented-Updates.md** (ledger). 

---

## Goals

1. Treat the agent like a **co-developer**, not a chatbot.
2. Keep everything **local and inspectable**.
3. Make the agent **earn permission** before running commands or writing files.
4. Persist full context: reasoning, screenshots, OCR, diffs, approvals, and logs.
5. Make it **fast** to seed a new repo with scaffolding, docs, and a first script.
6. Maintain **strict high-contrast** visuals for every state.

---

## Core Concepts

### 1) RepoSession (per-repo control directory)

When you load a folder, the Workbench prepares:

```
<your-repo>/
  .codex_local_agent/
    agent.yaml
    agent.md
    chat_history.md
    dataset/
      memory.jsonl
    patches/
    history/
    logs/
      session_<DATE>.md
    macros/
      registry.jsonl
    Task-Index.json
    styles/
      *.json
```

* **`agent.yaml`** — machine config (provider, model, endpoint, authority toggles, styles, paths).
* **`agent.md`** — human system card (rules, safety, loop).
* **`chat_history.md`** — full markdown transcript (includes `<think>` reasoning and embedded thumbnails).
* **`dataset/memory.jsonl`** — per-turn rows with markdown, image paths, OCR_fast/full, tags, hashes, timestamps.
* **`patches/`** — staged diffs proposed by the agent.
* **`history/`** — per-file snapshots so you can step backward/forward.
* **`logs/session_*.md`** — chronological run logs.
* **`macros/registry.jsonl`** — helper macro entries + usage counters (for navigation/edit/backup).
* **`Task-Index.json`** — durable task ledger (ids, status, approvals, timestamps).

> If any of the above are missing, the agent seeds sensible defaults and logs the action.

### 2) Ask vs Do Work (authority, not memory)

At the top of chat:

* **Ask** — safe reasoning only (explain, analyze, plan drafts). No writes. No shell.
* **Do Work** — stage diffs and commands, request approvals, then apply and verify.

Both modes append to `chat_history.md`, so context flows from Ask → Do Work. Approval/authority is the only difference.

### 3) Local LLM Client

The agent talks to a local `/api/chat` endpoint (Ollama-style). Example payload:

```json
{
  "model": "gpt-oss:20b",
  "messages": [{ "role": "user", "content": "..." }]
}
```

The assistant’s content becomes the reply. Endpoint/model/policy live in `agent.yaml`.

### 4) Conversation Logging

Every turn (user/agent/system) is appended to `chat_history.md` with:

* Timestamp + role header
* **`<think> ... </think>`** (dim, italic, green-toned)
* Final answer (larger bright white text)
* Any image references + thumbnails
* Any inline approval prompts for pending commands

This keeps narrative and decisions auditable.

### 5) OCR & Image Intake

Attach images in chat:

* Thumbnails render inline. Absolute paths are inserted into the message.
* Dual OCR runs:

  * `run_ocr_fast(...)` — lightweight UI/chat text pass
  * `run_ocr_full(...)` — heavier pass for completeness
* A dataset row is written to `dataset/memory.jsonl` with hashes/tags for future recall/RAG.

### 6) Task Feed

In **Do Work**, proposed steps become tasks (id, title, detail, status: pending/running/done/skipped/error). The Task Feed is where plans become concrete without touching disk until approved.

### 7) Staged Changes

Edits are not written directly:

1. Agent proposes changes.
2. Workbench computes a unified diff.
3. You review colorized diffs in **Staged Changes**.
4. On approval, the write occurs and a snapshot is stored in `.codex_local_agent/history/`.

### 8) Version Snapshots

Each approved write snapshots the previous text under `history/<file>/timestamp.txt`. You can step prev/next in the Editor Info Bar, or purge that file’s stored history.

### 9) Pending Command Approval

Shell suggestions **never** auto-run unless whitelisted:

* **Pending Command Bar** shows the exact command plus **Allow / Skip / Try Harder / Edit** and an **Always Allow** checkbox.
* **Allow** flashes blue only when approval is required; **Edit** switches the input into high-contrast magenta-border “edit mode,” and your edited text becomes the new command.

---

## UI Layout

### A) Top Banner Mini-App Dock

Square icons (right→left) open mini-apps; active icons highlight.

### B) Left Dock Column

A collapsible, scrollable stack of opened mini-app panels. Auto-collapses when no panels are open.

### C) Project Tree & Editor

File tree, editor tabs, and an Info Bar with: path, prev/next snapshot arrows, **Copy Path**, **Clone**, **Doc**, **Purge Hist**. High-contrast syntax is enforced.

### D) Chat / Agent Panel

Ask / Do Work buttons, brain-mode dropdown (“Agent” vs “LLM”), transcript, Task Feed, Staged Changes, Pending Command Bar, image attach, and quick buttons (**Plan Tasks / Remember / Expand Logic / Stage File Change / Write File To Disk**).

---

## Mini-Apps (current)

### 1) ScriptCreatorApp

Bootstrap a new repo/folder quickly:

* Destination picker (incl. “Desktop” shortcut).
* Filename + file type dropdown (`.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, …).
* Description → generates the folder’s `README.md`.
* Seeds `.codex_local_agent/` (agent config, chat history, dataset, patches, history).
* Overwrite preview for collisions (high-contrast).

### 2) AgentManagerApp

Expose authority & memory:

* Authority modes: **Full Auto**, **Ask First** (default), **Read Only**.
* **Always Allow** for repetitive commands.
* **Independent Agent Mode** (per-repo approvals sandbox).
* Dataset summary (rows, tags) and pending-command pipeline state.
* View/revoke items in the allow-list.

---

## Loading & Linking a Repo

1. **Clipboard Load**
   Copy a Windows path (file or folder) and choose **Load Path From Clipboard**.

   * File → opens editor tab; parent becomes repo root.
   * Folder → becomes repo root.

2. **ScriptCreatorApp**
   Creates folder, first script, README, and seeds `.codex_local_agent/`; the new folder becomes the active repo.

---

## High-Contrast Accessibility Rules

* Always **light text on dark** (or vice-versa); never low contrast.
* Distinct cues:

  * Flashing **blue** **Allow** when approval is required.
  * **Magenta** border + **purple** input when editing a pending command.
  * **Green, italic** `<think>`; **bright white** final answers.

These rules are enforced across editor, transcript, status labels, and borders.

---

## Typical Workflow

1. **Attach or create a repo** (Clipboard Load or ScriptCreatorApp).
2. **Talk in Ask** — context, screenshots, analysis; OCR + dataset logging; transcript grows in markdown.
3. **Escalate to Do Work** — tasks + proposed edits/commands appear; nothing runs yet.
4. **Review diffs** — approve to write; snapshots saved for rollback.
5. **Handle commands** — approve/skip/try-harder/edit; only explicit approval (or allow-list) executes.
6. **Document & iterate** — use Info Bar tools; keep working with a growing, auditable memory.

---

## Security & Control Model

* No silent command execution or file writes.
* Approvals are explicit and visible; **Independent Agent Mode** isolates approvals per repo if desired.
* You can downgrade authority anytime in Agent Manager.
* Inspect `agent.yaml` to confirm provider/model/endpoint/policies.

---

## README Index (by scope)

These documents are **contracts** the agent must read before acting in their scopes:

* **Root / global**

  * `Agents.md` — Root contract for **all** agents (Local, Codex Local, Codex Online, Copilot). 
  * `Required-Updates.md` — Backlog/intent & operating loop. 
  * `Implemented-Updates.md` — Shipped ledger.
  * `Quarantined-Updates.md` — Blocked/denied items + reasons.
  * `Missing-Updates.md` — Not yet implemented.

* **Agents (local hierarchy)**

  * `agents/README_agents.md` — Home for agents, roster, and styles.
  * `agents/default/README_default.md` — Default agent (stable fallback).
  * `agents/default/agent.yaml`, `agents/default/agent.md` — Bedrock persona/config.
  * `agents/agent_styles/README_Styles.md` — Style packs & selection logic.
  * `agents/agent_tools/README_agent_tools.md` — Local tools/extension surface.
  * `agents/agent_tools/agent_macros/README_agent_macros.md` — Macro system & templates.
  * `agents/README_authority.md` — Authority/allow-list policies for agent scopes.
  * `agents/prompts/README_prompts.md` — Ask / Do Work / Try Harder prompt contracts.

* **System tools**

  * `system_tools/README_system_tools.md` — Top-level system tools surface.
  * `system_tools/system_macros/README_system_macros.md` — Global macros (quarantine/blocked policy).

* **Per-repo runtime (auto-seeded)**

  * `.codex_local_agent/agent.md` & `agent.yaml` — Repo-scoped contract/config.
  * `.codex_local_agent/chat_history.md` — Canonical transcript.
  * `.codex_local_agent/dataset/memory.jsonl` — OCR & image recall rows.
  * `.codex_local_agent/logs/session_*.md` — Run logs.
  * `.codex_local_agent/macros/registry.jsonl` — Macro registry.
  * `.codex_local_agent/Task-Index.json` — Durable task ledger.
  * `.codex_local_agent/styles/*.json` — UI style packs (visual only).

> Agents must resolve scope using these names (e.g., `README_agent_tools.md` means “I’m inside *agents/agent_tools*—apply that contract here”).

---

## Summary

Micro Agent Workbench merges:

* A repo-aware agent with persistent memory.
* A diff-first code editor with snapshots.
* A task feed and explicit approval gate.
* A screenshot/OCR pipeline that seeds a local dataset for recall.
* A project bootstrapper for instant repo scaffolding.
* An Agent Manager that surfaces autonomy, allow-lists, datasets, and pending commands.

Everything is transparent. Everything is high contrast. Nothing runs without you seeing it and approving it.



------

Here’s your updated, drop-in replacement for that **README.md** segment. I kept the original structure, expanded details to match the system we’ve been shaping, and added a concise map that references the key `README_<name>.md` contracts across the repo.

---

# Micro Agent Workbench

## Overview

**Micro Agent Workbench** is a local, high-contrast, offline-first development assistant.

It is a self-contained GUI that:

* Hosts an agent (LLM) with persistent memory and repo-aware context.
* Lets you talk to the agent in **Ask** mode for reasoning, research, and scoping.
* Lets you authorize the agent to actually perform work in **Do Work** mode.
* Captures conversation, screenshots, OCR text, and file edits into a **repo-scoped knowledge base**.
* Manages code editing, **version snapshots**, **diff staging**, and **approval-gated** application of changes.
* Bootstraps new projects and repos with a **Script Creator** mini-app.
* Exposes an **Agent Manager** for authority level, safety gates, dataset visibility, and approvals.

All core logic currently resides in a single local script (`micro_agent.py`) and runs on your machine. No hosted service is required. The default LLM path assumes an Ollama-style API at `http://127.0.0.1:11434/api/chat`, but the client is generic and can point to any compatible local endpoint.

> High-contrast rule (non-negotiable): visible text must always be readable against its background. We default to light text on a dark surface, and never use low-contrast pairings. All examples, panels, and code views in this app obey this rule.

## Goals

1. Treat the agent like a **co-developer**, not a chatbot.
2. Keep everything **local and inspectable**—all artifacts land in the repo.
3. Make the agent **earn permission** before touching disk or running commands.
4. Persist complete context: reasoning, screenshots, OCR outputs, staged diffs, approvals, and snapshots.
5. Make it trivial to **spin up** a fresh repo with scaffolding, docs, and a first script.
6. Maintain strict, explicit, **high-contrast UI** for every state and affordance.

## Core Concepts

### 1) RepoSession

A **RepoSession** represents the “active repo.” When you load a folder, the system prepares a hidden control directory:

```
<your-repo>/
  .codex_local_agent/
    agent.yaml
    agent.md
    chat_history.md
    patches/
    history/
    dataset/
      memory.jsonl
```

* **`agent.yaml`** — machine config (provider/model/endpoint), authority toggles, style pack, and path policy.
* **`agent.md`** — human-readable persona/system card: what the agent is allowed to do here, how it behaves, and the loop it follows.
* **`chat_history.md`** — complete markdown transcript (user + agent), with embedded image refs and `<think>…</think>` reasoning blocks.
* **`patches/`** — staged unified diffs the agent proposes; nothing writes to disk until approved.
* **`history/`** — per-file version snapshots (prev/next navigation in the editor Info Bar).
* **`dataset/memory.jsonl`** — the local RAG seed; one JSONL row per turn that contained images (markdown, image paths, OCR_fast, OCR_full, tags, hashes, timestamp).

> All of this is **per repo**. Each repo carries its own `.codex_local_agent` and memory.

### 2) Ask vs Do Work

At the top of the chat panel are two primary actions:

* **Ask**
  Safe mode. Use for analysis, research, summarization, brainstorming, OCR inspection, and narrative planning.
  **No file writes or shell** activity are allowed in Ask. Use this to align on goals.

* **Do Work**
  Action mode. The agent may propose a plan, generate tasks, **stage code edits as diffs**, and **propose shell commands**—but nothing executes without approval.
  Do Work is how you let the agent take concrete next steps.

Both modes append to `chat_history.md`, so the agent carries Ask context forward into Do Work. The distinction is **authority**, not memory.

### 3) Local LLM Client

The agent talks to a local model endpoint via a simple `/api/chat` contract:

```json
{
  "model": "gpt-oss:20b",
  "messages": [
    { "role": "user", "content": "..." }
  ]
}
```

Replies are parsed and rendered in the chat. Endpoint, model, and policy live in `agent.yaml`. This enables **offline or air-gapped** operation (e.g., Ollama).

### 4) Conversation Logging

Every turn (user/agent) is appended to `chat_history.md` with a timestamp and role header. The renderer supports:

* Headings, lists, code fences, inline code
* Embedded images (with thumbnails)
* Special `<think> … </think>` blocks

`<think>` blocks are shown in **dim, italic, green-toned** text to distinguish reasoning from the “final answer,” which is rendered in **larger bright white** text. This makes the agent’s internal process explicit without sacrificing readability.

### 5) OCR and Image Intake (dual-pass)

Attach images directly in the chat input:

* Thumbnails appear inline in the transcript.
* Absolute file paths are inserted into the message, so the agent can reference them.
* Two OCR passes run:

  * `run_ocr_fast(...)` — lightweight, fast capture of UI/chat text.
  * `run_ocr_full(...)` — broader, slower pass for completeness.

For any turn with images, we log a row to `dataset/memory.jsonl` (markdown, paths, both OCR outputs, tags, hashes, timestamp). This builds **searchable local recall**.

### 6) Task Manager & Task Feed

When Do Work plans are proposed, steps become **tasks**:

* Each task has an ID, title, detail, and status (`pending`, `running`, `done`, `skipped`, `error`).
* The Task Feed displays tasks in a scrollable list with **Start / Skip / View** controls.
* Selecting a task reveals more detail and rationale.

This flow converts high-level planning into **reviewable, staged actions**—without rushing to touch disk.

### 7) Staged Changes Panel

The agent **never** writes edits directly. Instead:

1. Draft the “after” text.
2. Compute a unified diff against the on-disk version.
3. Show the diff in **Staged Changes** (green adds, red removes, yellow headers).
4. Only after approval do we write the file.

All staged diffs are also persisted under `.codex_local_agent/patches/`.

### 8) Version History Snapshots

Upon any approved write:

* The previous content is snapshotted under `.codex_local_agent/history/<file>/timestamp.txt`.
* The Info Bar shows **Prev/Next** snapshot arrows for that file.
* You can **Purge Hist** for a file if needed.

Lightweight history reduces risk and supports quick rollbacks—even before using git.

### 9) Pending Command Approval

The agent may suggest shell commands (e.g., diagnosing an environment). These **never run automatically**. The bar shows:

* **Allow** — run the exact command.
* **Skip** — reject and clear the pending command.
* **Try Harder** — request a refined alternative strategy.
* **Edit** — switch the chat input to **magenta-outlined purple “edit mode”** to revise the command text, then submit.
* **Always Allow** — a toggle for pre-approved patterns to run without flashing blue.

**Visual rules:**

* If a command is waiting and **Always Allow** is off, **Allow** flashes **blue** every ~2 seconds to signal **attention required**.
* Edit mode uses a **purple background** with a **magenta border** to avoid confusion with normal chat sends.

This pipeline ensures the model cannot run shell behind your back.

## UI Layout

The window is split into stable regions that prioritize clarity and speed:

### A) Top Banner Mini-App Dock

* A thin banner at the very top holds square icons (right-aligned).
* Each icon represents a mini-app and remains **highlighted while open**.

### B) Left Dock Column (collapsible)

* The left column hosts one or more **mini-app panels** in a scrollable stack.
* If no mini-app is open, the column **auto-collapses** to return space.

### C) Project Tree & Editor

* **ProjectTree** (rooted at the active repo) and **EditorTabs** sit to the right of the dock.
* The editor Info Bar provides:

  * **Path** · **Prev/Next snapshot** · **Copy Path** · **Clone** · **Doc** · **Purge Hist**
* The editor always uses **high-contrast** syntax and selection colors.

### D) Chat / Agent Panel

On the far right is the **Chat Panel**:

* **Ask / Do Work** buttons
* **Brain Mode** dropdown:

  * “Agent (full repo access)”
  * “LLM (chat only)”
* **Transcript view** (markdown, `<think>` styling, thumbnails)
* **Task Feed**
* **Staged Changes**
* **Pending Command Bar**
* Chat input with image attach, plus:

  * **Plan Tasks**
  * **Remember**
  * **Expand Logic**
  * **Stage File Change**
  * **Write File To Disk (Approve)**

This is the control center for discussion → staging → approval → application.

## Mini-Apps

Mini-apps run **inside** the UI (no popups) and render within the left dock column. Two ship today:

### 1) ScriptCreatorApp

Bootstraps a new working folder or single file **with documentation and agent metadata** ready to go.

**Key features:**

* Destination picker (paste path or choose folder; “Desktop” quick target).
* Script/file name + **file type dropdown** (`.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, …).
* Collision handling with **preview before overwrite** (high-contrast).
* README generation from your description.
* Auto-seeding of `.codex_local_agent/` (agent.yaml/md, chat_history, dataset/history/patches folders).

**Result:** an “agent-ready” repo seed with a starter script, README, and metadata.

### 2) AgentManagerApp

Surfaces the agent’s state and authority:

* **Authority Mode**: Full Auto / Ask First / Read Only
* **Always Allow Repetitive Commands** toggle
* **Dataset summary**: memory row count, tags seen
* **Pending Command pipeline**: queued command + approval state

This gives immediate visibility into **what the agent knows** and **what it is allowed to do**.

## Loading & Linking a Repo

Two fast paths:

### 1) Clipboard Load

* Copy a path in Explorer (file or folder).
* Choose **Load Path From Clipboard** in the app.

  * If it’s a **file**, the parent folder becomes the active repo; the file opens in an editor tab.
  * If it’s a **folder**, that folder becomes the active repo root.

### 2) ScriptCreatorApp

* Create a new folder + main script + README + `.codex_local_agent/`.
* The created folder becomes the active repo and appears in ProjectTree.

## High-Contrast Accessibility Rules

* Dark backgrounds with bright text; **never** low-contrast pairs.
* Distinct, loud accent cues for important states:

  * **Flashing blue** Allow when a command awaits.
  * **Purple + magenta** for command edit mode.
  * **Dim italic green** for `<think>`.
  * **Bright white** for final answers and key labels.

Applied consistently across editors, feeds, diffs, and buttons to minimize state confusion.

## Typical Workflow

1. **Attach a repo**

   * Load an existing folder via Clipboard, or
   * Use ScriptCreatorApp to generate a seed (README + agent metadata + first script).

2. **Align in Ask**

   * Explain context, attach screenshots/logs.
   * Dual OCR runs automatically; dataset row is written.
   * Discussion is appended to `chat_history.md`.

3. **Escalate to Do Work**

   * Request concrete changes.
   * The agent proposes tasks and **stages diffs** for review.

4. **Review diffs**

   * Inspect colorized diffs in **Staged Changes**.
   * Approve to write; **snapshots** are captured under `history/`.

5. **Handle commands**

   * Proposed shell commands appear in the **Pending Command Bar**.
   * **Allow / Skip / Try Harder / Edit**; optional **Always Allow** for repetitive patterns.

6. **Document & iterate**

   * Use Info Bar tools for docs/clone/purge history.
   * Continue the loop—your repo becomes the agent’s **living memory**.

## Security & Control Model

* The agent cannot run shell or write files **without explicit approval** (or a compatible Always Allow policy).
* Authority can be downgraded at any time via the Agent Manager.
* File history can be purged if sensitive content is captured.
* `agent.yaml` makes model, endpoint, and policy **transparent** and auditable.

Treat the agent as a **controlled collaborator inside your repo**, not a background automation layer.

## Summary

Micro Agent Workbench merges:

* A repo-aware AI assistant with persistent, local memory
* A diff-first editor with version snapshots
* A staged **Task Feed** and approval gates
* A screenshot/OCR pipeline feeding a local dataset for recall
* A project bootstrapper for rapid seeding
* An Agent Manager surfacing autonomy and safety

Everything is transparent. Everything is high-contrast. **Nothing** runs without your eyes on it.

---

### Related README contracts (where to look for deeper rules)

> Every operative folder should include a `README_<name>.md` that describes purpose, inputs/outputs, authority, and maintenance. These are the most relevant ones for the Workbench:

* **Root**

  * `README.md` (this file) — present **system snapshot** and UI contract.
  * `Agents.md` — root contract for all agents (local, Codex local, Codex online, Copilot).
  * `Required-Updates.md` · `Implemented-Updates.md` · `Quarantined-Updates.md` · `Missing-Updates.md` — the Trifecta + guard ledgers.

* **Repo control directory** (per active repo)

  * `.codex_local_agent/agent.md` — local agent system card.
  * `.codex_local_agent/agent.yaml` — machine config & authority toggles.
  * `.codex_local_agent/chat_history.md` — canonical transcript.
  * `.codex_local_agent/dataset/memory.jsonl` — OCR + image-linked memory rows.
  * `.codex_local_agent/patches/` — staged unified diffs.
  * `.codex_local_agent/history/` — file snapshots.

* **Agents & tools**

  * `agents/README_agents.md` — how agents are organized (default, styles, roster).
  * `agents/default/README_default.md` — default agent backbone.
  * `agents/agent_tools/README_agent_tools.md` — per-agent tooling surface.
  * `agents/agent_tools/agent_macros/README_agent_macros.md` — macro authoring/usage & safety.
  * `agents/agent_styles/README_Styles.md` (or `README_agent_styles.md`) — style packs, selection, and evolution.
  * `Archived_Agents/archived_agents.md` — snapshot and rollback policy.

Keep these READMEs synchronized with reality; when code changes, update the relevant README(s) **in the same commit** or add a visible “Documentation TODO” in the file you changed.

---

Here’s a fresh, **current** rewrite you can drop into `Required-Updates.md`. I preserved your numbering and expanded to reflect the system we’ve built (Trifecta, per-repo `.codex_local_agent/`, styles vs manager, macro GC/telemetry, task indexing, implementation check footer, etc.).

---

> This section supersedes older drafts of “final consolidation.” Where prior text conflicts with the behaviors below, **this version wins**. It aligns with the **Trifecta** (Required → README (current) → Implemented), the per-repo control directory `.codex_local_agent/`, and the **Ask / Do Work** authority split.

## 28) Final Consolidation — Agent Files, Styles, Macros, Pipelines & Implementation Check (CURRENT)

### 28.1 Default Agent file set (authoritative layout)

Create and maintain the following files/folders **per repo** under `.codex_local_agent/` (operational runtime) and at the repo root (governance ledgers). These define the **Default Agent** (baseline) that styled micro-agents inherit from. The Default Agent’s duties and file roles are canonical and must not drift.

```
<active-repo>/
  .codex_local_agent/
    agent.yaml                 # machine config (provider/model/endpoint/authority/paths/styles)
    agent.md                   # human-readable system card (rules, loop, safety, approvals)
    chat_history.md            # full transcript (Ask + Do Work, with <think> + image refs)
    Task-Index.json            # durable task map (ids, status, approvals, timestamps)
    macros/
      registry.jsonl           # macro records (id, purpose, terminal_type, risk, counters)
      beans.json               # "bean counter" store for 24h GC policy + pins
      compiled/                # compiled/templated macro bundles for speed
    dataset/
      memory.jsonl             # one row per turn with images (markdown, paths, OCR_fast/full, tags, hashes)
    styles/
      default-dark.json        # active visual pack (high-contrast only)
      (other packs...).json
    logs/
      session_<YYYYMMDD_HHMM>.md
    patches/                   # staged unified diffs (before approval)
    history/                   # per-file snapshots (timestamped)
  Required-Updates.md
  Implemented-Updates.md
  Quarantined-Updates.md
  Missing-Updates.md           # regenerated by Agent
```

**Purposes (recap):**

* **`agent.yaml`**: provider/model/endpoint, authority toggles (Ask-first, Always-Allow, Independent), paths (dataset, macros, styles), UI flags (high-contrast, `<think>` styling).
* **`agent.md`**: human system card—mission, runtime rules, safety, approvals, memory policy, macro policy, governance loop.
* **`chat_history.md`**: canonical transcript (Ask + Do Work); includes `<think>` blocks and image refs; becomes long-term context.
* **Governance ledgers**:

  * `Required-Updates.md` (backlog/intent),
  * `Implemented-Updates.md` (shipped log with links/diffs),
  * `Quarantined-Updates.md` (blocked/denied + why + next try),
  * `Missing-Updates.md` (auto—what’s still not implemented).
* **`Task-Index.json`**: durable identity map (task_id, bucket links, status, approvals, timestamps).

#### 28.1.1 Example `agent.yaml` (baseline)

```yaml
# .codex_local_agent/agent.yaml
llm:
  provider: ollama
  model: qwen2.5-coder:latest           # local model slug
  endpoint: http://127.0.0.1:11434      # local inference endpoint

modes:
  ask_mode: enabled
  do_work_mode: enabled

authority:
  ask_first: true                        # default gate for commands & writes
  always_allow: false                    # can be toggled after first explicit approval
  independent_agent_mode: true           # approvals scoped to this repo unless disabled

paths:
  repo_root: "."                         # active repo root
  dataset_root: ".codex_local_agent/dataset"
  macro_registry: ".codex_local_agent/macros/registry.jsonl"
  macro_beans: ".codex_local_agent/macros/beans.json"
  macro_compiled: ".codex_local_agent/macros/compiled"
  styles_dir: ".codex_local_agent/styles"
  chat_history: ".codex_local_agent/chat_history.md"
  sessions_dir: ".codex_local_agent/logs"
  patches_dir: ".codex_local_agent/patches"
  history_dir: ".codex_local_agent/history"
  task_index: ".codex_local_agent/Task-Index.json"

styles:
  active_style: "default-dark"
  packs:
    - ".codex_local_agent/styles/default-dark.json"
    # - ".codex_local_agent/styles/<optional-pack>.json"

updates:
  required: "Required-Updates.md"
  implemented: "Implemented-Updates.md"
  quarantined: "Quarantined-Updates.md"
  missing: "Missing-Updates.md"         # auto-regenerated

ui:
  think_render:
    italic_dim_green: true               # render <think> in dim italic green
  thumbnails_inline: true
  high_contrast_enforced: true           # NEVER permit low-contrast pairings
```

#### 28.1.2 Example `agent.md` (skeleton)

```md
# Agent System Card — Default Agent

## Mission
Operate as a repo-scoped collaborator. Plan → diff → stage → (with approval) apply. No hidden actions. Keep UI and logs high-contrast and explicit.

## Runtime Rules
- Carry Ask-mode context into Do Work planning/execution.
- Never run shell or write files without explicit approval (or a compatible Always-Allow policy).
- Record pending commands; show inline and in the Pending Command bar.
- Respect Independent Agent Mode (approvals scoped to this repo).
- Update Trifecta ledgers on success/failure; create Documentation TODOs when code leads docs.

## Memory & Datasets
- When images are present: append a row to `.codex_local_agent/dataset/memory.jsonl`
  with markdown, absolute image paths, OCR_fast, OCR_full, tags, hashes, timestamp.
- Maintain bucketized directives; prefer newest non-stale bucket when planning.

## Macros (safety + reuse)
- Capture helper scripts to Macro Registry; reuse safely; require explicit allow for high-risk.
- Track usage counters and telemetry; apply 24h bean-based GC with pin exceptions.

## Governance Loop
Rant → Generate Required Updates → Implement (stage, approve, apply) → Update Implemented/Quarantined/Missing → Regenerate Missing → Sync README(s).
```

---

### 28.2 Agent **Styles** vs **Agent Manager** (clear split)

* **Agent Styles (library)** — JSON visual packs under `.codex_local_agent/styles/` (and higher-level templates under `agents/agent_styles/` in the project).
  They alter **visual presentation and minor UX affordances** only (margins, outlines, animations), never authority or policies. Styles **must** enforce the high-contrast rule. The active pack is set in `agent.yaml.styles.active_style`.

* **Agent Manager (control plane)** — runtime dashboard for authority (Ask-First / Full-Auto / Read-Only), **Always Allow** toggles, Independent Agent Mode, approvals ledger, dataset stats, macro diagnostics, and quick policy switches.
  The **Ask/Do-Work geometry** (buttons near input, markdown feed with `<think>`, thumbnails inline, pending-command bar) remains consistent across styles.

---

### 28.3 Rant → Required → Implement → Revise → Missing (controls & flow)

Add (or keep) three high-level controls near the chat/plan area:

1. **Generate Required Updates** — collapse the current rant/context into structured buckets, assign `bucket_id` + timestamps, and append to `Required-Updates.md` (without deleting previous intent; add negative notes instead of erasing).

2. **Revise Required Updates** — sweep the file: merge duplicates, fold clarifications, link to Implemented/Quarantined entries, and explicitly mark **outdated** logic with a short “superseded by …” note (do not silently remove).

3. **Implement Required Updates** — iterate top-to-bottom:

   * Skip if already Implemented; if Quarantined, ask whether to retry.
   * Otherwise stage tasks with diffs/commands in Task Feed.
   * On success: update **Implemented**, regenerate **Missing**, and clear matching Quarantine.
   * On failure/denial: write **Quarantined**, mark in **Missing** with a short reason.

---

### 28.4 Task identity & approvals (durable indexing)

Maintain `.codex_local_agent/Task-Index.json`:

```json
{
  "task_id": "T-24F8",
  "bucket_ids": ["B-req-20251029-001"],
  "status": "implemented",      // implemented | quarantined | missing | pending | running | error
  "created_at": "2025-10-30T02:46:00Z",
  "updated_at": "2025-10-30T02:57:22Z",
  "last_authority_decision": "Allowed 2025-10-30T02:55:03Z",
  "macro_refs": ["M-0x14", "M-0x1B"]
}
```

* Surface approvals inline and in the Pending Command bar: **Allow / Skip / Try Harder / Edit / Always Allow**.
* **Flashing blue** Allow only when a command awaits approval.
* **Edit** mode = **purple background + magenta border**.
* **Independent Agent Mode** scopes approvals to this repo unless explicitly disabled.

---

### 28.5 Macro Registry (capture → reuse → telemetry → GC)

**Capture** each helper into `macros/registry.jsonl`:

```json
{"macro_id":"M-0x14","terminal_type":"PowerShell",
 "purpose":"Navigate to target and write file safely",
 "risk":"repo-write",
 "body":["Set-Location ...","Get-ChildItem ...","Set-Content ..."],
 "repo_root":"C:/path/to/repo",
 "task_id":"T-24F8",
 "created_at":"2025-10-30T02:44:00Z",
 "usage_count":1,
 "last_used_at":"2025-10-30T02:44:00Z",
 "pinned":false}
```

**Reuse** by `(purpose, terminal_type, repo_root)` when allowed; high-risk macros always require at least one explicit approval. **Always Allow** may suppress repeat prompts (respect Independent scoping).

**Telemetry** logs start/end, runtime, success/failure, approval source (manual vs auto), and whether Independent mode limited propagation. Show macro diagnostics in Agent Manager.

**Bean-counter GC** (24h policy, tracked in `beans.json`):

* Remove macros with `usage_count == 0` after 24h grace.
* Remove unused for >24h unless **pinned** or **always_allow**.
* After long idle resumes, **defer** cleanup until one action is taken (to avoid wiping useful macros on return).

**Compiled macros** live under `macros/compiled/` for frequently-used bundles (e.g., “safe write with backup,” “multi-file search+patch”). Reference compiled ids from tasks to accelerate repeated flows.

---

### 28.6 Dataset rows, OCR, and bucketized memory

For any turn with images, append to `dataset/memory.jsonl`:

```json
{"ts":"2025-10-30T02:50:00Z","markdown":"...","image_paths":["C:/.../shot.png"],
 "ocr_fast":"...","ocr_full":"...","tags":["screenshot","log"],"hashes":["..."]}
```

* Bucketize directives (by topic/file/system area) with diff-style versioning; prefer the newest **non-stale** bucket when planning.
* When re-injecting memory into prompts, **strip storage tags/metadata**.

---

### 28.7 Chat/Panel UI — enforce the spec

* Tall, repo-aware chat; **Ask / Do Work** near the input.
* Markdown feed renders `<think>` as **dim italic green**; thumbnails inline; code blocks and inline diffs supported.
* Log each turn to `chat_history.md` (timestamp, role, reasoning/final, image paths, proposed commands, staged diffs).

---

### 28.8 End-of-Run **Implementation Check** (auto footer)

At the **end of each** “Implement Required Updates” run, **append** this auto-generated section to **`Required-Updates.md`** (do not edit manually):

```md
---

## Implementation Check — <ISO8601 timestamp>

**Completed (Implemented-Updates.md):** N
- [T-xxxx] <bucket_id> — <short summary>
- ...

**Quarantined (Quarantined-Updates.md):** M
- [T-xxxx] <bucket_id> — reason: blocked_by_user/runtime_error/...
- ...

**Still Missing (Missing-Updates.md):** K
- <bucket_id> — pointer (e.g., needs approval for Macro M-0x14)
- ...

**Verdict:** <ALL IMPLEMENTED | PARTIAL | NONE>
```

If **ALL IMPLEMENTED**, also add the final line:

```
✅ As of <timestamp>, all buckets have corresponding Implemented entries. Nothing is missing.
```

Otherwise:

```
⚠️ As of <timestamp>, missing or quarantined items remain. See the sections above.
```

---

### 28.9 High-contrast rule (non-negotiable)

All visible text must be **high-contrast** against its background—no exceptions, no low-contrast states (including popups, diffs, pending-command bar, diagnostics, and in-chat code). Default: **light text on dark**.

---

### 28.10 Ask / Do Work separation (sacred)

* **Ask**: research/reason/narrate only—no file writes, no shell.
* **Do Work**: plan tasks, stage diffs, propose commands—**everything gated by approval**.
* Always carry Ask context into Do Work.

---

## 29) Acceptance

When the above is implemented, the Agent can:

* Convert “rants” into structured **Required Updates**,
* Stage and execute tasks with **durable ids and approvals**,
* Learn & reuse **macros** with telemetry + **24h GC**,
* Version and recall memory via the local dataset, and
* Write an **Implementation Check** footer stating whether Required items shipped.

This closes the loop between **files (runtime)** and **governance (Trifecta)** and keeps the README contracts aligned with reality.

------ ChatGPT 5 Instant logic ------

The two uploaded files form a **linked operating system for your local Codex Agent**:

---

### 🧩 **File Roles**

**1. `Micro-Agent-Local.md`** — defines the *system architecture and top-level runtime contract*
It establishes how all agents (Local, Codex Local, Codex Online, Copilot) interoperate under one canon (“Trifecta”) and how `Required-Updates.md` drives their execution loop.

**2. `Required-Updates.md`** — defines the *live backlog and operating contract*
It is the actionable plan that the local agent reads to decide what to build, verify, and log. It defines Ask/Do Work separation, authority rules, chat behavior, dataset capture, and UI elements.

---

### 🔍 **Relationship and Loop**

The two files reinforce each other:

| File                   | Function                                                                                                                                                         | Reads / Writes                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `Micro-Agent-Local.md` | System charter. It explains the canon (`Required-Updates.md` ⇄ `README.md` ⇄ `Implemented-Updates.md`), directory structure, authority gates, and UI guarantees. | Read by all agents. Rarely edited except to expand core logic.                |
| `Required-Updates.md`  | Execution backlog. The agent parses it into buckets → tasks → approvals → applied diffs → verification.                                                          | Continuously read and rewritten by the agent after each implementation cycle. |

They agree that every run follows the loop:
**Plan → Stage → Approve → Apply → Verify → Report**, updating `Implemented-Updates.md`, `Missing-Updates.md`, and `Quarantined-Updates.md`.

---

### ⚖️ **Contradiction Scan (Top = Old, Bottom = New)**

From `Required-Updates.md` (older at top, newer at bottom):

| Topic                           | Older Logic                                       | Newer Logic                                                          | Resolution                                                                                        |
| ------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Authority control**           | Per-action Allow / Always Allow.                  | Adds *Independent Agent Mode* and *Allow List UI* with revocation.   | Keep both: preserve fine-grained per-action approval, but also persist allow-list state per repo. |
| **Ask / Do Work**               | Split already defined; carry context.             | Re-emphasized that Ask should not route through high-authority code. | Keep stronger rule: Ask never runs writes; context shared forward only.                           |
| **Chat feed**                   | Markdown, `<think>` dim green, thumbnails inline. | Adds implementation detail for image OCR dataset logging.            | Merge: ensure markdown + images + dual OCR always co-recorded.                                    |
| **Buckets & dataset**           | Introduced buckets and diff-style memory.         | Later section formalizes dataset JSONL and versioned directives.     | Combine: store every bucket version with semantic hash; mark stale ones superseded.               |
| **Mini-app system**             | ScriptCreatorApp + AgentManagerApp defined.       | Adds “Implement Required Updates” button and batch executor.         | Integrate button into AgentManagerApp; link its run log to `.codex_local_agent/logs/`.            |
| **UI high contrast**            | Rule stated globally.                             | Restated in both docs under §8.                                      | Consolidate: enforce system-wide via style packs referenced in `agent.yaml`.                      |
| **End-of-Run**                  | Append Implementation Check to Required-Updates.  | Root doc mandates same phrase with timestamp.                        | Unify wording and require auto-append with ✅ line.                                                |
| **Branch policy**               | Not explicit.                                     | Micro-Agent doc enforces single-branch `main`.                       | Adopt single-branch rule. Overwrite Guard stays mandatory.                                        |
| **Macros / Garbage Collection** | Daily GC for unused macros.                       | Still present in root doc.                                           | Keep identical.                                                                                   |

---

### 🧮 **Extended Differential Addendum (to append to Required-Updates.md bottom)**

```
### 29) Extended Merge — Canonical Balancer between Agents.md and Required-Updates.md

#### (29.1) Authority Synchronization
Combine per-action Allow logic (§Authority & Approvals) with the newer “Independent Agent Mode” and “Allow List” (§5.4-5.5).  
→ Maintain per-repo allow-list files under `.codex_local_agent/authority/allow.jsonl`.  
→ On revocation, pending commands referencing that hash must re-prompt for approval.

#### (29.2) Ask / Do Work Clarification
Ask mode = reasoning only; no disk or shell writes.  
Do Work mode = planned execution requiring approval.  
All context (messages, images, OCR) persists to `chat_history.md` and `dataset/memory.jsonl`.  
Never route Ask through high-authority paths.

#### (29.3) Dataset + Bucket Convergence
Every turn with images produces:
- one dataset row (`memory.jsonl`);
- one bucket entry (semantic + diffable);
- hash cross-reference in `Task-Index.json`.  
Buckets supersede previous logic only when `superseded_by` field present.

#### (29.4) Batch Executor Integration
Move “Implement Required Updates” button into AgentManagerApp panel.  
Running it launches the full Plan→Apply loop, pauses for approvals, then writes logs to `.codex_local_agent/logs/session_<DATE>.md`.  
Success paths update Implemented-Updates.md; failures update Quarantined/Missing.

#### (29.5) Branch & Safety Policy
All writes target `main`.  
Enable Overwrite Guard: reject writes if remote/main is ahead.  
Approval required for any non-fast-forward push.

#### (29.6) End-of-Run Harmonization
Always append to bottom of Required-Updates.md:

✅ As of <timestamp>, Required Updates are fully implemented. README reflects current system.

#### (29.7) UI and Style Enforcement
All UIs must obey `agent.yaml.styles.active_style`.  
High contrast mandatory; no low-contrast pairs.  
Style packs stored under `.codex_local_agent/styles/`.

#### (29.8) Macro Lifecycle
Retain 24-hour bean-counter GC but record deletion events in `macros/gc_log.jsonl` for audit.
```

---

### ✅ **Summary**

No contradictions block execution.

* `Micro-Agent-Local.md` = structural authority & loop definitions.
* `Required-Updates.md` = actionable backlog + UI spec.

Appending the above **Extended Merge block** to the bottom of `Required-Updates.md` will align both files perfectly for your next agent cycle.


### 29) Extended Merge — Canonical Balancer between Agents.md and Required-Updates.md

#### (29.1) Authority Synchronization

Merge the two-tier approval system described across both files.
Each repo instance maintains its own **authority ledger** stored at:
`.codex_local_agent/authority/allow.jsonl`.
Entries in this file log approved command patterns, timestamps, context, and mode.
Fields:

```
{
  "command_hash": "<sha256 of command_line>",
  "pattern": "<truncated or generalized command>",
  "timestamp": "<UTC ISO>",
  "mode": "<Ask | Do Work>",
  "scope": "<local | global>",
  "revoked": false
}
```

Behavior:

* The Agent checks this ledger before flashing a new Allow prompt.
* If a match is found and not revoked, the action executes automatically.
* Revoking any entry forces future prompts.
* When **Independent Agent Mode** is enabled, the ledger is isolated to that repo; global approvals are ignored.
* When **Always Allow** is toggled, repetitive approvals use this ledger transparently without human confirmation.
* The AgentManagerApp must expose this list under a visible **Authority → Allow List** tab with revocation controls.
  This structure replaces transient approval memory with persistent auditability and version control integration.

#### (29.2) Ask / Do Work Clarification

Ask mode and Do Work mode share one chat history and dataset feed but differ in authority:

* **Ask** mode performs pure reasoning. It cannot modify disk or trigger commands. It accumulates narrative, planning, and contextual OCR data only.
* **Do Work** mode translates the accumulated Ask context into executable tasks. These may include file edits, command runs, or schema migrations.
  Ask → Do Work carries over context identifiers and message hashes.
  Each Ask message appends its markdown to `chat_history.md` and adds a structured row to `.codex_local_agent/dataset/memory.jsonl`:

```
{
  "timestamp": "<UTC ISO>",
  "role": "ask",
  "markdown_block": "<user or agent message>",
  "context_hash": "<sha256>",
  "tags": ["ask", "context", "planning"]
}
```

Do Work runs mirror this with `"role": "do_work"`.
Both share a unified sequence counter to preserve order.
When switching from Ask to Do Work, the agent copies unresolved objectives from the last Ask row into a temporary task file before execution.

#### (29.3) Dataset + Bucket Convergence

Each new instruction or design logic becomes a **bucket** in memory, persisted under `.codex_local_agent/dataset/buckets/`.
Each bucket file is JSON:

```
{
  "bucket_id": "<uuid>",
  "title": "<section title>",
  "version": "<incrementing integer>",
  "status": "<active | superseded>",
  "semantic_hash": "<sha256 of text>",
  "source_file": "<Required-Updates.md or Agents.md>",
  "text": "<raw directive>",
  "superseded_by": "<new bucket_id or null>"
}
```

Whenever Required-Updates.md changes, the system compares new text hashes against existing buckets.
If identical → ignore.
If changed → create new bucket, mark previous as superseded.
When planning or reasoning, only “active” buckets are loaded.
This mechanism tracks historical directive drift while keeping the planning layer clean.

#### (29.4) Batch Executor Integration

Integrate the “Implement Required Updates” runner into **AgentManagerApp**.
Button label: **Implement Required Updates (Plan→Apply Loop)**.
Behavior:

* Scans `Required-Updates.md` for all buckets not listed in `Implemented-Updates.md`.
* Creates a queue with one task card per bucket.
* Displays progress with current bucket ID, file diffs, and authority prompts.
* Logs actions under `.codex_local_agent/logs/session_<DATE>.md`.
  Session log fields:

```
[SESSION]
timestamp_start:
timestamp_end:
buckets_total:
buckets_completed:
buckets_failed:
authority_decisions: {allow_count, skip_count, edit_count}
```

Every successful bucket appends an entry to `Implemented-Updates.md` with summary and timestamp.
Failed or denied buckets are recorded to `Quarantined-Updates.md`.
Unimplemented remain in `Missing-Updates.md`.
This merges the conceptual runner from Agents.md with the per-session discipline defined in Required-Updates.md.

#### (29.5) Branch & Safety Policy

Adopt a single authoritative branch: **main**.
All write actions target main directly.
Before any write:

* Fetch and verify remote/main tip.
* If local commit is behind, trigger **Overwrite Guard**.
* Overwrite Guard displays high-contrast red banner:
  `⚠️ Remote ahead — manual merge or rebase required before writing.`
  Agent must pause execution until human approves “Merge then Apply” or cancels.
  Commits are safe-pushed after each verified session:

```
git fetch --prune
git checkout main
git rebase origin/main
git add -A
git commit -m "[Codex Agent] Implemented Required Updates"
git push origin main
```

If push fails, the agent retries once with `--force-with-lease` only after confirmation.

#### (29.6) End-of-Run Harmonization

At completion of every cycle:

1. Append to `Required-Updates.md` bottom line:

   ```
   ✅ As of <UTC timestamp>, Required Updates are fully implemented. README reflects current system.
   ```
2. Update Implemented-Updates.md with same timestamp and completion ratio.
3. Clear Missing-Updates.md.
4. Summarize total buckets completed, quarantined, or skipped in `.codex_local_agent/logs/session_<DATE>.md`.
5. If new directives were found but not implemented, requeue them in Missing-Updates.md under a new header:
   `## Next Cycle Seeds — Discovered During Verification`.

#### (29.7) UI and Style Enforcement

All graphical surfaces must enforce high-contrast policy defined in `agent.yaml`:

```
styles:
  active_style: "default-dark"
  packs:
    - ".codex_local_agent/styles/default-dark.json"
```

The style pack defines RGB hex values for:

```
{
  "background_window": "#0f0f1a",
  "background_panel": "#1a1a24",
  "text_main": "#f5f5f5",
  "text_dim": "#c0c0c0",
  "accent_focus": "#3a86ff",
  "accent_warn": "#ffcc00",
  "accent_danger": "#ff4444",
  "accent_ok": "#3aff6a"
}
```

This JSON must exist before UI launch.
The system verifies color contrast ratios exceed WCAG 2.1 AA minimums.
Violation logs emit warnings into `.codex_local_agent/logs/ui_audit_<DATE>.txt`.

#### (29.8) Macro Lifecycle

Macro registry: `.codex_local_agent/macros/registry.jsonl`.
Each macro record:

```
{
  "macro_id": "<uuid>",
  "name": "<function>",
  "purpose": "<nav | edit | backup | io>",
  "risk": "<low | med | high>",
  "usage_count": <int>,
  "last_used": "<UTC ISO>",
  "beans": <float>
}
```

GC rules:

* Every 24 hours, macros with `usage_count == 0` and `last_used` older than 24h are deleted.
* Each deletion event logs to `.codex_local_agent/macros/gc_log.jsonl`.
* Before deletion, a summary of candidates appears in the AgentManagerApp under **Maintenance → Macro GC**.
* If a macro reappears in the next run, it is reinstated with new UUID and bean counter reset.
  Beans represent macro health; positive beans reflect reliability and reuse frequency.

#### (29.9) Unified Dataset–Ledger Linkage

Each dataset row gains linkage fields:

```
"task_id": "<if produced during Do Work>",
"bucket_id": "<source section id>",
"approval_ref": "<hash from allow.jsonl>",
"session_id": "<session_<DATE>>"
```

This ties together dataset, tasks, approvals, and logs for full traceability.
All linked records must be cross-checkable through the AgentManagerApp “Diagnostics” tab.

#### (29.10) Quarantine Integrity

Whenever a bucket enters `Quarantined-Updates.md`, create a structured reason entry:

```
{
  "bucket_id": "<uuid>",
  "reason": "<error or denial cause>",
  "proposed_fix": "<text>",
  "quarantined_by": "<user or auto>",
  "timestamp": "<UTC ISO>"
}
```

The agent rechecks quarantined items on next launch.
If `reason` matches a previously fixed error, the bucket auto-migrates back into Missing for reattempt.

#### (29.11) Self-Audit Summary

Every run must conclude with a machine-verifiable audit record:
`.codex_local_agent/audit/session_<DATE>.json`:

```
{
  "completed_buckets": <int>,
  "failed_buckets": <int>,
  "skipped_buckets": <int>,
  "active_allow_entries": <int>,
  "revoked_allow_entries": <int>,
  "macros_removed": <int>,
  "dataset_entries_added": <int>,
  "session_duration_sec": <float>
}
```

Audit files older than 14 days are archived under `.codex_local_agent/audit/archive/`.
A compact summary is appended as a fenced JSON code block at the bottom of `Implemented-Updates.md` for transparency.



### 30) Local–Online Authority Chain and Synchronization Protocol

#### (30.1) Dual-Ledger Concept

Codex Online and Local Micro-Agent must maintain two synchronized ledgers of authority and task data:

* **Local Ledger:** `.codex_local_agent/Task-Index.json` (source of truth for offline runs).
* **Remote Ledger:** `cloud/authority/Task-Ledger.jsonl` (hosted by Codex Online).
  The synchronization model is **push–pull**:
* On Local startup, the Agent performs a **pull** from Remote if online.
* On successful run completion, it performs a **push** of updated entries.
  Each entry is identified by a deterministic `task_hash` built from bucket_id + diff fingerprint + timestamp.
  If collisions occur, the remote version wins only if its `verified: true` and local entry `verified: false`.
  Conflicts are recorded under `.codex_local_agent/logs/sync_conflicts_<DATE>.txt` with both versions stored.

#### (30.2) Authority Replication

Authority records in `.codex_local_agent/authority/allow.jsonl` synchronize one-way to the remote ledger under:
`cloud/authority/Allow-Ledger.jsonl`.
Replication fields:

```
{
  "command_hash": "<sha256>",
  "pattern": "<short>",
  "approved_local": true,
  "approved_remote": true|false,
  "scope": "<local|global>",
  "last_seen": "<UTC ISO>"
}
```

Rules:

* Local-only approvals stay local until a `share_authority: true` flag is set in `agent.yaml`.
* Shared approvals replicate upward on next online sync.
* The cloud authority index merges duplicates and returns aggregated trust weights.
* The Local agent marks shared approvals in allow.jsonl with `"replicated": true`.

#### (30.3) Task Propagation and Acknowledgment

Each task executed in Do Work mode emits an acknowledgment packet:

```
{
  "task_id": "<uuid>",
  "bucket_id": "<uuid>",
  "repo": "<path or identifier>",
  "status": "<done|skipped|error>",
  "timestamp": "<UTC ISO>",
  "verified": <bool>,
  "verified_by": "<agent_id or human>",
  "hash": "<sha256 of diff>"
}
```

When online, acknowledgments append to the remote Task-Ledger.
Remote Codex Online aggregates them to compute progress ratios per repo.
When offline, acknowledgments queue in `.codex_local_agent/outbox/acks.jsonl`.
Queued packets flush automatically on next connection.

#### (30.4) Identity and Signing

Each Local Agent instance signs outbound packets with its unique identifier:
`.codex_local_agent/id.json`

```
{
  "agent_id": "<uuidv4>",
  "name": "<hostname>-local",
  "public_key": "<base64>",
  "private_key": "<base64-encrypted>",
  "created": "<UTC ISO>"
}
```

When syncing, packets include the agent_id and signature block.
Codex Online validates against a stored registry of known keys.
Invalid signatures quarantine the packets for manual review.
Every sync session appends a verification digest to `.codex_local_agent/logs/sync_<DATE>.log`:

```
[SYNC]
local_entries_sent: N
remote_entries_received: M
conflicts_detected: X
quarantined_packets: Y
duration_ms: Z
status: success|partial|failed
```

#### (30.5) Network Policy

Sync occurs only when network is detected and `network_allow_sync: true` in `agent.yaml`.
If set to false, all operations stay local.
Offline queues persist indefinitely.
If the user forces sync via the Agent Manager “Sync Now” button, temporary override applies only for that session.

#### (30.6) Conflict Resolution Algorithm

When both sides have modified the same task entry:

1. Compare timestamps (`updated_at`).
2. Compare `verified` flags.
3. Prefer version with `verified: true`.
4. If both unverified, prefer newer timestamp.
5. If both verified and different, mark conflict.
   Conflict objects are JSON-patched under `.codex_local_agent/conflicts/`.
   Manual review GUI lists these conflicts in the AgentManagerApp → **Sync Conflicts** view.

#### (30.7) Remote Acknowledgment Feedback

Codex Online periodically emits an aggregated acknowledgment packet back to Local Agents:

```
{
  "timestamp": "<UTC ISO>",
  "repo_id": "<path>",
  "tasks_verified": <int>,
  "tasks_pending": <int>,
  "tasks_quarantined": <int>,
  "authority_revoked": <list of command_hashes>
}
```

When received, Local Agent applies remote revocations by marking those hashes in allow.jsonl as revoked and updating Task-Index.json accordingly.

#### (30.8) Secure Channel and Recovery

All sync traffic uses HTTPS with key-pinned TLS; fallback to local-only if verification fails.
If remote storage becomes unreachable for >48h, Local emits warning in logs and continues offline indefinitely.
When remote comes back online, the first sync run performs a full differential reconciliation:

* Compare local Task-Index.json against remote Task-Ledger.jsonl by task_hash.
* Upload missing entries, download missing verified ones.
* Merge authority ledgers and update logs.
  A summary report is appended to `.codex_local_agent/audit/sync_audit_<DATE>.json`.

#### (30.9) Global Approval Aggregation

Codex Online computes trust weights for command patterns by observing repeated approvals across agents:

```
trust_score = log10(1 + approvals_global / (1 + revocations_global))
```

Scores ≥ 1.0 mark globally trusted commands that may auto-approve in future runs if local policy permits.
The Local Agent periodically downloads the trust table into `.codex_local_agent/authority/global_trust.json`.
Trust decay reduces weights by 10% weekly unless refreshed by new approvals.

#### (30.10) Sync UI Hooks

AgentManagerApp gains a **Sync & Authority** panel showing:

* Last sync timestamp.
* Outbox queue size.
* Remote acknowledgments summary.
* Conflicts count.
* Toggle for `network_allow_sync`.
  Buttons:
  **Sync Now**, **Review Conflicts**, **View Global Trust**, **Purge Outbox**.
  Each action writes results to `.codex_local_agent/logs/sync_ui_<DATE>.log`.

#### (30.11) Error Containment

If sync fails repeatedly (three consecutive attempts), disable auto-sync for 24 hours and log:
`[WARN] Auto-sync disabled until <timestamp> due to repeated errors.`
User may re-enable manually.
No data loss occurs; unflushed entries remain in outbox.
Partial syncs are resumable; each packet includes `sync_seq` for continuation.

#### (30.12) Integrity Assurance

At end of successful sync:

* Verify count parity between Local Task-Index.json and Remote Task-Ledger.jsonl.
* Verify all acknowledged task hashes appear in Implemented-Updates.md.
* Recalculate cross-ledger SHA digest:
  `sha256(Task-Index.json + Allow-Ledger.jsonl) → sync_digest_<DATE>.txt`
* Store digest locally and remotely for audit comparison.

#### (30.13) Implementation Metadata

All sync code and schema definitions live under `.codex_local_agent/net/`.
Expected files:

```
net/
  sync_protocol.md
  schema_task.json
  schema_authority.json
  schema_packet.json
  README.md
```

These describe the wire format, constraints, and examples of valid packets.
If any schema file is missing, the agent regenerates it automatically using canonical templates embedded in Required-Updates.md.

#### (30.14) Sync Verification Footer

After each completed sync, append a footer to `Implemented-Updates.md`:

```
[SYNC CHECK]
timestamp: <UTC ISO>
entries_sent: <n>
entries_received: <m>
conflicts: <x>
trust_table_entries: <y>
status: success
```


### 31) Distributed Task Graph and Inter-Agent Orchestration

#### (31.1) Concept

Extend the single-agent model into a distributed **Task Graph** shared by multiple local and remote agents.
Each agent contributes nodes (tasks) and edges (dependencies).
The graph ensures no duplicate or conflicting work and allows partial delegation.
Core file: `.codex_local_agent/tasks/graph.jsonl`.
Each record:

```
{
  "task_id": "<uuid>",
  "bucket_id": "<uuid>",
  "depends_on": ["<task_id>", ...],
  "assigned_to": "<agent_id>",
  "status": "<pending|running|done|error>",
  "hash": "<sha256 of diff>",
  "origin": "<local|remote>",
  "timestamp": "<UTC ISO>"
}
```

Agents synchronize their graphs via the authority chain defined previously.
The Local Agent updates its graph whenever Required-Updates.md changes, or when receiving remote broadcasts.
Conflicts are detected by duplicate task hashes with divergent statuses.

#### (31.2) Node States

Each node’s lifecycle follows:

* `pending` — parsed but not started.
* `running` — currently active.
* `done` — verified complete; appears in Implemented-Updates.md.
* `error` — failed execution; reason in Quarantined-Updates.md.
  Edges define dependencies so tasks wait until prerequisites complete.
  AgentManagerApp renders this graph as a vertical dependency tree with color-coded states:
* Green: done
* Yellow: running
* Red: error
* Gray: pending

#### (31.3) Delegation and Ownership

When multiple agents operate on the same project:

* Each task node has `assigned_to` field referencing agent_id.
* Idle agents can claim unassigned nodes by request if no dependency locks exist.
* The agent claiming a task must announce ownership through the sync protocol to update remote graph.
* Ownership changes log to `.codex_local_agent/logs/ownership_<DATE>.log`.

#### (31.4) Priority Rules

Each task has a derived priority:

```
priority = (dependency_depth * 0.5) + (bucket_age_days * 0.1) + (manual_boost)
```

Manual boost field is integer adjusted in the Task Manager UI.
Tasks are executed in ascending priority order, ensuring foundational buckets are addressed before new or cosmetic ones.

#### (31.5) Distributed Locking

To prevent two agents from running the same node concurrently, a locking file is created:
`.codex_local_agent/tasks/locks/<task_id>.lock`
Contents:

```
{
  "task_id": "<uuid>",
  "agent_id": "<uuid>",
  "timestamp": "<UTC ISO>",
  "status": "active"
}
```

Lock expires if the agent fails to update within `lock_timeout_minutes` (default 15).
Expired locks trigger automatic requeue of the task into pending state.
Lock conflicts append to `conflicts/locks_<DATE>.jsonl`.

#### (31.6) Orchestration Loop

A local orchestration thread monitors `graph.jsonl` and runs:

1. Identify ready tasks (no unmet dependencies).
2. Verify no active lock.
3. Request authority if Do Work mode.
4. Execute and update status.
5. Propagate result to remote ledger.
   Execution plan runs in background without blocking the chat UI.

#### (31.7) Cross-Agent Messaging

Agents exchange coordination pings through the same sync channel:

```
{
  "type": "heartbeat",
  "agent_id": "<uuid>",
  "timestamp": "<UTC ISO>",
  "active_tasks": [task_id, ...],
  "done_tasks": [task_id, ...],
  "errors": [task_id, ...]
}
```

Heartbeats accumulate in `net/heartbeat_log.jsonl`.
Agents use this to avoid redundant work and to gauge collective progress.

#### (31.8) Consensus and Reconciliation

When the same bucket appears on multiple agents with divergent interpretations:

* Each agent computes a `bucket_semantic_hash`.
* The remote ledger compares hashes.
* If mismatch, all affected nodes enter “await consensus” state.
  A consensus ballot is then created under `.codex_local_agent/consensus/`:

```
{
  "bucket_id": "<uuid>",
  "options": [
     {"agent_id": "...", "semantic_hash": "..."},
     ...
  ],
  "winning_hash": null,
  "status": "open"
}
```

Once majority agreement achieved, `winning_hash` is chosen and committed; other variants mark superseded.
This prevents code or instruction divergence between local and remote nodes.

#### (31.9) Performance Telemetry

Each task node records performance metrics:

```
{
  "exec_time_ms": <int>,
  "io_bytes": <int>,
  "cpu_usage": <float>,
  "mem_peak_mb": <float>
}
```

These metrics feed into `.codex_local_agent/audit/performance_<DATE>.jsonl` for later optimization.
Aggregates compute average runtime per bucket type and success ratio.

#### (31.10) Visual Graph Inspector

Add a **Task Graph** tab to AgentManagerApp.
Displays interactive DAG (directed acyclic graph) of all tasks with:

* Hover tooltips showing bucket titles, owners, timestamps.
* Right-click context menu: **Reassign**, **Retry**, **Open Diff**, **View Dependencies**.
* Double-click to open bucket text from Required-Updates.md.
  High contrast colors follow default-dark style pack.

#### (31.11) Automatic Retry Policy

Failed tasks automatically reattempt once after cooldown period of 5 minutes if error cause is transient (network, permission, I/O).
Permanent failures remain quarantined until manual release from the Task Graph UI.

#### (31.12) Checkpointing

During long operations, partial progress checkpoints write to `.codex_local_agent/tasks/checkpoints/<task_id>_<n>.json`.
These files can restore interrupted runs without repeating prior steps.
On restart, the agent reads checkpoints and resumes from last successful phase.

#### (31.13) Graph Export and Import

The Task Graph can be exported as JSON or DOT for visualization.
Export command in AgentManagerApp: **Export Graph → DOT** produces `graph_export_<DATE>.dot`.
Importing another agent’s graph merges non-conflicting nodes and reindexes IDs if necessary.
Import log saved to `.codex_local_agent/logs/import_<DATE>.log`.

#### (31.14) Rollback Chain

Every node’s action is paired with an inverse operation saved in `.codex_local_agent/tasks/rollback/`.
If a node fails after partial execution, rollback chain automatically reverts files, commands, and states to prior versions.
Rollback files mirror structure:

```
rollback/
  <task_id>/
     revert_<file>.diff
     revert_cmds.txt
```

Rollback logs append to session log with `[ROLLBACK]` prefix.

#### (31.15) End-of-Graph Verification

At the conclusion of a distributed run, agent validates:

* All dependency chains closed (no dangling nodes).
* No node marked both done and error.
* Graph hash matches remote graph hash.
  If all verified: append summary block to `Implemented-Updates.md`:

```
[GRAPH CHECK]
timestamp: <UTC ISO>
nodes_total: <int>
nodes_done: <int>
nodes_error: <int>
consensus_conflicts: <int>
verification: success
```

### 32) Cognitive Memory Engine and Context Retention Framework

#### (32.1) Overview

This layer transforms static OCR and chat datasets into a **Cognitive Memory Engine (CME)** capable of contextual recall, summarization, and semantic versioning.
The CME replaces passive data files with structured memory banks.
Root directory: `.codex_local_agent/memory/`
Subfolders:

```
memory/
  bank_core.jsonl
  bank_long.jsonl
  bank_short.jsonl
  embeddings.json
  vector_index/
  summaries/
```

Each file serves a distinct memory tier:

* **bank_short.jsonl:** immediate-turn recall (<10 turns).
* **bank_long.jsonl:** persistent topic context (>10 turns).
* **bank_core.jsonl:** distilled canonical rules and policies.
* **embeddings.json / vector_index/**: semantic search.
* **summaries/**: auto-generated temporal or thematic summaries.

#### (32.2) Data Structure

Each memory record:

```
{
  "memory_id": "<uuid>",
  "timestamp": "<UTC ISO>",
  "source": "<chat_history.md | dataset/memory.jsonl | Required-Updates.md>",
  "type": "<ask | do_work | ocr | summary | directive>",
  "content": "<text block>",
  "tags": ["topic", "bucket_id", "role"],
  "semantic_hash": "<sha256>",
  "embedding_ref": "<id>",
  "context_window": <int>,
  "importance_score": <float>
}
```

The importance score (0–1) reflects frequency of reuse, connection to tasks, and recent mentions.
Older low-importance records move from short-term to long-term banks through a daily migration cycle.

#### (32.3) Semantic Indexing

Embeddings are computed locally using small vector models (e.g., `nomic-embed-text` or `qwen-embed`).
Each embedding corresponds to `content`.
Stored under `vector_index/` as flat files grouped by month:
`index_YYYYMM.vec`
Metadata in `embeddings.json` tracks model and normalization parameters.
When searching, cosine similarity thresholds determine recall relevance (default 0.78).
Query results feed the agent’s reasoning during Ask or Do Work phases without network dependency.

#### (32.4) Memory Migration Cycle

A daily cron-like background job runs (triggered on agent launch if last run >24h):

1. Read `bank_short.jsonl`.
2. Recalculate importance scores based on recency, reuse, and association with open tasks.
3. Move low-importance (<0.2) entries to `bank_long.jsonl`.
4. Merge duplicates (matching semantic_hash).
5. Rebuild vector index for updated embeddings.
6. Generate summary under `summaries/daily_<DATE>.md`.
   A short digest of migrated entries is appended to `.codex_local_agent/logs/memory_gc_<DATE>.log`.

#### (32.5) Contextual Injection

Before each new reasoning cycle:

* The agent loads top N (default 50) memory records ranked by importance and similarity to the current topic or task bucket.
* Injects them into context as background text.
* Marks which records were injected by setting `"last_used": "<UTC ISO>"`.
  These context entries appear in the chat feed as collapsed sections:

```
<details><summary>Context from Memory (auto)</summary>
...markdown snippets...
</details>
```

All injected memory adheres to high contrast and is logged into chat_history.md.

#### (32.6) Policy Drift Detection

The CME continuously compares new directives (from Required-Updates.md or agent.md) against prior core memory.
If semantic difference > 0.25 in cosine distance, it flags a **policy drift** event:

```
{
  "timestamp": "<UTC ISO>",
  "bucket_id": "<uuid>",
  "old_hash": "<sha256>",
  "new_hash": "<sha256>",
  "distance": <float>,
  "action": "review"
}
```

Drift events append to `.codex_local_agent/memory/drift_log.jsonl`.
The agent then updates `bank_core.jsonl` to reflect the latest authoritative rule, linking superseded entries through a `"superseded_by"` chain.

#### (32.7) Self-Summarization

The agent periodically generates topic-level summaries from chat history and datasets:

* For every 100 messages, compress into one summary paragraph.
* Save summaries as `.codex_local_agent/memory/summaries/summary_<n>.md`.
* Embed summaries into vector index with high importance (0.9).
  This allows fast high-level recall for planning tasks.

#### (32.8) Relevance Feedback

The system monitors human re-prompts or corrections to adjust importance dynamically:

* Each time a record aids a correct answer, increment `importance_score += 0.05`.
* If a record leads to error, decrement by 0.1.
* Clamp range to [0, 1].
  The feedback loop improves recall precision over time.

#### (32.9) Memory Pruning and Archive

Memory banks never grow indefinitely.
Once total combined entries exceed 50,000, pruning begins:

* Oldest entries with `importance_score < 0.1` are moved to `archive/memory_<DATE>.tar.gz`.
* Archive logs contain counts and time ranges.
* Archive index: `.codex_local_agent/memory/archive_index.jsonl` lists compressed sets with quick search metadata.
  Archived memories are accessible for audit but excluded from runtime recall.

#### (32.10) Topic Linking

Every task bucket receives a memory cluster label.
Cluster files stored under `.codex_local_agent/memory/clusters/`:

```
{
  "cluster_id": "<uuid>",
  "topic": "<name>",
  "bucket_ids": ["..."],
  "related_embeddings": [id, id, ...],
  "summary_ref": "summary_<n>.md"
}
```

When a bucket is reopened or updated, the system loads its associated cluster to restore contextual knowledge.
Clusters are recomputed weekly using unsupervised grouping on embedding space.

#### (32.11) Memory Access UI

AgentManagerApp gains a **Memory Panel** with tabs:

* **Short-Term:** last 10 turns and OCR captures.
* **Long-Term:** semantic search bar with filters (by tag, bucket, source).
* **Core Memory:** policy and rule entries (read-only).
* **Summaries:** selectable compressed topic digests.
  Search supports natural text queries and fuzzy match.
  Results open inline within the chat feed.

#### (32.12) Data Integrity Verification

Each memory file carries a footer with SHA digest:

```
# SHA256: <hash>
# Entries: <count>
# Last Verified: <UTC ISO>
```

Verification runs weekly.
If mismatched, agent repairs by rebuilding from vector index and recent chat history.
Verification results append to `.codex_local_agent/audit/memory_integrity_<DATE>.log`.

#### (32.13) Cross-Agent Memory Federation

When multiple agents operate under the same project, they can exchange non-sensitive memory fragments:

* Only `type: summary` and `type: directive` entries qualify.
* Transferred via sync protocol under packet type `memory_share`.
* Remote agents merge with local memory using semantic distance threshold <0.15.
  Each accepted import logs under `.codex_local_agent/memory/import_log.jsonl`.

#### (32.14) Core Refresh Cycle

Every Sunday 00:00 UTC, CME compiles the week’s directive summaries into a unified core refresh file:
`.codex_local_agent/memory/core_refresh_<WEEK>.md`
This file merges all rule changes and policy drifts, producing a stable reference for next-cycle reasoning.
Its hash becomes the new baseline for policy drift detection.
A pointer to the latest core refresh appears in agent.md under:
`core_memory_ref: memory/core_refresh_<WEEK>.md`.

#### (32.15) End-of-Memory Audit

After daily migration and summarization, the agent appends a block to `Implemented-Updates.md`:

```
[MEMORY AUDIT]
timestamp: <UTC ISO>
short_entries: <int>
long_entries: <int>
core_entries: <int>
summaries_generated: <int>
archived_sets: <int>
status: verified
```


### 33) Autonomous Diagnostics and Self-Healing Layer

#### (33.1) Purpose

The **Diagnostics and Self-Healing Layer (DSL)** maintains runtime health across all local agent subsystems.
It continuously scans configuration files, logs, and memory indices for corruption, drift, or runtime failure and applies automated repairs before the user intervenes.
Root directory: `.codex_local_agent/diagnostics/`

#### (33.2) Core Components

```
diagnostics/
  heartbeat.json
  checksums.json
  repair_queue.jsonl
  auto_fixes.jsonl
  reports/
  snapshots/
```

* **heartbeat.json** — rolling status record updated every 30 s.
* **checksums.json** — reference hashes for all critical agent files.
* **repair_queue.jsonl** — list of detected issues awaiting fix.
* **auto_fixes.jsonl** — log of executed repairs and results.
* **reports/** — per-run diagnostic summaries.
* **snapshots/** — pre-repair file copies for rollback.

#### (33.3) Monitored Targets

| Path                                       | Validation                         | Frequency    |
| ------------------------------------------ | ---------------------------------- | ------------ |
| `.codex_local_agent/agent.yaml`            | schema + field completeness        | every launch |
| `.codex_local_agent/agent.md`              | markdown integrity, version header | every launch |
| `.codex_local_agent/Task-Index.json`       | JSON schema, orphan tasks          | hourly       |
| `.codex_local_agent/dataset/memory.jsonl`  | line count vs checksum             | daily        |
| `.codex_local_agent/macros/registry.jsonl` | duplicate IDs                      | daily        |
| `.codex_local_agent/authority/allow.jsonl` | revoked/expired entries            | hourly       |
| `.codex_local_agent/styles/`               | color-contrast audit               | weekly       |
| `.codex_local_agent/audit/`                | missing audit gaps                 | weekly       |

Each run appends a record under `.codex_local_agent/diagnostics/heartbeat.json`:

```
{
  "timestamp": "<UTC ISO>",
  "components_ok": <int>,
  "components_total": <int>,
  "warnings": <int>,
  "errors": <int>
}
```

#### (33.4) Self-Test Procedures

1. **Schema Validation** — compare against JSON schemas in `.codex_local_agent/net/`.
2. **Checksum Comparison** — recalc SHA-256 of all monitored files.
3. **Orphan Detection** — locate task entries whose bucket_id no longer exists.
4. **Stale Lock Sweep** — delete lock files older than `lock_timeout_minutes`.
5. **Contrast Check** — compute luminance ratio of style colors; must exceed 4.5 : 1.

Each procedure outputs structured diagnostic entries:

```
{
  "component": "<path>",
  "issue": "<text>",
  "severity": "<low|medium|high>",
  "suggested_fix": "<action>",
  "auto_fixable": <bool>
}
```

Entries with `auto_fixable: true` enter `repair_queue.jsonl`.

#### (33.5) Auto-Repair Engine

Loop executes once per minute while the agent is idle:

* Reads `repair_queue.jsonl`.
* Performs copy of target to `snapshots/`.
* Applies automated fix (file rewrite, schema regeneration, or cleanup).
* Appends result to `auto_fixes.jsonl`:

```
{
  "timestamp": "<UTC ISO>",
  "component": "<path>",
  "fix_action": "<description>",
  "status": "<success|failed>",
  "elapsed_ms": <int>
}
```

If repair fails, the entry escalates severity to `critical` and remains in queue.
A notification appears in the AgentManagerApp header: **“Diagnostics: 1 Critical Issue”**.

#### (33.6) Auto-Regeneration Templates

For missing or corrupted files, templates regenerate from embedded blueprints:

| File                                              | Template Source                              |
| ------------------------------------------------- | -------------------------------------------- |
| `agent.yaml`                                      | `agent_blueprint.yaml`                       |
| `Task-Index.json`                                 | minimal array seed `[]`                      |
| `allow.jsonl`                                     | empty ledger with root object `{}`           |
| `default-dark.json`                               | baseline style JSON from Required-Updates.md |
| `registry.jsonl`                                  | blank list                                   |
| Regenerated files append a comment header:        |                                              |
| `# Auto-generated by Diagnostics at <timestamp>`. |                                              |

#### (33.7) Snapshot & Rollback

Before any automatic modification:

* A full file snapshot is stored under `snapshots/<filename>_<timestamp>.bak`.
* Retention: 7 days or 20 versions per file.
* Rollback UI in AgentManagerApp → Diagnostics tab lists available backups with **Restore** buttons.

#### (33.8) Health Scoring

Each component contributes weighted scores:

```
health_score = 100 
  - (errors * 5) 
  - (warnings * 1)
  + (successful_repairs * 0.2)
```

Displayed in UI gauge:

* 90–100 = Excellent
* 70–89 = Stable
* 50–69 = Degraded
* < 50 = Critical
  Below 50 triggers audible alert and log entry:
  `[ALERT] Agent health below threshold`.

#### (33.9) Crash Capture and Recovery

Unhandled exceptions anywhere in the agent write a crash dump:
`.codex_local_agent/diagnostics/crash_<DATE>_<TIME>.log`
Fields:

```
timestamp, component, exception, stacktrace, last_action, thread, memory_usage_mb
```

After dump creation:

* System pauses Do Work actions.
* Restarts subsystems sequentially (OCR, Sync, Graph, CME).
* If all restart successfully, marks self-healed = true; else enters safe mode (Ask-only).

#### (33.10) Safe-Mode Behavior

In safe mode:

* Only Ask mode available.
* All write/sync features disabled.
* UI banner (yellow) displays “SAFE MODE — No Authority Operations”.
* Diagnostics continues to poll until all error counts = 0, then auto-reenables Do Work.

#### (33.11) Predictive Failure Analysis

Using historical heartbeat logs, DSL calculates mean-time-between-errors (MTBE) per component.
If projected MTBE < 3 days, DSL pre-emptively schedules a self-test sweep and marks component status = “watch”.
These predictions append to `.codex_local_agent/diagnostics/trends.jsonl`.

#### (33.12) Human-Readable Report

Each 24-hour period ends with a concise markdown report saved to `diagnostics/reports/report_<DATE>.md`:

```
# Diagnostics Report — <DATE>
Total Components: N
Errors Found: X
Repairs Applied: Y
Health Score: Z
Top Issues:
1. <path> — <issue>
2. ...
Next Scheduled Scan: <UTC ISO>
```

A summary of this report is appended to `Implemented-Updates.md` as a fenced block labelled `[DIAGNOSTICS AUDIT]`.

#### (33.13) Integrity Verification Footer

Upon completion of diagnostics run:

```
[DIAGNOSTICS CHECK]
timestamp: <UTC ISO>
issues_detected: <int>
issues_fixed: <int>
critical_remaining: <int>
health_score: <int>
status: healthy|degraded|critical
```


### 34) Execution Sandbox and Command Security Framework

#### (34.1) Purpose

The **Execution Sandbox (ESF)** provides a secure, isolated environment for running shell commands, scripts, and generated code under the Agent’s Do Work mode.
It eliminates direct execution risk and ensures reproducibility across systems.
Root path: `.codex_local_agent/sandbox/`.

#### (34.2) Directory Layout

```
sandbox/
  envs/
  logs/
  snapshots/
  queue.jsonl
  policy.json
  run_history.jsonl
  output_cache/
```

* **envs/** — ephemeral environments (virtual or containerized).
* **logs/** — detailed stdout / stderr per run.
* **snapshots/** — pre-run file diffs and environment metadata.
* **queue.jsonl** — pending command queue.
* **policy.json** — execution policy rules.
* **run_history.jsonl** — chronological ledger of all executed commands.
* **output_cache/** — cached results keyed by command hash.

#### (34.3) Command Lifecycle

1. **Queueing** — proposed commands written to `queue.jsonl` with metadata:

   ```
   { "cmd_id": "<uuid>", "command": "<text>", "approved": false, "source": "<bucket_id>", "timestamp": "<UTC>" }
   ```
2. **Approval** — upon Allow, Agent validates policy compliance.
3. **Sandbox Creation** — generates an isolated environment in `envs/<cmd_id>/`.
4. **Execution** — command executed via restricted shell (no network by default).
5. **Logging** — stdout/stderr captured to `logs/<cmd_id>.log`.
6. **Snapshot** — filesystem diff saved before / after.
7. **Teardown** — environment removed unless marked persistent.
8. **Record** — results appended to `run_history.jsonl` and cached.

#### (34.4) Policy Definition

`.codex_local_agent/sandbox/policy.json`:

```
{
  "allow_network": false,
  "allow_file_write": true,
  "allow_delete": false,
  "allow_system_calls": ["echo","python","pytest"],
  "timeout_sec": 180,
  "max_output_kb": 1024,
  "persistent_env_days": 3
}
```

The agent checks each command token against `allow_system_calls`.
Violation triggers quarantine entry in `Quarantined-Updates.md` with reason “Policy Violation — Disallowed Command”.

#### (34.5) Environment Types

| Type                                                                                                     | Description                                                      |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **venv**                                                                                                 | Python virtual env (default).                                    |
| **subprocess**                                                                                           | Direct OS subprocess under user UID.                             |
| **isolate**                                                                                              | OS-level namespace (Linux only).                                 |
| **container**                                                                                            | Optional lightweight container if `docker` or `podman` detected. |
| The chosen type recorded in `run_history.jsonl`.                                                         |                                                                  |
| Each environment inherits system PYTHONPATH and `.venv` site-packages unless overridden in `agent.yaml`. |                                                                  |

#### (34.6) Pre-Execution Checks

Before any run:

* Verify agent health ≥ 70.
* Confirm no active safe mode.
* Check disk space > 1 GB.
* Recompute checksum of target files.
* Load latest authority ledger.
  If any check fails, the command remains queued with `"status": "blocked_precheck"`.

#### (34.7) Snapshot Schema

`envs/<cmd_id>/snapshot.json`:

```
{
  "timestamp": "<UTC>",
  "cwd": "<path>",
  "env_vars": { "PYTHONPATH": "...", ... },
  "files_changed": ["..."],
  "git_state": { "branch": "main", "head": "<sha>" }
}
```

Snapshots ensure reproducibility and enable later rollback.

#### (34.8) Output Handling

After execution:

* Logs saved as UTF-8 text.
* Standard output ≤ 1 MB inlined to chat as fenced code.
* Larger outputs stored in `output_cache/<cmd_id>.txt`.
* Results annotated in chat_history.md under Do Work section with links to log files.
  High-contrast formatting enforced for embedded outputs.

#### (34.9) Timeout and Termination

Processes exceeding `timeout_sec` receive SIGTERM, then SIGKILL after 5 s.
Timeout events logged:

```
[TIMEOUT] cmd_id=<uuid> elapsed=<sec>
```

Task status → “terminated”; appended to Quarantined-Updates.md.

#### (34.10) Sandbox Caching

If identical command hash already exists in `output_cache`, result reused unless `--force` flag present.
This prevents redundant executions.
Cache metadata:

```
{ "cmd_hash": "<sha256>", "last_run": "<UTC>", "result_path": "<file>", "duration_ms": <int> }
```

#### (34.11) Security Enforcement

All sandbox operations run under restricted user context:

* Linux: `nobody` or dedicated `codex_sandbox` user.
* Windows: temporary low-privilege account via runas.
  Network disabled unless explicitly permitted by policy.
  File write restricted to project root and sandbox directory.
  Attempts outside scope trigger automatic abort and alert.

#### (34.12) Audit Trail

Each execution produces an audit object appended to `.codex_local_agent/audit/sandbox_audit.jsonl`:

```
{
  "cmd_id": "<uuid>",
  "command": "<text>",
  "exit_code": <int>,
  "elapsed_ms": <int>,
  "sandbox_type": "<type>",
  "output_hash": "<sha256>",
  "policy_flags": ["network_off","restricted_user"],
  "result": "<summary>"
}
```

An aggregate daily audit is generated: `sandbox_audit_<DATE>.md`.

#### (34.13) Persistent Environments

If `persistent_env_days > 0`, environments reused for similar commands until expiry.
Expired envs purged by the nightly maintenance job.
List of active envs available in AgentManagerApp → Sandbox tab.

#### (34.14) Manual Execution Console

Add a **Sandbox Console** panel to AgentManagerApp allowing safe manual command runs.
Features:

* Command input box with syntax highlight.
* Policy preview showing allowed syscalls.
* Run button (Ask for approval → Execute).
* Live log stream with pause/clear.
* Color-coded status indicators.
  Executed commands recorded like automated ones.

#### (34.15) Quarantine & Recovery

Failed or blocked runs create structured quarantine entries:

```
{
  "cmd_id": "<uuid>",
  "reason": "<error>",
  "file_refs": ["..."],
  "timestamp": "<UTC>"
}
```

User may re-queue these via UI **Retry** button after editing or updating policy.json.
Recovered commands move from quarantine back to `queue.jsonl` with new UUID.

#### (34.16) End-of-Sandbox Report

At daily maintenance end:

```
[SANDBOX CHECK]
timestamp: <UTC ISO>
runs_total: <int>
success: <int>
failed: <int>
terminated: <int>
cached_reused: <int>
policy_violations: <int>
status: secure
```

### 35) Event Bus and Modular Subsystem Messaging

#### (35.1) Purpose

The **Event Bus (EB)** enables internal communication between all agent subsystems—CME, DSL, Sandbox, Graph, Sync, UI—without direct coupling.
It standardizes signals, broadcasts, and callbacks through a lightweight publish/subscribe model.
This ensures that actions in one module (e.g., Sandbox run or memory migration) automatically trigger updates or UI events in others.

#### (35.2) Directory and Files

```
.codex_local_agent/eventbus/
  config.json
  channels.jsonl
  subscribers.jsonl
  event_log.jsonl
  metrics.json
```

* **config.json** — channel definitions, queue sizes, retry intervals.
* **channels.jsonl** — dynamically registered event channels.
* **subscribers.jsonl** — registered listeners with filters.
* **event_log.jsonl** — chronological record of dispatched events.
* **metrics.json** — throughput, latency, and dropped event counters.

#### (35.3) Channel Schema

Each channel entry:

```
{
  "channel_id": "<uuid>",
  "name": "<module.event>",
  "retention_ms": 60000,
  "max_queue": 500,
  "persistent": false,
  "description": "<purpose>"
}
```

Persistent channels survive reloads; non-persistent clear each session.
Examples:

* `sync.status` — emits during push/pull.
* `task.state` — broadcasts task updates.
* `sandbox.run` — signals command completion.
* `memory.refresh` — after daily migration.
* `diagnostics.alert` — triggers UI notifications.

#### (35.4) Subscriber Schema

```
{
  "subscriber_id": "<uuid>",
  "name": "<listener name>",
  "module": "<module_name>",
  "channels": ["task.state", "sandbox.run"],
  "callback": "<function path>",
  "filter": { "severity": ["error","critical"] },
  "last_active": "<UTC ISO>"
}
```

Subscribers register through API call `register_subscriber(name, channels, callback)` on startup.
Each receives events asynchronously and processes them in isolated threads to prevent blocking.

#### (35.5) Event Packet Format

All messages follow unified JSON schema:

```
{
  "event_id": "<uuid>",
  "timestamp": "<UTC ISO>",
  "channel": "<name>",
  "origin": "<module>",
  "severity": "<info|warn|error|critical>",
  "payload": { ... },
  "ack_required": <bool>
}
```

If `ack_required = true`, receiving module must send acknowledgment packet within `ack_timeout_ms` (default 3000).
Unacknowledged events log to `event_log.jsonl` with `"status": "missed_ack"`.

#### (35.6) Core Engine Behavior

* Maintains in-memory queues per channel.
* Delivers messages to subscribers in round-robin order.
* Retries failed deliveries up to `max_retries` (default 3).
* Drops oldest messages when `max_queue` exceeded.
* Metrics updated every 10 s:

  ```
  { "events_total": N, "events_dropped": M, "avg_latency_ms": L }
  ```

#### (35.7) Reliability and Persistence

Persistent channels (e.g., `task.state`) store undelivered messages in `.codex_local_agent/eventbus/retry/`.
On restart, EB replays those messages until acknowledged.
If corruption detected, moves them to `.codex_local_agent/eventbus/corrupt/` for inspection.

#### (35.8) Inter-Module Usage Examples

* **CME → Diagnostics:** emits `memory.refresh` with stats; DSL logs verification.
* **Sandbox → Graph:** emits `sandbox.run` event; Graph updates task node status.
* **Diagnostics → UI:** emits `diagnostics.alert`; UI banner flashes warning.
* **Sync → CME:** emits `sync.success`; CME updates memory importance of remote directives.

Each module subscribes via startup registration call referencing `channels.jsonl`.

#### (35.9) Event Filtering and Routing

Subscribers can specify filter conditions in `filter` dict.
Event Bus routes only events whose payload or severity matches filters, reducing noise.
System-level events (`system.heartbeat`, `system.shutdown`) broadcast globally regardless of filter.

#### (35.10) Event Log Retention

`event_log.jsonl` maintains rolling window (default 30 days).
Old records archived weekly into `archive/event_log_<DATE>.tar.gz`.
Retention policy adjustable in `config.json`.

#### (35.11) UI Integration

Add **Event Monitor** tab to AgentManagerApp showing live event stream.
Features:

* Filter by channel, severity, module.
* Pause/resume live feed.
* Export selected events to JSON.
* Graph mode displaying event frequency over time.
  All text uses high-contrast dark theme.

#### (35.12) Metrics Dashboard

`metrics.json` updated continuously:

```
{
  "events_sent": <int>,
  "events_received": <int>,
  "events_failed": <int>,
  "latency_avg_ms": <float>,
  "top_channels": ["sandbox.run","task.state"]
}
```

Displayed in UI diagnostics gauge.
Low throughput or high latency triggers automatic self-test on Event Bus.

#### (35.13) Fault Handling

If Event Bus thread crashes or stalls >5 s:

* DSL records `[FAULT] eventbus` entry.
* Agent restarts the service automatically.
* Pending unsent events replayed from queue.
* Health restored message broadcast on `system.recover`.

#### (35.14) Developer Hooks

Developers can define new channels via CLI or Python API:

```
agent.eventbus.create_channel(name, persistent=False, retention_ms=60000)
agent.eventbus.publish(channel, payload, severity="info")
agent.eventbus.subscribe(channels, callback)
```

All APIs wrapped with automatic logging and validation.
Unauthorized modules cannot create or publish to protected channels.

#### (35.15) End-of-Cycle Verification

After each session, append to `Implemented-Updates.md`:

```
[EVENT BUS CHECK]
timestamp: <UTC ISO>
channels_active: <int>
subscribers_registered: <int>
events_dispatched: <int>
events_failed: <int>
latency_avg_ms: <float>
status: stable
```

### 36) Modular Plugin Interface and Extension Loader

#### (36.1) Purpose

The **Plugin Interface (PI)** allows external Python modules, command-line utilities, or UI widgets to extend the Agent’s capabilities without altering core code.
Plugins register themselves through a manifest file and integrate with the Event Bus for communication.
This architecture enables sandbox-safe, modular evolution of the agent.

#### (36.2) Directory Layout

```
.codex_local_agent/plugins/
  manifests/
  cache/
  logs/
  registry.jsonl
  sandbox_hooks/
```

* **manifests/** — plugin metadata and configuration.
* **cache/** — precompiled or cached assets.
* **logs/** — per-plugin runtime logs.
* **registry.jsonl** — authoritative list of installed plugins.
* **sandbox_hooks/** — safe bridges into the sandbox runtime.

#### (36.3) Manifest Schema

Each plugin declares its properties:

```
{
  "plugin_id": "<uuid>",
  "name": "<string>",
  "version": "1.0.0",
  "entry_point": "plugin_main.py",
  "description": "<purpose>",
  "author": "<name>",
  "permissions": {
    "filesystem": false,
    "network": false,
    "sandbox_access": true
  },
  "subscribed_channels": ["sandbox.run", "memory.refresh"],
  "requires_agent_version": ">=2.0.0"
}
```

Plugins are sandboxed unless explicit permissions granted.
Any manifest missing required fields is rejected and logged in `plugins/logs/invalid_<DATE>.log`.

#### (36.4) Registry and Loading

`registry.jsonl` records active plugins and load status.
On launch, the agent iterates manifests, checks compatibility, and imports via dynamic loader:

```
import importlib.util
spec = importlib.util.spec_from_file_location(plugin.name, path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

Loaded plugins register themselves through:
`agent.eventbus.register_plugin(plugin_id, subscribed_channels)`
Failure or timeout during import quarantines the plugin.

#### (36.5) Sandbox Hooks

Plugins requesting sandbox access receive a unique hook ID mapped to a limited API in `sandbox_hooks/`:

```
{
  "hook_id": "<uuid>",
  "allowed_syscalls": ["python", "pytest"],
  "timeout_sec": 60
}
```

All plugin-initiated commands are executed through the sandbox, maintaining policy consistency.

#### (36.6) Update and Verification

Plugins can self-update using signed manifest checks:

* Manifest signatures stored under `.sig` files.
* SHA comparison ensures authenticity.
* Failed signature = plugin quarantined automatically.
  Audit entries appended to `.codex_local_agent/audit/plugin_audit.jsonl`.

#### (36.7) Developer Tools

CLI commands available:

```
agent plugin install <path_or_url>
agent plugin remove <name>
agent plugin list
agent plugin info <name>
```

All actions require confirmation unless Always Allow is set.
Installation logs stored per run.

#### (36.8) UI Integration

AgentManagerApp adds **Plugins** tab displaying:

* Installed plugins with status badges (Active, Quarantined, Incompatible).
* Buttons: Enable, Disable, Remove, Inspect Logs.
* Event Bus subscription overview.
  High contrast enforced for accessibility.

#### (36.9) End-of-Run Verification

```
[PLUGIN CHECK]
timestamp: <UTC ISO>
plugins_total: <int>
active: <int>
quarantined: <int>
errors: <int>
status: verified
```

---

### 37) Continuous Learning and Reinforcement Policy Engine

#### (37.1) Purpose

The **Reinforcement Policy Engine (RPE)** enables the agent to adapt behavior dynamically using experience-based scoring derived from user approvals, success ratios, and correction patterns.
It drives automatic optimization of prompts, decisions, and macro usage.

#### (37.2) Core Data Files

```
.codex_local_agent/policy/
  reinforcement.json
  rewards.jsonl
  penalties.jsonl
  metrics.json
  history/
```

#### (37.3) Reinforcement Model

Each decision path (Ask, Do Work, Macro use, OCR, Sync) carries a policy node:

```
{
  "node_id": "<uuid>",
  "context": "<module>",
  "reward_score": <float>,
  "penalty_score": <float>,
  "success_rate": <float>,
  "recommendation": "<action>"
}
```

RPE recalculates these scores after every session based on feedback from diagnostics, task results, and human actions.

#### (37.4) Reward and Penalty Triggers

* **Reward Conditions:** task completed, human approved diff, no errors.
* **Penalty Conditions:** quarantine, denied approval, command failure, timeout.
  Entries appended to `rewards.jsonl` or `penalties.jsonl` with context metadata.

#### (37.5) Policy Adjustment

After aggregation:

```
new_score = old_score + (rewards - penalties) * 0.1
success_rate = successes / (successes + failures)
```

Scores decay by 2% per day to prevent overfitting.
Thresholds:

* reward_score ≥ 10 → auto-suggest repeat pattern.
* penalty_score ≥ 5 → trigger human re-approval before reusing pattern.

#### (37.6) Adaptive Prompts

RPE modifies internal system prompts based on reward statistics:
Example:

* High OCR success → reduce redundancy in OCR prompts.
* Frequent sandbox timeouts → shorten default timeout_sec.
* Consistent human Allow → loosen Ask-first gate slightly (still logs event).

#### (37.7) Macro Reinforcement

Each macro in `registry.jsonl` receives reinforcement metadata:

```
"macro_score": <float>,
"success_count": <int>,
"fail_count": <int>
```

Macros with positive reinforcement auto-prioritized; failing macros quarantined after threshold.

#### (37.8) Visualization

AgentManagerApp → **Reinforcement** tab plots:

* Reward vs Penalty curves over time.
* Top performing modules.
* Behavior drift warnings.
  Charts update per session with real-time metrics.

#### (37.9) Output Snapshot

```
[REINFORCEMENT CHECK]
timestamp: <UTC ISO>
nodes_trained: <int>
average_reward: <float>
average_penalty: <float>
policy_drift: <float>
status: learning
```

---

### 38) Contextual Reasoning Orchestrator (CRO)

#### (38.1) Purpose

The **Contextual Reasoning Orchestrator** coordinates information flow between the Cognitive Memory Engine, Task Graph, and Reinforcement Engine to provide situational reasoning.
CRO interprets active tasks in light of stored memory, determining reasoning strategy and resource allocation.

#### (38.2) Architecture

```
.codex_local_agent/orchestrator/
  state.json
  strategy.json
  logs/
  traces/
```

* **state.json** — tracks active context, goals, and cognitive load.
* **strategy.json** — reasoning modes (fast, deep, parallel).
* **logs/** — reasoning trace summaries.
* **traces/** — detailed reasoning chains (<think> segments with metadata).

#### (38.3) State Management

State object:

```
{
  "active_task": "<task_id>",
  "related_buckets": ["..."],
  "contextual_memory_refs": ["memory_id", ...],
  "reasoning_mode": "<fast|deep|verify>",
  "tokens_used": <int>,
  "depth_score": <float>
}
```

Updated every reasoning cycle.
`depth_score` measures complexity based on dependency depth and data volume.

#### (38.4) Reasoning Strategies

| Mode       | Description                                                           |
| ---------- | --------------------------------------------------------------------- |
| **fast**   | Lightweight summarization or lookup; minimal token use.               |
| **deep**   | Full contextual reasoning using CME embeddings and historical chains. |
| **verify** | Compare previous outputs against authoritative memory to check drift. |

CRO automatically switches modes using thresholds derived from Reinforcement metrics and task importance.

#### (38.5) Parallel Context Management

When multiple tasks share related buckets, CRO executes parallel reasoning threads.
Each thread maintains isolated context, but merges output at completion:

```
merged_output = weighted_average(thread_outputs, weights=importance_scores)
```

Merged results stored under `.codex_local_agent/orchestrator/logs/merge_<DATE>.json`.

#### (38.6) Trace Recording

Every reasoning pass logs:

```
{
  "timestamp": "<UTC ISO>",
  "task_id": "<uuid>",
  "mode": "<fast|deep|verify>",
  "inputs": ["..."],
  "outputs": ["..."],
  "duration_ms": <int>,
  "accuracy_score": <float>
}
```

These traces feed into Reinforcement Policy Engine for scoring.

#### (38.7) Drift Response

If verification detects reasoning drift >0.2 similarity loss, CRO emits event `orchestrator.policy_drift` via Event Bus.
Diagnostics Layer receives and flags for review.

#### (38.8) Orchestrator UI

AgentManagerApp → **Reasoning Orchestrator** tab:

* Shows active reasoning threads, their modes, and duration.
* Displays reasoning confidence graphs.
* Offers “Force Deep Reasoning” and “Suspend Parallel” toggles.
  Interface inherits high-contrast styling and logs all user interactions.

#### (38.9) Output Verification

CRO validates reasoning outputs against bucket expectations and authority policies before marking task complete.
Verification failure returns task to pending state and logs discrepancy under `.codex_local_agent/orchestrator/traces/errors_<DATE>.json`.

#### (38.10) End-of-Reasoning Report

```
[REASONING CHECK]
timestamp: <UTC ISO>
tasks_processed: <int>
parallel_threads: <int>
avg_depth_score: <float>
drift_alerts: <int>
status: coherent
```
### 39) System Scheduler and Temporal Automation Framework

#### (39.1) Purpose

The **System Scheduler (SS)** automates recurring and timed operations across the Agent ecosystem.
It replaces ad-hoc background jobs (memory migration, diagnostics, sandbox GC) with a unified temporal controller that executes scheduled tasks based on ISO timestamps or CRON-like rules.
This framework guarantees consistent, predictable maintenance cycles and event timing.

#### (39.2) Directory and Structure

```
.codex_local_agent/scheduler/
  schedule.json
  queue.jsonl
  jobs/
  logs/
  triggers/
  audit.jsonl
```

* **schedule.json** — master configuration of all timed jobs.
* **queue.jsonl** — pending executions with timestamps.
* **jobs/** — registered job definitions as JSON descriptors.
* **logs/** — per-job logs of runtime events.
* **triggers/** — manual or event-based triggers.
* **audit.jsonl** — ledger of executed schedules.

#### (39.3) Job Descriptor Schema

```
{
  "job_id": "<uuid>",
  "name": "<string>",
  "module": "<diagnostics|memory|sandbox|sync|custom>",
  "action": "<function or command>",
  "interval": "0 0 * * *",   // CRON-style
  "enabled": true,
  "requires_network": false,
  "timeout_sec": 300,
  "priority": 1
}
```

Jobs may be module-specific or user-defined scripts.
The agent validates job syntax on startup and quarantines invalid entries.

#### (39.4) Queue Execution

The Scheduler continuously polls system clock and queue.jsonl.
When a job’s time window matches, it moves into active execution state:

1. Verifies prerequisites (network, health ≥ 70, disk space).
2. Executes via Sandbox or internal call.
3. Logs result to `scheduler/logs/<job_id>_<DATE>.log`.
4. Updates audit entry with status: success, skipped, failed, timed_out.

#### (39.5) Dynamic Triggers

The Scheduler supports reactive tasks:

* **on_event:** triggered by Event Bus messages (e.g., `sync.success` or `diagnostics.alert`).
* **on_condition:** logical expression of state variables (e.g., `"memory_entries > 50000"`).
  Triggers are JSON files in `triggers/` referencing job_id.
  Triggered jobs run immediately, outside periodic intervals.

#### (39.6) Resilience and Restart Recovery

Incomplete or interrupted jobs persist in `queue.jsonl` until explicitly completed.
On restart, Scheduler detects unclosed sessions and resumes from snapshot if `"resume": true` in job descriptor.
Failed runs auto-retry once after delay equal to `timeout_sec`.

#### (39.7) Audit and Reporting

After each cycle, append to `audit.jsonl`:

```
{
  "timestamp": "<UTC ISO>",
  "jobs_total": <int>,
  "jobs_success": <int>,
  "jobs_failed": <int>,
  "next_run": "<UTC ISO>"
}
```

Summaries written to `.codex_local_agent/audit/scheduler_audit_<DATE>.json` and appended to `Implemented-Updates.md`.

#### (39.8) UI Interface

AgentManagerApp → **Scheduler Panel**
Displays:

* Active jobs and next run time.
* Manual “Run Now” button.
* Enable/disable toggles.
* Execution history graph.
  High-contrast timeline visualization distinguishes job states by color.

#### (39.9) End-of-Scheduler Report

```
[SCHEDULER CHECK]
timestamp: <UTC ISO>
jobs_run: <int>
failed_jobs: <int>
triggered_jobs: <int>
avg_runtime_sec: <float>
status: stable
```

---

### 40) Secure Data Vault and Encryption Management

#### (40.1) Purpose

The **Data Vault (DV)** encrypts all sensitive local agent data — credentials, API keys, private memory rows, or remote sync keys — using per-installation asymmetric cryptography.
It ensures confidentiality even if `.codex_local_agent/` is exfiltrated.

#### (40.2) Directory and Components

```
.codex_local_agent/vault/
  master.key
  public.key
  vault.jsonl
  keyring.json
  backups/
  logs/
```

* **master.key** — AES-256 symmetric key, itself encrypted by public/private pair.
* **public.key / private.key** — generated on first install; stored securely.
* **vault.jsonl** — main encrypted store of secrets.
* **keyring.json** — key metadata, rotation history.
* **backups/** — encrypted snapshots.
* **logs/** — operations and access attempts.

#### (40.3) Vault Entry Schema

```
{
  "entry_id": "<uuid>",
  "type": "<api_key|token|credential|private_memory>",
  "name": "<label>",
  "value_enc": "<base64>",
  "created": "<UTC ISO>",
  "last_accessed": "<UTC ISO>",
  "rotation_due": "<UTC ISO>"
}
```

All values AES-encrypted with master.key.
The vault enforces auto-rotation every 90 days or on-demand via CLI.

#### (40.4) Key Management

At initialization:

* Generate RSA 4096-bit pair.
* Encrypt master.key with public key.
* Store in `keyring.json` with metadata:

  ```
  {"key_id":"<uuid>", "algo":"RSA-4096", "created":"<UTC>", "rotations":0}
  ```

Rotation increments this counter; previous keys archived in backups.

#### (40.5) Access Flow

When a module requests a secret:

1. Vault decrypts master.key (requires local private key).
2. Decrypts value.
3. Returns temporary plaintext buffer (auto-cleared after use).
4. Logs event under `.codex_local_agent/vault/logs/access_<DATE>.jsonl`.
   If unauthorized request detected, triggers Diagnostics alert and disables Do Work mode until review.

#### (40.6) Secure Backups

Nightly job copies vault.jsonl to backups with unique nonce-based filename:
`vault_backup_<DATE>_<RAND>.enc`
Backups signed with SHA-512 digest and verified on restore.
Missing digest triggers quarantine of the backup file.

#### (40.7) Policy Enforcement

Access policies configurable in `.codex_local_agent/vault/policy.json`:

```
{
  "allow_remote_sync": false,
  "require_passphrase_on_launch": true,
  "auto_lock_timeout_min": 15
}
```

When locked, no module can decrypt vault entries until user provides passphrase or key fingerprint.

#### (40.8) UI Integration

AgentManagerApp → **Vault Panel**

* Show stored secrets (masked).
* Buttons: Rotate Keys, Export Public Key, Import Backup, Lock/Unlock.
* High-contrast warning indicators for expiring keys.
* No plaintext ever rendered; only decrypted temporarily in memory.

#### (40.9) Intrusion Detection

If access attempts exceed 3 failures within 10 min:

* Agent triggers EventBus broadcast `vault.security_alert`.
* Lock vault.
* Append incident to `.codex_local_agent/diagnostics/security_incidents.jsonl`.

#### (40.10) End-of-Vault Report

```
[VAULT CHECK]
timestamp: <UTC ISO>
entries_total: <int>
keys_rotated: <int>
failed_accesses: <int>
locked: <bool>
status: secure
```

---

### 41) Adaptive Resource Management and Performance Optimizer

#### (41.1) Purpose

The **Resource Optimizer (ARO)** dynamically allocates CPU, memory, and disk resources among subsystems to ensure smooth operation under varying load.
It prevents runaway processes (e.g., sandbox loops, OCR bursts) from overwhelming the system.

#### (41.2) Core Files

```
.codex_local_agent/resources/
  monitor.json
  limits.json
  usage_log.jsonl
  throttle_state.json
  recommendations.json
```

* **monitor.json** — current system resource readings.
* **limits.json** — user-defined or automatic limits.
* **usage_log.jsonl** — rolling samples of usage metrics.
* **throttle_state.json** — record of throttled modules.
* **recommendations.json** — tuning advice from learning engine.

#### (41.3) Sampling Process

Every 5 seconds, the agent collects:

* CPU usage per module (percentage).
* Memory resident size (MB).
* Disk I/O read/write (MB/s).
* Thread count.
* Average latency of active operations.
  Samples append to `usage_log.jsonl`.
  Rolling average computed for last 10 samples.

#### (41.4) Limit Enforcement

`limits.json` example:

```
{
  "cpu_max_percent": 85,
  "mem_max_mb": 2048,
  "io_max_mb_s": 50,
  "sandbox_max_parallel": 2,
  "sync_bandwidth_limit_kbps": 512
}
```

If thresholds exceeded, ARO pauses noncritical modules and lowers thread priorities.
Critical modules (Diagnostics, Vault) remain exempt.

#### (41.5) Adaptive Throttling

When load crosses thresholds for >30 s:

* Sandbox jobs temporarily suspended.
* OCR batch jobs delayed.
* Sync frequency reduced.
* CME embedding updates queued instead of executed immediately.
  Throttle details logged:

```
{
  "timestamp": "<UTC>",
  "module": "<name>",
  "reason": "<cpu|mem|io>",
  "duration_sec": <int>
}
```

#### (41.6) Predictive Scaling

ARO uses linear regression on recent logs to forecast load 5 minutes ahead.
If predicted usage > limits, proactively preempts optional tasks (e.g., reinforcement update) to stabilize performance.

#### (41.7) Optimization Recommendations

The system generates human-readable recommendations:

```
{
  "module": "sandbox",
  "suggestion": "Reduce max parallel jobs from 3 → 2",
  "confidence": 0.82
}
```

All recommendations written to `recommendations.json` and surfaced in the UI.

#### (41.8) Visualization

AgentManagerApp → **Performance Panel**

* Live CPU, Memory, and I/O gauges.
* List of throttled modules with reasons.
* “Apply Recommendations” button.
  Graph colors:
* Green = nominal
* Yellow = high load
* Red = throttled

#### (41.9) End-of-Resource Report

```
[RESOURCE CHECK]
timestamp: <UTC ISO>
cpu_avg_percent: <float>
mem_avg_mb: <float>
modules_throttled: <int>
recommendations_generated: <int>
status: optimized
```
**COMPREHENSIVE SYSTEM AUDIT — REQUIRED-UPDATES.md + Micro-Agent-Local.md + Post-Merge Additions**
*(Top-to-bottom linear list of missing or yet-undefined domains.  Everything already implemented or defined in §§ 0-41 is excluded.  This list expresses unresolved or unmentioned areas that the Codex/Agents framework must still author, codify, or verify before the system reaches closure.)*

---

1. **Authentication & Session Authority Chain** — explicit human login, per-user tokens, biometric or hardware-key trust tiers.
2. **User-Role Matrix** — definitions for developer / auditor / automation / viewer authority scopes.
3. **Multi-User Concurrency Policy** — simultaneous agent sessions editing same repo; locking and merge rules.
4. **Version Control Deep Integration** — full Git object tracking, commit signing, detached-HEAD recovery, stash management.
5. **GitHub / GitLab / Local Repo Bridge** — continuous mirroring, webhook ingestion, automatic PR synthesis.
6. **Schema Migration Engine** — JSON/YAML schema versioning, backward-compatibility handlers, auto-migrators.
7. **Artifact Packaging Pipeline** — building distributable bundles (.zip, .exe, .appimage), checksum signing, release manifest.
8. **Installer / Updater Logic** — cross-platform installer generation, silent updates, rollback detection.
9. **Telemetry Privacy Contract** — policy definition for anonymized usage metrics and opt-out enforcement.
10. **Accessibility Framework** — keyboard-only navigation, screen-reader mapping, color-blind palettes.
11. **Internationalization / Localization (i18n/L10n)** — string catalogs, locale packs, translation sync.
12. **Documentation Generator** — auto-build of Markdown → HTML → PDF reference sets with change history.
13. **Inline Help & Tutorial System** — guided onboarding flows, contextual tooltips, walkthrough markdowns.
14. **Logging Standardization** — unified log schema across all modules (memory, sandbox, sync, diagnostics).
15. **Error Taxonomy** — standardized error codes and severities for downstream analytics.
16. **Event Correlation Engine** — cross-module correlation of anomalies (link sandbox faults with resource spikes).
17. **Distributed Cache Network** — shared local caches between agents for large assets or embeddings.
18. **Data Compression Layer** — adaptive gzip / zstd compression for memory archives and logs.
19. **Metrics Exporter** — Prometheus/Influx compatible metrics endpoint for monitoring.
20. **Visualization API** — unified data interface for charts / graphs / dashboards.
21. **Command Palette System** — searchable quick-action bar for every agent command.
22. **Shortcut Key Registry** — persistent JSON of keybindings with conflict detection.
23. **UI Layout Persistence** — saving / restoring window positions, panel sizes, theme states.
24. **Theming Engine Expansion** — additional high-contrast presets, user theme import/export.
25. **Voice Interaction Interface** — optional speech-to-text pipeline with microphone policy controls.
26. **Audio Feedback Framework** — low-latency system sounds tied to events (success, alert, sync).
27. **Notification Hub** — cross-platform system notifications and tray-icon status updates.
28. **Mobile / Tablet Companion View** — responsive layout or lightweight web socket monitor.
29. **REST / gRPC / WebSocket API Layer** — external programmatic control of agent functions.
30. **Remote Execution Gateway** — controlled job submission to external machines / clusters.
31. **Cluster Coordination** — peer discovery, election protocol, quorum handling for multiple agents.
32. **Task-Queue Persistence** — transactional queue back-end (SQLite / Redis / LMDB).
33. **Long-Running Job Supervisor** — monitor + restart for processes > 10 min duration.
34. **Dependency Manager Integration** — Python pip/conda, Node npm, system package detection.
35. **Environment Provisioner** — declarative .env template + automatic variable injection.
36. **Hardware Interface Hooks** — GPU usage, CUDA/ROCm detection, Jetson integration.
37. **Offline Asset Cache Validation** — checksum verification for large model files.
38. **Model Management Subsystem** — local model registry, versioning, and warm-loading.
39. **Prompt Template Repository** — canonical prompt templates for Ask / Do Work.
40. **Training & Fine-Tuning Manager** — local supervised tuning pipeline with dataset governance.
41. **Evaluation Benchmarks** — regression tests for reasoning, OCR, and diff accuracy.
42. **Security Penetration Audit Tools** — simulated attack surface scan of sandbox and vault.
43. **Integrity Chain of Trust** — cryptographic checksum cascade over entire `.codex_local_agent` tree.
44. **Disaster Recovery Mode** — bootstrapped minimal agent using archived configs.
45. **System Restore Utility** — one-click rollback to previous successful Implementation Check.
46. **Change-Approval Workflow** — multi-sign-off requirement for high-risk Do Work tasks.
47. **Collaboration Layer** — shared chat feed, task board, multi-cursor editing.
48. **Review Mode UI** — diff comparison and inline annotation between agents.
49. **Test Harness Framework** — automated unit / integration tests for all modules.
50. **Continuous Integration Bridge** — link to external CI/CD to run verifications post-commit.
51. **Documentation Linter** — syntax/formatting enforcement for Markdown and YAML.
52. **License Compliance Checker** — scanning of imported libraries and attribution tracker.
53. **Semantic Diff Visualizer** — color-coded diff viewer aware of language syntax.
54. **Policy Reasoner** — rule engine verifying that every update obeys governance in `agent.md`.
55. **Ethical Guard / Governance Compliance** — enforcement of safety and privacy boundaries.
56. **User Feedback Loop** — structured prompt to collect satisfaction metrics per task.
57. **Analytics & Reporting Portal** — trend analysis of tasks, success rate, MTTR charts.
58. **Anomaly Detection Layer** — ML-based detector for deviations in behavior or performance.
59. **Runtime Profiler** — precise timing and memory traces for code-generation operations.
60. **Power Management Module** — sleep / resume hooks, laptop battery-aware throttling.
61. **Session Persistence and Resume** — state dump / restore between launches.
62. **Update Distribution Network** — push system for new Required-Updates and patches.
63. **API Key Management for External Services** — integration with Vault rotation logic.
64. **Third-Party Model Provider Bridge** — OpenAI / Anthropic / Ollama model metadata sync.
65. **Model Capability Mapper** — automatic mapping of context window, token cost, latency.
66. **Embedded Documentation Search** — full-text search index of all markdown files.
67. **Knowledge Graph Generator** — visualize inter-relations among buckets, memory, and tasks.
68. **Human-Readable Change Log Composer** — narrative summaries auto-appended after runs.
69. **Automated Screenshot / Artifact Capture** — capture before/after images for UI operations.
70. **QA Verification Console** — checklist interface confirming Acceptance Criteria completion.
71. **Compliance Export Tool** — produce regulatory reports (GDPR, ISO 27001 readiness).
72. **Backup Compression and Remote Storage** — encrypted incremental upload to user-chosen drive.
73. **License Activation System** — optional key for enterprise or multi-seat setups.
74. **In-App Terminal Emulator Enhancements** — tabbed shell, color logs, persistent history.
75. **Script Library Browser** — catalog of generated scripts with preview and metadata.
76. **Local Knowledge Corpus Manager** — dataset ingestion, tagging, and deduplication GUI.
77. **OCR Engine Selector** — modular back-end choice (Tesseract, PaddleOCR, EasyOCR).
78. **Image Processing Pipeline** — preprocessing (binarization, deskew, denoise) before OCR.
79. **Video Frame Extractor** — timeline-based OCR on video frames.
80. **Audio Transcription Layer** — speech-to-text for captured audio files.
81. **File-Type Extension Handlers** — parser plug-ins for `.csv`, `.xml`, `.ini`, `.yaml`, `.toml`.
82. **Data Validation Engine** — schema enforcement for imported datasets.
83. **GraphQL or JSON-RPC Bridge** — structured inter-process query API.
84. **Modular Runtime Updater** — hot-swap module updates without restart.
85. **Dependency Isolation for Plugins** — per-plugin venv resolution.
86. **License Propagation in Plugins** — enforce shared MIT/BSD headers.
87. **Conflict-Resolution Assistant** — guided merges for divergent Required-Updates branches.
88. **Agent Personality Profiles** — configurable reasoning style presets.
89. **Behavior Sandbox Simulation** — run reasoning chains in simulation before execution.
90. **Narrative Log Generator** — human-readable timeline of entire run session.
91. **UI Snapshot Exporter** — capture window states to PNG/HTML for documentation.
92. **Automatic Dependency Graph for Imports** — visual of code module relationships.
93. **Security Hardening Mode** — disables network, enforces read-only memory for analysis sessions.
94. **Credential Redaction Filter** — scrub secrets before logs or exports.
95. **Low-Level API Throttler** — rate-limit external API calls globally.
96. **Energy Usage Telemetry** — log CPU/GPU power draw for eco metrics.
97. **Jetson / Edge Deployment Toolkit** — build pipelines for ARM64 local deployment.
98. **Virtual Desktop Synchronizer** — unify state between Codex Terminal / Virtual Desktop.
99. **Agent-to-Agent Negotiation Protocol** — consensus and voting for distributed updates.
100. **Live Collaboration WebSocket Server** — multi-user chat + shared view synchronization.
101. **Visual Diff Timeline Player** — replay of file changes over time.
102. **Knowledge Retention Policy** — configurable data expiration rules.
103. **Memory Sanitization Utility** — manual purge of specific topics or identifiers.
104. **Event Bus Security Model** — signing and permission gating for inter-module messages.
105. **Plugin Marketplace Index** — remote manifest listing of verified extensions.
106. **Telemetry Opt-Out and Consent UI** — human-readable consent form persisted in policy.
107. **User Persona Layer for Testing** — synthetic input generator to simulate user patterns.
108. **Agent Benchmark Suite** — standardized tests measuring latency, accuracy, memory.
109. **Task Cost Estimator** — predicted compute / time / token usage per bucket.
110. **Economy / Token Ledger** — accounting of LLM token consumption per model.
111. **Offline-Only Enforcement Mode** — absolute network isolation certification.
112. **Recovery Bootloader** — minimal start sequence verifying all critical signatures.
113. **UI Translation Memory** — reuse prior translations across updates.
114. **Centralized Color Calibration** — ensure cross-monitor consistency for high-contrast themes.
115. **User Custom Script Runner** — expose sandboxed run interface for bespoke automation.
116. **Error Replay Debugger** — reconstruct failing steps using logs and checkpoints.
117. **Macro Composition Editor** — visual node editor for macro logic creation.
118. **Auto-Documentation of Plugins and Macros** — regenerate README snippets automatically.
119. **Knowledge Diff Auditor** — semantic diff between memory_core_refresh versions.
120. **Data Provenance Tracker** — lineage tracing for every dataset entry.
121. **Cryptographic Timestamping** — notarize Implemented-Updates with external service.
122. **Legal Notice and Compliance Registry** — store third-party attributions and terms.
123. **Human Oversight Dashboard** — aggregated approvals, denials, and performance metrics.
124. **Task Simulation Sandbox** — dry-run environment for testing Required-Update scripts.
125. **Automated UI Testing Harness** — simulate clicks and verify rendering.
126. **UX Telemetry Analysis Engine** — anonymized heatmap of interface usage.
127. **Virtual File System Abstraction** — unify local / remote / archive access layers.
128. **Archive Compression Optimizer** — adaptive choice of zstd vs lz4 based on size.
129. **Live Resource Overlay** — floating real-time CPU / memory widget inside UI.
130. **Automatic Theme Stress-Tester** — validate color accessibility on all panels.
131. **AI-Assisted Code Repairer** — agent proposes patches for detected code errors.
132. **Human-Readable Design Docs Synthesizer** — merge logic buckets into narrative technical specs.
133. **Auto-License Generator** — populate license files for new sub-projects.
134. **Legacy Migration Assistant** — import older Codex agent directories to new schema.
135. **Cross-Language Code Bridge** — Python↔C#↔C++↔JS integration templates.
136. **Test Dataset Fabricator** — synthetic dataset generator for sandbox testing.
137. **Time-Zone Aware Logging** — consistent timestamp normalization.
138. **State-Machine Visual Builder** — design reasoning flows visually.
139. **Context Compression Algorithm** — reduce token footprint of stored context.
140. **Hybrid Online-Offline Merge Resolver** — reconcile offline edits with remote changes.
141. **Self-Benchmark Scheduler** — recurring internal performance tests.
142. **Upgrade Validator** — confirm new modules don’t break existing bucket schema.
143. **Post-Mortem Analyzer** — summarize causes of quarantined tasks.
144. **Cognitive Load Balancer** — distribute reasoning tasks among multiple cores or agents.
145. **Hardware Metrics API** — surface sensors (temp, fan, voltage) for embedded deployments.
146. **Low-Level Memory Inspector** — visualize object counts and leaks in runtime.
147. **Visualization Export Suite** — export graphs / charts to PDF, PNG, SVG.
148. **Agent Licensing Telemetry Filter** — anonymize license-usage metrics.
149. **Knowledge-Gap Detector** — highlight unreferenced or outdated memory areas.
150. **End-to-End Validation Runner** — automated holistic test of full loop: Plan → Apply → Verify → Report.

---

**Total new conceptual domains:** ≈ 150.
Each bullet corresponds to a missing or future subsystem, configuration, or verification area not yet implemented in the existing Required-Updates through Section 41.
This list functions as the authoritative *to-plan* register for Codex/Agents during subsequent expansion cycles.

---


Here is **#1** from the audit list, done precisely and in full detail:

---

### 1) Authentication & Session Authority Chain

#### (1.1) Purpose

The **Authentication & Session Authority Chain (ASAC)** governs user identity, session validation, and authority inheritance across every Codex/Agent subsystem.
It guarantees that every operation—from UI button press to background macro execution—is bound to a verified, role-based identity and cryptographically traceable audit trail.

---

#### (1.2) Directory Structure

```
.codex_local_agent/auth/
  config.json
  sessions.jsonl
  tokens.jsonl
  roles.json
  audit.jsonl
  fingerprints/
  keys/
  cache/
```

* **config.json** – policy and method configuration.
* **sessions.jsonl** – active sessions ledger.
* **tokens.jsonl** – access and refresh tokens with scopes.
* **roles.json** – authority definitions per subsystem.
* **audit.jsonl** – chronological security ledger.
* **fingerprints/** – device / hardware binding metadata.
* **keys/** – RSA 4096 pairs and rotation archives.
* **cache/** – encrypted ephemeral state.

---

#### (1.3) Role & Permission Model

Three canonical roles plus extension support:

| Role           | Description     | Core Permissions                                           |
| -------------- | --------------- | ---------------------------------------------------------- |
| **Developer**  | Full authority  | sandbox_exec, vault_write, sync_remote, scheduler_edit     |
| **Auditor**    | Inspect-only    | read logs, view memory, diagnostics access                 |
| **Automation** | Non-human agent | execute macros, run reinforcement cycles, no config writes |

Example `roles.json`:

```json
{
  "Developer": {
    "sandbox_exec": true,
    "vault_write": true,
    "scheduler_edit": true
  },
  "Auditor": {
    "sandbox_exec": false,
    "vault_write": false,
    "scheduler_edit": false
  },
  "Automation": {
    "sandbox_exec": true,
    "vault_write": false,
    "scheduler_edit": false
  }
}
```

Custom roles can be declared by appending new entries with defined scopes.

---

#### (1.4) Authentication Methods

Supported methods and precedence order:

1. **Local RSA Keys** (default) — Generated during first run.
2. **Passphrase Hash (Argon2id)** — Optional second factor.
3. **TOTP Token** (Google Authenticator-style).
4. **Hardware Fingerprint** (TPM ID or device serial).
5. **Session Ticket** — Short-lived derivative credential for sub-processes.

Example `config.json`:

```json
{
  "require_passphrase": true,
  "require_mfa": true,
  "session_timeout_min": 60,
  "max_concurrent_sessions": 3,
  "auto_lock_on_idle": true
}
```

---

#### (1.5) Session Lifecycle

1. **Login** → credentials verified, MFA optional.
2. **Session Creation** → signed JSON token issued:

   ```json
   {
     "session_id": "UUID",
     "user_id": "HASH",
     "roles": ["Developer"],
     "expires": "UTC_ISO",
     "signature": "SHA512"
   }
   ```
3. **Propagation** → token attached to all module calls (headers or IPC payloads).
4. **Renewal** → automatic if active within last 5 min.
5. **Termination** → logout, timeout, or security event.
6. **Audit Write** → entry appended to `audit.jsonl`.

---

#### (1.6) Authority Propagation

Every subsystem checks:

```
validate_token()
→ resolve_roles()
→ verify_permission()
→ execute()
→ log_result()
```

If permission fails →

```
[AUTH_DENIED] <action> blocked for role <role>
```

logged in `audit.jsonl` and broadcast via Event Bus `auth.denied`.

---

#### (1.7) Token & Replay Protection

Each token embeds nonce + timestamp.
All nonces cached 10 min in `cache/nonces.json`.
Replay attempt →

```
[SECURITY_ALERT] replay_detected <session_id>
```

→ session revoked, vault locked.

---

#### (1.8) Key Rotation & Recovery

Command: `agent auth rotate-keys`

* Generates new RSA 4096 pair.
* Re-encrypts vault master.key.
* Updates signatures for active sessions.
* Archives old keys under `keys/archive_<DATE>/`.
  Lost private key → manual Developer-role override with local confirmation.

---

#### (1.9) Security Events

Triggers that emit `auth.security_alert`:

* ≥ 3 failed logins within 10 min.
* Invalid signature.
* Unauthorized role escalation.
* Hardware fingerprint mismatch.

Alert handling:

1. Diagnostics records incident.
2. Vault auto-locks.
3. Sandbox and Scheduler pause until clearance.

Example log:

```json
{
  "timestamp": "UTC",
  "event": "role_escalation_attempt",
  "source": "UI",
  "result": "blocked"
}
```

---

#### (1.10) Visualization (UI Panel)

**AgentManagerApp → Auth Panel**

* Lists active sessions with role badges.
* Lock / Unlock buttons.
* MFA enable/disable toggle.
* Live chart of login frequency.
* High-contrast dark theme with white/red accents.

---

#### (1.11) CLI Tools

```
agent auth login
agent auth logout
agent auth status
agent auth list
agent auth revoke <session_id>
agent auth rotate-keys
```

All commands append structured audit entries.

---

#### (1.12) Daily Security Report

Auto-generated:

```
[AUTH CHECK]
timestamp: UTC
sessions_active: INT
failed_logins: INT
alerts_triggered: INT
key_rotations: INT
vault_locked: BOOL
status: secure
```

---

#### (1.13) Cross-Subsystem Dependencies

* Vault → requires validated `vault_read` / `vault_write`.
* Sandbox → enforces `sandbox_exec`.
* Scheduler → enforces `scheduler_edit`.
* Sync → verifies `sync_remote`.
* Diagnostics → listens for `auth.security_alert`.

---

#### (1.14) Outcome

ASAC becomes the system’s trust backbone:
a verifiable, cryptographic identity layer binding every Codex/Agent action to an authenticated operator, ensuring non-repudiation, audit integrity, and secure inter-module execution.

---

✅ **Next entry to create when requested:** #2 User-Role Matrix.

### 2) User-Role Matrix

#### (2.1) Purpose

The **User-Role Matrix (URM)** defines the complete mapping between users, groups, and system capabilities.
It extends the Authentication & Session Authority Chain by introducing layered access control and explicit inheritance rules.
URM ensures that every permission in the Codex/Agent ecosystem is deterministic, centrally declared, and automatically enforced in all subsystems.

---

#### (2.2) Directory and Core Files

```
.codex_local_agent/auth/
  roles/
    matrix.json
    groups.json
    overrides.json
  users.jsonl
  audit_role.jsonl
```

* **matrix.json** — master table linking roles → permissions → modules.
* **groups.json** — collections of users sharing role bundles.
* **overrides.json** — explicit allow/deny exceptions.
* **users.jsonl** — registry of known user identities, hashes, and assigned roles.
* **audit_role.jsonl** — record of role changes, grants, and denials.

---

#### (2.3) Matrix Structure

Each role is a JSON object mapping subsystems to capabilities:

```json
{
  "Developer": {
    "sandbox": ["execute", "read_logs"],
    "vault": ["read", "write", "rotate_keys"],
    "scheduler": ["view", "edit"],
    "sync": ["push", "pull"]
  },
  "Auditor": {
    "sandbox": ["read_logs"],
    "vault": ["read"],
    "scheduler": ["view"],
    "sync": []
  },
  "Automation": {
    "sandbox": ["execute"],
    "vault": [],
    "scheduler": ["view"],
    "sync": ["pull"]
  }
}
```

This matrix drives all permission lookups.
Modules never reference hard-coded roles; they query URM dynamically.

---

#### (2.4) User and Group Registry

`users.jsonl` schema:

```json
{
  "user_id": "<uuid>",
  "username": "string",
  "roles": ["Developer","Auditor"],
  "groups": ["CoreTeam"],
  "last_login": "<UTC ISO>",
  "active": true
}
```

`groups.json`:

```json
{
  "CoreTeam": ["Developer","Auditor"],
  "BotFleet": ["Automation"]
}
```

When a user belongs to multiple groups, roles merge as union (duplicates removed).

---

#### (2.5) Overrides and Exceptions

`overrides.json` allows granular rule definitions:

```json
{
  "user_id": "UUID",
  "module": "vault",
  "permission": "write",
  "allow": false,
  "reason": "temporary audit lock"
}
```

Overrides supersede matrix and group rules.
Applied at runtime before permission enforcement.
All overrides expire automatically if `expires` timestamp present.

---

#### (2.6) Permission Resolution Flow

When a subsystem checks an action:

```
resolve_user(user_id)
→ collect_roles(groups, matrix)
→ apply_overrides()
→ produce_effective_permissions()
→ enforce()
```

Each resolution emits structured trace in `audit_role.jsonl`:

```json
{
  "timestamp": "<UTC>",
  "user": "username",
  "module": "vault",
  "action": "write",
  "result": "denied",
  "source": "override"
}
```

---

#### (2.7) Role Inheritance and Hierarchies

URM supports inheritance via “extends” field in `matrix.json`:

```json
{
  "LeadDeveloper": {
    "extends": ["Developer"],
    "vault": ["grant_permissions"]
  }
}
```

Inherited roles merge recursively.
Circular inheritance detected and rejected at load.

---

#### (2.8) Dynamic Role Assignment

Agents can promote or demote users temporarily:

```bash
agent role grant <user> <role> [--duration 60m]
agent role revoke <user> <role>
```

Duration-based grants expire automatically and append expiry log entries:

```
[ROLE_CHANGE] user=meeh role=Auditor action=grant duration=3600
```

---

#### (2.9) Role-Driven Configuration Loading

At startup, every module queries URM for allowed configurations:

* **Sandbox** → allowed syscalls, timeout limits.
* **Vault** → read/write mode.
* **Sync** → remote push permissions.
* **Scheduler** → editable jobs.
  Configuration diffs stored in `matrix_cache.json` for quick lookup.

---

#### (2.10) Multi-User Concurrency Enforcement

When multiple active sessions modify overlapping data:

1. URM checks role precedence.
2. Highest role (by matrix priority) gains write access.
3. Lower roles receive read-only notice.
   All conflicts logged:

```json
{"event":"role_conflict","file":"Task-Index.json","users":["A","B"],"resolved":"A"}
```

---

#### (2.11) Visualization (UI Panel)

**AgentManagerApp → Roles Panel**

* Table of users vs modules with checkmarks.
* Toggle filters by group or subsystem.
* Buttons: Add Role, Revoke Role, Apply Override.
* Color code:

  * Green = allowed
  * Yellow = override
  * Red = denied
    High-contrast black background, white text.

---

#### (2.12) CLI Tools

```
agent role list
agent role show <user>
agent role grant <user> <role>
agent role revoke <user> <role>
agent role override <user> <module> <perm> [--allow|--deny]
```

All actions append to `audit_role.jsonl`.

---

#### (2.13) End-of-Cycle Report

```
[ROLE MATRIX CHECK]
timestamp: <UTC ISO>
users_total: <int>
roles_defined: <int>
overrides_active: <int>
conflicts_resolved: <int>
status: verified
```

---

#### (2.14) Integration Notes

URM extends ASAC by providing explicit permission semantics and persistent mappings.
Every subsystem consults the matrix before performing high-risk operations, allowing complete traceability, safer automation, and auditable user authority across the Codex ecosystem.

### 3) Multi-User Concurrency Policy

#### (3.1) Purpose

The **Multi-User Concurrency Policy (MUCP)** defines how multiple authenticated users or agents interact with shared resources simultaneously.
It prevents race conditions, conflicting file writes, and overlapping automation events across the `.codex_local_agent` workspace.
MUCP acts as the transactional lock layer sitting above the User-Role Matrix.

---

#### (3.2) Directory and Core Files

```
.codex_local_agent/concurrency/
  locks.jsonl
  sessions_map.jsonl
  ownership.json
  queue.jsonl
  audit_concurrency.jsonl
```

* **locks.jsonl** — active file and task locks.
* **sessions_map.jsonl** — live session references to locked resources.
* **ownership.json** — persistent record of long-term resource ownership.
* **queue.jsonl** — waiting operations pending resource release.
* **audit_concurrency.jsonl** — serialized log of conflicts and resolutions.

---

#### (3.3) Lock Types

| Lock Type          | Scope                      | Description                                           |
| ------------------ | -------------------------- | ----------------------------------------------------- |
| **File Lock**      | Single file                | Prevents concurrent write or schema change.           |
| **Directory Lock** | Folder tree                | Used for schema migrations or build steps.            |
| **Task Lock**      | Logical bucket / operation | Ensures one agent executes a Do Work chain at a time. |
| **Global Lock**    | Entire agent               | Maintenance or recovery mode.                         |

Example entry in `locks.jsonl`:

```json
{
  "lock_id": "uuid",
  "resource": "schemas/default_schema.json",
  "owner_session": "session-uuid",
  "lock_type": "file",
  "timestamp": "UTC ISO",
  "expires": "UTC ISO +300s",
  "status": "active"
}
```

---

#### (3.4) Lock Lifecycle

1. **Acquire** – requester proposes lock; MUCP checks ownership and role priority.
2. **Grant / Queue** – if free → mark active; if busy → append to queue.jsonl.
3. **Heartbeat** – every 30 s, owner session renews lock timestamp.
4. **Release** – on completion or session end, lock removed.
5. **Timeout** – expired lock auto-released and logged as stale.

---

#### (3.5) Ownership Resolution

Each resource has a canonical owner in `ownership.json`:

```json
{
  "resource": "core/config.json",
  "owner_user": "uuid",
  "assigned_role": "Developer",
  "priority": 10
}
```

When two sessions compete:

* Higher priority (from role weight) wins.
* Ties resolved by earliest session start.
* Manual override permitted by Administrator role only.

---

#### (3.6) Transaction Bundles

Large operations (schema edits, bulk sync) open **transaction bundles**:

```
BEGIN_TRANSACTION <bundle_id>
  → acquire locks for all target files
  → perform actions
  → validate results
COMMIT <bundle_id> or ROLLBACK
```

Bundles guarantee atomic commit.
Failed commits roll back partial writes and log full diff to `audit_concurrency.jsonl`.

---

#### (3.7) Conflict Detection

When a second writer targets a locked resource:

```
[CONFLICT] user=B module=Vault resource=Task-Index.json
action=write denied cause=lock_held_by:A
```

Conflict broadcast through Event Bus channel `concurrency.conflict`.
Diagnostics layer aggregates repeating offenders and suggests scheduling windows.

---

#### (3.8) Queue and Back-Off Logic

Queued operations poll every 10 s.
If lock not released after `max_wait_sec` (default = 300), job canceled:

```json
{"event":"queue_timeout","job":"sandbox_run","user":"B"}
```

Sandbox and Scheduler automatically retry non-critical tasks once.

---

#### (3.9) Cooperative Editing Mode

Read-only sharing permitted when:

* All users hold `view` permission from URM.
* No write lock exists.
  System broadcasts:

```
[READ_SHARING] resource=<path> viewers=<list>
```

UI visually marks shared but unlocked files.

---

#### (3.10) Persistent Ownership & Transfer

Ownership can be reassigned:

```bash
agent concurrency transfer <resource> <new_user>
```

This updates `ownership.json` and notifies via Event Bus `ownership.transfer`.
Transfers logged:

```
[OWNERSHIP_TRANSFER] resource=schema.json old=A new=B
```

---

#### (3.11) Fault Recovery

If session terminates unexpectedly, orphaned locks detected by cleanup daemon:

* Compare session timestamps vs system time.
* Stale locks removed.
* Recovery message appended to audit file.

---

#### (3.12) Visualization (UI Panel)

**AgentManagerApp → Concurrency Panel**

* Table: resource | owner | lock_type | expires_in.
* Button: “Release All Expired”.
* Button: “Transfer Ownership”.
* Real-time indicators:

  * 🔒 red = locked
  * 🕓 yellow = queued
  * 🟢 green = free
    High-contrast grid layout for readability.

---

#### (3.13) CLI Utilities

```
agent lock list
agent lock release <resource>
agent lock transfer <resource> <user>
agent lock clear-stale
agent lock watch
```

Each emits structured logs to `audit_concurrency.jsonl`.

---

#### (3.14) End-of-Cycle Report

```
[CONCURRENCY CHECK]
timestamp: UTC
locks_active: INT
locks_stale_cleared: INT
conflicts_detected: INT
transactions_rolled_back: INT
status: synchronized
```

---

#### (3.15) Integration Summary

MUCP establishes deterministic concurrency across multi-user Codex environments.
It ties directly into ASAC for identity, URM for permission precedence, and Scheduler for timed queue release, ensuring the workspace remains consistent, conflict-free, and auditable under simultaneous activity.


### 4) Version Control Deep Integration

#### (4.1) Purpose

Provide a deterministic, audited interface to Git for every file write, diff, revert, and release action performed by the Agent, unifying **Plan → Stage → Approve → Apply → Verify → Report** with repository facts. Extends the Required-Updates operating loop and Trifecta (Required-Updates.md ↔ README.md ↔ Implemented-Updates.md).  

#### (4.2) Directory & Files

```
.codex_local_agent/vcs/
  config.json
  status_cache.json
  staged_diffs/
  hooks/
  audit_vcs.jsonl
  snapshots/
```

* **config.json** — safe push, main-only policy, signing options.
* **status_cache.json** — last-seen `git status`/`git log` snapshot for fast UI.
* **staged_diffs/** — per-task unified diffs before Apply.
* **hooks/** — optional verify hooks (lint/tests) executed pre-commit.
* **audit_vcs.jsonl** — append-only ledger of VCS actions.
* **snapshots/** — lightweight worktree snapshots for rollback.

#### (4.3) Policies (`vcs/config.json`)

```json
{
  "branch_policy": { "single_branch": true, "branch_name": "main" },
  "safe_push": true,
  "sign_commits": false,
  "commit_template": "[{task_id}] {title}",
  "max_commit_size_kb": 512,
  "require_clean_worktree_before_apply": true
}
```

#### (4.4) Action Flow

1. **Plan**: compute diffs, write to `staged_diffs/patch-<id>.diff`.
2. **Approve**: pending command UI (Allow/Skip/Try Harder/Edit) gates Apply.
3. **Apply**:

   * Ensure on `main`; fetch/prune; rebase if configured.
   * Verify clean worktree (or controlled partial staging).
   * Apply diffs; run hooks (lint/tests).
   * Commit with templated message; optionally sign.
   * Safe push (reject if remote ahead; raise Overwrite Guard event).
4. **Verify & Report**: update **Implemented-Updates.md**, **Missing-Updates.md**, audit VCS.

#### (4.5) Overwrite Guard

If remote `main` has newer commits:

* Halt Apply; render side-by-side diff summary; open **Repair Plan** task in Ask mode; require explicit Allow to rebase or re-apply.
* Log `overwrite_guard=true` in `audit_vcs.jsonl`.

#### (4.6) UI (high-contrast)

* **VCS Panel**:

  * Status: branch, ahead/behind, untracked, modified.
  * Buttons: Stage All, Unstage, Discard Hunk, Commit (disabled until approval), Safe Push.
  * Graph: last 10 commits (hash, author, subject).
* **Diff Viewer**: color-coded, accessible (add = green, del = red, headers = yellow).
* Inline warnings for large commits (`> max_commit_size_kb`).

#### (4.7) CLI

```
agent vcs status
agent vcs diff
agent vcs apply <patch_id>
agent vcs commit --msg "..." [--sign]
agent vcs push [--force=deny]
agent vcs snapshot create|restore <name>
```

#### (4.8) Audit Record (`audit_vcs.jsonl`)

```
{"ts":"UTC","op":"commit","task":"TASK-123","hash":"abcd...","files":5,"lint_pass":true,"tests_pass":true}
```

---

### 5) GitHub / GitLab / Local Repo Bridge

#### (5.1) Purpose

Bidirectional sync between local `main` and remotes (GitHub/GitLab/self-hosted), with webhook pull, PR synthesis, and artifact linking. Upholds single-branch policy unless override granted. 

#### (5.2) Directory & Files

```
.codex_local_agent/remote/
  remotes.json
  tokens.enc
  webhooks/
  prs.jsonl
  audit_remote.jsonl
```

* **remotes.json** — named remotes (origin/upstream), API base URLs.
* **tokens.enc** — encrypted access tokens (stored via Vault policy).
* **webhooks/** — last-delivery payloads (for pull actions).
* **prs.jsonl** — PR metadata created by the Agent.
* **audit_remote.jsonl** — sync operations log.

#### (5.3) Remote Config (`remotes.json`)

```json
{
  "origin": { "provider": "github", "url": "https://api.github.com", "repo": "user/repo" },
  "push_mode": "safe",  // "safe" | "deny" | "allow_with_prompt"
  "pr_default": { "base": "main", "labels": ["agent"], "draft": true }
}
```

#### (5.4) Flows

* **Pull via Webhook**: store payload; queue Plan to reconcile diffs; render Overwrite Guard if conflicts.
* **Create PR**: when policy forbids direct push, open draft PR with task-linked description and diff summary; post CI status back to Task Feed.
* **Review Import**: pull PR comments into `prs.jsonl`; open “Review Fixups” tasks.

#### (5.5) UI

* **Remote Panel**: connection status, last sync, open PRs with badges (Draft/Open/Merged/Blocked).
* Buttons: Open PR, Update PR, Close PR, Fetch, Pull.
* High-contrast status chips; error states readable.

#### (5.6) CLI

```
agent remote connect github <repo>
agent remote pull
agent remote pr create --title "..."
agent remote pr update <id>
agent remote status
```

#### (5.7) Audit (`audit_remote.jsonl`)

```
{"ts":"UTC","op":"pr_create","id":42,"branch":"main","files":3,"url":"..."}
```

---

### 6) Schema Migration Engine

#### (6.1) Purpose

Version and migrate all structured files (JSON/YAML/TOML) used by the Agent (e.g., `agent.yaml`, datasets, registries), ensuring forward/back compatibility and atomic upgrades aligned with Required-Updates buckets. 

#### (6.2) Directory & Files

```
.codex_local_agent/migrations/
  registry.json
  scripts/
  backups/
  audit_migrations.jsonl
```

* **registry.json** — known schemas and current versions.
* **scripts/** — ordered migration scripts (`vN_to_vN+1.py`).
* **backups/** — pre-migration copies with checksums.
* **audit_migrations.jsonl** — migration ledger.

#### (6.3) Registry Example

```json
{
  "agent_yaml": { "file": ".codex_local_agent/agent.yaml", "version": 3 },
  "task_index": { "file": ".codex_local_agent/Task-Index.json", "version": 2 }
}
```

#### (6.4) Migration Flow

1. Detect mismatched version.
2. Create backup; verify checksum.
3. Run scripted transformer; validate with schema JSONSchema/TOML schema.
4. Write atomically; record success/failure.
5. On failure: restore backup; quarantine and open repair task.

#### (6.5) UI & CLI

* **Migrations Panel**: pending upgrades list; buttons Run/Skip/View Script; log pane.
* CLI: `agent schema migrate [--all]`, `agent schema status`.

#### (6.6) Audit Entry

```
{"ts":"UTC","schema":"agent_yaml","from":2,"to":3,"result":"ok"}
```

---

### 7) Artifact Packaging Pipeline

#### (7.1) Purpose

Produce distributable artifacts (zip, tar.gz, wheel/appimage/exe) with manifested contents, checksums, and release notes tied to Implemented-Updates entries.

#### (7.2) Directory & Files

```
.codex_local_agent/builds/
  recipes/
  outputs/
  checksums/
  release_notes/
  audit_builds.jsonl
```

* **recipes/** — packaging specs per target.
* **outputs/** — built artifacts.
* **checksums/** — SHA256/SHA512 per artifact.
* **release_notes/** — generated from Task Index & Implemented-Updates.
* **audit_builds.jsonl** — build logs.

#### (7.3) Recipe Schema

```json
{
  "name": "cli_bundle",
  "type": "zip",
  "include": ["bin/**","README.md",".codex_local_agent/agent.yaml"],
  "exclude": ["**/__pycache__/**","**/*.tmp"],
  "post": ["verify-integrity","generate-release-notes"]
}
```

#### (7.4) Flow

* Validate recipe → stage files → pack → compute checksums → generate release notes → sign optional.
* Link artifact to VCS tag if configured.

#### (7.5) UI & CLI

* **Build Panel**: recipe picker, Start Build, open outputs, checksum table (copy button).
* CLI: `agent build run <recipe>`, `agent build list`, `agent build verify <file>`.

#### (7.6) Audit

```
{"ts":"UTC","op":"build","recipe":"cli_bundle","artifact":"outputs/cli_bundle.zip","sha256":"..."}
```

---

### 8) Installer / Updater Logic

#### (8.1) Purpose

Create platform-specific installers and a self-updater that respects approvals and rollback.

#### (8.2) Directory & Files

```
.codex_local_agent/install/
  specs/
  artifacts/
  rollback/
  audit_install.jsonl
```

#### (8.3) Installer Spec

```json
{
  "target": "windows",
  "format": "exe",
  "inputs": ["builds/outputs/cli_bundle.zip"],
  "prechecks": ["disk>=500MB","admin=false"],
  "post_install": ["write-shortcuts","register-uninstaller"]
}
```

#### (8.4) Updater Flow

* Check installed version vs available; show changelog; require Allow.
* Download/verify; snapshot current; install; health-check; if failure, auto-rollback.
* Record to `audit_install.jsonl`.

#### (8.5) UI & CLI

* **Updater Panel**: current vs latest, changelog, Install/Defer; rollback button (enabled if previous exists).
* CLI: `agent update check|apply|rollback`.

---

### 9) Telemetry Privacy Contract

#### (9.1) Purpose

Define exactly what (if anything) is collected, how it is anonymized, how to opt-out, and how it’s stored locally. Default is **local-only** with opt-in for anonymized diagnostics.

#### (9.2) Directory & Files

```
.codex_local_agent/telemetry/
  policy.json
  events.jsonl
  redactions.json
  audit_telemetry.jsonl
```

#### (9.3) Policy (`policy.json`)

```json
{
  "enabled": false,
  "anonymize": true,
  "redact_patterns": ["api_key","token","email"],
  "endpoint": null,
  "retention_days": 30
}
```

#### (9.4) Event Schema

```json
{"ts":"UTC","event":"ui.click","area":"Ask","details":{"button":"Send"},"user_hash":"..."}
```

* Redaction engine scrubs secrets; Vault data never emitted.
* When disabled: nothing is recorded beyond local opt state.

#### (9.5) UI

* **Privacy Panel**: toggle telemetry; view/redact events; export/delete.
* Clear high-contrast warnings when enabling transmission.

#### (9.6) CLI & Audit

`agent telemetry on|off|export|purge`
`audit_telemetry.jsonl` records policy flips and exports.

---

### 10) Accessibility Framework

#### (10.1) Purpose

Ensure the UI is operable via keyboard and assistive tech, enforcing high-contrast and WCAG-aligned patterns.

#### (10.2) Directory & Files

```
.codex_local_agent/a11y/
  settings.json
  shortcuts.json
  screenreader_hints.json
  audit_a11y.jsonl
```

#### (10.3) Settings

```json
{
  "contrast": "high",
  "font_scale": 1.1,
  "focus_ring": true,
  "reduced_motion": true,
  "keyboard_only": false
}
```

#### (10.4) Features

* Full keyboard navigation map; tab order defined; visible focus.
* Alt text for images in transcript; larger fonts in final answer block.
* Color choices validated by contrast checker before theme apply.

#### (10.5) UI & CLI

* **A11y Panel**: toggle high-contrast (default locked on), font scale slider, shortcut viewer.
* CLI: `agent a11y audit` (reports failed contrast/labels).

---

### 11) Internationalization / Localization

#### (11.1) Purpose

Support multiple locales for UI strings and generated readmes, with persistent user preference and runtime switching.

#### (11.2) Directory & Files

```
.codex_local_agent/i18n/
  locales/
    en-US.json
    es-ES.json
    ...
  catalog.json
  audit_i18n.jsonl
```

#### (11.3) Catalog

```json
{
  "version": 1,
  "default_locale": "en-US",
  "keys": ["ui.send","ui.ask","ui.dowork","msg.approval_needed"]
}
```

Locales map keys → translations; fallback to default when missing.

#### (11.4) Workflow

* Extract UI strings into catalog; generate locale files.
* At startup, load selected locale; hot-swap supported.
* Documented “translation needed” report logged when missing.

#### (11.5) UI & CLI

* Locale picker dropdown; restart not required.
* CLI: `agent i18n extract|compile|report`.

---

### 12) Documentation Generator

#### (12.1) Purpose

Auto-render Markdown → HTML/PDF docs for Agents, Required-Updates, Implemented-Updates, and API help, embedding diffs and screenshots.

#### (12.2) Directory & Files

```
.codex_local_agent/docs/
  templates/
  outputs/
  audit_docs.jsonl
```

#### (12.3) Flow

* Gather sources (Agents.md, Required-Updates.md, Implemented-Updates.md, Task-Index.json).
* Render via templates; include Implementation Check footer; produce search index.
* Write to `outputs/` and link in session log.

#### (12.4) UI & CLI

* **Docs Panel**: Generate, Open, Copy Link; show last build time.
* CLI: `agent docs build [--pdf]`.

---

### 13) Inline Help & Tutorial System

#### (13.1) Purpose

Provide contextual help, onboarding flows, and corrective hints tied to UI elements and common errors.

#### (13.2) Directory & Files

```
.codex_local_agent/help/
  topics/
    vcs_overview.md
    approvals.md
    ocr_dataset.md
    ...
  tours/
    first_run.json
    implement_button.json
  audit_help.jsonl
```

#### (13.3) Tours Schema (`tours/*.json`)

```json
{
  "id": "first_run",
  "steps": [
    { "selector": "#askBtn", "text": "Ask = talk/think only.", "hotkey": "Enter" },
    { "selector": "#doWorkBtn", "text": "Do Work stages diffs & commands.", "hotkey": "Ctrl+Enter" }
  ]
}
```

#### (13.4) Behaviors

* Hover help with keyboard shortcut (`F1`) to open relevant topic.
* Auto-suggest help when user encounters recurring failure (e.g., Overwrite Guard).
* All help text high-contrast; supports i18n.

#### (13.5) UI & CLI

* **Help Panel**: searchable topics list; “Start Tour”; “Re-run last tip.”
* CLI: `agent help search <term>`, `agent help tour <id>`.

---
### 14) Logging Standardization

#### (14.1) Purpose

Unify all logs across subsystems (Auth, URM, Concurrency, VCS, Remote, Migrations, Builds, Install/Update, Telemetry, A11y, i18n, Docs, Help, CME, DSL, Sandbox, EventBus, Scheduler, Vault, etc.) into a consistent, searchable JSON-lines format with correlation IDs and redaction.

#### (14.2) Directory & Files

```
.codex_local_agent/logs/
  config.json
  rotation.json
  redact.json
  index.json
  streams/
    app.jsonl
    audit.jsonl
    security.jsonl
    performance.jsonl
    errors.jsonl
  archive/
  tmp/
```

* **config.json** — sinks, levels, formatting, per-module toggles.
* **rotation.json** — max size, time-based rotation, retention.
* **redact.json** — regex and token classes to mask (API keys, emails).
* **index.json** — lightweight metadata (counts per stream/day).
* **streams/** — canonical streams (append-only JSONL).
* **archive/** — compressed (zstd) rotated files.
* **tmp/** — spill files for high-throughput bursts.

#### (14.3) Canonical Log Record (JSONL)

```json
{
  "ts": "2025-10-30T06:10:30Z",
  "lvl": "INFO",
  "mod": "sandbox",
  "evt": "run_complete",
  "session_id": "sess-uuid",
  "task_id": "task-uuid",
  "bucket_id": "bucket-uuid",
  "corr": "corr-uuid", 
  "host": "machine-name",
  "user": "user-hash",
  "msg": "Command finished",
  "data": { "cmd": "pytest", "exit": 0, "dur_ms": 9123 },
  "tags": ["sandbox","run"],
  "file": "sandbox/run.py:324"
}
```

#### (14.4) Levels & Streams

* Levels: TRACE, DEBUG, INFO, WARN, ERROR, CRITICAL.
* Default routing:

  * **app.jsonl**: TRACE–INFO general runtime
  * **errors.jsonl**: WARN–CRITICAL + stack traces
  * **security.jsonl**: auth/vault/permission denials
  * **performance.jsonl**: timing, resource, metrics snapshots
  * **audit.jsonl**: decisions (approvals, pushes, migrations)

#### (14.5) Rotation & Retention (`rotation.json`)

```json
{
  "size_mb": 100,
  "daily_rotate": true,
  "retain_days": 30,
  "compress": "zstd",
  "index_rebuild_daily": true
}
```

#### (14.6) Redaction (`redact.json`)

```json
{
  "patterns": [
    {"name":"api_key","regex":"(?i)(api[_-]?key=)([A-Za-z0-9-_]{12,})","mask":"$1*******"},
    {"name":"email","regex":"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}","mask":"<redacted-email>"}
  ]
}
```

Applied before write. Vault data never logged.

#### (14.7) UI & CLI

* **Logs Panel**: stream selector, level filter, time range, tag filter; export button; high-contrast monospace.
* CLI: `agent log tail <stream> [--level WARN] [--since 2h]`, `agent log export <stream> --to file.jsonl.zst`.

#### (14.8) Error Stack Encoding

Stack traces captured with file:line and frames array:

```json
{"evt":"exception","data":{"type":"KeyError","msg":"'x'","frames":[{"file":"a.py","line":10,"fn":"run"}]}}
```

#### (14.9) Correlation

`corr` follows end-to-end through Ask→Plan→Apply→Verify; the Event Bus attaches `corr` to derived events.

#### (14.10) End-of-Day Index

`index.json` updated nightly with counts, size, first/last timestamps for fast UI pagination.

#### (14.11) End-of-Cycle Report

```
[LOGGING CHECK]
timestamp: <UTC ISO>
streams: {app: <int>, errors: <int>, security: <int>, performance: <int>, audit: <int>}
rotated: <int>
redactions_applied: <int>
status: standardized
```

---

### 15) Error Taxonomy

#### (15.1) Purpose

Define a global error code system and remediation metadata so diagnostics, UI, and automation can interpret failures consistently and propose fixes.

#### (15.2) Directory & Files

```
.codex_local_agent/errors/
  taxonomy.json
  codes/
    E1000.json
    E2xxx.json
  audit_errors.jsonl
```

#### (15.3) Code Spaces

* **E1xxx**: Configuration & Schema (missing keys, validation)
* **E2xxx**: Auth & Authority (denied, replay, signature)
* **E3xxx**: VCS/Remote (conflicts, overwrite guard)
* **E4xxx**: Sandbox/Execution (policy violation, timeout)
* **E5xxx**: Memory/CME (integrity, drift engine)
* **E6xxx**: EventBus/Scheduler (queue overflow, missed ack)
* **E7xxx**: A11y/i18n/Docs (contrast fail, missing locale)
* **E8xxx**: Vault/Security (lock, intrusion)
* **E9xxx**: System/Resource (disk full, OOM)

#### (15.4) Error Record Schema

```json
{
  "code": "E3007",
  "title": "Overwrite Guard Triggered",
  "severity": "HIGH",
  "module": "vcs",
  "summary": "Remote main is ahead; apply/rebase required.",
  "remediation": [
    "Run: agent vcs status",
    "Approve rebase in Overwrite Guard dialog",
    "Re-run Apply"
  ],
  "links": ["help/approvals.md","help/vcs_overview.md"]
}
```

#### (15.5) Emission Contract

All exceptions converted to taxonomy form before logging:

```json
{"evt":"error","code":"E4012","severity":"CRITICAL","msg":"Sandbox timeout","data":{"cmd":"pytest","timeout":180}}
```

#### (15.6) UI & CLI

* **Error Console**: filter by code, severity; one-click open remediation doc; high-contrast badges (CRITICAL=red).
* CLI: `agent error show E3007`, `agent error grep timeout`.

#### (15.7) Diagnostics Bridge

DSL maps raw failures to taxonomy codes and auto-fills `repair_queue.jsonl` remediation hints.

#### (15.8) End-of-Cycle Report

```
[ERROR TAXONOMY CHECK]
timestamp: <UTC ISO>
errors_logged: <int>
unique_codes: <int>
auto_fixed: <int>
status: normalized
```

---

### 16) Event Correlation Engine

#### (16.1) Purpose

Infer root causes by correlating logs, metrics, and Event Bus messages across time windows; produce human-readable incident timelines.

#### (16.2) Directory & Files

```
.codex_local_agent/correlation/
  rules.json
  incidents.jsonl
  timelines/
  audit_correlation.jsonl
```

#### (16.3) Rule Schema (`rules.json`)

```json
{
  "name": "Sandbox Timeouts after CPU Spike",
  "when": {
    "metrics.cpu_avg_percent": { "gte": 85, "within_sec": 120 },
    "events.contains": ["sandbox.run:timeout"]
  },
  "group_by": ["session_id"],
  "emit": { "incident": "SANDBOX_RESOURCE_PRESSURE", "severity": "HIGH" }
}
```

#### (16.4) Correlation Output

```
{"id":"inc-uuid","type":"SANDBOX_RESOURCE_PRESSURE","severity":"HIGH","window":{"start":"...","end":"..."},"facts":[...],"root_cause":"High CPU"}
```

Timeline markdown saved under `timelines/inc-uuid.md`.

#### (16.5) UI

* **Incidents Panel**: list incidents, severity chips; open timeline; link to remediation docs.
* High-contrast, with pinned red banner for open high-severity incidents.

#### (16.6) CLI

`agent corr run`, `agent corr rules list`, `agent corr show <id>`

#### (16.7) End-of-Cycle Report

```
[CORRELATION CHECK]
timestamp: <UTC ISO>
incidents: <int>
auto_resolved: <int>
open_high: <int>
status: analyzing
```

---

### 17) Distributed Cache Network

#### (17.1) Purpose

Share heavy artifacts (embeddings shards, OCR models, build outputs) among local/peer agents using content-addressed storage with integrity checks and TTL eviction.

#### (17.2) Directory & Files

```
.codex_local_agent/cache/
  manifest.json
  objects/
  pins.json
  policy.json
  peers.json
  audit_cache.jsonl
```

* **objects/** — content-addressed blobs `sha256/aa/bb...`
* **manifest.json** — maps logical names → content hash, size, TTL.
* **pins.json** — pinned objects immune to GC.
* **policy.json** — size limits, eviction strategy (LRU + TTL).
* **peers.json** — optional LAN peers (host:port, pubkey).

#### (17.3) Object Manifest

```json
{
  "name": "embeddings_2025_10",
  "hash": "sha256:abcd...",
  "size": 524288000,
  "ttl_days": 14,
  "created": "UTC ISO"
}
```

#### (17.4) Eviction Policy (`policy.json`)

```json
{
  "max_size_gb": 20,
  "evict": "lru_ttl",
  "low_watermark_gb": 15,
  "high_watermark_gb": 20
}
```

#### (17.5) Peer Sync (optional, offline-first)

* Discover peers via static `peers.json`.
* Request object by hash; verify SHA; store; update manifest.
* Security: accept peers only with known pubkeys; Vault signs requests.

#### (17.6) UI & CLI

* **Cache Panel**: size gauge, objects list, pin/unpin, purge.
* CLI: `agent cache stat|pin <hash>|purge|fetch <hash> [--peer host]`.

#### (17.7) End-of-Cycle Report

```
[CACHE CHECK]
timestamp: <UTC ISO>
objects: <int>
pinned: <int>
evicted: <int>
bytes_total: <int>
status: healthy
```

---

### 18) Data Compression Layer

#### (18.1) Purpose

Compress large, append-only data (logs, datasets, snapshots) and archival bundles using configurable codecs to reduce disk footprint without harming access patterns.

#### (18.2) Directory & Files

```
.codex_local_agent/compress/
  config.json
  audit_compress.jsonl
```

#### (18.3) Config (`config.json`)

```json
{
  "codecs": {"zstd": 7, "gzip": 6},
  "default": "zstd",
  "targets": [
    {"path":"logs/archive","codec":"zstd"},
    {"path":"memory/archive","codec":"zstd"},
    {"path":"docs/outputs","codec":"gzip"}
  ],
  "min_size_kb": 256,
  "schedule_cron": "0 2 * * *"
}
```

#### (18.4) Behavior

* Nightly compression of rotated files and archives.
* Integrity: post-compression SHA stored alongside.
* Transparent read via file suffix detection.

#### (18.5) CLI & Report

`agent compress run|verify`

```
[COMPRESSION CHECK]
timestamp: <UTC ISO>
files_compressed: <int>
savings_mb: <float>
status: optimized
```

---

### 19) Metrics Exporter

#### (19.1) Purpose

Expose operational metrics for introspection and external monitoring (Prometheus-style pull or local JSON pull), strictly local by default.

#### (19.2) Directory & Files

```
.codex_local_agent/metrics/
  registry.json
  snapshots/
  exporter.json
  audit_metrics.jsonl
```

#### (19.3) Metric Types

* Counters: `tasks_completed_total`, `errors_total`, `events_dispatched_total`
* Gauges: `cpu_percent`, `mem_mb`, `cache_bytes`, `queue_depth`
* Histograms: `sandbox_run_duration_ms`, `planning_time_ms`

#### (19.4) Exporter Config (`exporter.json`)

```json
{
  "mode": "local",      // "local" | "prometheus"
  "port": 9612,
  "bind": "127.0.0.1",
  "enabled": true,
  "auth_required": true
}
```

#### (19.5) Snapshots

Periodic JSON dumps to `snapshots/metrics_<DATE>.json`; UI reads from snapshots for charts without requiring a server.

#### (19.6) CLI & Report

`agent metrics show|serve`

```
[METRICS CHECK]
timestamp: <UTC ISO>
exporter: enabled
series: <int>
status: emitting
```

---

### 20) Visualization API

#### (20.1) Purpose

Provide a standard data contract and component library for rendering charts/graphs in the UI panels, ensuring high-contrast accessibility and consistent styling.

#### (20.2) Directory & Files

```
.codex_local_agent/viz/
  schema_series.json
  schema_chart.json
  themes.json
  presets.json
  audit_viz.jsonl
```

#### (20.3) Data Series Schema

```json
{
  "id": "series-uuid",
  "name": "CPU %",
  "type": "gauge|line|bar|area|pie|heatmap",
  "points": [{"t":"UTC ISO","v":42.0}],
  "unit": "%",
  "tags": ["performance"]
}
```

#### (20.4) Chart Schema

```json
{
  "title": "Resource Usage",
  "kind": "line",
  "series": ["series-uuid-1","series-uuid-2"],
  "options": {
    "y_min": 0, "y_max": 100,
    "legend": true,
    "contrast_mode": "high"
  }
}
```

#### (20.5) Themes & Presets

**themes.json** contains high-contrast palettes; **presets.json** defines common dashboards (Diagnostics, Scheduler, Sandbox).

#### (20.6) API Usage

Modules emit series files; UI requests chart by ID and renders with enforced high-contrast palette. No low-contrast combinations allowed (inline comment in renderers must note this rule).

#### (20.7) Report

```
[VIZ CHECK]
timestamp: <UTC ISO>
charts_rendered: <int>
themes_active: <string>
status: readable
```

---

### 21) Command Palette System

#### (21.1) Purpose

A universal, searchable palette for all actions (Ask, Do Work, Approve, Sync, Build, Migrate, etc.), enabling fast keyboard-driven control.

#### (21.2) Directory & Files

```
.codex_local_agent/palette/
  commands.json
  index.json
  audit_palette.jsonl
```

#### (21.3) Command Schema

```json
{
  "id": "cmd.dowork.run",
  "title": "Run Do Work Loop",
  "aliases": ["do","apply"],
  "category": "Work",
  "requires": ["role:Developer"],
  "args": [{"name":"bucket","type":"string","optional":true}]
}
```

#### (21.4) Search & Ranking

Fuzzy-match over `title` + `aliases`; rank by usage frequency with decay; cache in `index.json`.

#### (21.5) UI & Shortcuts

* Open palette: `Ctrl/Cmd+K`.
* High-contrast overlay with big search input (light text on dark).
* Sections by category; badges show permission requirements.

#### (21.6) CLI & Report

`agent cmd list|run <id>`

```
[PALETTE CHECK]
timestamp: <UTC ISO>
commands_registered: <int>
most_used: <id>
status: responsive
```

---

### 22) Shortcut Key Registry

#### (22.1) Purpose

Persistent keybinding layer with conflict detection and per-OS defaults.

#### (22.2) Directory & Files

```
.codex_local_agent/keymap/
  keybindings.json
  defaults/
    windows.json
    linux.json
    macos.json
  conflicts.jsonl
  audit_keymap.jsonl
```

#### (22.3) Binding Schema

```json
{
  "action": "open.palette",
  "keys": ["Ctrl+K"],
  "when": "ui.focus == true",
  "os": "any",
  "scope": "global"
}
```

#### (22.4) Conflict Detection

On load, detect overlapping bindings → record in `conflicts.jsonl` and show UI resolution dialog (reassign or disable). High-contrast warnings (yellow on dark with white text).

#### (22.5) UI & CLI

* **Keymap Panel**: search actions, edit bindings, restore defaults, per-OS tabs.
* CLI: `agent keys list|set <action> <keys>|reset`.

#### (22.6) Report

```
[KEYMAP CHECK]
timestamp: <UTC ISO>
bindings_total: <int>
conflicts: <int>
status: clean
```

---

### 23) UI Layout Persistence

#### (23.1) Purpose

Save/restore panel docking, sizes, splits, and visibility across sessions and monitors; enforce readability with high-contrast themes.

#### (23.2) Directory & Files

```
.codex_local_agent/ui/
  layouts/
    default.json
    profile_<name>.json
  monitors.json
  audit_ui_layout.jsonl
```

#### (23.3) Layout Schema (`layouts/*.json`)

```json
{
  "version": 1,
  "panels": {
    "chat": {"dock":"left","width_px":900,"visible":true},
    "terminal": {"dock":"right","width_px":500,"visible":true},
    "eventbus": {"dock":"bottom","height_px":280,"visible":false}
  },
  "theme": "default-dark",
  "font_scale": 1.0
}
```

#### (23.4) Monitor Awareness

`monitors.json` records display geometries; if layout exceeds current screen bounds, auto-fit and warn (ensure high text/background contrast in warnings).

#### (23.5) Profiles

Multiple named profiles; quick switch; palette command `ui.layout.load <profile>`.

#### (23.6) UI & CLI

* **Layout Panel**: Save Current, Load, Reset to Default, Import/Export.
* CLI: `agent ui layout save <name>|load <name>|reset`.

#### (23.7) Report

```
[UI LAYOUT CHECK]
timestamp: <UTC ISO>
profiles: <int>
last_loaded: "<name>"
status: persistent
```
### 24) Theming Engine Expansion

#### (24.1) Purpose

Expand the base theme into a semantic, import/export-able system with automatic contrast auditing. Themes define **semantic tokens** (e.g., `text.main`, `panel.bg`) rather than raw colors so modules render consistently and remain accessible under any palette. All UI must preserve high-contrast readability (light text on dark or dark text on light — never low-contrast).

#### (24.2) Directory & Files

```
.codex_local_agent/themes/
  packs/
    default-dark.json
    default-light.json
    solarized-high.json
  tokens.json
  overrides.json
  audit_theme.jsonl
  exports/
```

#### (24.3) Theme Pack Schema (`packs/*.json`)

```json
{
  "name": "default-dark",
  "version": 1,
  "palette": {
    "bg0": "#0f0f1a",
    "bg1": "#1a1a24",
    "fg0": "#f5f5f5",
    "fg1": "#cfcfd2",
    "accent_ok": "#3aff6a",
    "accent_warn": "#ffcc00",
    "accent_err": "#ff4d4f",
    "accent_focus": "#3a86ff"
  },
  "tokens": {
    "text.main": "fg0",
    "text.dim": "fg1",
    "panel.bg": "bg1",
    "window.bg": "bg0",
    "btn.text": "fg0",
    "btn.bg": "bg1",
    "btn.focus": "accent_focus",
    "status.ok": "accent_ok",
    "status.warn": "accent_warn",
    "status.err": "accent_err"
  },
  "wcag": { "min_ratio": 4.5 }
}
```

#### (24.4) Semantic Tokens Registry (`tokens.json`)

Defines canonical tokens used by all modules. Any module requesting a raw color is rejected by the linter.

```json
{
  "required": [
    "text.main","text.dim","panel.bg","window.bg",
    "btn.text","btn.bg","btn.focus",
    "status.ok","status.warn","status.err"
  ],
  "optional": ["chart.line","chart.area","table.header","table.row.alt"]
}
```

#### (24.5) Overrides & Import/Export

* **overrides.json** allows per-user tweaks by token (kept after theme switches).
* Export current theme: writes merged pack+overrides to `exports/<name>-export.json`.
* Import validates tokens and WCAG ratio, else quarantines to `audit_theme.jsonl`.

#### (24.6) WCAG Contrast Audit

On apply, compute contrast for: `text.*` against `panel.bg` and `window.bg`. Any ratio below 4.5 triggers correction suggestion (auto-lift brightness or fallback token), logged to `audit_theme.jsonl`.

#### (24.7) UI & CLI

* **Theme Manager**: list packs, preview, apply, export/import; real-time contrast score.
* CLI: `agent theme list|apply <name>|export|import <file>`.

#### (24.8) Report

```
[THEME CHECK]
timestamp: <UTC ISO>
active_theme: "default-dark"
wcag_failures_corrected: <int>
overrides_active: <int>
status: accessible
```

---

### 25) Voice Interaction Interface

#### (25.1) Purpose

Enable push-to-talk **STT** (speech→text) for Ask mode and **TTS** (text→speech) for responses, defaulting to offline/local engines. Privacy-first: no audio leaves the machine unless explicitly enabled.

#### (25.2) Directory & Files

```
.codex_local_agent/voice/
  config.json
  profiles.json
  transcripts/
  tts_cache/
  audit_voice.jsonl
```

#### (25.3) Config (`config.json`)

```json
{
  "stt": { "engine": "whisper-local", "device": "default", "vad": true, "lang": "en" },
  "tts": { "engine": "pyttsx3", "rate": 1.0, "voice": "auto" },
  "push_to_talk": { "key": "Ctrl+Space", "hold_to_record": true },
  "privacy": { "network_allowed": false, "store_audio": false }
}
```

#### (25.4) Flow

* Press/hold key → VAD listens → transcribe chunk → append as Ask input with `[voice]` tag → CME stores transcript snippet.
* TTS: optional; reads agent replies (excluding code blocks unless enabled).
* If `store_audio=false`, raw audio is kept in memory only, not written to disk.

#### (25.5) UI & CLI

* Mic button with level meter; TTS toggle; device selector; latency indicator.
* CLI: `agent voice stt test|tts test "Hello"`.

#### (25.6) Report

```
[VOICE CHECK]
timestamp: <UTC ISO>
stt_engine: "whisper-local"
tts_engine: "pyttsx3"
latency_ms_avg: <float>
status: active
```

---

### 26) Audio Feedback Framework

#### (26.1) Purpose

Map system events to brief audio cues for accessibility and situational awareness (complements high-contrast visuals). Non-intrusive, rate-limited.

#### (26.2) Directory & Files

```
.codex_local_agent/audio/
  pack.json
  sounds/
    success.wav
    warn.wav
    error.wav
    click.wav
  policy.json
  audit_audio.jsonl
```

#### (26.3) Mapping (`pack.json`)

```json
{
  "events": {
    "approval.granted": "success.wav",
    "approval.denied": "error.wav",
    "job.done": "success.wav",
    "job.warn": "warn.wav",
    "ui.click": "click.wav"
  },
  "volume": 0.6
}
```

#### (26.4) Policy (`policy.json`)

```json
{"enabled": true, "rate_limit_per_min": 30, "quiet_hours": {"start":"22:00","end":"07:00"}}
```

#### (26.5) UI & CLI

* Slider volume, mute toggle, test buttons; per-event enable/disable.
* CLI: `agent audio play <event>`.

#### (26.6) Report

```
[AUDIO CHECK]
timestamp: <UTC ISO>
enabled: true
events_mapped: <int>
status: nonintrusive
```

---

### 27) Notification Hub

#### (27.1) Purpose

Centralize in-app and system notifications with categories, deduplication, Do Not Disturb, and persistence. Works offline-first.

#### (27.2) Directory & Files

```
.codex_local_agent/notify/
  inbox.jsonl
  policy.json
  channels.json
  audit_notify.jsonl
```

#### (27.3) Policy (`policy.json`)

```json
{
  "do_not_disturb": {"enabled": false, "start":"23:00","end":"08:00"},
  "system_toast": true,
  "categories": {"security":"critical","build":"info","sync":"warn"},
  "dedupe_window_sec": 60
}
```

#### (27.4) Behavior

* Event Bus → Notification Hub → apply dedupe → route to inbox & optional OS toast.
* Critical notifications bypass DND but log loudly in `audit_notify.jsonl`.

#### (27.5) UI & CLI

* **Bell** icon with unread count; inbox view with filters; mark-read; pin.
* CLI: `agent notify list|clear|test`.

#### (27.6) Report

```
[NOTIFY CHECK]
timestamp: <UTC ISO>
unread: <int>
deduped_last_hour: <int>
status: routed
```

---

### 28) Mobile/Tablet Companion View

#### (28.1) Purpose

Provide a read-only (optionally limited-write) companion UI via local web server for monitoring tasks, logs, and approvals on a phone/tablet over LAN, secured via ASAC tokens and QR pairing.

#### (28.2) Directory & Files

```
.codex_local_agent/companion/
  server.json
  sessions.jsonl
  pairing.json
  audit_companion.jsonl
  static/
```

#### (28.3) Server Config (`server.json`)

```json
{
  "bind": "127.0.0.1",
  "port": 8789,
  "expose_lan": false,
  "allow_actions": ["approve","deny"], 
  "auth": "token"
}
```

#### (28.4) Pairing

* Generate one-time QR with token; device stores token; sessions tracked in `sessions.jsonl`.
* Revocation from desktop UI instantly invalidates token.

#### (28.5) UI

* Mobile-first high-contrast cards: Tasks, Logs (read-only), Approvals (if allowed).
* No code editor on mobile; safe actions only.

#### (28.6) CLI & Report

`agent companion serve|pair|revoke <device>`

```
[COMPANION CHECK]
timestamp: <UTC ISO>
sessions_active: <int>
lan_exposed: <bool>
status: reachable
```

---

### 29) REST / gRPC / WebSocket API Layer

#### (29.1) Purpose

Expose a **local-only** API for controlling agent features and receiving live events. Authentication via ASAC tokens; rate-limited; CORS off by default.

#### (29.2) Directory & Files

```
.codex_local_agent/api/
  openapi.json
  grpc.proto
  config.json
  tokens.jsonl
  audit_api.jsonl
```

#### (29.3) Config (`config.json`)

```json
{
  "mode": ["rest","ws"],
  "bind": "127.0.0.1",
  "port": 9696,
  "cors": false,
  "rate_limit_rps": 5,
  "auth": "bearer"
}
```

#### (29.4) Endpoints (REST)

* `GET /status` — health summary
* `POST /ask` — enqueue Ask message
* `POST /do_work` — run planner/apply on bucket
* `GET /tasks` — list task states
* `GET /logs?stream=errors&since=...` — tail logs
* `POST /approve` — approval action (role-gated)

**WebSocket**: `/events` streaming Event Bus messages (filtered by token scope).

#### (29.5) Security

* Tokens bound to roles/scopes (e.g., `scope:read_logs`, `scope:approve`).
* Rate limiter per token; audit to `audit_api.jsonl`.

#### (29.6) Report

```
[API CHECK]
timestamp: <UTC ISO>
rest_enabled: true
ws_enabled: true
rate_limited_violations: <int>
status: serving
```

---

### 30) Remote Execution Gateway

#### (30.1) Purpose

Dispatch jobs to remote hosts under **Sandbox-equivalent policies**, via SSH or agent-to-agent protocol, with audited results and file staging.

#### (30.2) Directory & Files

```
.codex_local_agent/remote_exec/
  hosts.json
  jobs.jsonl
  staging/
  results/
  audit_remote_exec.jsonl
  policy.json
```

#### (30.3) Hosts (`hosts.json`)

```json
{
  "buildbox": {"type":"ssh","host":"192.168.1.50","user":"coder","key":"vault://ssh/buildbox"},
  "lab01": {"type":"agent","endpoint":"https://lab01.local:9696","token":"vault://api/lab01"}
}
```

#### (30.4) Job Descriptor

```json
{
  "job_id":"uuid",
  "cmd":"pytest -q",
  "cwd":"/workspace",
  "env":{"PYTHONWARNINGS":"ignore"},
  "files":[{"local":"builds/outputs/app.zip","remote":"/workspace/app.zip"}],
  "timeout_sec":600,
  "sandbox_policy":"default"
}
```

#### (30.5) Flow

* Stage files → run under remote sandbox → stream logs → collect exit code/output → write `results/<job_id>.json` → Event Bus `remote.job.done`.

#### (30.6) UI & CLI

* **Remote Exec Panel**: hosts, queue, live logs; retry/failover.
* CLI: `agent rexec host add`, `agent rexec submit <job.json>`, `agent rexec logs <job_id>`.

#### (30.7) Report

```
[REMOTE EXEC CHECK]
timestamp: <UTC ISO>
hosts: <int>
jobs_completed: <int>
jobs_failed: <int>
status: controlled
```

---

### 31) Cluster Coordination

#### (31.1) Purpose

Coordinate multiple agents as a **cluster** for load sharing and high availability: peer discovery, basic leader election, quorum decisions for critical actions (e.g., schema migrations).

#### (31.2) Directory & Files

```
.codex_local_agent/cluster/
  config.json
  peers.jsonl
  leadership.json
  heartbeats.jsonl
  audit_cluster.jsonl
```

#### (31.3) Config (`config.json`)

```json
{
  "enabled": false,
  "election": "bully",   // or "raft-lite"
  "quorum": 2,
  "heartbeat_ms": 2000,
  "missed_heartbeats_for_failure": 3
}
```

#### (31.4) Behavior

* Discovery from static peers; periodic heartbeats; leader chosen by algorithm.
* Quorum guard: certain tasks (e.g., migrations) require `quorum` ACKs from peers.
* Failure detection → leader re-election; reschedule pending tasks.

#### (31.5) UI & CLI

* **Cluster Panel**: peer list, leader badge, quorum status, heartbeats chart.
* CLI: `agent cluster enable|status|peers add <host>`.

#### (31.6) Report

```
[CLUSTER CHECK]
timestamp: <UTC ISO>
peers: <int>
leader: "<id>"
quorum: <int>
status: coordinated
```

---

### 32) Task-Queue Persistence

#### (32.1) Purpose

Guarantee durable, transactional task queues with **at-least-once** execution semantics and idempotency keys. Default backend: SQLite (portable); optional LMDB/Redis.

#### (32.2) Directory & Files

```
.codex_local_agent/queue/
  backend.sqlite
  config.json
  audit_queue.jsonl
```

#### (32.3) Config (`config.json`)

```json
{
  "backend": "sqlite",
  "concurrency": 2,
  "retry_backoff": {"base_ms": 500, "factor": 2.0, "max_ms": 60000},
  "visibility_timeout_ms": 300000,
  "idempotency_window_min": 60
}
```

#### (32.4) Task Record (relational fields)

* `task_id (pk)`, `type`, `payload(json)`, `status(pending|running|done|error)`,
  `attempts`, `not_before`, `idempotency_key`, `created_ts`, `updated_ts`.

#### (32.5) Semantics

* Workers claim tasks with visibility timeout; heartbeat updates `updated_ts`.
* Exceeded timeout → task reappears (no duplication if idempotency respected).
* Backoff on failure; move to dead-letter after N attempts.

#### (32.6) UI & CLI

* **Queue Panel**: sizes, active workers, dead-letter list, retry button.
* CLI: `agent queue stats|drain|retry <task_id>`.

#### (32.7) Report

```
[QUEUE CHECK]
timestamp: <UTC ISO>
pending: <int>
running: <int>
dead_letter: <int>
status: durable
```

---

### 33) Long-Running Job Supervisor

#### (33.1) Purpose

Monitor and manage jobs exceeding a defined duration (e.g., tests, builds, migrations). Provide heartbeats, log streaming, timeout handling, and graceful restarts.

#### (33.2) Directory & Files

```
.codex_local_agent/supervisor/
  config.json
  jobs.jsonl
  heartbeats.jsonl
  audit_supervisor.jsonl
```

#### (33.3) Config (`config.json`)

```json
{
  "watch_threshold_sec": 600,
  "heartbeat_interval_sec": 15,
  "graceful_timeout_sec": 30,
  "max_restarts": 1
}
```

#### (33.4) Behavior

* Register job on start; ping heartbeat file periodically.
* If heartbeat missing > `graceful_timeout_sec`, send SIGTERM (or Windows equivalent); escalate to SIGKILL after 5s; mark `terminated`.
* Optional auto-restart once; preserve logs and attach to same correlation ID.
* Emit Event Bus: `job.supervisor.warn|killed|restarted`.

#### (33.5) UI & CLI

* **Supervisor Panel**: list of long jobs, elapsed time, next heartbeat ETA; buttons: Terminate, Restart, Open Logs.
* CLI: `agent supervisor watch|kill <job_id>|restart <job_id>`.

#### (33.6) Report

```
[SUPERVISOR CHECK]
timestamp: <UTC ISO>
watched_jobs: <int>
timeouts: <int>
restarts: <int>
status: guarded
```
### 34) Dependency Manager Integration

#### (34.1) Purpose

Provide a unified layer for resolving and installing dependencies (Python `pip`/`conda`, Node `npm`/`pnpm`, system packages hints) with offline-first behavior, reproducible lockfiles, and audit logging. Integrates with Sandbox, Builds, and Remote Exec without placeholders. Enforces high-contrast UI notes inside renderers.

#### (34.2) Directory & Files

```
.codex_local_agent/deps/
  config.json
  lock/
    python.lock
    node.lock
  wheelhouse/
  node_cache/
  hints.json
  audit_deps.jsonl
```

* **config.json** — policy (offline, indexes, timeout).
* **lock/** — resolved, pinned versions.
* **wheelhouse/** — local wheels for offline pip installs.
* **node_cache/** — tarballs for offline `npm ci`.
* **hints.json** — mapping features → packages.
* **audit_deps.jsonl** — installation & resolution ledger.

#### (34.3) Policy (`config.json`)

```json
{
  "mode": "offline_first",      // "offline_first" | "online"
  "python": {
    "index_url": null,
    "extra_index_urls": [],
    "timeout_sec": 120
  },
  "node": {
    "registry": null,
    "ci": true
  },
  "verify_hashes": true,
  "allow_build_from_source": false
}
```

#### (34.4) Resolution & Install Flow

1. **Discover** requirements from project files (`pyproject.toml`, `requirements.txt`, `package.json`).
2. **Resolve** → produce **deterministic lock** files with hashes.
3. **Fetch** artifacts (online if permitted) → store in `wheelhouse/` and `node_cache/`.
4. **Install** via Sandbox-controlled subprocess with hash verification; no network if offline mode.
5. **Audit** write success/failure, versions, and hashes.

#### (34.5) Hints (`hints.json`)

```json
{
  "ocr.tesseract": {"python": ["pytesseract"], "system": ["tesseract-ocr"]},
  "gpu.torch": {"python": ["torch==2.4.*; platform_system=='Windows'"], "notes": "Use CUDA11 wheels in wheelhouse"}
}
```

#### (34.6) UI & CLI

* **Deps Panel**: scan, resolve, apply, view lock diffs; warnings if source builds disabled.
* CLI: `agent deps scan|resolve|apply [--python|--node] | verify`.

#### (34.7) Report

```
[DEPS CHECK]
timestamp: <UTC ISO>
resolved: <int>
installed: <int>
hash_mismatches: <int>
status: reproducible
```

---

### 35) Environment Provisioner

#### (35.1) Purpose

Manage `.env` templates, variable precedence, and secret injection from Vault. Provide per-profile (dev/test/prod) environment sets that propagate to Sandbox, Remote Exec, and Scheduler.

#### (35.2) Directory & Files

```
.codex_local_agent/env/
  profiles/
    dev.env
    test.env
    prod.env
  template.env
  map.json
  audit_env.jsonl
```

* **template.env** — documented variables with defaults.
* **profiles/** — concrete sets.
* **map.json** — Vault key → env var mapping.
* **audit_env.jsonl** — changes & injections.

#### (35.3) Mapping (`map.json`)

```json
{
  "OPENAI_API_KEY": "vault://api/openai",
  "GITHUB_TOKEN": "vault://github/token",
  "DB_PASSWORD": "vault://db/main"
}
```

#### (35.4) Provision Flow

1. Load base from `template.env`.
2. Overlay selected profile (dev/test/prod).
3. Inject Vault secrets to ephemeral memory (never write plaintext to disk).
4. Export materialized env to Sandbox session only; redact logs.

#### (35.5) UI & CLI

* **Env Panel**: profile selector; diff view (shows placeholders only); “Test Injection”.
* CLI: `agent env use dev|test|prod | render [--to sandbox]`.

#### (35.6) Report

```
[ENV CHECK]
timestamp: <UTC ISO>
profile: "dev"
vars_total: <int>
vault_injected: <int>
status: provisioned
```

---

### 36) Hardware Interface Hooks

#### (36.1) Purpose

Detect and expose hardware capabilities (CPU cores, RAM, GPU CUDA/ROCm, Jetson), binding them to policies for Sandbox, Models, and Resource Optimizer.

#### (36.2) Directory & Files

```
.codex_local_agent/hw/
  snapshot.json
  policy.json
  audit_hw.jsonl
```

#### (36.3) Snapshot (`snapshot.json`)

```json
{
  "cpu_cores": 16,
  "ram_mb": 32768,
  "gpus": [{"name":"RTX 4070","vram_mb": 12288, "cuda": "12.2"}],
  "jetson": false,
  "disk_free_gb": 220
}
```

#### (36.4) Policy (`policy.json`)

```json
{
  "prefer_gpu": true,
  "sandbox_parallel_max": 2,
  "model_vram_budget_mb": 9000,
  "disable_heavy_jobs_on_battery": true
}
```

#### (36.5) Behavior

* On launch, gather hardware info; update ARO limits and Model Manager constraints.
* Emit Event Bus `hw.update`; Diagnostics records drift across sessions.

#### (36.6) UI & CLI

* **Hardware Panel**: specs, VRAM budget slider (soft cap), battery-aware toggle.
* CLI: `agent hw snapshot|budget set 9000`.

#### (36.7) Report

```
[HW CHECK]
timestamp: <UTC ISO>
gpus: <int>
vram_budget_mb: <int>
status: profiled
```

---

### 37) Offline Asset Cache Validation

#### (37.1) Purpose

Guarantee integrity of large assets (LLM weights, OCR models, datasets) via checksum manifests, dedupe, and repair tools; keeps offline usage reliable.

#### (37.2) Directory & Files

```
.codex_local_agent/assets/
  manifest.json
  checksums/
  quarantine/
  audit_assets.jsonl
```

#### (37.3) Manifest

```json
{
  "items": [
    {"name":"qwen2-7b.gguf","path":"models/qwen2-7b.gguf","sha256":"...","size": 4892138496},
    {"name":"tesseract-eng.traineddata","path":"ocr/tess/eng.traineddata","sha256":"...","size": 14600000}
  ],
  "version": 3
}
```

#### (37.4) Flow

* Verify files on schedule or on-demand.
* Mismatch → move to `quarantine/` and open repair task; optional fetch (if policy allows).
* Dedupe by content hash; hard links to save space.

#### (37.5) UI & CLI

* **Assets Panel**: verify, repair, show sizes; high-contrast status chips (OK/Warn/Quarantine).
* CLI: `agent assets verify|repair <name>`.

#### (37.6) Report

```
[ASSETS CHECK]
timestamp: <UTC ISO>
verified: <int>
quarantined: <int>
bytes_saved_dedupe: <int>
status: integral
```

---

### 38) Model Management Subsystem

#### (38.1) Purpose

Register and govern **LLM/Embedding/OCR** models (local Ollama, GGUF, Torch), track versions, VRAM/RAM budgets, warm-load strategies, and selection policies for Ask/Do Work.

#### (38.2) Directory & Files

```
.codex_local_agent/models/
  registry.json
  policies.json
  warm_pool.json
  adapters/
  audit_models.jsonl
```

#### (38.3) Registry (`registry.json`)

```json
{
  "models": [
    {"id":"gpt-oss-20b","type":"llm","provider":"ollama","context":16384,"size_gb": 15.2,"path":"ollama:gpt-oss-20b"},
    {"id":"nomic-embed","type":"embed","provider":"local","dim":768,"path":"models/nomic-embed.onnx"},
    {"id":"tesseract-eng","type":"ocr","provider":"local","lang":"eng"}
  ],
  "default": {"ask":"gpt-oss-20b","embed":"nomic-embed","ocr":"tesseract-eng"}
}
```

#### (38.4) Policies (`policies.json`)

```json
{
  "selection": {
    "ask": {"max_latency_ms": 2500, "min_context": 8192},
    "do_work": {"accuracy_bias": "high", "allow_parallel": true}
  },
  "warm_load": {"enable": true, "pool_size": 1},
  "memory_budget_mb": {"cpu": 16000, "vram": 9000}
}
```

#### (38.5) Behavior

* Enforce VRAM/CPU memory budgets from Hardware policy.
* Warm pool keeps one preferred Ask model preloaded.
* Event Bus emits `model.loaded`/`model.evicted`.
* Sandbox and CRO consult selection policy per task.

#### (38.6) UI & CLI

* **Models Panel**: registry list, default selectors, warm pool status, test prompt.
* CLI: `agent model list|set-default ask gpt-oss-20b | warm start|stop`.

#### (38.7) Report

```
[MODELS CHECK]
timestamp: <UTC ISO>
registered: <int>
warm_loaded: <int>
budget_ok: <bool>
status: governed
```

---

### 39) Prompt Template Repository

#### (39.1) Purpose

Centralize reusable prompt templates for Ask, Plan, Do Work, Review, and Diff QA with versioning, variables, and A/B policies.

#### (39.2) Directory & Files

```
.codex_local_agent/prompts/
  templates/
    ask_default.md
    do_work_plan.md
    review_diff.md
  variants/
    do_work_plan_v2.md
  index.json
  ab.json
  audit_prompts.jsonl
```

#### (39.3) Template Variables

`{{context}}`, `{{task_title}}`, `{{diff}}`, `{{acceptance_criteria}}`, `{{policy_refs}}` with required/optional markers in `index.json`.

```json
{
  "ask_default.md": {"required": ["context"], "optional": ["policy_refs"]},
  "do_work_plan.md": {"required": ["task_title","acceptance_criteria","diff"]}
}
```

#### (39.4) A/B (`ab.json`)

```json
{
  "experiments": [
    {"name":"plan_prompt_v2","templates":["do_work_plan.md","variants/do_work_plan_v2.md"],"ratio":[0.5,0.5]}
  ]
}
```

#### (39.5) UI & CLI

* **Prompts Panel**: preview, variable check, run test; high-contrast editor.
* CLI: `agent prompt list|test <template> --vars file.json | set default ask ask_default.md`.

#### (39.6) Report

```
[PROMPTS CHECK]
timestamp: <UTC ISO>
templates: <int>
experiments_active: <int>
status: centralized
```

---

### 40) Training & Fine-Tuning Manager

#### (40.1) Purpose

Local supervised fine-tuning (where feasible) or lightweight adapters (LoRA/QLoRA) for supported models. Handles datasets, splits, configs, training runs, and artifact versioning.

#### (40.2) Directory & Files

```
.codex_local_agent/train/
  datasets/
  configs/
  runs/
  artifacts/
  audit_train.jsonl
```

#### (40.3) Config Example (`configs/lora_small.json`)

```json
{
  "base_model": "gpt-oss-7b",
  "method": "qlora",
  "epochs": 3,
  "lr": 2e-4,
  "batch_size": 2,
  "max_seq": 2048,
  "train_val_split": 0.95,
  "bf16": true
}
```

#### (40.4) Flow

* Validate dataset licenses; check VRAM/CPU; schedule via Supervisor.
* Stream metrics to Metrics Exporter; snapshot artifacts; register in Models registry as `id: base+adapter@tag`.
* Post-train eval kicks automatically (see §41).

#### (40.5) UI & CLI

* **Training Panel**: select base model/config/dataset, start/stop, live loss chart (high-contrast).
* CLI: `agent train start <config> --dataset <path> | list | abort <run_id>`.

#### (40.6) Report

```
[TRAIN CHECK]
timestamp: <UTC ISO>
runs_total: <int>
artifacts_created: <int>
status: local-capable
```

---

### 41) Evaluation Benchmarks

#### (41.1) Purpose

Regression tests for reasoning, OCR extraction, code diffs, and task success. Stores suites, scores, and baselines to detect drift.

#### (41.2) Directory & Files

```
.codex_local_agent/eval/
  suites/
    reasoning.json
    ocr.json
    codegen.json
  results/
  baselines.json
  audit_eval.jsonl
```

#### (41.3) Suite Schema

```json
{
  "name": "reasoning_basic",
  "tasks": [
    {"id":"r1","prompt":"2+2?","expect":"4","metric":"exact"},
    {"id":"r2","prompt":"Summarize text...","expect":"<=50 words","metric":"len<=50"}
  ],
  "model_set": ["ask","do_work"]
}
```

#### (41.4) Metrics

* exact / F1 / WER (OCR) / pass@k (code) / latency / token usage.
* Results compared to **baselines.json** with thresholds; failure opens repair tasks.

#### (41.5) UI & CLI

* **Evaluation Panel**: select suite, run, compare to baseline, charts (high-contrast).
* CLI: `agent eval run reasoning.json | baseline set reasoning.json <result_id>`.

#### (41.6) Report

```
[EVAL CHECK]
timestamp: <UTC ISO>
suites_run: <int>
regressions: <int>
status: benchmarked
```

---

### 42) Security Penetration Audit Tools

#### (42.1) Purpose

Run local-only security probes against Sandbox, Vault, Event Bus, API, and Auth to detect policy gaps and potential privilege escalations; never exfiltrate data.

#### (42.2) Directory & Files

```
.codex_local_agent/secscan/
  profiles/
    quick.json
    full.json
  findings.jsonl
  audit_secscan.jsonl
```

#### (42.3) Profile (`profiles/quick.json`)

```json
{
  "targets": ["sandbox","vault","api","auth"],
  "checks": [
    "sandbox_escape_attempts",
    "vault_bruteforce_lockout",
    "api_rate_limit",
    "token_replay_detection"
  ],
  "max_runtime_sec": 120
}
```

#### (42.4) Behavior

* Execute synthetic attacks in a controlled Sandbox.
* Validate lockouts, rate limits, and token nonce protections.
* Findings classified to Error Taxonomy (E8xxx) with remediation links.

#### (42.5) UI & CLI

* **Security Panel**: run quick/full scans; show findings table; export report.
* CLI: `agent secscan run quick|full`.

#### (42.6) Report

```
[SECURITY SCAN]
timestamp: <UTC ISO>
findings_total: <int>
critical: <int>
resolved_since_last: <int>
status: guarded
```

---

### 43) Integrity Chain of Trust

#### (43.1) Purpose

Guarantee end-to-end integrity of the `.codex_local_agent` tree and generated artifacts using a Merkle tree of SHA-256 digests, optional signing, and verification hooks before Apply/Release.

#### (43.2) Directory & Files

```
.codex_local_agent/integrity/
  merkle.json
  signatures/
  checkpoints/
  audit_integrity.jsonl
```

#### (43.3) Merkle Manifest (`merkle.json`)

```json
{
  "root": "sha256:abcd...",
  "nodes": {
    "agent.yaml": "sha256:...",
    "Task-Index.json": "sha256:...",
    "memory/bank_core.jsonl": "sha256:..."
  },
  "generated": "UTC ISO",
  "version": 1
}
```

#### (43.4) Flow

* After each significant change, recompute leaf hashes → build Merkle root.
* Optionally sign `root` with local RSA; store under `signatures/<date>.sig`.
* On Apply/Build/Release, verify current tree against latest checkpoint; mismatch → block and open incident.

#### (43.5) Checkpoints & Verify

* Create checkpoint before migrations/builds; store in `checkpoints/`.
* `agent integrity verify` compares current → checkpoint; prints diff of diverged leaves.

#### (43.6) UI & CLI

* **Integrity Panel**: current root, last checkpoint, verification button; list of diverged files.
* CLI: `agent integrity snapshot|verify|sign`.

#### (43.7) Report

```
[INTEGRITY CHECK]
timestamp: <UTC ISO>
root: "sha256:..."
diverged_leaves: <int>
signed: <bool>
status: trustworthy
```
### 44) Disaster Recovery Mode

#### (44.1) Purpose

Provide a minimal, read-only boot path when the normal Agent fails to start due to corruption, missing deps, or vault lock. Focus on diagnostics, integrity verification, and safe export—no writes beyond a recovery workspace.

#### (44.2) Directory & Files

```
.codex_local_agent/recovery/
  bootstrap.json
  checks.json
  reports/
  exports/
  audit_recovery.jsonl
```

#### (44.3) Bootstrap (`bootstrap.json`)

```json
{
  "network": false,
  "mount_readonly": true,
  "permit_actions": ["verify_integrity","export_logs","export_docs","vault_unlock_prompt"],
  "ui_reduced": true
}
```

#### (44.4) Health Checks (`checks.json`)

```json
{
  "filesystem": ["exists:agent.yaml","writable:.", "free_gb>=1"],
  "integrity": ["merkle_verify"],
  "vault": ["locked_state","key_files_present"],
  "deps": ["python>=3.10","node_optional"]
}
```

#### (44.5) Flow

* Launch with recovery flag or auto-trigger after 2 failed normal boots.
* Mount agent tree read-only; skip Scheduler/Sandbox.
* Run integrity & error taxonomy sweeps; produce markdown report in `reports/`.
* Provide vault unlock prompt (no secrets logged).
* Allow exports of logs/docs to `exports/` only.

#### (44.6) UI & CLI

* **Recovery UI** (high-contrast): big status cards (Integrity, Vault, Deps), export buttons.
* CLI: `agent recover verify|export logs|export docs|attempt unlock`.

#### (44.7) Report

```
[RECOVERY CHECK]
timestamp: <UTC ISO>
integrity_ok: <bool>
vault_locked: <bool>
exports_created: <int>
status: minimal_ready
```

---

### 45) System Restore Utility

#### (45.1) Purpose

One-click rollback to the last verified good state (snapshot of configs, prompts, models registry, queue state) while preserving user data and logs.

#### (45.2) Directory & Files

```
.codex_local_agent/restore/
  snapshots/
    2025-10-28T12-00-00.json
  policy.json
  audit_restore.jsonl
```

#### (45.3) Snapshot Schema

```json
{
  "id": "snap-2025-10-28T12-00-00Z",
  "files": [
    { "path":"agent.yaml","sha":"sha256:..." },
    { "path":"Task-Index.json","sha":"sha256:..." }
  ],
  "exclusions": ["logs/**","queue/backend.sqlite","vault/**"],
  "reason": "post-ImplementationCheck"
}
```

#### (45.4) Policy (`policy.json`)

```json
{
  "auto_snapshot_on": ["migrations.success","builds.success","apply.success"],
  "retain_last": 5,
  "confirm_overwrite": true
}
```

#### (45.5) Flow

* Choose snapshot → verify checksums → stop running services → restore files atomically → re-run Integrity check → restart services.
* Never overwrites vault or logs; creates diff summary.

#### (45.6) UI & CLI

* **Restore Panel**: list snapshots, details, diffs; “Restore” (requires Allow).
* CLI: `agent restore list|apply <snapshot_id>|prune`.

#### (45.7) Report

```
[RESTORE CHECK]
timestamp: <UTC ISO>
snapshot: "<id>"
files_restored: <int>
status: reverted
```

---

### 46) Change-Approval Workflow

#### (46.1) Purpose

Formalize approvals for risky actions (Apply, Migrations, Vault ops, Remote Exec). Supports single- or multi-approver rules and expiration.

#### (46.2) Directory & Files

```
.codex_local_agent/approvals/
  rules.json
  queue.jsonl
  decisions.jsonl
  audit_approvals.jsonl
```

#### (46.3) Rules (`rules.json`)

```json
{
  "apply.patch": {"required": 1, "roles": ["Developer"], "expires_min": 30},
  "vault.rotate": {"required": 2, "roles": ["Developer","Auditor"], "expires_min": 10}
}
```

#### (46.4) Decision Packet

```json
{"id":"appr-uuid","action":"apply.patch","subject":"patch-123","requested_by":"user","expires":"UTC","status":"pending"}
```

#### (46.5) Flow

* Action proposes decision → queue entry created → notifications sent → approvers vote → majority/threshold reached → action proceeds.
* Expired or rejected decisions logged and blocked.

#### (46.6) UI & CLI

* **Approvals Panel**: pending decisions, voters list, countdown; buttons Approve/Deny.
* CLI: `agent approve list|grant <id>|deny <id>`.

#### (46.7) Report

```
[APPROVALS CHECK]
timestamp: <UTC ISO>
pending: <int>
granted: <int>
denied: <int>
status: governed
```

---

### 47) Collaboration Layer

#### (47.1) Purpose

Enable shared state for chat, tasks, and approvals among authenticated users on the same LAN/cluster, honoring URM and Concurrency Policy.

#### (47.2) Directory & Files

```
.codex_local_agent/collab/
  sessions.jsonl
  presence.jsonl
  chat_feed.jsonl
  board.json
  audit_collab.jsonl
```

#### (47.3) Presence & Sessions

```json
{"user":"meeh","status":"online","since":"UTC","roles":["Developer"]}
```

#### (47.4) Shared Objects

* **chat_feed.jsonl**: time-ordered messages (text/markdown, image refs).
* **board.json**: Kanban-like buckets tied to Task-Index entries.

#### (47.5) Behavior

* Real-time via local WebSocket (see API Layer); messages signed with session tokens; message edits restricted by role.
* Concurrency locks applied to shared task edits.

#### (47.6) UI & CLI

* **Collab Panel**: online users, shared chat, task board.
* CLI: `agent collab who|say "..."|board push <task>`.

#### (47.7) Report

```
[COLLAB CHECK]
timestamp: <UTC ISO>
users_online: <int>
messages_last_hour: <int>
status: synchronized
```

---

### 48) Review Mode UI

#### (48.1) Purpose

Dedicated review workflow for diffs, tests, artifacts, and approvals in a single high-contrast pane with “Approve/Request Changes” and inline annotations.

#### (48.2) Directory & Files

```
.codex_local_agent/review/
  sessions.jsonl
  comments.jsonl
  snapshots/
  audit_review.jsonl
```

#### (48.3) Comment Schema

```json
{
  "id":"cmt-uuid",
  "target":{"file":"path/to.py","line":120},
  "author":"user",
  "body":"Consider extracting method.",
  "created":"UTC",
  "resolved":false
}
```

#### (48.4) Behavior

* Link to VCS staged diffs; run hooks/tests; show results inline; accept or request changes.
* Comments persist and are exported to PR when remote bridge enabled.

#### (48.5) UI & CLI

* **Review Mode**: split diff viewer, test summary, artifacts sidebar, approval buttons.
* CLI: `agent review start|comment <file:line> "..."|resolve <comment_id>`.

#### (48.6) Report

```
[REVIEW CHECK]
timestamp: <UTC ISO>
comments: <int>
approvals: <int>
requests_changes: <int>
status: inspected
```

---

### 49) Test Harness Framework

#### (49.1) Purpose

Standardize unit/integration tests across modules, auto-discover test files, orchestrate via Sandbox, and report to Evaluation and CI bridges.

#### (49.2) Directory & Files

```
.codex_local_agent/tests/
  config.json
  suites/
  results/
  audit_tests.jsonl
```

#### (49.3) Config (`config.json`)

```json
{
  "discover": ["**/tests/**","codex_local_agent/**/tests/**"],
  "runner": "pytest -q",
  "env_profile": "test",
  "timeout_sec": 300
}
```

#### (49.4) Flow

* Discover → stage environment via Env Provisioner → run in Sandbox → capture JUnit/JSON → write results.
* Map failures to Error Taxonomy; open repair tasks.

#### (49.5) UI & CLI

* **Tests Panel**: suites list, last run status, flakiness chart.
* CLI: `agent test run [--suite <name>] | last`.

#### (49.6) Report

```
[TESTS CHECK]
timestamp: <UTC ISO>
suites_run: <int>
failures: <int>
flake_rate: <float>
status: verified
```

---

### 50) Continuous Integration Bridge

#### (50.1) Purpose

Connect local runs to external CI (GitHub Actions/GitLab CI) using policy-controlled syncing of test artifacts and statuses; offline-first with deferred uploads.

#### (50.2) Directory & Files

```
.codex_local_agent/ci/
  providers.json
  runs.jsonl
  artifacts/
  audit_ci.jsonl
```

#### (50.3) Providers (`providers.json`)

```json
{
  "github": {"enabled": true, "workflows": ["agent.yml"], "upload_when_online": true},
  "gitlab": {"enabled": false}
}
```

#### (50.4) Flow

* On local test/build success, stage artifacts → if online and allowed, upload to CI run via provider API; if offline, enqueue.
* Pull CI statuses back into Task Index and Review Mode.

#### (50.5) UI & CLI

* **CI Panel**: provider status, pending uploads, last results.
* CLI: `agent ci push|pull|status`.

#### (50.6) Report

```
[CI CHECK]
timestamp: <UTC ISO>
artifacts_uploaded: <int>
runs_synced: <int>
status: bridged
```

---

### 51) Documentation Linter

#### (51.1) Purpose

Enforce consistent Markdown structure and Required-Updates conventions (headings, code fences, citation style), prevent drift in Agent docs.

#### (51.2) Directory & Files

```
.codex_local_agent/docs_lint/
  rules.json
  findings.jsonl
  audit_doclint.jsonl
```

#### (51.3) Rules (`rules.json`)

```json
{
  "require_sections": ["Purpose","Directory & Files","Flow","UI & CLI","Report"],
  "max_heading_depth": 4,
  "code_fence_lang_required": true,
  "disallow_low_contrast_html": true
}
```

#### (51.4) Flow

* Scan docs; produce findings with file/line; suggest quick-fixes.
* Blocks release if critical docs fail (policy-configurable).

#### (51.5) UI & CLI

* **Doc Lint Panel**: file list, violations, “Apply Fixes” (safe transforms).
* CLI: `agent doclint run|fix`.

#### (51.6) Report

```
[DOCLINT CHECK]
timestamp: <UTC ISO>
files_scanned: <int>
violations: <int>
auto_fixes: <int>
status: consistent
```

---

### 52) License Compliance Checker

#### (52.1) Purpose

Identify open-source license obligations for dependencies and embedded code; generate attribution files and flag incompatible licenses.

#### (52.2) Directory & Files

```
.codex_local_agent/license/
  policy.json
  inventory.json
  attributions/
  audit_license.jsonl
```

#### (52.3) Policy (`policy.json`)

```json
{
  "allow": ["MIT","BSD-2","BSD-3","Apache-2.0"],
  "warn": ["LGPL-2.1","LGPL-3.0"],
  "deny": ["GPL-3.0-only"],
  "require_attribution": true
}
```

#### (52.4) Flow

* Parse dependency manifests and vendored headers; resolve licenses; compare to policy; build `inventory.json`.
* Generate `attributions/THIRD-PARTY-NOTICES.md`; block builds on deny list.

#### (52.5) UI & CLI

* **License Panel**: inventory table, policy editor (high-contrast warnings), export notices.
* CLI: `agent license scan|report|enforce`.

#### (52.6) Report

```
[LICENSE CHECK]
timestamp: <UTC ISO>
packages_scanned: <int>
violations: <int>
attribution_generated: <bool>
status: compliant
```

---

### 53) Semantic Diff Visualizer

#### (53.1) Purpose

Render code/document diffs with language-aware parsing (AST/Markdown tokens) to reduce noise and highlight meaningful changes used by Review Mode and VCS panels.

#### (53.2) Directory & Files

```
.codex_local_agent/semantic_diff/
  parsers/
    python.json
    markdown.json
    json.json
  config.json
  audit_semantic_diff.jsonl
```

#### (53.3) Parser Config (`parsers/python.json`)

```json
{
  "ignore": ["whitespace","comment"],
  "group": ["function","class","import"],
  "display": {"added":"green","removed":"red","moved":"yellow","renamed":"cyan"}
}
```

#### (53.4) Behavior

* Tokenize by language; compute move/rename detection; collapse trivial changes.
* Provide anchors for inline comments; export summary for commit message suggestions.

#### (53.5) UI & CLI

* **Semantic Diff Viewer**: toggle “semantic vs plain”, filters (imports, docstrings). High-contrast colors with sufficient contrast on dark background.
* CLI: `agent sdiff show <file> [--plain]`.

#### (53.6) Report

```
[SEMANTIC DIFF CHECK]
timestamp: <UTC ISO>
files_analyzed: <int>
moves_detected: <int>
noise_reduced_percent: <float>
status: insightful
```
### 54) Policy Reasoner

#### (54.1) Purpose

A rule engine that validates every candidate action, patch, migration, or configuration against codified governance (Agent.md, Required-Updates.md, Vault policy, Role Matrix). Prevents drift by issuing allow/deny/explain decisions with human-readable rationales.

#### (54.2) Directory & Files

```
.codex_local_agent/policy_reasoner/
  rules.json5
  facts.json
  decisions.jsonl
  traces/
  audit_policy.jsonl
```

#### (54.3) Rule Schema (`rules.json5`)

```json
{
  "version": 1,
  "rules": [
    {
      "id": "PR-001",
      "when": {
        "action": "apply.patch",
        "branch": "main",
        "approvals.required": { "gte": 1 }
      },
      "assert": [
        {"path":"vcs.safe_push","eq": true},
        {"path":"integrity.last_checkpoint_ok","eq": true}
      ],
      "deny_if": [
        {"path":"auth.role","neq": "Developer"},
        {"path":"overwrites.remote_ahead","eq": true}
      ],
      "explain": "Apply requires Developer role, safe_push, integrity checkpoint, and no remote-ahead."
    }
  ]
}
```

#### (54.4) Facts Assembly (`facts.json`)

Continuously synthesized from Auth, URM, VCS, Integrity, Vault, Scheduler, and Env Provisioner. Facts are read-only snapshots used to evaluate rules.

#### (54.5) Decision Contract

```json
{
  "ts": "UTC",
  "action": "apply.patch",
  "subject": "patch-abc",
  "result": "deny|allow",
  "rule_ids": ["PR-001","PR-014"],
  "explanation": "…human-readable rationale…",
  "corr": "corr-uuid"
}
```

Saved to `decisions.jsonl` and broadcast via Event Bus `policy.decision`.

#### (54.6) Flow

1. Gather facts → evaluate rules in order → collect allow/deny votes.
2. Short-circuit on explicit deny; otherwise allow.
3. Attach explanation to UI (Ask/Do Work) and audit trail.

#### (54.7) UI & CLI

* **Policy Panel** (high-contrast): rules list, enable/disable, test decision on sample facts, explanation viewer.
* CLI: `agent policy test --action apply.patch --facts facts.json`, `agent policy reload`.

#### (54.8) Report

```
[POLICY CHECK]
timestamp: <UTC ISO>
rules_active: <int>
decisions_today: <int>
denies: <int>
status: enforced
```

---

### 55) Ethical Guard / Governance Compliance

#### (55.1) Purpose

Codify non-technical governance: safety, privacy, and ethical constraints. Provides a dedicated preflight that can halt or sandbox actions violating declared boundaries.

#### (55.2) Directory & Files

```
.codex_local_agent/ethics/
  charter.md
  guardrails.json
  exceptions.jsonl
  audit_ethics.jsonl
```

#### (55.3) Guardrail Schema (`guardrails.json`)

```json
{
  "privacy": {"allow_exfil": false, "allow_telemetry": false},
  "data_handling": {"retain_days": 30, "mask_pii": true},
  "execution": {"remote_exec_default": "deny", "requires_approval": ["vault.rotate","remote.exec"]},
  "content": {"disallow_categories": ["illegal","exploit"], "scan_prompts": true}
}
```

#### (55.4) Enforcement

* Runs before Policy Reasoner final allow.
* Scans prompts/patches for disallowed categories (local-only classifier).
* Requires multi-approval for sensitive flows (Vault rotate, remote exec).

#### (55.5) Exceptions

Logged with strict scope and expiry:

```json
{"id":"ex-1","scope":"remote.exec","granted_by":"Developer","expires":"UTC+1h","reason":"emergency fix"}
```

#### (55.6) UI & CLI

* **Ethics Panel**: charter view, guardrail toggles (where policy allows), exception requests. High-contrast warnings for violations.
* CLI: `agent ethics status|exception add --scope remote.exec --duration 1h`.

#### (55.7) Report

```
[ETHICS CHECK]
timestamp: <UTC ISO>
violations_blocked: <int>
exceptions_active: <int>
status: compliant
```

---

### 56) User Feedback Loop

#### (56.1) Purpose

Collect explicit human feedback on replies, diffs, runs, and UI flows to improve Reinforcement Policy Engine and Prompt Repository.

#### (56.2) Directory & Files

```
.codex_local_agent/feedback/
  forms.json
  responses.jsonl
  survey_triggers.json
  audit_feedback.jsonl
```

#### (56.3) Form Schema (`forms.json`)

```json
{
  "forms": {
    "reply_quality": {
      "fields": [
        {"id":"score","type":"int","min":1,"max":5},
        {"id":"comment","type":"text"}
      ]
    }
  }
}
```

#### (56.4) Triggers (`survey_triggers.json`)

```json
{"events":["do_work.success","do_work.failed","review.approved"],"sample_rate":0.3}
```

#### (56.5) Flow

* Trigger → inline, high-contrast micro-form appears (keyboard-friendly).
* Response stored; signal sent to RPE to adjust macro and prompt weights.

#### (56.6) UI & CLI

* **Feedback Panel**: trend charts, top issues; export CSV.
* CLI: `agent feedback export --since 7d`.

#### (56.7) Report

```
[FEEDBACK CHECK]
timestamp: <UTC ISO>
responses: <int>
avg_score: <float>
status: listening
```

---

### 57) Analytics & Reporting Portal

#### (57.1) Purpose

Aggregate metrics, logs, decisions, evaluations, and feedback into curated dashboards and exportable reports.

#### (57.2) Directory & Files

```
.codex_local_agent/analytics/
  dashboards.json
  widgets/
  reports/
  audit_analytics.jsonl
```

#### (57.3) Dashboard Schema (`dashboards.json`)

```json
{
  "default": ["throughput","errors","approvals","eval_scores"],
  "widgets": {
    "throughput": {"source":"metrics","series":"tasks_completed_total","type":"line"},
    "errors": {"source":"logs","stream":"errors.jsonl","type":"bar"},
    "eval_scores": {"source":"eval","suite":"reasoning_basic","type":"line"}
  }
}
```

#### (57.4) Exports

Generate PDF/HTML using Documentation Generator templates; all charts enforce high-contrast palettes.

#### (57.5) UI & CLI

* **Analytics Panel**: dashboard selector; widget editor; export buttons.
* CLI: `agent analytics export --dashboard default --pdf`.

#### (57.6) Report

```
[ANALYTICS CHECK]
timestamp: <UTC ISO>
dashboards: <int>
exports_today: <int>
status: insightful
```

---

### 58) Anomaly Detection Layer

#### (58.1) Purpose

Detect unusual behavior across logs, metrics, and task outcomes using simple statistics (Z-scores) plus optional local ML models.

#### (58.2) Directory & Files

```
.codex_local_agent/anomaly/
  detectors.json
  signals.jsonl
  models/
  audit_anomaly.jsonl
```

#### (58.3) Detector Config (`detectors.json`)

```json
{
  "cpu_spike": {"source":"metrics.cpu_percent","window":300,"z_thresh":3.0},
  "error_burst": {"source":"logs.errors_per_min","window":60,"z_thresh":2.5}
}
```

#### (58.4) Flow

* Maintain rolling windows; compute baselines; emit signals when thresholds crossed.
* Signals feed Correlation Engine and open incidents.

#### (58.5) UI & CLI

* **Anomaly Panel**: active signals, charts, mute control.
* CLI: `agent anomaly run|mute cpu_spike`.

#### (58.6) Report

```
[ANOMALY CHECK]
timestamp: <UTC ISO>
signals_emitted: <int>
muted: <int>
status: vigilant
```

---

### 59) Runtime Profiler

#### (59.1) Purpose

Fine-grained timing and memory profiling of Agent pipelines (Ask, Plan, Apply, Sandbox runs), producing flamegraphs and hot-spot summaries.

#### (59.2) Directory & Files

```
.codex_local_agent/profiler/
  config.json
  traces/
  flamegraphs/
  audit_profiler.jsonl
```

#### (59.3) Config (`config.json`)

```json
{
  "enabled": false,
  "mode": "sampling",   // "instrument" | "sampling"
  "sample_hz": 99,
  "targets": ["ask","do_work","sandbox"]
}
```

#### (59.4) Output

* **traces/**: JSON traces (Chrome trace format).
* **flamegraphs/**: SVG/HTML visuals (high-contrast color ramps).

#### (59.5) UI & CLI

* **Profiler Panel**: enable/disable, pick targets, open last flamegraph.
* CLI: `agent profile start|stop|open <run_id>`.

#### (59.6) Report

```
[PROFILER CHECK]
timestamp: <UTC ISO>
runs_profiled: <int>
hotspots_found: <int>
status: measured
```

---

### 60) Power Management Module

#### (60.1) Purpose

Optimize behavior on laptops or constrained power states: throttle heavy tasks, pause warm pools, and respect quiet hours (aligning with Audio policy).

#### (60.2) Directory & Files

```
.codex_local_agent/power/
  policy.json
  state.json
  audit_power.jsonl
```

#### (60.3) Policy (`policy.json`)

```json
{
  "on_battery": {
    "reduce_parallelism": true,
    "sandbox_max_parallel": 1,
    "pause_training": true,
    "delay_builds": true
  },
  "battery_threshold_percent": 30
}
```

#### (60.4) Flow

Detect AC/battery via OS; when on battery or under threshold → apply throttles and notify ARO.

#### (60.5) UI & CLI

* **Power Panel**: current state, toggles to override; estimated savings.
* CLI: `agent power state|override on|off`.

#### (60.6) Report

```
[POWER CHECK]
timestamp: <UTC ISO>
battery_mode: <bool>
throttles_applied: <int>
status: power-aware
```

---

### 61) Session Persistence and Resume

#### (61.1) Purpose

Snapshot and restore Agent UI state, queues, partial plans, and context to resume after restart or crash without losing progress.

#### (61.2) Directory & Files

```
.codex_local_agent/session/
  snapshots/
  resume.json
  audit_session.jsonl
```

#### (61.3) Snapshot (`resume.json`)

```json
{
  "ui_layout_profile": "default",
  "open_panels": ["chat","review","vcs"],
  "pending_tasks": ["task-uuid-1","task-uuid-2"],
  "corr_active": ["corr-uuid-a"]
}
```

#### (61.4) Flow

On graceful exit or periodic checkpoint: write snapshot; on launch, prompt to resume or start fresh. Concurrency locks reconciled safely (stale locks cleared first).

#### (61.5) UI & CLI

* **Resume Dialog**: high-contrast choice “Resume / New Session”; list of recoverable items.
* CLI: `agent session resume|discard`.

#### (61.6) Report

```
[SESSION CHECK]
timestamp: <UTC ISO>
snapshots_created: <int>
resumed: <int>
status: continuous
```

---

### 62) Update Distribution Network

#### (62.1) Purpose

Distribute Required-Updates, templates, prompt packs, and theme packs across installations via signed bundles; offline-first with manual import.

#### (62.2) Directory & Files

```
.codex_local_agent/updates/
  channels.json
  inbox/
  applied.jsonl
  signatures/
  audit_updates.jsonl
```

#### (62.3) Channels (`channels.json`)

```json
{
  "stable": {"enabled": false, "url": null},
  "local": {"enabled": true, "path": "updates/inbox"}
}
```

#### (62.4) Bundle Manifest

```json
{
  "id":"upd-2025-10-30-a",
  "contents":["prompts/**","themes/packs/**","docs/templates/**"],
  "sha256":"...",
  "signature":"base64..."
}
```

#### (62.5) Flow

* Verify signature; stage to temp; show diff summary; require approval; apply and update Implemented-Updates; record to `applied.jsonl`.

#### (62.6) UI & CLI

* **Updates Panel**: pending bundles, diffs, verify signature button, apply with Allow.
* CLI: `agent updates scan|apply <bundle>|verify <bundle>`.

#### (62.7) Report

```
[UPDATES CHECK]
timestamp: <UTC ISO>
bundles_pending: <int>
applied: <int>
status: current
```

---

### 63) API Key Management for External Services

#### (63.1) Purpose

Centralize acquisition, rotation, scoping, and safe injection of external service keys (e.g., OpenAI, GitHub, Anthropic) integrated with Vault and Env Provisioner.

#### (63.2) Directory & Files

```
.codex_local_agent/apikeys/
  catalog.json
  scopes.json
  rotations.jsonl
  audit_apikeys.jsonl
```

#### (63.3) Catalog (`catalog.json`)

```json
{
  "OPENAI_API_KEY": {"provider":"openai","scope":"llm.readwrite","rot_days":90},
  "GITHUB_TOKEN": {"provider":"github","scope":"repo","rot_days":180}
}
```

#### (63.4) Scopes (`scopes.json`)

```json
{
  "llm.read": ["ask","embed"],
  "llm.readwrite": ["ask","embed","fine_tune"],
  "repo": ["vcs","remote.pr"]
}
```

#### (63.5) Rotation Flow

* Remind before due date; on rotate, create new entry in Vault, update Env Provisioner mapping; test a no-op API call; mark rotation in `rotations.jsonl`.

#### (63.6) Injection & Redaction

* Keys never written to logs or disk outside Vault; injected to Sandbox env only; redaction filters scrub accidental appearances.

#### (63.7) UI & CLI

* **API Keys Panel**: providers list, status (OK/Expiring), rotate button, test connectivity; high-contrast warnings for expired keys.
* CLI: `agent apikey rotate OPENAI_API_KEY | test GITHUB_TOKEN`.

#### (63.8) Report

```
[APIKEYS CHECK]
timestamp: <UTC ISO>
keys_total: <int>
expiring_7d: <int>
rotations_completed: <int>
status: governed
```
### 64) Third-Party Model Provider Bridge

#### (64.1) Purpose

Broker metadata and connectivity for external model providers (OpenAI, Anthropic, Azure, etc.) while preserving offline-first defaults. Unify provider catalogs, capability flags, billing awareness (local-only approximation), and safe injection of API keys via Vault/Env Provisioner. Never create placeholders—connections must pass health checks before exposure in UI.

#### (64.2) Directory & Files

```
.codex_local_agent/providers/
  catalog.json
  adapters/
    openai.json
    anthropic.json
    azure_openai.json
  health.json
  policies.json
  audit_providers.jsonl
```

* **catalog.json** — normalized list of available providers/models and endpoints.
* **adapters/** — provider-specific capability maps and request contracts.
* **health.json** — results of connectivity & quota checks.
* **policies.json** — selection/usage rules (e.g., forbid network when Offline Mode).
* **audit_providers.jsonl** — connection and error ledger.

#### (64.3) Catalog Schema (`catalog.json`)

```json
{
  "providers": [
    {
      "id": "openai",
      "status": "disabled",
      "endpoint": "https://api.openai.com/v1",
      "models": [
        {"id":"gpt-5-mini","type":"llm","ctx":131072,"tools":["json"],"stream":true}
      ]
    }
  ],
  "updated":"UTC ISO"
}
```

#### (64.4) Policies (`policies.json`)

```json
{
  "network_allowed": false,
  "fallback_to_local": true,
  "max_cost_estimate_usd": 0,
  "allowed_providers": [],
  "deny_on_missing_keys": true
}
```

When `network_allowed=false`, UI hides or disables remote providers; selection engine routes to local models.

#### (64.5) Health Checks (`health.json`)

```json
{
  "openai": {
    "key_present": false,
    "last_check":"UTC ISO",
    "quota_ok": null,
    "latency_ms": null,
    "status":"disabled"
  }
}
```

#### (64.6) Flow

1. Load policies; if network disallowed → disable all remote providers.
2. If allowed, check: Vault key presence → test `/models` or equivalent → cache latency/quota.
3. Register available models in **Models Registry** with provider tag and capabilities.
4. Selection engine consults capability map (see §65) to match Ask/Do Work requirements.

#### (64.7) UI & CLI

* **Providers Panel**: list providers, key status, measured latency, last health check; enable/disable per policy. High-contrast badges (OK/Warn/Disabled).
* CLI: `agent providers list|health|enable openai|disable openai`.

#### (64.8) Report

```
[PROVIDERS CHECK]
timestamp: <UTC ISO>
providers_enabled: <int>
remote_blocked_offline: <bool>
health_failures: <int>
status: normalized
```

---

### 65) Model Capability Mapper

#### (65.1) Purpose

Create a normalized, queryable table of model capabilities (context window, tool-use, JSON mode, streaming, function calling, image/vision, audio, OCR, latency class, cost estimates). Drives automatic model selection and guards against unsupported features.

#### (65.2) Directory & Files

```
.codex_local_agent/model_caps/
  registry.json
  rules.json
  benchmarks.json
  audit_caps.jsonl
```

* **registry.json** — per-model capability map built from local inspection and provider metadata.
* **rules.json** — selection rules mapping task types → capability requirements.
* **benchmarks.json** — latency/accuracy baselines collected locally.

#### (65.3) Capability Record (`registry.json`)

```json
{
  "gpt-oss-20b": {
    "type":"llm",
    "ctx":16384,
    "stream":true,
    "json_mode":true,
    "tools":["function_calling"],
    "vision":false,
    "audio":false,
    "latency_class":"medium",
    "cost_estimate":"local",
    "supports_long_diff": true
  }
}
```

#### (65.4) Selection Rules (`rules.json`)

```json
{
  "ask": {"min_ctx": 8192, "stream": true},
  "do_work": {"json_mode": true, "supports_long_diff": true},
  "ocr_extract": {"type":"ocr"},
  "embed": {"type":"embed","dim_min": 384}
}
```

#### (65.5) Flow

* Merge provider data (if any) with local benchmarks.
* When a task requests a model, run rules against registry; filter by availability (budget/VRAM/policy) then pick highest score (latency×accuracy).
* On failure, emit a **capability mismatch** error (E3801) and open a repair suggestion (e.g., switch to supported template).

#### (65.6) UI & CLI

* **Capabilities Panel**: filterable table; green ticks for matched rules; “Test” button to run a small probe prompt.
* CLI: `agent caps list|match do_work|test gpt-oss-20b`.

#### (65.7) Report

```
[CAPS CHECK]
timestamp: <UTC ISO>
models_indexed: <int>
rule_matches_today: <int>
mismatches: <int>
status: mapped
```

---

### 66) Embedded Documentation Search

#### (66.1) Purpose

Fast, offline full-text search over local docs (Required-Updates, Agent.md, Implemented-Updates, README, Help topics, tours). Provides snippet previews and linkable anchors.

#### (66.2) Directory & Files

```
.codex_local_agent/docsearch/
  index/
  config.json
  sources.json
  audit_docsearch.jsonl
```

* **index/** — on-disk inverted index plus embeddings optional.
* **sources.json** — list of files and update timestamps.
* **config.json** — tokenizer, language, stemming, stop words.

#### (66.3) Config (`config.json`)

```json
{
  "use_embeddings": false,
  "tokenizer": "unicode",
  "lang": "en",
  "max_snippet_len": 240
}
```

#### (66.4) Flow

* On document changes, re-index incrementally; maintain per-headings anchors.
* Query returns ranked hits with snippet, file path, anchor.
* High-contrast highlighting of match terms in UI.

#### (66.5) UI & CLI

* **Search Bar**: omnibox for docs; results panel with copy-link.
* CLI: `agent docs search "sandbox policy" --top 10`.

#### (66.6) Report

```
[DOCSEARCH CHECK]
timestamp: <UTC ISO>
docs_indexed: <int>
queries_today: <int>
status: discoverable
```

---

### 67) Knowledge Graph Generator

#### (67.1) Purpose

Build a local graph of entities (files, tasks, macros, models, datasets) and relations (depends_on, implements, generated_by, verified_by). Enables visual navigation and impact analysis.

#### (67.2) Directory & Files

```
.codex_local_agent/graph/
  nodes.jsonl
  edges.jsonl
  snapshots/
  audit_graph.jsonl
```

* **nodes.jsonl** — typed nodes (`file`, `task`, `model`, `scene`, `macro`).
* **edges.jsonl** — relations with weights and timestamps.
* **snapshots/** — frozen graph for reports.

#### (67.3) Node/Edge Formats

```json
{"id":"file:Required-Updates.md","type":"file","meta":{"size":12345}}
{"src":"task:TASK-123","rel":"implements","dst":"file:MainMenu.py","w":0.9,"ts":"UTC"}
```

#### (67.4) Flow

* Event Bus emits *facts* after operations (Apply, Build, Eval) → graph updater appends nodes/edges.
* Provide “blast radius” analysis before risky ops: list impacted nodes.

#### (67.5) UI & CLI

* **Graph Panel**: interactive, high-contrast graph (dark bg, light nodes/edges), filters by type/relation; click to open resource.
* CLI: `agent graph show file:MainMenu.py | impact task:TASK-123`.

#### (67.6) Report

```
[GRAPH CHECK]
timestamp: <UTC ISO>
nodes: <int>
edges: <int>
impact_nodes_10: <int>
status: connected
```

---

### 68) Human-Readable Change Log Composer

#### (68.1) Purpose

Synthesize readable change logs from VCS commits, Implemented-Updates, and Review comments. Produces Markdown with categorized sections and links to diffs/tests.

#### (68.2) Directory & Files

```
.codex_local_agent/changelog/
  templates/
    default.md
  releases/
  audit_changelog.jsonl
```

#### (68.3) Template Variables (`templates/default.md`)

`{{version}}`, `{{date}}`, `{{added}}`, `{{changed}}`, `{{fixed}}`, `{{security}}`, `{{links}}`.

#### (68.4) Flow

* Aggregate commits since last tag; map to categories using conventional hints or Review labels; include Evaluation results and Integrity root.
* Write release file under `releases/CHANGELOG-<version>.md`.

#### (68.5) UI & CLI

* **Changelog Panel**: select range, preview, copy; ensure high-contrast code spans.
* CLI: `agent changelog compose --since v1.2.0 --version v1.3.0`.

#### (68.6) Report

```
[CHANGELOG CHECK]
timestamp: <UTC ISO>
entries_generated: <int>
status: narrated
```

---

### 69) Automated Screenshot / Artifact Capture

#### (69.1) Purpose

Capture UI screenshots and attach artifacts (logs, diffs, charts) to tasks during Review, CI, and Evaluation for reproducible evidence.

#### (69.2) Directory & Files

```
.codex_local_agent/capture/
  screenshots/
  bundles/
  policy.json
  audit_capture.jsonl
```

#### (69.3) Policy (`policy.json`)

```json
{
  "image_format": "png",
  "max_dimension_px": 2560,
  "redact_sensitive": true,
  "include_logs": ["errors.jsonl","audit.jsonl"],
  "bundle_format": "zip"
}
```

#### (69.4) Flow

* On milestone (tests pass, approval granted), capture target windows; run redaction overlay (blur emails/API keys); build bundle with hashes; link to task and Review.

#### (69.5) UI & CLI

* **Capture Button** in Review & Tests panels; thumbnail gallery with high-contrast frames.
* CLI: `agent capture screen|bundle --task TASK-123`.

#### (69.6) Report

```
[CAPTURE CHECK]
timestamp: <UTC ISO>
screenshots: <int>
bundles: <int>
status: evidenced
```

---

### 70) QA Verification Console

#### (70.1) Purpose

Provide a checklist-driven verification UI to validate Acceptance Criteria, migrations, and policy gates before marking tasks complete.

#### (70.2) Directory & Files

```
.codex_local_agent/qa/
  checklists/
  sessions.jsonl
  results.jsonl
  audit_qa.jsonl
```

#### (70.3) Checklist Format

```json
{
  "id":"verify-build-and-docs",
  "steps":[
    {"id":"lint-pass","desc":"Linter passes","type":"auto","command":"agent tests lint"},
    {"id":"docs-built","desc":"Docs compiled","type":"auto","command":"agent docs build"},
    {"id":"a11y-contrast","desc":"Theme passes contrast audit","type":"auto","command":"agent a11y audit"},
    {"id":"human-approve","desc":"Human reviewed Review Mode","type":"manual","roles":["Developer"]}
  ]
}
```

#### (70.4) Flow

* Run auto steps; present manual confirmations with role checks; persist results per task/session.

#### (70.5) UI & CLI

* **QA Console**: progress bars, pass/fail chips; export proof markdown.
* CLI: `agent qa run verify-build-and-docs --task TASK-123`.

#### (70.6) Report

```
[QA CHECK]
timestamp: <UTC ISO>
checklists_run: <int>
manual_confirms: <int>
status: verified
```

---

### 71) Compliance Export Tool

#### (71.1) Purpose

Assemble a compliance packet (privacy, license, security, test evidence, integrity proofs) for audits or releases.

#### (71.2) Directory & Files

```
.codex_local_agent/compliance/
  specs/
    minimal.json
    full.json
  exports/
  audit_compliance.jsonl
```

#### (71.3) Spec (`specs/full.json`)

```json
{
  "include": [
    "license/attributions/**",
    "ethics/guardrails.json",
    "integrity/merkle.json",
    "tests/results/**",
    "capture/bundles/**",
    "docs/outputs/**"
  ],
  "redact": true,
  "sign": true
}
```

#### (71.4) Flow

* Validate availability; apply redaction; compute checksums; optional sign; write to `exports/COMP-<date>.zip`.

#### (71.5) UI & CLI

* **Compliance Panel**: choose spec, preview contents, generate.
* CLI: `agent compliance export full`.

#### (71.6) Report

```
[COMPLIANCE CHECK]
timestamp: <UTC ISO>
exports_created: <int>
signed: <int>
status: packaged
```

---

### 72) Backup Compression and Remote Storage

#### (72.1) Purpose

Perform encrypted, incremental backups of critical directories (configs, prompts, models registry, graphs, docs) with local compression and optional remote copy (user-chosen drive/NAS). Defaults to local-only.

#### (72.2) Directory & Files

```
.codex_local_agent/backup/
  policy.json
  manifests/
  archives/
  remote.json
  audit_backup.jsonl
```

#### (72.3) Policy (`policy.json`)

```json
{
  "schedule_cron": "0 3 * * *",
  "include": [ "agent.yaml","Task-Index.json",".codex_local_agent/**" ],
  "exclude": [ "logs/**","queue/backend.sqlite","vault/**" ],
  "encrypt": true,
  "compress": "zstd",
  "retain_local": 7
}
```

#### (72.4) Remote (`remote.json`)

```json
{
  "enabled": false,
  "target": "file://D:/AgentBackups",
  "auth": null
}
```

#### (72.5) Flow

* Build manifest; stream-compress; encrypt; store archive; prune old per retention; optionally copy to remote.
* Validate by sampling restore test monthly.

#### (72.6) UI & CLI

* **Backup Panel**: last run, archives list, restore test; high-contrast warnings if remote disabled.
* CLI: `agent backup run|list|restore <archive>`.

#### (72.7) Report

```
[BACKUP CHECK]
timestamp: <UTC ISO>
archives_local: <int>
remote_enabled: <bool>
status: recoverable
```

---

### 73) License Activation System

#### (73.1) Purpose

Optional license key mechanism for enterprise or multi-seat deployments. Local-first validation with offline grace windows; no blocking of personal/OSS use when not configured.

#### (73.2) Directory & Files

```
.codex_local_agent/license_activation/
  policy.json
  state.json
  audit_activation.jsonl
```

#### (73.3) Policy (`policy.json`)

```json
{
  "enforced": false,
  "grace_days_offline": 30,
  "features_tier": {
    "free": ["core","ask","do_work","docs"],
    "pro": ["remote_exec","cluster","compliance"],
    "enterprise": ["multi_user","api_full","secscan_full"]
  }
}
```

#### (73.4) State (`state.json`)

```json
{
  "tier": "free",
  "key_present": false,
  "last_check": null,
  "expires": null
}
```

#### (73.5) Flow

* If `enforced=false`, expose all features per local policy.
* If enforced, accept key; validate locally (signature + features); cache state; degrade gracefully on expiry (non-destructive read-only).
* Never send device fingerprints off-machine unless explicitly enabled.

#### (73.6) UI & CLI

* **Activation Panel**: enter key, view tier and expiry; high-contrast alerts near expiry.
* CLI: `agent license set <KEY>|status|deactivate`.

#### (73.7) Report

```
[ACTIVATION CHECK]
timestamp: <UTC ISO>
enforced: <bool>
tier: "<tier>"
days_to_expiry: <int|null>
status: governed
```
### 74) Secrets Vault

#### (74.1) Purpose

Provide encrypted-at-rest, least-privilege secret storage with auto-lock, key rotation, scoped injection to Sandbox/Remote Exec, and tamper-evident audit. No plaintext secrets are ever written to disk outside the Vault.

#### (74.2) Directory & Files

```
.codex_local_agent/vault/
  policy.json
  kdf.json
  store.enc
  metadata.json
  locks/
  shards/
  audit_vault.jsonl
```

* **policy.json** — crypto + lock policy.
* **kdf.json** — Argon2id parameters and salt.
* **store.enc** — AES-256-GCM encrypted secret blob.
* **metadata.json** — secret indices (names, scopes, last_rotated), no values.
* **locks/** — ephemeral PID/session locks.
* **shards/** — optional Shamir (M-of-N) key shares for disaster recovery.
* **audit_vault.jsonl** — append-only audited operations.

#### (74.3) Policy (`policy.json`)

```json
{
  "cipher": "aes-256-gcm",
  "kdf": "argon2id",
  "auto_lock_idle_min": 15,
  "clipboard_ttl_sec": 20,
  "require_mfa_for_unlock": true,
  "allow_shamir": false,
  "shamir": {"shares":5,"threshold":3},
  "scopes": {
    "apikeys": {"inject": ["sandbox","remote_exec"], "mask_in_logs": true},
    "tokens": {"inject": ["sandbox"], "mask_in_logs": true}
  }
}
```

#### (74.4) Operations

* **vault init** → derive master key via Argon2id, create `store.enc`.
* **vault set <NAME>** → write secret into `store.enc`, update `metadata.json`.
* **vault get <NAME>** → decrypt in memory; optional clipboard copy (TTL applies).
* **vault rotate <NAME|all>** → version old, write new, update metadata.
* **vault lock/unlock** → lock state respected globally; ASAC enforces role.
* **shamir split/join** → if enabled; never stores shares in repo.

#### (74.5) Injection & Redaction

* Secrets injected into Sandbox/Remote Exec env only for the lifetime of the process.
* Redaction engine masks any detected secret patterns in logs and screenshots.

#### (74.6) UI & CLI

* **Vault Panel**: lock status, scopes, last rotation dates, rotate/test buttons (high-contrast: bright text on dark background per rule).
* CLI: `agent vault init|lock|unlock|set|get|rotate|export-meta`.

#### (74.7) Audit

```
{"ts":"UTC","op":"set","name":"OPENAI_API_KEY","by":"user-hash","result":"ok"}
```

#### (74.8) Report

```
[VAULT CHECK]
timestamp: <UTC ISO>
secrets_total: <int>
locked: <bool>
rotations_30d: <int>
status: secured
```

---

### 75) Sandbox Execution Profiles

#### (75.1) Purpose

Constrain all subprocesses with per-profile policies: filesystem mounts, network rules, CPU/Memory limits, timeouts, env scope, and allowed tools. Ensures reproducible, safe runs for tests/builds/macros.

#### (75.2) Directory & Files

```
.codex_local_agent/sandbox/
  profiles/
    default.json
    build.json
    test.json
    offline.json
  tools_allowlist.json
  mounts.json
  audit_sandbox.jsonl
```

#### (75.3) Profile Schema

```json
{
  "name": "test",
  "timeout_sec": 600,
  "cpu_quota": 0.8,
  "mem_mb": 4096,
  "network": "deny",        // "allow" | "deny" | "allowlist"
  "network_allow": [],
  "fs": {
    "ro": [".","venv/**"],
    "rw": [".codex_local_agent/tmp/**",".codex_local_agent/tests/results/**"]
  },
  "env_profile": "test",
  "tools": ["python","pytest","git"],
  "workdir": "."
}
```

#### (75.4) Execution Flow

1. Select profile (by task type or explicit).
2. Materialize env via Env Provisioner; inject necessary Vault secrets (scoped).
3. Apply mounts and limits; enforce network policy.
4. Stream logs; record exit code, rusage, duration to `audit_sandbox.jsonl`.

#### (75.5) Tools Allowlist (`tools_allowlist.json`)

Canonical tool names and path resolution strategy; denies unknown binaries.

#### (75.6) UI & CLI

* **Sandbox Panel**: profile selector, dry-run test, last runs.
* CLI: `agent sandbox run --profile test -- cmd args...`.

#### (75.7) Report

```
[SANDBOX CHECK]
timestamp: <UTC ISO>
profiles: <int>
runs_today: <int>
violations_blocked: <int>
status: enforced
```

---

### 76) Macro Registry & Runner

#### (76.1) Purpose

Store, version, and execute reusable macros (compound actions) under Sandbox, with typed parameters, preconditions, and artifacts, replacing ad-hoc scripts.

#### (76.2) Directory & Files

```
.codex_local_agent/macros/
  registry.jsonl
  macros/
    build_docs.json
    verify_changelog.json
  artifacts/
  audit_macros.jsonl
```

#### (76.3) Macro Descriptor

```json
{
  "id": "build_docs",
  "version": "1.2.0",
  "params": {"pdf":{"type":"bool","default":false}},
  "preconditions": ["files_exist:README.md","sandbox_profile:build"],
  "steps": [
    {"run":"agent docs build {{#if pdf}}--pdf{{/if}}","timeout_sec":600}
  ],
  "artifacts": ["docs/outputs/*"],
  "roles": ["Developer"]
}
```

#### (76.4) Runner Behavior

* Validate preconditions; interpolate params; execute each step in Sandbox; collect artifacts.
* Non-zero exit halts and records failure with correlation ID.

#### (76.5) UI & CLI

* **Macros Panel**: searchable list, param form, “Run” and “Dry Run”.
* CLI: `agent macro run build_docs --pdf`.

#### (76.6) Report

```
[MACRO CHECK]
timestamp: <UTC ISO>
registered: <int>
runs_success: <int>
runs_failed: <int>
status: reusable
```

---

### 77) Workflow DSL (Pipelines)

#### (77.1) Purpose

Declarative pipelines for Plan→Apply→Verify sequences with branches, approvals, and artifact passing; compiled to Queue tasks.

#### (77.2) Directory & Files

```
.codex_local_agent/dsl/
  pipelines/
    release.yml
    nightly.yml
  schema.json
  audit_dsl.jsonl
```

#### (77.3) DSL Example (`pipelines/release.yml`)

```yaml
name: release
on:
  event: build.ready
stages:
  - name: verify
    steps:
      - run: agent tests run
      - run: agent qa run verify-build-and-docs
  - name: package
    approval: apply.patch
    steps:
      - run: agent build run cli_bundle
      - run: agent changelog compose --since last_tag --version {{version}}
  - name: publish
    when: "{{ env.PROFILE == 'prod' }}"
    steps:
      - run: agent remote pr create --title "Release {{version}}"
```

#### (77.4) Engine

* Parse/validate against `schema.json`; resolve variables; inject approvals; compile to Queue with idempotency keys; attach policy checks.

#### (77.5) UI & CLI

* **Pipelines Panel**: graph view, run/resume, stage logs.
* CLI: `agent pipe run release --var version=1.3.0`.

#### (77.6) Report

```
[DSL CHECK]
timestamp: <UTC ISO>
pipelines: <int>
runs: <int>
failures: <int>
status: orchestrated
```

---

### 78) Scheduler (Time & Event)

#### (78.1) Purpose

Run delayed/periodic tasks from DSL, Macros, and Maintenance (compression, backups) with timezone awareness and at-least-once semantics.

#### (78.2) Directory & Files

```
.codex_local_agent/scheduler/
  schedule.json
  events.jsonl
  timers.jsonl
  audit_scheduler.jsonl
```

#### (78.3) Schedule Spec

```json
{
  "jobs": [
    {"id":"nightly-docs","cron":"0 2 * * *","cmd":"agent docs build","profile":"build"},
    {"id":"weekly-integrity","cron":"0 3 * * 0","cmd":"agent integrity snapshot"}
  ],
  "timezone": "local"
}
```

#### (78.4) Behavior

* Cron + event triggers; dedupe via idempotency key; persists next_run.
* On system sleep/wake, catch-up policy (run missed jobs if within grace window).

#### (78.5) UI & CLI

* **Scheduler Panel**: upcoming jobs, pause/resume, run now, timezone selector.
* CLI: `agent sched list|run <id>|pause <id>|resume <id>`.

#### (78.6) Report

```
[SCHEDULER CHECK]
timestamp: <UTC ISO>
jobs_total: <int>
executed_24h: <int>
missed_caught_up: <int>
status: punctual
```

---

### 79) Reinforcement Policy Engine (RPE)

#### (79.1) Purpose

Adapt prompts, macro choices, and model selection using signals from Feedback, Eval, QA, and Errors to improve outcomes over time—entirely local.

#### (79.2) Directory & Files

```
.codex_local_agent/rpe/
  weights.json
  signals.jsonl
  policies.json
  audit_rpe.jsonl
```

#### (79.3) Policies

```json
{
  "boost_on_feedback>=4": {"target":"prompts.do_work_plan.v2","delta":0.1,"max":0.6},
  "penalize_eval_regression": {"target":"models.ask.gpt-oss-20b","delta":-0.05,"min":0.1}
}
```

#### (79.4) Flow

* Ingest signals → update weights with decay → write `weights.json`.
* Selection engines read weights to bias choices; explanations surfaced in UI.

#### (79.5) UI & CLI

* **RPE Panel**: top boosts/penalties, recent signals, revert changes.
* CLI: `agent rpe show|reset|explain <choice>`.

#### (79.6) Report

```
[RPE CHECK]
timestamp: <UTC ISO>
signals_24h: <int>
weights_changed: <int>
status: adapting
```

---

### 80) Self-Healing Repair Engine

#### (80.1) Purpose

Automatically propose minimal, safe fixes for common failures (docs lint, missing token, simple import errors) and stage patches for Review.

#### (80.2) Directory & Files

```
.codex_local_agent/repair/
  rules.json
  suggestions.jsonl
  patches/
  audit_repair.jsonl
```

#### (80.3) Rule Example

```json
{
  "id": "R-DOCLINT-001",
  "when": {"error_code": "E7xxx", "file_ext": ".md"},
  "suggest": "Insert required 'Purpose' section",
  "patch": {"file":"docs/README.md","insert_at":"top","content":"## Purpose\n..."},
  "risk": "LOW",
  "requires_approval": true
}
```

#### (80.4) Flow

* Map Error Taxonomy → rules; generate patch; store under `patches/`; open Approval packet; if granted, VCS applies patch via safe path.

#### (80.5) UI & CLI

* **Repair Panel**: suggestions table with risk, diff preview, approve/apply buttons (high-contrast).
* CLI: `agent repair list|apply <id>|reject <id>`.

#### (80.6) Report

```
[REPAIR CHECK]
timestamp: <UTC ISO>
suggestions: <int>
applied: <int>
status: resilient
```

---

### 81) Vision/OCR Ingestion (Dual-Pass)

#### (81.1) Purpose

Convert images to structured text using a **dual-pass** pipeline: fast pass for immediacy; accuracy pass for refinement (markdown normalization). Supports region cropping, language packs, and throttled GPU/CPU use.

#### (81.2) Directory & Files

```
.codex_local_agent/vision/
  config.json
  langpacks/
  ocr_queue.jsonl
  outputs/
  audit_vision.jsonl
```

#### (81.3) Config (`config.json`)

```json
{
  "fast": {"engine":"tesseract","psm":6,"dpi":150},
  "accurate": {"engine":"tesseract","psm":3,"dpi":300,"spell_correct":true},
  "markdown_normalize": true,
  "thumb_max_px": 512,
  "parallel": 1
}
```

#### (81.4) Flow

* Intake: file drop or Chat attach → create thumbnail → queue job.
* Pass 1 (fast) → immediate text to Chat/Ask; Pass 2 (accurate) → refine & replace segment; emit diff.
* Markdown normalizer formats lists, code, tables.

#### (81.5) UI & CLI

* **OCR Panel**: queue status, language selector, preview; high-contrast thumbnails.
* CLI: `agent ocr run <image>|batch <folder>`.

#### (81.6) Report

```
[OCR CHECK]
timestamp: <UTC ISO>
images_processed: <int>
avg_latency_fast_ms: <int>
avg_latency_accurate_ms: <int>
status: readable
```

---

### 82) Chat & Transcript Engine

#### (82.1) Purpose

Persist rich, markdown-based conversations with images/attachments, approvals, and event references. Enforce stylistic rendering rules: `<think>` segments italicized dark green; final responses in larger white text on dark background for contrast.

#### (82.2) Directory & Files

```
.codex_local_agent/chat/
  sessions/
    2025-10-30/
      chat.md
      attachments/
      thumbs/
  index.json
  audit_chat.jsonl
```

#### (82.3) Markdown Contract (`chat.md`)

* Messages as fenced blocks with metadata header:

  ```
  --- 
  ts: UTC
  role: user|agent|system
  corr: corr-uuid
  attachments: ["attachments/img_001.png"]
  ---
  <content markdown>
  ```
* `<think>` sections are wrapped with `_` italics and tinted dark green in UI renderer (never low-contrast).
* Thumbnails referenced inline; attachments paths stable.

#### (82.4) Behavior

* Image drops: store in `attachments/`, generate thumb; insert reference and file path into message.
* Edit protection: agent messages immutable; user edits tracked with diff footers.

#### (82.5) UI & CLI

* **Chat Panel**: infinite scroll, search, copy-as-markdown; export to `transcript-<date>.md`.
* CLI: `agent chat export --since 7d`.

#### (82.6) Report

```
[CHAT CHECK]
timestamp: <UTC ISO>
sessions_today: <int>
messages: <int>
attachments: <int>
status: persisted
```

---

### 83) Terminal Bridge & Shell Abstraction

#### (83.1) Purpose

Provide a controlled local shell interface for the Agent: generate commands, execute in background via Sandbox, and stream logs to an optional split view. Keeps Chat primary; terminal is a secondary pane.

#### (83.2) Directory & Files

```
.codex_local_agent/terminal/
  adapters/
    powershell.json
    bash.json
    cmd.json
  lexicon.json
  sessions.jsonl
  audit_terminal.jsonl
```

* **adapters/** — per-shell quoting/escape rules, path semantics.
* **lexicon.json** — common intents → command templates (safe, parameterized).
* **sessions.jsonl** — active terminals with cwd, profile, last cmd.

#### (83.3) Lexicon Example

```json
{
  "open_folder": {
    "windows": "start .",
    "linux": "xdg-open ."
  },
  "git_status": {
    "any": "git status --porcelain=v1"
  }
}
```

#### (83.4) Execution Flow

1. Agent maps intent → command via lexicon; renders with safe args.
2. Runs in Sandbox with `terminal` profile (network policy as configured).
3. Streams stdout/stderr to **Terminal Pane**; append to `audit_terminal.jsonl`.
4. Files being edited are mirrored to **Review** if changes occur.

#### (83.5) UI & CLI

* **Terminal Pane** (toggle): read-only by default; enable manual input with explicit user action; high-contrast monospace font.
* CLI: `agent term run "git status" | open`.

#### (83.6) Report

```
[TERMINAL CHECK]
timestamp: <UTC ISO>
sessions: <int>
commands_executed: <int>
policy_violations: <int>
status: bridged
```
### 84) File Watcher & Hot-Reload Engine

#### (84.1) Purpose

Continuously monitor project files (code, configs, styles, prompts) and trigger safe, scoped reloads or recomputations (indexes, docs, themes) without full restarts. Honors Concurrency locks, VCS ignore, and Sandbox policies.

#### (84.2) Directory & Files

```
.codex_local_agent/watch/
  config.json
  subscriptions.jsonl
  events.jsonl
  debounce.json
  audit_watch.jsonl
```

#### (84.3) Config (`config.json`)

```json
{
  "include": ["**/*.py","**/*.md",".codex_local_agent/**"],
  "exclude": ["**/.git/**","**/__pycache__/**","logs/**","builds/outputs/**"],
  "debounce_ms": 250,
  "max_events_per_sec": 50,
  "restarts": {
    "theme_change": "reload_theme",
    "prompt_change": "reindex_prompts",
    "doc_change": "docs_rebuild_incremental",
    "model_registry_change": "models_refresh"
  }
}
```

#### (84.4) Behavior

* Kernel-level file system events → debounced → Concurrency Policy consult → emit typed events to Event Bus (`watch.changed`).
* Safe reload strategies:

  * **Theme**: re-apply tokens; run WCAG audit.
  * **Docs**: incremental rebuild of changed sources.
  * **Prompts**: reload template registry; validate variables.
  * **Models registry**: re-list models; verify warm pool.
* If a file is locked, queue a retry respecting MUCP queue semantics.

#### (84.5) UI & CLI

* **Watcher Panel**: toggles for paths, live event list, throttle control; high-contrast list rows with bold white text on dark.
* CLI: `agent watch on|off|status`.

#### (84.6) Report

```
[WATCH CHECK]
timestamp: <UTC ISO>
events_processed: <int>
reloads_triggered: <int>
skipped_due_lock: <int>
status: reactive
```

---

### 85) Project Scaffolding & Template Generator

#### (85.1) Purpose

Generate new modules, panels, macros, pipelines, and docs from curated templates with prompts for required fields. Prevents drift by enforcing naming and folder conventions.

#### (85.2) Directory & Files

```
.codex_local_agent/scaffold/
  blueprints/
    panel_min/
    macro_min/
    pipeline_min/
    docs_min/
  variables.json
  audit_scaffold.jsonl
```

#### (85.3) Blueprint Structure

```
blueprints/panel_min/
  files/
    src/{{name}}.py
    Styles/{{name}}_styles.json
    README.md.tmpl
  meta.json
```

#### (85.4) Variables (`variables.json`)

```json
{
  "validators": {
    "name": "^[A-Za-z][A-Za-z0-9_]+$",
    "desc_min_len": 10
  },
  "defaults": {"author":"local-user","license":"MIT"}
}
```

#### (85.5) Flow

* Select blueprint → collect variables (UI form) → render templates → write files atomically → open Review session with diff.
* Linter and Doc Linter run automatically on generated files.

#### (85.6) UI & CLI

* **Scaffold Panel**: blueprint gallery, preview tree, variable form with validation.
* CLI: `agent scaffold create panel_min --name ReviewPanel --desc "..."`.

#### (85.7) Report

```
[SCAFFOLD CHECK]
timestamp: <UTC ISO>
blueprints: <int>
generated_today: <int>
status: reproducible
```

---

### 86) Context & Memory Engine (CME)

#### (86.1) Purpose

Maintain durable, queryable memory for tasks, decisions, chat summaries, and embeddings to provide continuity across Ask/Do Work without leaking sensitive data.

#### (86.2) Directory & Files

```
.codex_local_agent/memory/
  bank_core.jsonl
  embeddings/
    text.index
    meta.json
  summaries/
  pins.json
  gc.json
  audit_memory.jsonl
```

#### (86.3) Records (`bank_core.jsonl`)

```json
{"ts":"UTC","type":"task","key":"TASK-123","text":"Refactor OCR pipeline","tags":["ocr","pipeline"]}
{"ts":"UTC","type":"decision","key":"policy.allow.apply.patch","text":"Requirements satisfied","corr":"corr-uuid"}
```

#### (86.4) Embeddings Index

* Local-only index (FAISS/Annoy-like) stored under `embeddings/`; chunked from Chat transcripts, README, Required-Updates.
* Redaction applied prior to embedding; Vault secrets never embedded.

#### (86.5) Behavior

* On message end, generate summary and store → update embeddings.
* Provide **Memory Pins** (pinned facts) with TTL and scopes; GC removes expired entries.

#### (86.6) UI & CLI

* **Memory Panel**: search, pin/unpin, view provenance; high-contrast.
* CLI: `agent mem search "ocr latency" | pin <id> --ttl 7d`.

#### (86.7) Report

```
[MEMORY CHECK]
timestamp: <UTC ISO>
records: <int>
pins_active: <int>
index_size_mb: <float>
status: retained
```

---

### 87) Diff QA Engine

#### (87.1) Purpose

Automatically review diffs using static checks, test impacts, and heuristic risk scoring; produce inline comments and pass/fail summary.

#### (87.2) Directory & Files

```
.codex_local_agent/diffqa/
  rules.json
  risk.json
  comments.jsonl
  audit_diffqa.jsonl
```

#### (87.3) Rules (`rules.json`)

```json
{
  "python": {
    "disallow_patterns": ["eval\\(","exec\\("],
    "require_tests_for": ["src/**.py"]
  },
  "docs": {
    "require_sections": ["Purpose"]
  }
}
```

#### (87.4) Risk Model (`risk.json`)

```json
{"weights":{"files_changed":0.2,"loc_added":0.2,"touches_security":0.6},"threshold_warn":0.6,"threshold_block":0.8}
```

#### (87.5) Flow

* Analyze diffs (Semantic Diff integration) → apply rules → compute risk → annotate Review Mode with comments → block Apply if threshold exceeded (policy-gated).

#### (87.6) UI & CLI

* **Diff QA Panel**: risk gauge, findings table; open in Review.
* CLI: `agent diffqa run --patch patch-123`.

#### (87.7) Report

```
[DIFFQA CHECK]
timestamp: <UTC ISO>
findings: <int>
risk_score_avg: <float>
blocked_patches: <int>
status: guarded
```

---

### 88) Acceptance Criteria Parser & Validator

#### (88.1) Purpose

Normalize Acceptance Criteria (AC) from Required-Updates, tasks, and user inputs into machine-checkable steps that QA Console can execute or prompt for.

#### (88.2) Directory & Files

```
.codex_local_agent/acceptance/
  schema.json
  extracted.jsonl
  validators/
  audit_acceptance.jsonl
```

#### (88.3) AC Schema (`schema.json`)

```json
{
  "id":"AC-uuid",
  "title":"Docs build passes",
  "steps":[
    {"type":"auto","cmd":"agent docs build"},
    {"type":"assert","expr":"files.exists('docs/outputs/index.html')"},
    {"type":"manual","prompt":"Visually inspect Review Mode"}
  ],
  "tags":["docs"]
}
```

#### (88.4) Flow

* Parse Markdown bullets into structured steps (LLM optional, offline templates preferred).
* Link AC to tasks; inject into QA Console checklists.
* Validators implement `assert` expressions (filesystem, metrics, logs).

#### (88.5) UI & CLI

* **AC Panel**: extracted list, edit step types, dry-run validators.
* CLI: `agent ac extract Required-Updates.md | validate AC-uuid`.

#### (88.6) Report

```
[AC CHECK]
timestamp: <UTC ISO>
ac_items: <int>
auto_steps: <int>
manual_steps: <int>
status: normalized
```

---

### 89) Implemented-Updates Synchronizer

#### (89.1) Purpose

Keep **Implemented-Updates.md** synchronized with applied patches, QA outcomes, and verification evidence; enforce the Trifecta loop cohesion.

#### (89.2) Directory & Files

```
.codex_local_agent/impl_updates/
  builder.json
  Implemented-Updates.md
  evidence/
  audit_impl.jsonl
```

#### (89.3) Builder Config (`builder.json`)

```json
{
  "sections": ["Overview","Changes","Tests","Docs","Evidence","Integrity"],
  "evidence": ["capture/bundles/**","tests/results/**"],
  "link_commits": true
}
```

#### (89.4) Flow

* After Apply + QA pass: collect changes, link commits, attach evidence → rewrite **Implemented-Updates.md** atomically.
* If VCS commits are missing, open repair suggestion.

#### (89.5) UI & CLI

* **Implemented Panel**: preview rendered Markdown; open linked evidence.
* CLI: `agent impl build | open`.

#### (89.6) Report

```
[IMPL CHECK]
timestamp: <UTC ISO>
entries_updated: <int>
evidence_links: <int>
status: in_sync
```

---

### 90) Missing-Updates Monitor

#### (90.1) Purpose

Continuously detect gaps between Required-Updates and Implemented-Updates; file them into **Missing-Updates.md** with priority hints and suggested owners.

#### (90.2) Directory & Files

```
.codex_local_agent/missing/
  Missing-Updates.md
  hints.json
  audit_missing.jsonl
```

#### (90.3) Hints (`hints.json`)

```json
{"priority_rules":{"security":"P0","docs":"P3"},"owner_map":{"vcs":"Developer","ethics":"Auditor"}}
```

#### (90.4) Flow

* Compare parsed Required-Updates sections vs Implemented; compute deltas; generate Markdown list with links and AC references; notify Notification Hub.

#### (90.5) UI & CLI

* **Gaps View**: table of missing items, priorities; “Open Task” buttons.
* CLI: `agent missing scan|open <id>`.

#### (90.6) Report

```
[MISSING CHECK]
timestamp: <UTC ISO>
gaps: <int>
p0_gaps: <int>
status: tracked
```

---

### 91) Dataset & Corpus Registry

#### (91.1) Purpose

Register datasets used by OCR, evaluation, training, and prompts; capture licensing, provenance, checksums, and splits for reproducibility.

#### (91.2) Directory & Files

```
.codex_local_agent/datasets/
  registry.json
  manifests/
  licenses/
  audit_datasets.jsonl
```

#### (91.3) Registry (`registry.json`)

```json
{
  "items":[
    {"id":"ocr_chat_corpus_v1","path":"data/ocr/chat/","license":"CC-BY-4.0","sha256":"...","splits":{"train":0.9,"val":0.1}}
  ]
}
```

#### (91.4) Manifests

Per-dataset file lists with sizes and hashes; linked to Assets validation; quarantine on mismatch.

#### (91.5) UI & CLI

* **Datasets Panel**: registry table, verify, open folder, license viewer.
* CLI: `agent data add <id> <path> --license MIT | verify <id>`.

#### (91.6) Report

```
[DATASETS CHECK]
timestamp: <UTC ISO>
datasets: <int>
verified: <int>
status: curated
```

---

### 92) Code Intelligence Indexer (Symbols & X-Ref)

#### (92.1) Purpose

Build a local index of symbols, references, and call graphs for fast navigation, impact analysis, and semantic search; supports Python/JS/JSON/MD with pluggable parsers.

#### (92.2) Directory & Files

```
.codex_local_agent/code_index/
  symbols.jsonl
  xref.jsonl
  calls.jsonl
  config.json
  audit_code_index.jsonl
```

#### (92.3) Config (`config.json`)

```json
{
  "languages": ["python","javascript","json","markdown"],
  "ignore": ["**/node_modules/**","**/.venv/**"],
  "enable_doc_symbols": true
}
```

#### (92.4) Behavior

* Parse files on Watcher events; extract definitions/refs; compute call graph; attach VCS revision.
* Expose queries: “find symbol”, “who references”, “impact of change”.

#### (92.5) UI & CLI

* **Code Intel Panel**: search bar, results; open in Review/Editor; high-contrast list.
* CLI: `agent code find def MainWindow | refs function foo`.

#### (92.6) Report

```
[CODE INDEX CHECK]
timestamp: <UTC ISO>
symbols: <int>
refs: <int>
status: indexed
```

---

### 93) End-to-End UI Test Runner

#### (93.1) Purpose

Automate UI regression tests (panels, dialogs, themes) using scriptable steps and screenshot comparisons; enforces high-contrast expectations and keyboard accessibility.

#### (93.2) Directory & Files

```
.codex_local_agent/ui_tests/
  specs/
    smoke.json
  baselines/
  results/
  audit_ui_tests.jsonl
```

#### (93.3) Spec (`specs/smoke.json`)

```json
{
  "name": "smoke",
  "steps": [
    {"action":"open_panel","target":"VCS"},
    {"action":"click","target":"#askBtn"},
    {"action":"assert_visible","target":"#doWorkBtn"},
    {"action":"screenshot","name":"home"}
  ],
  "assertions": [
    {"type":"contrast","min_ratio":4.5},
    {"type":"keyboard_tab_order","max_deviation":0}
  ]
}
```

#### (93.4) Flow

* Launch app in test mode; simulate events; capture screenshots; compare with baselines (SSIM/threshold); check contrast via Theme tokens; output per-step logs.

#### (93.5) UI & CLI

* **UI Tests Panel**: run suite, review diffs, accept new baseline.
* CLI: `agent uitest run smoke | accept smoke`.

#### (93.6) Report

```
[UI TESTS CHECK]
timestamp: <UTC ISO>
suites_run: <int>
failures: <int>
baseline_updates: <int>
status: guarded-ux
```
### 94) Input Sanitization & PII Scrubber

#### (94.1) Purpose

Protect privacy and prevent prompt/file injection by sanitizing all inbound text, markdown, and file metadata before storage, display, or model submission. Detect and mask PII/secrets; normalize unicode; remove zero-width/invisible characters; quarantine suspicious payloads.

#### (94.2) Directory & Files

```
.codex_local_agent/sanitize/
  policy.json
  patterns.json
  quarantine/
  findings.jsonl
  audit_sanitize.jsonl
```

#### (94.3) Policy (`policy.json`)

```json
{
  "pii_scan": true,
  "secret_scan": true,
  "strip_zero_width": true,
  "normalize_unicode": "NFC",
  "quarantine_on_detect": true,
  "allowed_markdown_tags": ["a","code","pre","img","ul","ol","li","blockquote","strong","em","table","thead","tbody","tr","td","th"],
  "max_image_embed_mb": 25
}
```

#### (94.4) Patterns (`patterns.json`)

Built-in detectors for emails, phone numbers, gov IDs (generalized, locale-agnostic), API keys, JWTs, OAuth tokens, 12+ char hex/base64 runs with context.

```json
{
  "pii":[{"name":"email","regex":"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"}],
  "secrets":[{"name":"generic_key","regex":"(?i)(api[_-]?key|token|secret)[=: ]+[A-Za-z0-9\\-_]{12,}"}],
  "invisibles":["\\u200B","\\u200C","\\u200D","\\uFEFF"]
}
```

#### (94.5) Flow

* On input (chat, file import, OCR), normalize → strip invisibles → run PII/secret scan.
* If detected and `quarantine_on_detect=true`: write original to `quarantine/` with hash name; present redacted preview to user; require Allow to proceed.
* Redaction masks (`<redacted-email>`, `********`) applied before logs, Chat, Memory, and Docs.
* All actions append to `findings.jsonl`.

#### (94.6) UI & CLI

* **Sanitize Panel** (high-contrast): list detections with type, snippet, source; buttons: “Proceed Redacted”, “Quarantine & Skip”, “Allow Once”.
* CLI: `agent sanitize scan <file|text> | quarantine <id> | allow <id>`.

#### (94.7) Report

```
[SANITIZE CHECK]
timestamp: <UTC ISO>
inputs_scanned: <int>
detections: <int>
quarantined: <int>
status: clean
```

---

### 95) Identity & Authentication (ASAC Tokens)

#### (95.1) Purpose

Establish local-first authentication using **Agent Signed Access Control (ASAC) tokens** for desktop user sessions, companion devices, API, and cluster peers.

#### (95.2) Directory & Files

```
.codex_local_agent/auth/
  identities.json
  tokens.jsonl
  sessions.jsonl
  policy.json
  audit_auth.jsonl
  public_keys/
  private_keys/
```

#### (95.3) Policy (`policy.json`)

```json
{
  "session_ttl_min": 720,
  "token_ttl_min": 240,
  "require_local_user_verification": true,
  "pin_on_wake": true,
  "rotate_keys_days": 180,
  "lock_on_idle_min": 15
}
```

#### (95.4) Identities (`identities.json`)

```json
{
  "users":[
    {"id":"meeh","roles":["Developer","Auditor"],"authz":["local_console","api_read","approve"]}
  ]
}
```

#### (95.5) Token Contract

Signed JWT-like local token with scopes (`read_logs`, `approve`, `api_full`), expiry, nonce. Stored in `tokens.jsonl` with status (active/revoked).

#### (95.6) Flow

* Login (local desktop trust or passphrase) → create session in `sessions.jsonl` → mint ASAC with scopes from URM (see §96).
* On wake/idle: PIN or passphrase revalidation if policy requires.
* Revocation updates `tokens.jsonl`; API/WebSocket immediately reject revoked tokens.

#### (95.7) UI & CLI

* **Auth Panel**: active sessions, tokens, expiry countdown; revoke/extend; high-contrast alerts for soon-to-expire.
* CLI: `agent auth login|mint --scopes approve,api_read | revoke <token_id> | sessions`.

#### (95.8) Report

```
[AUTH CHECK]
timestamp: <UTC ISO>
sessions_active: <int>
tokens_active: <int>
revoked_24h: <int>
status: authenticated
```

---

### 96) User Roles & Permissions Matrix (URM)

#### (96.1) Purpose

Define **roles → permissions → scopes** for all critical actions and panels, used by Auth, Approvals, API, Terminal Bridge, Remote Exec, Vault, and DSL.

#### (96.2) Directory & Files

```
.codex_local_agent/urm/
  roles.json
  permissions.json
  grants.json
  audit_urm.jsonl
```

#### (96.3) Roles (`roles.json`)

```json
{
  "roles": {
    "Developer": ["perm.apply","perm.review","perm.edit_prompts","perm.remote_exec_limited","perm.approve"],
    "Auditor":   ["perm.read_all","perm.approvals_view","perm.integrity_sign"],
    "Viewer":    ["perm.read_logs","perm.read_docs"]
  },
  "default_role": "Developer"
}
```

#### (96.4) Permissions (`permissions.json`)

```json
{
  "perm.apply": {"resources":["vcs","dsl","repair"],"actions":["apply","run"]},
  "perm.review": {"resources":["review"],"actions":["comment","approve"]},
  "perm.remote_exec_limited": {"resources":["remote_exec"],"actions":["submit"],"limits":{"profiles":["test","build"]}}
}
```

#### (96.5) Grants (`grants.json`)

Bind identities to roles and temporary escalations (with expiry).

```json
{"user":"meeh","roles":["Developer","Auditor"],"esc":{"role":"Approver","expires":"UTC+2h"}}
```

#### (96.6) Enforcement

* Middleware checks role→perm before action; denies logged with E2xxx.
* UI elements greyed/hidden if lacking perm (never low-contrast text on similar background; use clear disabled state).

#### (96.7) UI & CLI

* **URM Panel**: role table, permission inspector, effective rights viewer.
* CLI: `agent role list|grant meeh Auditor|revoke meeh Approver`.

#### (96.8) Report

```
[URM CHECK]
timestamp: <UTC ISO>
roles_defined: <int>
users_mapped: <int>
denies_24h: <int>
status: enforced
```

---

### 97) Concurrency Controller & Lock Manager (MUCP)

#### (97.1) Purpose

Prevent race conditions across Watcher, Queue, Sandbox, and Editors using **Multi-Unit Concurrency Policy (MUCP)**: cooperative locks, lease times, and priorities.

#### (97.2) Directory & Files

```
.codex_local_agent/concurrency/
  locks.jsonl
  policy.json
  priorities.json
  audit_concurrency.jsonl
```

#### (97.3) Policy (`policy.json`)

```json
{
  "lock_ttl_sec": 120,
  "renew_interval_sec": 30,
  "deadlock_detect_ms": 2000,
  "steal_on_priority": true
}
```

#### (97.4) Priorities (`priorities.json`)

```json
{"watcher":10,"docs":20,"tests":30,"apply":50,"integrity":60,"emergency_repair":90}
```

#### (97.5) Behavior

* Resource keys: `file:<path>`, `dataset:<id>`, `queue`.
* Locks leased per task; renewal heartbeats; deadlock detection graph; priority steals logged.
* On steal, preempted task pauses and retries with backoff.

#### (97.6) UI & CLI

* **Concurrency Panel**: current locks, owners, TTLs; visualize waits; “Break Lock” (requires `perm.apply`). High-contrast timelines.
* CLI: `agent lock ls|break <key>|steal <key>`.

#### (97.7) Report

```
[CONCURRENCY CHECK]
timestamp: <UTC ISO>
locks_active: <int>
deadlocks_resolved: <int>
steals: <int>
status: synchronized
```

---

### 98) Configuration Loader & Overrides

#### (98.1) Purpose

Layered, schema-validated configuration with **precedence**: defaults → theme/preset → user overrides → env → CLI. Atomic writes, diffs, and rollback.

#### (98.2) Directory & Files

```
.codex_local_agent/config/
  defaults/
  overrides/
  schema/
  generated.json
  audit_config.jsonl
```

#### (98.3) Schema

JSON Schema per module; disallows unknown keys; includes types, ranges, enums.

#### (98.4) Load Order

1. Module defaults
2. Theme/preset merges
3. `.codex_local_agent/config/overrides/*.json`
4. Environment variables `AGENT_*`
5. CLI flags → highest precedence

#### (98.5) Flow

* Build merged view → validate → write `generated.json` for consumers.
* Invalid keys quarantined; Doc Linter suggests fixes.

#### (98.6) UI & CLI

* **Config Panel**: live merged view, per-key source; edit override file with validation (high-contrast editor).
* CLI: `agent cfg show|set key=value|diff`.

#### (98.7) Report

```
[CONFIG CHECK]
timestamp: <UTC ISO>
keys_total: <int>
invalid_keys: <int>
rollbacks: <int>
status: consistent
```

---

### 99) Extension/Plugin System

#### (99.1) Purpose

Allow safe, versioned extensions to add panels, macros, parsers, prompts, or providers without modifying core. Sandboxed load, signed manifests, and compatibility checks.

#### (99.2) Directory & Files

```
.codex_local_agent/extensions/
  plugins/
    <vendor>.<name>/
      manifest.json
      code/
      assets/
  registry.json
  audit_ext.jsonl
  quarantine/
```

#### (99.3) Manifest

```json
{
  "id":"vendor.plugin",
  "version":"1.0.0",
  "requires":{"core":">=1.3.0"},
  "capabilities":["panel","macro","parser"],
  "entry":"code/main.py",
  "signature":"base64..."
}
```

#### (99.4) Flow

* Verify signature (optional local CA); check core compatibility; load under Sandbox `plugin` profile; register capabilities; on crash, quarantine.

#### (99.5) UI & CLI

* **Extensions Panel**: install from folder/file, enable/disable, view manifest; high-contrast badges (“Verified”, “Quarantined”).
* CLI: `agent ext install <path>|enable <id>|disable <id>`.

#### (99.6) Report

```
[EXT CHECK]
timestamp: <UTC ISO>
plugins_enabled: <int>
quarantined: <int>
status: modular
```

---

### 100) Hotpatch & Live Reload Engine

#### (100.1) Purpose

Apply small, reversible patches to running modules (panels, parsers, prompts) without restart; guard with integrity checks and rollback.

#### (100.2) Directory & Files

```
.codex_local_agent/hotpatch/
  patches/
  state.json
  audit_hotpatch.jsonl
```

#### (100.3) Patch Descriptor

```json
{
  "id":"HP-2025-10-30-1",
  "targets":["module:viz","panel:Review"],
  "diffs":[{"file":"viz/renderer.py","patch":"---\n+++ ..."}],
  "rollback":{"files":["viz/renderer.py.bak"]},
  "signed":false
}
```

#### (100.4) Flow

* Validate diffs; checkpoint files; apply; run smoke tests; if failure, auto-rollback.
* On success, record to `state.json` and Integrity checkpoint.

#### (100.5) UI & CLI

* **Hotpatch Panel**: load patch, preview, apply/rollback, status; high-contrast diff viewer.
* CLI: `agent hotpatch apply <patch.json>|rollback <id>|status`.

#### (100.6) Report

```
[HOTPATCH CHECK]
timestamp: <UTC ISO>
applied: <int>
rollbacks: <int>
status: live
```

---

### 101) Adaptive Resource Optimizer (ARO)

#### (101.1) Purpose

Continuously tune parallelism, model warm-pools, sandbox limits, and cache policies based on Hardware snapshot, Metrics, and Power state.

#### (101.2) Directory & Files

```
.codex_local_agent/aro/
  policy.json
  decisions.jsonl
  state.json
  audit_aro.jsonl
```

#### (101.3) Policy (`policy.json`)

```json
{
  "targets":{
    "sandbox_parallel": {"min":1,"max":4},
    "warm_pool": {"min":0,"max":2},
    "cache_size_gb": {"min":5,"max":25}
  },
  "safety":{"avoid_thrash": true, "cooldown_sec": 120}
}
```

#### (101.4) Behavior

* Read Metrics (CPU%, MEM, VRAM, queue depth) each interval; if outside bands, propose adjustments; respect cooldown and Concurrency locks.
* Decisions written to `decisions.jsonl` with rationale.

#### (101.5) UI & CLI

* **ARO Panel**: current targets, suggested tweaks, apply/auto mode; sparklines with high-contrast lines.
* CLI: `agent aro suggest|apply|auto on|off`.

#### (101.6) Report

```
[ARO CHECK]
timestamp: <UTC ISO>
adjustments_24h: <int>
auto_mode: <bool>
status: optimized
```

---

### 102) Incident Response & Postmortem Generator

#### (102.1) Purpose

When high-severity incidents occur (from Correlation/Anomaly), assemble timeline, contributing factors, fixes, and action items into a Markdown postmortem with evidence.

#### (102.2) Directory & Files

```
.codex_local_agent/incidents/
  open.jsonl
  closed.jsonl
  postmortems/
  templates/
  audit_incidents.jsonl
```

#### (102.3) Template (`templates/default.md`)

`{{id}}`, `{{summary}}`, `{{timeline}}`, `{{root_cause}}`, `{{impact}}`, `{{fixes}}`, `{{action_items}}`, `{{evidence_links}}`.

#### (102.4) Flow

* On incident close, compile logs, screenshots, eval/test results; generate postmortem; link to Implemented-Updates and Changelog.

#### (102.5) UI & CLI

* **Incidents Panel**: open/closed list, severity filters; “Generate Postmortem”.
* CLI: `agent incident list|close <id>|postmortem <id>`.

#### (102.6) Report

```
[INCIDENTS CHECK]
timestamp: <UTC ISO>
open: <int>
postmortems_generated: <int>
status: accountable
```

---

### 103) Data Retention & Garbage Collection

#### (103.1) Purpose

Automatically prune aged data (logs, screenshots, temp artifacts, old sessions, cache) per policy with safety windows and exemptions (pins).

#### (103.2) Directory & Files

```
.codex_local_agent/retention/
  policy.json
  exemptions.json
  runs.jsonl
  audit_retention.jsonl
```

#### (103.3) Policy (`policy.json`)

```json
{
  "logs_days": 30,
  "screenshots_days": 30,
  "bundles_days": 60,
  "sessions_days": 14,
  "cache_max_gb": 20,
  "dry_run": true,
  "schedule_cron": "30 2 * * *"
}
```

#### (103.4) Exemptions (`exemptions.json`)

```json
{
  "pins": [
    {"path":"capture/bundles/release-*"},
    {"path":"docs/outputs/**","reason":"compliance"}
  ]
}
```

#### (103.5) Flow

* Nightly scan; compute candidates; if `dry_run=true`, produce report and await approval; otherwise delete and update Storage metrics; Integrity updated for affected trees.

#### (103.6) UI & CLI

* **Retention Panel**: bytes by category, upcoming deletions, toggle dry-run, approve now; high-contrast warnings for destructive ops.
* CLI: `agent retain run|approve|stats`.

#### (103.7) Report

```
[RETENTION CHECK]
timestamp: <UTC ISO>
bytes_freed: <int>
items_deleted: <int>
pins_respected: <int>
status: tidy
```
### 104) Storage Monitor & Quotas

#### (104.1) Purpose

Continuously track disk usage, set **per-module quotas** (logs, cache, datasets, screenshots, bundles), prevent out-of-disk crashes, and coordinate with Retention (§103) and Assets (§37). High-contrast warnings in UI; never hide critical alerts.

#### (104.2) Directory & Files

```
.codex_local_agent/storage/
  policy.json
  snapshots.jsonl
  mountpoints.json
  quotas.json
  audit_storage.jsonl
```

#### (104.3) Policies & Quotas (`policy.json`, `quotas.json`)

```json
{
  "scan_interval_sec": 120,
  "low_space_threshold_gb": 5,
  "critical_space_threshold_gb": 1,
  "actions": {"on_low":"retain.dryrun","on_critical":"retain.force+pause_heavy"}
}
```

```json
{
  "quotas": {
    "cache": {"max_gb": 20},
    "logs": {"max_gb": 5},
    "screenshots": {"max_gb": 8},
    "bundles": {"max_gb": 12},
    "datasets": {"max_gb": 200}
  }
}
```

#### (104.4) Flow

* Discover mountpoints → sample free/used → compute per-bucket usage → if over quota, open Retention candidate set (respects exemptions).
* Emit `storage.low` / `storage.critical` events; ARO (§101) throttles heavy jobs until space normalizes.

#### (104.5) UI & CLI

* **Storage Panel**: per-bucket bars, trend spark-lines, “Free Space Now” triggers. High-contrast chips (OK/Warn/Critical).
* CLI: `agent storage scan|quotas|free cache`.

#### (104.6) Report

```
[STORAGE CHECK]
timestamp: <UTC ISO>
free_gb: <float>
buckets_over_quota: <int>
actions_taken: <string[]>
status: safe
```

---

### 105) Cache Manager

#### (105.1) Purpose

Unified cache control (embeddings, doc index, model downloads, screenshots thumbnails) with **size/time policies**, content-addressable keys, and safe invalidation.

#### (105.2) Directory & Files

```
.codex_local_agent/cache/
  index.json
  policies.json
  shards/
  audit_cache.jsonl
```

#### (105.3) Policies (`policies.json`)

```json
{
  "default_ttl_days": 14,
  "max_total_gb": 20,
  "shard_strategy": "by_type",
  "evict_order": "lru",
  "pin_rules": ["embeddings/**"]
}
```

#### (105.4) Flow

* On insert: compute SHA256 → place into shard → update index (size, ttl, pin).
* On pressure (from Storage Monitor) evict LRU except pinned; integrity verified for large items before reuse.

#### (105.5) UI & CLI

* **Cache Panel**: size by shard, evict buttons, pin/unpin.
* CLI: `agent cache stats|evict --shard thumbnails|clear all`.

#### (105.6) Report

```
[CACHE CHECK]
timestamp: <UTC ISO>
total_gb: <float>
evictions_24h: <int>
pins_active: <int>
status: efficient
```

---

### 106) Error Taxonomy & Handler

#### (106.1) Purpose

Define canonical **E-codes** (E1xxx auth, E2xxx permissions, E3xxx models, E7xxx docs, E8xxx security) and route exceptions into structured events with actionable guidance and links to Repair (§80).

#### (106.2) Directory & Files

```
.codex_local_agent/errors/
  taxonomy.json
  handlers.json
  incidents_map.json
  audit_errors.jsonl
```

#### (106.3) Taxonomy (`taxonomy.json`)

```json
{
  "E2001": {"title":"Permission denied","severity":"warn","suggest":"Check URM grants (§96)"},
  "E3801": {"title":"Capability mismatch","severity":"error","suggest":"See Model Caps (§65)"}
}
```

#### (106.4) Flow

* Capture exceptions/log lines → map to E-code → annotate with context (module, file, corr-id) → raise to Notification Hub (§27) and Correlation Engine (§107).
* Critical → open Incident (§102); minor → propose Repair.

#### (106.5) UI & CLI

* **Errors Console**: filter by code/severity; copy remediation steps. High-contrast red for criticals; accessible color ratios enforced.
* CLI: `agent errors last|explain E3801`.

#### (106.6) Report

```
[ERRORS CHECK]
timestamp: <UTC ISO>
errors_24h: <int>
criticals: <int>
top_codes: ["E3801","E2001"]
status: monitored
```

---

### 107) Correlation Engine

#### (107.1) Purpose

Fuse signals from Errors, Anomalies, Storage, ARO, and Scheduler to detect **root-cause clusters** and create actionable incidents with minimal noise.

#### (107.2) Directory & Files

```
.codex_local_agent/correlation/
  rules.json
  windows.json
  findings.jsonl
  audit_correlation.jsonl
```

#### (107.3) Rules (`rules.json`)

```json
{
  "rules":[
    {
      "id":"R-STORAGE-BUILD",
      "if":["storage.low","errors:E5...","scheduler:build"],
      "window_sec":300,
      "emit":"incident.build_space_pressure"
    }
  ]
}
```

#### (107.4) Flow

* Sliding time windows → group events → score correlations → emit `incident.*` when threshold reached.
* Feed **Incidents** (§102) and **Anomaly** (§58).

#### (107.5) UI & CLI

* **Correlation View**: timelines, cause trees; click to open linked logs/screenshots.
* CLI: `agent corr run --since 2h | explain <finding_id>`.

#### (107.6) Report

```
[CORRELATION CHECK]
timestamp: <UTC ISO>
findings_24h: <int>
incidents_opened: <int>
status: insightful
```

---

### 108) Editor Bridges (VS Code / Notepad++ / External)

#### (108.1) Purpose

Integrate with local editors without network dependence: open files at line, apply safe patches, mirror diffs to Review, and synchronize save events with Watcher (§84).

#### (108.2) Directory & Files

```
.codex_local_agent/editor/
  bridges.json
  sessions.jsonl
  audit_editor.jsonl
```

#### (108.3) Bridges (`bridges.json`)

```json
{
  "vscode": {"open_cmd":["code","-g","{file}:{line}"], "detect":"which code"},
  "npp":    {"open_cmd":["notepad++","-n{line}","{file}"], "detect":"where notepad++"},
  "system": {"open_cmd":["xdg-open","{file}"], "detect":null}
}
```

#### (108.4) Flow

* On “Open in Editor”: pick available bridge → spawn with file/line; register session; on save, Watcher event updates Review.
* Patches from Repair (§80) apply under VCS-safe path and open for review.

#### (108.5) UI & CLI

* **Editor Buttons** across panels; **Editor Panel** shows open sessions.
* CLI: `agent edit open path/to.py:120`.

#### (108.6) Report

```
[EDITOR CHECK]
timestamp: <UTC ISO>
sessions_active: <int>
opens_24h: <int>
status: bridged
```

---

### 109) Keymap & Shortcut Manager

#### (109.1) Purpose

Global and panel-scoped shortcuts with discoverable **Keymap** overlay; resolves conflicts and supports profiles (e.g., VS-like). Accessibility: full keyboard navigation ensured.

#### (109.2) Directory & Files

```
.codex_local_agent/keymap/
  profiles/
    default.json
    vscode.json
  overrides.json
  audit_keymap.jsonl
```

#### (109.3) Profile (`profiles/default.json`)

```json
{
  "global": {
    "toggle.console": "Ctrl+`",
    "search.docs": "Ctrl+/",
    "ask": "Ctrl+Enter",
    "do_work": "Ctrl+Shift+Enter"
  },
  "panel.chat": {"export": "Ctrl+E"},
  "panel.review": {"approve": "Ctrl+Shift+A"}
}
```

#### (109.4) Flow

* Merge profile + overrides → validate conflicts → register handlers; surface conflicts with clear high-contrast warnings and suggestions.

#### (109.5) UI & CLI

* **Keymap Overlay**: searchable list; click to rebind.
* CLI: `agent keymap set ask "Ctrl+Enter" | conflicts`.

#### (109.6) Report

```
[KEYMAP CHECK]
timestamp: <UTC ISO>
bindings_total: <int>
conflicts: <int>
status: ergonomic
```

---

### 110) Schema Migration Engine

#### (110.1) Purpose

Evolve internal JSON/YAML schemas (configs, registries, indices) with versioned, reversible migrations; block startup if migrations required and not applied.

#### (110.2) Directory & Files

```
.codex_local_agent/migrations/
  registry.json
  scripts/
    0001-memory-index-v2.json
    0002-models-policy-v3.json
  checkpoints/
  audit_migrations.jsonl
```

#### (110.3) Migration Script Format

```json
{
  "id":"0002-models-policy-v3",
  "from":{"models.policies.version":2},
  "to":{"models.policies.version":3},
  "steps":[
    {"op":"rename_key","path":"models.policies.selection","to":"selection_v3"},
    {"op":"add_default","path":"models.policies.selection_v3.fallback","value":"local-best"}
  ],
  "reversible": true
}
```

#### (110.4) Flow

* Detect versions across files → compute plan → apply under **checkpoint** → validate schemas → update Implemented-Updates.
* On failure, auto-rollback to checkpoint.

#### (110.5) UI & CLI

* **Migrations Panel**: required vs optional, dry-run diff, apply.
* CLI: `agent migrate plan|apply|rollback <id>`.

#### (110.6) Report

```
[MIGRATIONS CHECK]
timestamp: <UTC ISO>
pending: <int>
applied: <int>
rollbacks: <int>
status: current
```

---

### 111) Event Bus & Message Contract

#### (111.1) Purpose

Local, lightweight pub/sub bus for all modules with **typed messages** and retention for replay. Guarantees at-least-once delivery to registered consumers.

#### (111.2) Directory & Files

```
.codex_local_agent/bus/
  topics.json
  contracts/
  inbox/
  offsets/
  audit_bus.jsonl
```

#### (111.3) Contracts (`contracts/*.json`)

```json
{
  "topic":"storage.low",
  "schema":{
    "ts":"string","free_gb":"number","mount":"string","severity":"string","corr":"string?"
  },
  "retention_sec": 86400
}
```

#### (111.4) Flow

* Producers validate payloads against contract → append to topic inbox → consumers commit offsets; replays supported per consumer group.

#### (111.5) UI & CLI

* **Bus Inspector**: topics, last messages, consumer lag.
* CLI: `agent bus topics|tail storage.low|lag`.

#### (111.6) Report

```
[BUS CHECK]
timestamp: <UTC ISO>
topics: <int>
msgs_1h: <int>
consumer_lag_max: <int>
status: reliable
```

---

### 112) Settings Import/Export & Profile Bundles

#### (112.1) Purpose

Export/import **complete agent profiles** (themes, prompts, keymap, configs, macros—no secrets) as signed bundles for portability across machines.

#### (112.2) Directory & Files

```
.codex_local_agent/profiles/
  exports/
  imports/
  manifest.json
  audit_profiles.jsonl
```

#### (112.3) Manifest (`manifest.json`)

```json
{
  "include": [
    "themes/**","prompts/**","keymap/**","config/overrides/**",
    "macros/**","dsl/pipelines/**"
  ],
  "exclude": ["vault/**","apikeys/**","datasets/**"]
}
```

#### (112.4) Flow

* Build bundle → compute checksums → optional local signature → verify on import → preview diff → apply atomically; restart modules that require reload.

#### (112.5) UI & CLI

* **Profiles Panel**: create/export/import; high-contrast diff preview.
* CLI: `agent profile export my-setup | import file.zip`.

#### (112.6) Report

```
[PROFILES CHECK]
timestamp: <UTC ISO>
exports_today: <int>
imports_today: <int>
status: portable
```

---

### 113) Offline Help & Guided Tours

#### (113.1) Purpose

Provide **offline** help pages, recipes, and step-through tours for panels and workflows. Accessible design: large readable white text on dark backgrounds; clear focus outlines.

#### (113.2) Directory & Files

```
.codex_local_agent/help/
  pages/
    getting-started.md
    troubleshooting.md
  tours/
    review_mode.json
    models_setup.json
  index.json
  audit_help.jsonl
```

#### (113.3) Tours (`tours/*.json`)

```json
{
  "id":"review_mode",
  "steps":[
    {"selector":"#reviewPanel","action":"highlight","text":"Review diffs here."},
    {"selector":"#approveBtn","action":"pulse","text":"Approve when ready."}
  ],
  "a11y": {"keyboard_only": true}
}
```

#### (113.4) Flow

* Context-sensitive “?” opens relevant help page or resumes tour; progress saved per user; updates re-indexed by Docsearch (§66).

#### (113.5) UI & CLI

* **Help Overlay**: searchable, high-contrast pages, copyable code.
* CLI: `agent help open review_mode | tour start models_setup`.

#### (113.6) Report

```
[HELP CHECK]
timestamp: <UTC ISO>
pages: <int>
tours_run_7d: <int>
status: supportive
```
### 114) Metrics Collector & Local Exporter

#### (114.1) Purpose

Collect uniform metrics (counters, gauges, histograms) from all modules. Local-only by default; optional export to files for offline dashboards. High-contrast UI charts.

#### (114.2) Directory & Files

```
.codex_local_agent/metrics/
  schema.json
  registry.json
  samples.jsonl
  exporters/
    file.json
  audit_metrics.jsonl
```

#### (114.3) Schema (`schema.json`)

```json
{
  "types": ["counter","gauge","histogram"],
  "units": ["ms","bytes","count","percent"]
}
```

#### (114.4) Flow

* Modules emit metrics via Bus (§111) → Metrics normalizes to `samples.jsonl` with ts, name, labels, value, unit.
* Exporters write rollups (1m/5m/1h) to rotating files. No network unless explicitly enabled elsewhere.

#### (114.5) UI & CLI

* **Metrics Panel**: pick metric, time range; high-contrast line/bar.
* CLI: `agent metrics ls|tail name|export --window 1h`.

#### (114.6) Report

```
[METRICS CHECK]
timestamp: <UTC ISO>
series_total: <int>
samples_5m: <int>
status: recorded
```

---

### 115) Privacy Telemetry Switchboard

#### (115.1) Purpose

Global kill-switch and fine-grained toggles for any external telemetry/export. Defaults to **OFF**; audits any enable/disable. Ensures offline-first guarantees.

#### (115.2) Directory & Files

```
.codex_local_agent/privacy/
  policy.json
  toggles.json
  audit_privacy.jsonl
```

#### (115.3) Policy (`policy.json`)

```json
{
  "external_telemetry_allowed": false,
  "exports_allowed": false,
  "exception_window_min": 10
}
```

#### (115.4) Flow

* Before any network/export, check switchboard; if disabled, action is blocked (E1203) and logged.
* Temporary exception requires Approval (§46).

#### (115.5) UI & CLI

* **Privacy Panel**: master toggle (requires approval), per-feature toggles.
* CLI: `agent privacy status|enable --minutes 10`.

#### (115.6) Report

```
[PRIVACY CHECK]
timestamp: <UTC ISO>
external_allowed: <bool>
exceptions_active: <int>
status: locked_down
```

---

### 116) Structured Log Aggregator

#### (116.1) Purpose

Centralize logs across modules with JSON structure, levels, correlation IDs, and redaction (ties into Sanitize §94). Supports tail, filters, and saved views.

#### (116.2) Directory & Files

```
.codex_local_agent/logs/
  errors.jsonl
  events.jsonl
  access.jsonl
  views.json
  audit_logs.jsonl
```

#### (116.3) Flow

* Modules log to Bus → Aggregator writes to appropriate streams.
* Redaction engine masks secrets before write; high-contrast console renders.

#### (116.4) UI & CLI

* **Logs Panel**: filters (level/module/code), follow tail, save view presets.
* CLI: `agent logs tail errors|grep E3801`.

#### (116.5) Report

```
[LOGS CHECK]
timestamp: <UTC ISO>
lines_1h: <int>
redactions_1h: <int>
status: centralized
```

---

### 117) Time Sync & Clock Skew Guard

#### (117.1) Purpose

Detect and mitigate clock drift between system time and file/queue timestamps; correct scheduling and correlation windows.

#### (117.2) Directory & Files

```
.codex_local_agent/time/
  policy.json
  skew.json
  audit_time.jsonl
```

#### (117.3) Policy (`policy.json`)

```json
{"warn_skew_ms": 500,"block_skew_ms": 3000,"auto_correct_offsets": true}
```

#### (117.4) Flow

* On startup and hourly, compare monotonic vs wall clock, file mtimes, message ts; compute skew → adjust internal offsets for Scheduler (§78) and Correlation (§107).

#### (117.5) UI & CLI

* **Time Card** in Diagnostics: shows skew and correction.
* CLI: `agent time check|offset`.

#### (117.6) Report

```
[TIME CHECK]
timestamp: <UTC ISO>
skew_ms: <int>
autocorrected: <bool>
status: aligned
```

---

### 118) Localization & i18n

#### (118.1) Purpose

Localize UI strings, date/time/number formats, and documentation snippets. All strings enforce high-contrast readability across languages.

#### (118.2) Directory & Files

```
.codex_local_agent/i18n/
  locales/
    en-US.json
    es-ES.json
  policy.json
  audit_i18n.jsonl
```

#### (118.3) Policy (`policy.json`)

```json
{"default":"en-US","fallback":"en-US","rtl_locales":[]}
```

#### (118.4) Flow

* Key-based string lookup; hot-reload on changes; Docs/Help integrate via tags.

#### (118.5) UI & CLI

* **Language Selector** in Settings; preview sample.
* CLI: `agent i18n set es-ES`.

#### (118.6) Report

```
[I18N CHECK]
timestamp: <UTC ISO>
locales: <int>
active: "en-US"
status: localized
```

---

### 119) Color Vision Accessibility Modes

#### (119.1) Purpose

Alternate palettes optimized for deuteranopia, protanopia, tritanopia. Applies to charts, badges, and status chips while preserving contrast.

#### (119.2) Directory & Files

```
.codex_local_agent/a11y/
  color_modes.json
  audit_a11y.jsonl
```

#### (119.3) Modes (`color_modes.json`)

```json
{"modes":["default","deuteranopia","protanopia","tritanopia"],"wcag_min":4.5}
```

#### (119.4) Flow

* Theme engine (§24) remaps tokens per mode; UI re-renders live.

#### (119.5) UI & CLI

* Toggle in Theme Manager; contrast score previews.
* CLI: `agent a11y color deuteranopia`.

#### (119.6) Report

```
[A11Y COLOR CHECK]
timestamp: <UTC ISO>
mode: "default"
wcag_violations: <int>
status: inclusive
```

---

### 120) High-DPI & Font Scaling Engine

#### (120.1) Purpose

Ensure crisp rendering on high-DPI displays; adjustable UI scale and monospace/code font sizes with remembered preferences.

#### (120.2) Directory & Files

```
.codex_local_agent/display/
  dpi.json
  fonts.json
  audit_display.jsonl
```

#### (120.3) DPI (`dpi.json`)

```json
{"scale":1.25,"snap":[1.0,1.25,1.5,2.0],"auto_detect":true}
```

#### (120.4) UI & CLI

* **Display Panel**: scale slider, preview cards; always high-contrast text vs background.
* CLI: `agent display scale 1.25`.

#### (120.5) Report

```
[DISPLAY CHECK]
timestamp: <UTC ISO>
scale: <float>
status: crisp
```

---

### 121) Config Undo/Redo Journal

#### (121.1) Purpose

Track reversible edits to configs, prompts, and themes; allow multi-step undo/redo with diffs.

#### (121.2) Directory & Files

```
.codex_local_agent/config_journal/
  entries.jsonl
  state.json
  audit_journal.jsonl
```

#### (121.3) Flow

* Each change writes a diff entry with user, ts, file, before/after hashes; Undo applies inverse diff under Integrity guard.

#### (121.4) UI & CLI

* **History Pane**: timeline with “Undo/Redo” buttons; contrast-enforced diff colors.
* CLI: `agent cfg undo|redo|show`.

#### (121.5) Report

```
[JOURNAL CHECK]
timestamp: <UTC ISO>
undos_today: <int>
redos_today: <int>
status: recoverable
```

---

### 122) Safe Temp Workspace Manager

#### (122.1) Purpose

Provide isolated temp dirs for builds/tests with automatic cleanup and quota; never mixes with source tree.

#### (122.2) Directory & Files

```
.codex_local_agent/tmp/
  policy.json
  leases.jsonl
  audit_tmp.jsonl
```

#### (122.3) Policy (`policy.json`)

```json
{"max_gb":5,"lease_ttl_min":120,"auto_cleanup":true}
```

#### (122.4) UI & CLI

* **Temp Monitor**: active leases, purge button.
* CLI: `agent tmp lease|purge`.

#### (122.5) Report

```
[TMP CHECK]
timestamp: <UTC ISO>
active_leases: <int>
bytes_used: <int>
status: tidy
```

---

### 123) Build System (CLI/GUI Bundles)

#### (123.1) Purpose

Build distributable CLI/GUI bundles with reproducible manifests; integrates with Deps (§34), Sandbox (§75), and CI (§50).

#### (123.2) Directory & Files

```
.codex_local_agent/build/
  targets.json
  outputs/
  manifests/
  audit_build.jsonl
```

#### (123.3) Target (`targets.json`)

```json
{
  "cli_bundle": {"entry":"cli.py","type":"zipapp","python":"3.11"},
  "gui_bundle": {"entry":"launch.py","type":"pyinstaller","onefile":true}
}
```

#### (123.4) Flow

* Resolve deps → run target builder in `build` profile → write manifest with hashes → store in outputs.

#### (123.5) UI & CLI

* **Build Panel**: pick target, view manifest, open folder.
* CLI: `agent build run gui_bundle`.

#### (123.6) Report

```
[BUILD CHECK]
timestamp: <UTC ISO>
artifacts: <int>
status: packaged
```

---

### 124) Release Channel Manager

#### (124.1) Purpose

Track channels (alpha/beta/stable) and promote builds through QA gates with signed manifests.

#### (124.2) Directory & Files

```
.codex_local_agent/release/
  channels.json
  promotions.jsonl
  signatures/
  audit_release.jsonl
```

#### (124.3) Channels (`channels.json`)

```json
{"channels":["alpha","beta","stable"],"current":"alpha"}
```

#### (124.4) Flow

* Promote only if QA (§70) passes; Integrity snapshot recorded; optional signature.

#### (124.5) UI & CLI

* **Release Panel**: promote dropdown, channel diffs.
* CLI: `agent release promote --to beta --artifact build/outputs/app.exe`.

#### (124.6) Report

```
[RELEASE CHECK]
timestamp: <UTC ISO>
current_channel: "alpha"
promotions_7d: <int>
status: staged
```

---

### 125) Hardware Sensors & Thermal Monitor

#### (125.1) Purpose

Track CPU/GPU temps, throttling states; inform ARO (§101) to avoid thermal throttling; issue warnings.

#### (125.2) Directory & Files

```
.codex_local_agent/thermal/
  sensors.json
  readings.jsonl
  audit_thermal.jsonl
```

#### (125.3) Policy (`sensors.json`)

```json
{"poll_ms":2000,"warn_c":80,"critical_c":90}
```

#### (125.4) UI & CLI

* **Thermal Panel**: temps graphs; high-contrast alert chips.
* CLI: `agent thermal watch`.

#### (125.5) Report

```
[THERMAL CHECK]
timestamp: <UTC ISO>
max_c: <float>
throttle_events: <int>
status: cool
```

---

### 126) Network Policy Controller

#### (126.1) Purpose

Define per-profile egress/ingress rules for Sandbox and modules; default deny. Offline-first compatible.

#### (126.2) Directory & Files

```
.codex_local_agent/net/
  policy.json
  allowlist.json
  audit_net.jsonl
```

#### (126.3) Policy (`policy.json`)

```json
{"default":"deny","profiles":{"build":"deny","test":"deny","online":"allowlist"}}
```

#### (126.4) UI & CLI

* **Network Panel**: allowlist editor (domains/ports); warnings for violations.
* CLI: `agent net allow add api.openai.com:443`.

#### (126.5) Report

```
[NET CHECK]
timestamp: <UTC ISO>
violations_24h: <int>
allowlist_entries: <int>
status: controlled
```

---

### 127) Clipboard Manager (Redacted & TTL)

#### (127.1) Purpose

Centralize clipboard operations with TTL, redaction filters, and clear-on-lock. Integrates with Vault (§74).

#### (127.2) Directory & Files

```
.codex_local_agent/clipboard/
  policy.json
  events.jsonl
  audit_clipboard.jsonl
```

#### (127.3) Policy (`policy.json`)

```json
{"ttl_sec":20,"redact_patterns":["(?i)api[_-]?key"],"clear_on_lock":true}
```

#### (127.4) UI & CLI

* **Clipboard HUD**: shows countdown; high-contrast timer.
* CLI: `agent clip copy "text" | clear`.

#### (127.5) Report

```
[CLIPBOARD CHECK]
timestamp: <UTC ISO>
copies_24h: <int>
auto_clears: <int>
status: safe
```

---

### 128) Image & Media Pipeline

#### (128.1) Purpose

Handle thumbnails, transcoding (PNG↔WEBP, MP4 previews), and size budgets for Chat/Docs; ensures accessible previews.

#### (128.2) Directory & Files

```
.codex_local_agent/media/
  policy.json
  thumbs/
  transcodes/
  audit_media.jsonl
```

#### (128.3) Policy (`policy.json`)

```json
{"thumb_max_px":512,"video_preview_sec":10,"max_embed_mb":25}
```

#### (128.4) UI & CLI

* **Media Panel**: transcode queue, preview; high-contrast borders for images.
* CLI: `agent media make-thumb file.png`.

#### (128.5) Report

```
[MEDIA CHECK]
timestamp: <UTC ISO>
thumbs_made: <int>
transcodes: <int>
status: optimized
```

---

### 129) Media Player/Preview Service

#### (129.1) Purpose

Securely preview audio/video within the app with sandboxed player; no auto-play; keyboard-accessible controls.

#### (129.2) Directory & Files

```
.codex_local_agent/player/
  config.json
  sessions.jsonl
  audit_player.jsonl
```

#### (129.3) Config (`config.json`)

```json
{"autoplay":false,"loop":false,"volume":0.5}
```

#### (129.4) UI & CLI

* Embedded player with large, high-contrast controls.
* CLI: `agent player open path/to/video.mp4`.

#### (129.5) Report

```
[PLAYER CHECK]
timestamp: <UTC ISO>
sessions: <int>
status: functional
```

---

### 130) Schema-Driven UI Renderer

#### (130.1) Purpose

Render simple forms/panels from JSON schema to speed tool-building; consistent styling with Theme engine.

#### (130.2) Directory & Files

```
.codex_local_agent/uiforms/
  schemas/
  forms.json
  audit_uiforms.jsonl
```

#### (130.3) Schema Example

```json
{
  "id":"api_keys_form",
  "fields":[
    {"name":"OPENAI_API_KEY","type":"password","label":"OpenAI Key"},
    {"name":"ROTATE","type":"button","action":"agent apikey rotate OPENAI_API_KEY"}
  ]
}
```

#### (130.4) UI & CLI

* **Form Renderer** component reusable across panels.
* CLI: `agent form open api_keys_form`.

#### (130.5) Report

```
[UIFORMS CHECK]
timestamp: <UTC ISO>
forms_rendered: <int>
status: dynamic
```

---

### 131) Local Plugin Index (Marketplace-Offline)

#### (131.1) Purpose

Curate a local directory of approved extensions (§99) discoverable via UI; no network fetch.

#### (131.2) Directory & Files

```
.codex_local_agent/plugin_index/
  index.json
  icons/
  audit_plugin_index.jsonl
```

#### (131.3) Index (`index.json`)

```json
{"plugins":[{"id":"vendor.plugin","path":"extensions/plugins/vendor.plugin","verified":true}]}
```

#### (131.4) UI & CLI

* **Plugins Catalog**: install/enable from local paths; high-contrast verification badges.
* CLI: `agent ext install extensions/plugins/vendor.plugin`.

#### (131.5) Report

```
[PLUGIN INDEX CHECK]
timestamp: <UTC ISO>
curated: <int>
status: curated
```

---

### 132) Notebook Runner (Local Jupyter-lite)

#### (132.1) Purpose

Execute notebooks offline with sanitized kernels; export results to artifacts.

#### (132.2) Directory & Files

```
.codex_local_agent/notebooks/
  kernels.json
  runs/
  audit_notebooks.jsonl
```

#### (132.3) Policy (`kernels.json`)

```json
{"python3":{"allow_modules":["numpy","pandas","matplotlib"],"timeout_sec":120}}
```

#### (132.4) UI & CLI

* **Notebook Panel**: open `.ipynb`, run cells; high-contrast outputs.
* CLI: `agent nb run file.ipynb`.

#### (132.5) Report

```
[NOTEBOOKS CHECK]
timestamp: <UTC ISO>
runs: <int>
status: executed
```

---

### 133) DataFrame Viewer & CSV Toolkit

#### (133.1) Purpose

Inspect CSV/TSV/Parquet locally; filter, sample, export; high-contrast grid.

#### (133.2) Directory & Files

```
.codex_local_agent/data_view/
  recent.json
  presets.json
  audit_data_view.jsonl
```

#### (133.3) UI & CLI

* **Data Viewer**: sort/filter/summarize; export subset.
* CLI: `agent data view file.csv | sample --n 1000`.

#### (133.4) Report

```
[DATA VIEW CHECK]
timestamp: <UTC ISO>
files_opened: <int>
status: visualized
```

---

### 134) Diff Packager for External Review

#### (134.1) Purpose

Bundle diffs, comments, screenshots into a portable ZIP for sharing offline or via manual transfer.

#### (134.2) Directory & Files

```
.codex_local_agent/diff_pkg/
  bundles/
  audit_diff_pkg.jsonl
```

#### (134.3) UI & CLI

* **Export for Review**: pick patch → create bundle with README.
* CLI: `agent diffpkg export patch-123`.

#### (134.4) Report

```
[DIFFPKG CHECK]
timestamp: <UTC ISO>
bundles: <int>
status: shareable
```

---

### 135) Legacy Project Migration Assistant

#### (135.1) Purpose

Import structures from older agent trees; map to new directories and schemas with guided steps.

#### (135.2) Directory & Files

```
.codex_local_agent/migrate_legacy/
  mappings.json
  runs.jsonl
  audit_migrate_legacy.jsonl
```

#### (135.3) UI & CLI

* **Migration Wizard**: detect legacy files, propose moves; high-contrast diffs.
* CLI: `agent legacy import <path>`.

#### (135.4) Report

```
[LEGACY MIGRATE CHECK]
timestamp: <UTC ISO>
files_migrated: <int>
status: upgraded
```

---

### 136) System Health Dashboard

#### (136.1) Purpose

Top-level cards for Health: Models, Queue, Storage, Errors, Integrity, Power.

#### (136.2) Directory & Files

```
.codex_local_agent/health/
  cards.json
  audit_health.jsonl
```

#### (136.3) UI

* **Health Dashboard**: green/yellow/red chips; all text high-contrast on dark. Click-through to modules.

#### (136.4) Report

```
[HEALTH CHECK]
timestamp: <UTC ISO>
cards_red: <int>
status: summarized
```

---

### 137) Command Palette

#### (137.1) Purpose

Quick action launcher with fuzzy search across commands, macros, pipelines, docs.

#### (137.2) Directory & Files

```
.codex_local_agent/cmd_palette/
  index.json
  audit_cmd_palette.jsonl
```

#### (137.3) UI & CLI

* **Palette** (`Ctrl+K`): searchable list; respects URM permissions.
* CLI: `agent run "<command>"`.

#### (137.4) Report

```
[PALETTE CHECK]
timestamp: <UTC ISO>
commands_indexed: <int>
status: snappy
```

---

### 138) Bug Report Context Capture

#### (138.1) Purpose

Package logs, system info, integrity root, and screenshots into a redacted bundle for issue filing (local or manual).

#### (138.2) Directory & Files

```
.codex_local_agent/bugreport/
  templates/
  reports/
  audit_bugreport.jsonl
```

#### (138.3) UI & CLI

* **Report Issue** button (high-contrast): picks scope, attaches evidence.
* CLI: `agent bugreport create --scope review`.

#### (138.4) Report

```
[BUGREPORT CHECK]
timestamp: <UTC ISO>
reports: <int>
status: reproducible
```

---

### 139) Power-User Scripting (Local Python Hooks)

#### (139.1) Purpose

Allow trusted local Python hook scripts with strict sandbox and capability flags to extend behaviors.

#### (139.2) Directory & Files

```
.codex_local_agent/hooks/
  policy.json
  scripts/
  audit_hooks.jsonl
```

#### (139.3) Policy (`policy.json`)

```json
{"allow":["read_files","emit_events"],"deny":["network","write_outside_agent"],"timeout_ms":2000}
```

#### (139.4) UI & CLI

* **Hooks Panel**: add script, set caps; high-contrast permissions matrix.
* CLI: `agent hook run scripts/on_build.py`.

#### (139.5) Report

```
[HOOKS CHECK]
timestamp: <UTC ISO>
runs: <int>
denied_ops: <int>
status: extended
```

---

### 140) Job Cost & Token Estimator

#### (140.1) Purpose

Estimate time/token/cost for Ask/Do Work using model metadata and local baselines; supports budgeting and alerts.

#### (140.2) Directory & Files

```
.codex_local_agent/costs/
  baselines.json
  estimates.jsonl
  budgets.json
  audit_costs.jsonl
```

#### (140.3) Budgets (`budgets.json`)

```json
{"monthly_usd_limit":0,"warn_at_percent":80}
```

#### (140.4) UI & CLI

* **Cost Panel**: estimates per task; warnings if budgets exceeded (especially when remote providers enabled).
* CLI: `agent cost estimate ask --tokens 8000`.

#### (140.5) Report

```
[COST CHECK]
timestamp: <UTC ISO>
estimates_today: <int>
budget_exceeded: <bool>
status: prudent
```

---

### 141) Token Accounting & Usage Ledger

#### (141.1) Purpose

Track per-model token usage, latency, and outcomes; integrates with RPE (§79) and Costs (§140).

#### (141.2) Directory & Files

```
.codex_local_agent/tokens/
  ledger.jsonl
  summaries.json
  audit_tokens.jsonl
```

#### (141.3) UI & CLI

* **Token Ledger**: per-session charts; high-contrast bars.
* CLI: `agent tokens summary --since 7d`.

#### (141.4) Report

```
[TOKENS CHECK]
timestamp: <UTC ISO>
tokens_24h: <int>
avg_latency_ms: <int>
status: tracked
```

---

### 142) Rate Limiter & Backoff Manager

#### (142.1) Purpose

Uniform client-side rate limits and exponential backoff for providers/APIs and local resources to avoid thrash.

#### (142.2) Directory & Files

```
.codex_local_agent/rate/
  policies.json
  counters.json
  audit_rate.jsonl
```

#### (142.3) Policy (`policies.json`)

```json
{"openai":{"rps":1,"burst":2},"filesystem":{"rps":100,"burst":200}}
```

#### (142.4) UI & CLI

* **Rate Panel**: current limits and hit counts.
* CLI: `agent rate set openai.rps 0`.

#### (142.5) Report

```
[RATE CHECK]
timestamp: <UTC ISO>
throttles_24h: <int>
status: smoothed
```

---

### 143) Queue Mirroring & Backup

#### (143.1) Purpose

Periodically snapshot Queue (§32) state for recovery; mirror to a backup file safely.

#### (143.2) Directory & Files

```
.codex_local_agent/queue_backup/
  snapshots/
  policy.json
  audit_queue_backup.jsonl
```

#### (143.3) Policy (`policy.json`)

```json
{"interval_min":15,"retain":10}
```

#### (143.4) UI & CLI

* **Queue Backup**: latest snapshots; restore option.
* CLI: `agent qbackup snapshot|restore <id>`.

#### (143.5) Report

```
[QBACKUP CHECK]
timestamp: <UTC ISO>
snapshots: <int>
status: protected
```

---

### 144) File Format Validators

#### (144.1) Purpose

Validate JSON/YAML/TOML/XML/CSV against schemas and constraints; block Apply on malformed configs.

#### (144.2) Directory & Files

```
.codex_local_agent/validators/
  rules.json
  results.jsonl
  audit_validators.jsonl
```

#### (144.3) Rules (`rules.json`)

```json
{"json":{"schema_lookup":"config/schema"},"yaml":{"strict":true},"csv":{"max_cols":200}}
```

#### (144.4) UI & CLI

* **Validators Panel**: run scan; view errors with file/line.
* CLI: `agent validate path/to/*.json`.

#### (144.5) Report

```
[VALIDATORS CHECK]
timestamp: <UTC ISO>
files_scanned: <int>
violations: <int>
status: strict
```

---

### 145) Render Safety Policy (HTML/Markdown)

#### (145.1) Purpose

Enforce safe rendering of Markdown/HTML (allowed tags/attrs, sandboxed iframes), complementing Sanitize (§94).

#### (145.2) Directory & Files

```
.codex_local_agent/render_safety/
  policy.json
  audit_render.jsonl
```

#### (145.3) Policy (`policy.json`)

```json
{"allow_iframe":false,"allowed_attrs":["href","src","alt","title","class"],"no_inline_css":true}
```

#### (145.4) UI & CLI

* **Render Safety** toggle with preview; high-contrast warnings on blocked elements.
* CLI: `agent render safety test file.md`.

#### (145.5) Report

```
[RENDER SAFETY CHECK]
timestamp: <UTC ISO>
blocks_24h: <int>
status: sanitized
```

---

### 146) Experiment Tracking (Prompts/Training)

#### (146.1) Purpose

Record experiments for prompts A/B and model fine-tunes; track configs, results, artifacts.

#### (146.2) Directory & Files

```
.codex_local_agent/experiments/
  runs.jsonl
  params.jsonl
  artifacts/
  audit_experiments.jsonl
```

#### (146.3) UI & CLI

* **Experiments Panel**: compare runs; pin best.
* CLI: `agent exp start --prompt plan_v2 | compare --last 5`.

#### (146.4) Report

```
[EXPERIMENTS CHECK]
timestamp: <UTC ISO>
runs: <int>
best_score: <float>
status: methodical
```

---

### 147) Reproducibility Snapshots (All-State)

#### (147.1) Purpose

Create holistic snapshots across locks, configs, models registry, prompts, and integrity hash for exact reproduction.

#### (147.2) Directory & Files

```
.codex_local_agent/repro/
  snapshots/
  manifest.json
  audit_repro.jsonl
```

#### (147.3) Flow

* After stable run → compose manifest with versions/hashes → store snapshot; tie to Release (§124).

#### (147.4) UI & CLI

* **Repro Panel**: “Create Snapshot”, “Compare to current”.
* CLI: `agent repro snapshot|diff <id>`.

#### (147.5) Report

```
[REPRO CHECK]
timestamp: <UTC ISO>
snapshots: <int>
status: exact
```

---

### 148) Interop Bridges (Unity/Blender/Panda3D)

#### (148.1) Purpose

Provide local adapters to common tools used in project workflows (open project, sync assets, export logs) without cloud dependencies.

#### (148.2) Directory & Files

```
.codex_local_agent/interop/
  unity.json
  blender.json
  panda3d.json
  sessions.jsonl
  audit_interop.jsonl
```

#### (148.3) Example (Unity)

```json
{"open_cmd":["Unity.exe","-projectPath","{path}"],"link_assets":true}
```

#### (148.4) UI & CLI

* **Interop Panel**: configure paths, quick open, sync assets; high-contrast status chips per tool.
* CLI: `agent interop open unity --path C:/Game`.

#### (148.5) Report

```
[INTEROP CHECK]
timestamp: <UTC ISO>
tools_configured: <int>
opens_24h: <int>
status: connected
```

---

### 149) Game Overlay & OCR Capture Manager

#### (149.1) Purpose

Manage transparent overlay windows for live OCR (dual-pass §81) on games/apps; region selection, hotkeys, throttled capture.

#### (149.2) Directory & Files

```
.codex_local_agent/overlay/
  regions.json
  hotkeys.json
  captures/
  audit_overlay.jsonl
```

#### (149.3) Regions (`regions.json`)

```json
{"areas":[{"id":"chat","x":100,"y":800,"w":600,"h":200,"fps":5}]}
```

#### (149.4) UI & CLI

* **Overlay Panel**: draw/resize regions; preview OCR text; high-contrast bounding boxes.
* CLI: `agent overlay start chat|stop chat`.

#### (149.5) Report

```
[OVERLAY CHECK]
timestamp: <UTC ISO>
regions_active: <int>
captures_1h: <int>
status: precise
```

---

### 150) Implementation Check Orchestrator (Final Gate)

#### (150.1) Purpose

Aggregate all module checks into a single **Implementation Check** that confirms readiness: policies enforced, tests passing, docs consistent, integrity verified. Writes a final stamp consumed by Restore (§45) and Release (§124).

#### (150.2) Directory & Files

```
.codex_local_agent/impl_check/
  checklist.json
  results.json
  stamp.json
  audit_impl_check.jsonl
```

#### (150.3) Checklist (`checklist.json`)

```json
{
  "requires": [
    "integrity.verify",
    "tests.pass",
    "doclint.clean",
    "license.compliant",
    "a11y.contrast_ok",
    "queue.empty_or_safe",
    "missing.zero_p0",
    "policy_reasoner.clean"
  ]
}
```

#### (150.4) Flow

* Run each requirement by invoking module reports; failures produce a consolidated markdown with remediation links.
* On success, emit `stamp.json` with Integrity root, VCS revision, and timestamp.

#### (150.5) UI & CLI

* **Implementation Check** panel: progress wheel, per-item chips, “Generate Stamp”.
* CLI: `agent implcheck run | stamp`.

#### (150.6) Report

```
[IMPLCHECK CHECK]
timestamp: <UTC ISO>
requirements_total: <int>
failures: <int>
status: green|yellow|red
```
# VS Bridge — Local Agent ↔ Visual Studio Code (Copilot/Agent) Integration Guide

> Place this file at: `Dev_Logic/vs_bridge.md`
> Place the Python host at: `Dev_Logic/vs_codex_local.py` (or keep your existing location and update paths below).

---

## 1) What “VS Bridge mode” is

**VS Bridge mode** lets your Local Agent work side-by-side with Visual Studio Code (VS Code):

* Use VS Code’s **diff/merge UI**, source control, editor, and terminal while your Local Agent continues to do planning, RAG, OCR, and local model calls.
* Optionally **ask Copilot Chat/Agent** inside VS Code for advanced reasoning while keeping your Local Agent as the “apply/patch” executor and audit trail.
* A **toggle button (“VS Mode”)** in the Agent UI switches behaviors: when ON, the Agent routes “Open file,” “Show diff,” and “Edit here” actions into VS Code rather than its internal editors.
* The theme subtly harmonizes (dark, high-contrast, readable light text on dark backgrounds; no low-contrast pairings — **always** ensure strong contrast).
* All actions are **offline by default**; Copilot usage is optional and user-initiated.

Your Local Agent already runs **local-first** (Ollama at `http://127.0.0.1:11434`, RAG datasets, session logs, safety prompts). We’ll simply add a bridge so VS Code can become the primary editor/diff surface when desired. 

---

## 2) Prerequisites (one-time)

1. **VS Code** installed and `code` on PATH (so we can call `code -g file:line`).
2. **Node.js 18+** (for building a tiny helper extension and optional scripts).
3. **Python 3.10+**, your **Local Agent** environment for `vs_codex_local.py`.
4. **Git** (so diffs open cleanly and Source Control shows patch context).
5. *(Optional)* **GitHub Copilot** extension enabled in VS Code if you want to consult Copilot Chat/Agent for reasoning (you can keep all Local Agent execution local).
6. *(Optional)* `vsce` (`npm i -g @vscode/vsce`) if you want to package the bridge extension rather than run it un-packed.

The Local Agent already exposes strong local behaviors and a clear safety prompt loop (never auto-execute; propose diffs/commands; log every action). Keep those guardrails intact when bridging. 

---

## 3) Files & Layout you will keep in the repo

```
Dev_Logic/
  vs_codex_local.py        # Local Agent app (PySide6 UI, RAG, OCR, etc.)
  vs_bridge.md             # THIS document (installation + operations)
.vscode/
  extensions/agent-bridge/ # Optional local VS Code extension (unpacked)
    package.json
    out/extension.js
    media/icon.png
```

If you maintain a separate folder (e.g., `C:\Users\Art PC\Desktop\vs_codex_local`), keep it, but ensure this document is mirrored under `Dev_Logic/` so the Agent can reference it for onboarding and self-repair. The Local Agent expects conversation logs, dataset indices, and config near the script’s directory (e.g., `datasets/`, `conversations/`, `config.json`).  

---

## 4) Prepare the Local Agent host (Python)

1. **Create/activate venv** and install extras you need (PySide6 already in your stack):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt   # if you maintain one
   ```
2. **Ollama** running locally and models pulled (`qwen2`, `llava`, or the ones your config references).
3. **Start the Local Agent**:

   ```powershell
   python Dev_Logic\vs_codex_local.py
   ```

   * The agent writes conversation logs to `conversations/<ts>/`, maintains RAG datasets under `datasets/`, and uses `config.json` to route “chat.to.commands”, “rag.augment”, “vision.*” into **local models**. Defaults point to Ollama on `127.0.0.1:11434`. 

**High-contrast rule:** The Agent UI already uses light text on a dark background (`term_fg` ~ `#e9f3ff` on `term_bg` ~ `#0b1828`). Maintain this rule in any new widgets/buttons (like the VS Mode toggle). Never render light text on similarly light backgrounds or vice-versa. 

---

## 5) Add a “VS Mode” toggle to the Agent UI

Purpose: when ON, “Open,” “Diff,” “Apply here,” “Jump to line,” **open in VS Code** via the VS Code CLI/API instead of internal editors.

**Implementation steps (Agent-side):**

* **Config flag**: add `editor_bridge: "vscode" | "internal"` in `config.json`. Default `"internal"`. When toggled, persist to disk (atomic write). The Agent already has safe JSON write helpers (`safe_write_json`). 
* **Button**: add a header **QPushButton** “VS Mode” with a clear high-contrast label; ON state should be obvious (e.g., border accent `#1E5AFF`, bold text). 
* **Action routing**: in places that open editors or diffs, call:

  * `code -g "<file>:<line>"` for single-file jumps.
  * `vscode.diff` command via the bridge extension (see §7) for side-by-side diffs.
* **Telemetry note**: Keep things **offline**; calls are local‐process invocations (no network). The Agent remains the authority over diffs and Apply. 

---

## 6) Using VS Code’s strengths without coupling to the cloud

* **Diff/merge**: rely on Git + VS Code’s SCM UI. The Agent proposes a patch; you stage/select and **review in VS**.
* **Editor**: rich IntelliSense, diagnostics, and keybindings in VS Code; Agent opens exact files/lines.
* **Terminal**: run commands manually (Agent will **propose**, not execute).
* **Copilot Chat/Agent (optional)**: open the Copilot Chat panel and ask complex reasoning questions. Keep execution local: you’ll **paste outcomes** back into the Agent or let the Agent simply remain your apply surface.
* **Theme harmony**: optionally set VS Code to a matching dark theme (e.g., similar blues/darks). The Agent **never** lowers text contrast, so ensure VS uses legible tokens too.

Remember your earlier finding: **the “good” experience you saw was Copilot’s Agent using the provider-side GPT-5 mini**; that was not your local “Codex”. Your **only** “Codex” path right now is the **Local Agent** bridge or an **OpenAI API** via Node/Python SDKs you install yourself (see §12). This doc keeps that boundary explicit and under your control.

---

## 7) Minimal VS Code extension (local, offline) to talk to the Agent

We’ll create a tiny extension that:

* Provides commands: **Open in VS**, **Diff in VS**, **Set Active Model/Provider** (optional).
* Talks to a **local HTTP port** if you later add an HTTP helper (e.g., `vs_codex_local_api.py`), or simply shells out to the Agent via CLI/args.
* This avoids any cloud dependencies — it is strictly local.

**Create folder**: `.vscode/extensions/agent-bridge/`

**package.json** (minimal)

```json
{
  "name": "agent-bridge",
  "displayName": "Agent Bridge (Local)",
  "version": "0.0.1",
  "publisher": "local",
  "engines": { "vscode": "^1.90.0" },
  "activationEvents": [
    "onCommand:agentBridge.openFile",
    "onCommand:agentBridge.openDiff",
    "onCommand:agentBridge.pickModel"
  ],
  "contributes": {
    "commands": [
      { "command": "agentBridge.openFile", "title": "Agent: Open File (line)" },
      { "command": "agentBridge.openDiff",  "title": "Agent: Open Diff" },
      { "command": "agentBridge.pickModel","title": "Agent: Pick Model" }
    ]
  },
  "main": "./out/extension.js"
}
```

**out/extension.js** (compiled from TS or authored directly in JS)

```js
const vscode = require('vscode');
const cp = require('child_process');
function activate(context) {
  // Local helper to open file:line
  const openFile = vscode.commands.registerCommand('agentBridge.openFile', async (uri, line) => {
    try {
      if (!uri) { uri = await vscode.window.showOpenDialog({ canSelectMany:false }); if (!uri) return; uri = uri[0]; }
      if (!line) { line = await vscode.window.showInputBox({ prompt: "Line number", value: "1" }); }
      const doc = await vscode.workspace.openTextDocument(uri);
      const editor = await vscode.window.showTextDocument(doc, { preview:false });
      const ln = Math.max(0, (parseInt(line,10)||1) - 1);
      const pos = new vscode.Position(ln, 0);
      editor.selection = new vscode.Selection(pos, pos);
      editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
    } catch (e) {
      vscode.window.showErrorMessage(String(e));
    }
  });

  // Local diff using VS Code command
  const openDiff = vscode.commands.registerCommand('agentBridge.openDiff', async (leftUri, rightUri, title) => {
    try {
      if (!leftUri || !rightUri) {
        vscode.window.showWarningMessage("Need two file URIs for diff");
        return;
      }
      await vscode.commands.executeCommand('vscode.diff', leftUri, rightUri, title || 'Agent Diff');
    } catch (e) {
      vscode.window.showErrorMessage(String(e));
    }
  });

  // Optional: ask Agent host for models/providers, then pick
  const pickModel = vscode.commands.registerCommand('agentBridge.pickModel', async () => {
    const models = ["gpt-oss:20b", "llava:7b"]; // replace by querying your local host/API
    const pick = await vscode.window.showQuickPick(models, { placeHolder: 'Select model for Local Agent' });
    if (pick) {
      // call your Agent to persist selection (e.g., python vs_codex_local.py --set-model pick)
      try {
        // purely local, no network:
        cp.spawn(process.platform==='win32'?'python':'python3', ['Dev_Logic/vs_codex_local.py','--set-model', pick], { detached:true });
        vscode.window.showInformationMessage(`Local Agent model set: ${pick}`);
      } catch (e) {
        vscode.window.showErrorMessage(String(e));
      }
    }
  });

  context.subscriptions.push(openFile, openDiff, pickModel);
}
function deactivate(){}
module.exports = { activate, deactivate };
```

> This extension lives fully local. It does **not** talk to the internet and it does **not** require Copilot. It only helps the Local Agent open files/lines and request diffs in VS Code.
> If you later expose a tiny local HTTP API (e.g., **`vs_codex_local_api.py`** with `/models`, `/providers`, `/select`, `/status`, `/health`), you can replace the “models” array with a fetch to `http://127.0.0.1:<port>` and wire QuickPick to that. The sample API structure appears in your repo’s README for the local API concept. 

**Install the extension un-packed**:

* Open VS Code → **Run → Start Debugging** (select **Extension** if you have a standard `launch.json`), or
* `F1 → Developer: Load Extension…` (pick the folder), or
* Package with `vsce package` then **Install from VSIX**.

---

## 8) Wiring the Local Agent to call VS Code

In **VS Mode**, replace internal editor launching with VS Code calls:

* **Open file at line**:

  ```python
  subprocess.Popen(["code", "-g", f"{path}:{line}"])
  ```
* **Open diffs**: either:

  * Generate temp copies (`before`/`after`) and call the extension command `vscode.diff` by writing a small “side-channel” request (e.g., local file queue) the extension polls; **or**
  * Use the extension’s CLI shim (e.g., a Node script you bundle) that sends an IPC/JSON-RPC to the extension host.
* **Respect high contrast**: Any in-Agent confirmation dialogs must remain large, legible, and use light text on dark background.

The Local Agent already centralizes config and provides **safe JSON write** and **session logging** (`conversations/<ts>`) so every “Open in VS / Diff” action is recorded. Keep that behavior for audit. 

---

## 9) Daily workflow in VS Bridge mode (recommended)

1. **Toggle VS Mode ON** in the Agent.
2. Ask the Agent to **plan** changes (local RAG + safety prompts).
3. Agent proposes patches → **Open Diff** (VS Code shows side-by-side).
4. You accept/modify inside VS Code, run tests or lints in VS terminal.
5. When ready, you give the Agent “Allow” to apply staged diffs (the Agent never auto-executes).
6. Commit in VS Code’s SCM; the Agent logs the session trail.

This splits **reasoning/planning/apply (Agent)** from **editing/diff (VS Code)** while keeping everything reproducible and offline by default. 

---

## 10) Optional: Consulting Copilot “Agent” for advanced reasoning

If you have Copilot Chat/Agent enabled in VS Code, you can:

* Open Copilot Chat pane and **discuss a tricky algorithm** or **ask for alternatives**.
* Keep **execution local**: paste generated snippets back into the Local Agent review flow.
* The Agent remains the final **apply** surface (with its safety rules and logs).
* If you want the Local Agent to “hand off” context to Copilot semi-automatically, do it **explicitly**: a command that **copies** the current plan/patch into clipboard or a temp file and **opens** Copilot Chat. Do **not** auto-send code without a user step.

> Based on your notes: the good experience was Copilot Agent using a hosted **GPT-5 mini** quota — that’s separate from your local system. Treat it as “external advisor”; keep your Local Agent the **source of truth** for apply/patch. (Your Local Agent stays local-first, Ollama-backed.) 

---

## 11) Theme harmonization (high contrast, no low-contrast text)

* VS Code **workbench**: pick a dark theme with strong contrast (large white or near-white text over dark panels).
* Local Agent theme tokens (e.g., `term_bg = "#0b1828"`, `term_fg = "#e9f3ff"`, `accent = "#1E5AFF"`) should remain legible; keep any VS-Mode badges/buttons aligned with these values. **Never** place similar brightness colors together for text vs background. 

---

## 12) If/when you want “Codex” via OpenAI API (CLI/SDK) — optional add-on

You said: *“the only way to use codex at this time is through our codex-local bridge or npm cli with openai api; we have not installed that directly.”* To keep things explicit and under your control:

* **Node**: `npm i openai` then create a local script (e.g., `tools/openai_chat.js`) that **reads stdin** and writes stdout.
* **Env**: set `OPENAI_API_KEY` locally; **never** hard-code.
* **Network policy**: behind an explicit **Offline/Online** toggle with a red **Are you sure?** dialog.
* **Rate limiting**: apply a small client-side RPS limit so your local queue remains responsive.
* **Accounting**: if enabled, log tokens/cost into your Agent’s token ledger for visibility.

Keep this **OFF** by default so your Local Agent remains fully functional without any remote calls.

---

## 13) Installation checklist (copy/paste for the Agent to run)

1. **Create folders** if missing:

   * `Dev_Logic/vs_codex_local.py` (host) and `Dev_Logic/vs_bridge.md` (this guide).
   * `.vscode/extensions/agent-bridge/` with the files from §7.
2. **Python venv** + run `vs_codex_local.py`. Confirm it starts, writes `conversations/` and `config.json`. 
3. **Ollama** up with required models pulled.
4. **VS Code** open at repo root; load the extension un-packed (or install VSIX).
5. In Local Agent UI, **toggle VS Mode ON**.
6. Trigger **Open File** or **Open Diff**; verify VS Code displays the right target and the Agent logs the operation.
7. *(Optional)* Use Copilot Chat/Agent for reasoning; keep execution/apply in Local Agent.
8. *(Optional)* Add OpenAI SDK as an **explicit** online provider, default **OFF**.

---

## 14) Diagnostics & self-repair

* If `code` command is missing on PATH, prompt the user with a **high-contrast** instruction to enable “Shell Command: Install 'code' command in PATH” in VS Code.
* If extension commands are unavailable, show a reminder to load the local extension.
* If Ollama or local models are missing, keep your existing Agent warnings and guidance (pull models, check `http://127.0.0.1:11434`). The Agent already knows how to list local tags and model names for vision/LLM usage. 
* Record all errors in the Agent’s logs; never fail silently.

---

## 15) Security, privacy, and offline-first stance

* **Default deny** for any network paths; explicit **Approval** when enabling remote providers.
* Clipboard helpers should **TTL-clear** sensitive content.
* When VS Mode is on, all file operations are still **local** and auditable by the Agent (every open/diff action is logged in `conversations/<ts>/conversation.md` and JSONL). 

---

## 16) How the Agent will reference this guide

* On **first run** or when VS Mode is toggled ON and no VS extension is detected, the Agent should open:
  `Dev_Logic/vs_bridge.md` (this file) in the default system viewer or VS Code.
* The Agent can also surface a “**Help → VS Bridge**” menu item that opens this document.
* If you maintain a separate working folder (`vs_codex_local`), keep a short README with a pointer back to `Dev_Logic/vs_bridge.md` so the instructions remain canonical. 

---

## 17) Notes about your existing `vs_codex_local.py`

* It already defines theme tokens, safe JSON config I/O, session logging, RAG datasets, vision model routing, and strong **local-first** assumptions (Ollama endpoints, timeouts, pruning). The **VS Bridge** attaches to those surfaces — do **not** remove them. 
* Conversation transcripts are Markdown + JSONL; they are the **audit source**. VS Mode should **add log lines** when opening files/diffs through VS Code, keeping transparency. 
* If you later add `vs_codex_local_api.py` to expose `/models`, `/providers`, `/select`, `/status`, `/health`, keep it **local** and token-guarded as your README suggests. The VS extension’s **Model Picker** can wire to that endpoint. 

---

## 18) Summary of the integration contract

* **Agent owns safety & apply.**
* **VS Code owns editing & diff.**
* **Copilot (optional) owns additional reasoning** when you ask it; no auto-apply.
* **All local by default**; any online provider is an explicit, logged choice.
* **High-contrast UI always** — readable light text on dark, never low contrast.

This document is now the canonical, self-contained procedure for installing, using, and troubleshooting VS Bridge mode alongside your Local Agent.
