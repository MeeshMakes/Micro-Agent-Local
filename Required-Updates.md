

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



