

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



