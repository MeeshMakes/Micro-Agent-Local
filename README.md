This is the proposed `README.md` for the system. Content is based on the current design and implementation in `micro_agent.py`. 

---

# Micro Agent Workbench

## Overview

Micro Agent Workbench is a local, high-contrast, offline-first development assistant.

It is a self-contained GUI that:

* Hosts an agent (LLM) with memory and context.
* Lets you talk to the agent in "Ask" mode for reasoning and research.
* Lets you authorize the agent to actually perform work in "Do Work" mode.
* Captures conversation, screenshots, OCR text, and file edits into a repo-scoped knowledge base.
* Manages code editing, version snapshots, diff staging, and safe application of changes.
* Bootstraps new projects and repos with a Script Creator tool.
* Exposes an Agent Manager for authority level, safety gates, and memory state. 

All logic lives in one file (`micro_agent.py`) and runs locally. You do not need a hosted service. The default model path assumes an Ollama-style API (`http://127.0.0.1:11434/api/chat`), but the architecture is generic and can be pointed at any similar local endpoint. 

## Goals

1. Treat the agent like a co-developer, not like a chatbot.
2. Keep everything local and inspectable.
3. Make the agent earn permission before touching disk or running commands.
4. Persist full reasoning context, screenshots, OCR results, diffs, and approvals.
5. Make it fast to spin up a new repo with scaffolding, docs, and a first script.
6. Maintain strict visual clarity and high-contrast UI for all states. 

## Core Concepts

### 1. RepoSession

A `RepoSession` represents the "active repo."
When you load a folder, the system prepares a hidden control directory inside it:

```text
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

* `agent.yaml`
  Machine-readable config: model, endpoint, authority mode, and write/execute policy.

* `agent.md`
  Human-readable summary of what the agent is allowed to do, and how it behaves.

* `chat_history.md`
  Full markdown transcript between you and the agent.
  Includes message text, `<think>` reasoning blocks, and embedded image references.
  This is the canonical memory of the conversation.

* `patches/`
  Staged diffs the agent proposes for file edits.

* `history/`
  Version snapshots of files over time so you can step backward and forward per file.

* `dataset/memory.jsonl`
  The local "RAG seed."
  Each entry logs OCR output, screenshot paths, hashes, tags, and markdown context from that turn of conversation.
  This is how the system builds long-term recall of visuals, logs, screenshots, etc. 

All of this is per-repo. Every repo has its own `.codex_local_agent` directory and its own memory.

### 2. Ask vs Do Work

At the top of the chat panel there are two primary actions:

* **Ask**
  Safe mode.
  You are talking to the agent like a research assistant.
  The agent can reason, summarize, explain, brainstorm, analyze screenshots, reference previous context, and build narrative.
  The agent cannot plan changes, propose commands, or try to edit disk in this path.
  Ask is for alignment, scoping, and clarification.

* **Do Work**
  Action mode.
  You are authorizing the agent to plan work, generate tasks, draft code edits, produce diffs, and request commands.
  Do Work is how you let the agent produce concrete next steps.

Both modes write into `chat_history.md` so the agent can carry forward context between raw discussion (Ask) and execution planning (Do Work). The distinction is about authority, not memory. 

### 3. Local LLM Client

The agent talks to a local model endpoint using a simple `/api/chat` style API.
Payload format:

```json
{
  "model": "gpt-oss:20b",
  "messages": [
    { "role": "user", "content": "..." }
  ]
}
```

The response is parsed, and the assistant's content is treated as the agent reply.

This allows use of offline or air-gapped models (for example via Ollama) instead of depending on a remote service. The endpoint, model name, and policy are recorded in `agent.yaml`. 

### 4. Conversation Logging

Every turn (user and agent) is appended to `chat_history.md` with a timestamp and role header.
The conversation is stored in markdown so you can:

* Scroll the transcript in the UI.
* Inspect it in plain text at any time.
* Commit it to source control if you want.

The renderer supports:

* Headings
* Bullet lists
* Code fences
* Inline code
* Images with thumbnails
* Special `<think> ... </think>` blocks

`<think>` blocks are styled as dim, italic, green-toned text in the UI.
They visually separate “internal reasoning” from “final answer.”
The final answer is rendered in larger bright white text for readability.
This enforces truthfulness about what is reasoning vs what is instruction. 

### 5. OCR and Image Intake

You can attach images directly in the chat input.

When you attach images:

* The system displays thumbnails inline in the chat feed.
* The absolute file paths for those images are automatically inserted into the message text so the agent has direct reference.
* Two OCR passes run:

  * `run_ocr_fast(...)` for lightweight, high-speed capture of key UI/chat text.
  * `run_ocr_full(...)` for a more complete scan.

The output from OCR plus the message markdown and the image paths are logged into `dataset/memory.jsonl` inside the active repo. This creates a searchable dataset of screenshots and extracted text, tagged and hashed, which becomes the foundation for local semantic recall and RAG. 

### 6. Task Manager and Task Feed

When the agent is in Do Work mode and proposes work, those steps become tasks.

* Each task has an ID, title, detail text, and status.
* Status can be “pending,” “running,” “done,” “skipped,” or “error.”
* The Task Feed panel shows tasks in a scrollable list and lets you:

  * Start
  * Skip
  * View details

You can select a task to inspect more details, including agent-proposed rationale.
The Task Feed is how high-level plans turn into actionable steps without immediately touching disk or executing commands. 

### 7. Staged Changes Panel

The agent can draft file edits. It does not write them directly.

Instead:

1. The agent (in Do Work) proposes edits to a file.
2. The app computes a unified diff (before vs after).
3. That diff is shown in the Staged Changes panel with color-coded additions, deletions, and headers.
4. You review diffs before allowing them to become real file writes.

Only after you approve do we actually write to disk.
All staged diffs are also saved under `.codex_local_agent/patches/`. 

### 8. Version History Snapshots

Every time a file is saved or updated with approval:

* The previous content is snapshotted under `.codex_local_agent/history/<file>/timestamp.txt`.
* You can step back and forth through snapshots using arrows in the Editor Info Bar.
* You can purge a file’s stored history if needed.

This gives you lightweight version control even before using git. It also prevents silent destructive writes because you always have prior copies. 

### 9. Pending Command Approval

The agent can also suggest shell commands. For example, a PowerShell command to inspect environment state.

These proposed commands never run automatically.
The approval pipeline is explicit:

* The Pending Command Bar shows:

  * The exact pending command line.
  * A set of controls:

    * **Allow**
      Approve and run.
    * **Skip**
      Reject and clear.
    * **Try Harder**
      Ask the agent to retry the same goal with a “push harder / refine strategy” instruction.
    * **Edit**
      Let you edit the proposed command text before execution.
    * **Always Allow**
      A toggle that whitelists repeated patterns so they can self-run without flashing for approval.

Visual rules:

* If a command is waiting and `Always Allow` is off, the Allow button flashes blue every 2 seconds.
  This is intentional. It is a high-contrast “attention required” signal.
* When you press **Edit**, the chat input box switches to edit mode:

  * Background changes to a dark purple.
  * Border outline becomes magenta.
  * High-contrast styling makes it obvious you are editing the pending command, not sending normal chat.
* After you edit and Send, that becomes the new pending command text, and the chat box reverts to normal. 

This solves a critical problem: the model can propose shell actions, but it cannot run them behind your back.

## UI Layout

The window is split into structured regions. 

### A. Top Banner Mini-App Dock

* A thin banner at the very top holds a row of square icons, aligned from right to left.
* Each icon represents a “mini-app.”
* Clicking an icon opens that mini-app’s panel.
* The icon stays highlighted while that panel is open.

### B. Left Dock Column

* Mini-app panels live in a collapsible vertical column on the far left of the window.
* Panels stack vertically in a scrollable region.
* If no mini-apps are open, this column collapses to reclaim space.
* If one or more are open, the column is visible.

This is how you pop open extra utilities without leaving the main environment. Think of them as internal sidecar tools.

### C. Project Tree and Editor

To the right of the mini-app column you get:

* A file tree (`ProjectTree`) rooted at the active repo.
* Editor tabs (`EditorTabs`), each one a `CodeEditor`.
* An Info Bar under the editor with:

  * File path
  * Prev/Next snapshot arrows
  * Copy Path
  * Clone
  * Doc (ask agent for documentation/explanation)
  * Purge Hist (clear stored history for this file)

The editor enforces high-contrast syntax view: light text on dark background, and high-visibility selection colors.

### D. Chat / Agent Panel

On the right side sits the Chat Panel (`ChatPanel`):

* Ask / Do Work buttons
* Brain mode dropdown

  * “Agent (full repo access)”
  * “LLM (chat only)”
* Transcript view (markdown renderer with `<think>` styling and embedded thumbnails)
* Task Feed panel
* Staged Changes panel
* Pending Command Bar
* Chat input box with image attach
* Buttons:

  * Plan Tasks
  * Remember
  * Expand Logic
  * Stage File Change
  * Write File To Disk (Approve)

This panel is where you talk, review, approve, and push changes forward. 

## Mini-Apps

Mini-apps run inside the UI, not as external popups. They are accessed from the top banner dock and rendered in the collapsible left column. Two core mini-apps ship in the current design. 

### 1. ScriptCreatorApp

Purpose: bootstrap a brand new working folder or script file fast, with documentation and policy metadata already in place.

Features:

* Destination picker

  * You can paste a target path or pick a folder.
  * If the folder does not exist, it will be created.
  * There is also a one-click “Desktop” target to keep it simple.

* Script name + file type

  * Choose a filename.
  * Choose a file type from a dropdown like Windows “Save as type”:
    `.py`, `.md`, `.txt`, `.cs`, `.java`, `.cpp`, `.h`, `.html`, `.ps1`, `.json`, `.csv`, etc.
  * Default is Python.
  * If you provide no name, it defaults to `main.py`.

* Collision handling

  * If the target file already exists and has content:

    * The app previews that file in a popup.
    * You can confirm overwrite or cancel.

* Description box

  * You write a short description of the project or script purpose.
  * The system uses that description to auto-generate a `README.md` in the new folder.
  * That folder is also initialized with a `.codex_local_agent` directory (agent metadata, chat_history, dataset base, etc.) so the repo is immediately “agent-ready.”

Result: instant “new repo” seed with:

* A starter script.
* A README documenting intent.
* Agent config and memory scaffolding.
  This removes friction for starting a new tool, prototype, bot, or experiment. 

### 2. AgentManagerApp

Purpose: expose the agent’s state and authority controls.

Shows:

* Current authority mode:

  * Full Auto
    Agent can execute known-safe patterns without prompting.
  * Ask First
    Agent must ask before running commands or writing files.
  * Read Only
    Agent can propose but cannot execute or write.

* Policy flags from `agent.yaml`:

  * `require_command_allow`
  * `safe_write_outside_repo`

* “Always Allow Repetitive Commands” toggle:

  * If enabled, repeated commands in the same category auto-run without flashing blue prompts.

* Dataset summary:

  * How many memory records exist in `dataset/memory.jsonl`.
  * Which tags have been seen (like `screenshot`, `ocr_capture`).
  * Hashes of screenshots already logged.

* Pending Command pipeline state:

  * Shows what command is queued.
  * Shows if it is blocked waiting for approval.
  * Surfaces whether “Always Allow” is currently active. 

This gives you direct visibility into what the agent “knows,” what it plans to do next, and what level of autonomy it currently has.

## Loading and Linking a Repo

There are two main flows to define or change the active repo. 

### 1. Clipboard Load

* Copy a path in Explorer (Ctrl+C on a file or folder).
* Inside Micro Agent Workbench, choose "Load Path From Clipboard".

  * If the clipboard content is a file path:

    * That file is opened in an editor tab.
    * Its parent folder becomes the active repo root.
  * If the clipboard content is a folder path:

    * That folder becomes the active repo root.

This instantly “attaches” an existing codebase without having to browse in a dialog.

### 2. ScriptCreatorApp

* Use ScriptCreatorApp to create a new folder, main script, README, and agent metadata.
* That new folder is automatically treated as the active repo and is shown in the Project Tree.

## High-Contrast Accessibility Rules

The entire UI is explicitly designed for clarity:

* Dark backgrounds with bright text.
* No low-contrast states.
* Important states get unique, loud accents:

  * Flashing blue “Allow” button when an unapproved command is pending.
  * Magenta outline and purple background for “Edit Pending Command” mode.
  * Green italic blocks for `<think>` reasoning.
  * Bright white for final agent answers.

These rules are enforced everywhere, including editor text, task status labels, borders, and highlights. This reduces state confusion and makes it obvious when the agent is asking for permission versus just talking. 

## Typical Workflow

1. **Start or attach a repo**

   * Either load an existing folder via clipboard
   * Or create a new mini-project with ScriptCreatorApp
     (auto-generates `main.py` or other file, plus README and `.codex_local_agent`).

2. **Talk in Ask mode**

   * Use Ask to explain context, paste screenshots, get analysis.
   * Attach images of logs, game chat, UI, etc.
   * OCR runs automatically and stores text + image references in `dataset/memory.jsonl`.
   * All discussion is appended to `chat_history.md`.

3. **Escalate to Do Work**

   * Use Do Work to request concrete changes.
   * The agent proposes tasks and file edits.
   * New tasks show up in the Task Feed.
   * Proposed file edits generate diffs in Staged Changes.

4. **Review diffs**

   * Inspect color-coded diffs.
   * Approve staged changes to write them to disk.
   * Snapshots are stored under `.codex_local_agent/history/` so you can roll back.

5. **Handle commands**

   * If the agent wants to run a shell command, it goes to Pending Command.
   * The UI shows the exact command.
   * You can Allow (run), Skip, Try Harder, or Edit.
   * Only explicit approval (or Always Allow) executes anything.

6. **Document and iterate**

   * Use the Info Bar under the editor to generate docs for a file, clone it, or purge old snapshots.
   * Continue iterating. The agent now has memory of your screenshots, task history, and approved changes.

This loop repeats. Over time, the repo itself becomes the agent’s working memory, including design rationale, OCR’d screenshots of bugs, staged diffs, and final accepted writes. 

## Security and Control Model

* The agent cannot silently run commands.
* The agent cannot silently write to disk.
* All proposed work is visible and reviewable before execution.
* You can downgrade authority (Read Only) at any point in the Agent Manager.
* You can purge file history if sensitive content was captured.
* You can inspect `agent.yaml` at any time to confirm model, endpoint, and policies.

The design treats the agent as a controlled collaborator inside your repo, not as an external automation layer with hidden access. 

## Summary

Micro Agent Workbench is a local autonomous assistant plus an IDE shell.
It merges:

* A repo-aware AI assistant with persistent memory.
* A diff-first code editor with snapshot history.
* A task feed and approval gate for work.
* A screenshot/OCR pipeline that feeds a local dataset for future recall.
* A project bootstrapper that can spin up a new repo, script, and README in seconds.
* An Agent Manager that surfaces autonomy, safety gates, and memory state.

Everything is transparent. Everything is high contrast. Nothing runs without you seeing it and approving it. 
