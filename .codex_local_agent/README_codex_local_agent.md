# .codex_local_agent — Local Codex Bridge (Portable)

> **Purpose**: This folder contains a **portable installer + bridge** to run the **Codex Rust CLI** locally, wired to **Ollama** for models, and expose a **TCP/HTTP bridge** that other apps (e.g., Codex Terminal, micro-agent) can talk to.

**High-contrast policy**: Any UI we add later (e.g., embedded terminal) must enforce readable **light text on dark** or **dark on light**. No low-contrast pairings—ever. (Inline notes in the code remind this.)

---

## What lives here

- `codex_installer.py` — **One-click bootstrap**: download + verify Codex CLI (rust-v0.34.0), extract, write `~/.codex/config.toml` for **Ollama /v1 chat**, warm a model, and (optionally) start the **bridge**.
- `start_codex_bridge.py` — Launch Codex CLI **headless** with pipes and start a **bridge server** on `localhost:37915`:
  - **TCP** line gateway for multiple clients
  - **HTTP**: `GET /health` for status, `POST /send` to push a line to Codex
- `cli_client.py` — Tiny terminal client that connects to the bridge and lets you type lines to Codex.
- `verify_install.py` — Quick sanity checks: Ollama reachable, models listable, Codex exe runnable, bridge ports free/used.
- `config/config.toml` — Template for `~/.codex/config.toml` pointing Codex to **Ollama Chat API** (`/v1`).
- `manifests/INSTALL_MANIFEST.md` — A runnable, human-readable **install recipe & API doc** for integrators.
- `tools/probe_ollama.py` — Pings Ollama (`/api/version`, `/api/tags`) and prints results.
- `tools/send_text.py` — One-shot CLI: send a single line to the bridge from scripts/automation.
- `start_codex_bridge.bat` — Windows convenience launcher.
- `Setup_Codex_Local.bat` — Windows “do everything”: install + start bridge.
- `logs/` — where bridge & helper logs can land (created at runtime).

This exact layout mirrors what the Codex Terminal integration expects, and it’s compatible with a micro-agent that prefers simple TCP/HTTP hooks.

---

## Quick Start (Windows)

1) **Install Python 3.10+** and **Ollama** (run `ollama serve`).
2) Extract this ZIP into: `Micro-Agent-Local\.codex_local_agent\`
3) Double-click **Setup_Codex_Local.bat** (or run `py -3 codex_installer.py --bridge`)
   - The installer will:
     - Download Codex CLI from GitHub:
       `https://github.com/openai/codex/releases/download/rust-v0.34.0/codex-x86_64-pc-windows-msvc.exe.zip`
     - Verify SHA-256: `789563e58e6126de96329c8e154718409378831abcef3856c8b46527b20c08ac`
     - Extract to `./Codex-Transit/`
     - Write `~/.codex/config.toml` targeting **Ollama /v1 chat**
     - Warm your model (default: `qwen3:8b`) and start the **bridge** on `:37915`
4) Test the bridge:
   - `py -3 cli_client.py` → type `hello` and hit Enter.

> If Ollama isn’t running, the installer tries to launch it. You can also do `ollama serve` manually in a separate terminal.

---

## How the bridge works (overview)

- Starts Codex CLI as a hidden child process with **stdin/stdout pipes**.
- Spins up two servers on the same port `:37915`:
  - **HTTP** for health & programmatic send:
    - `GET /health` → `{"codex":"ok|down","clients":N}`
    - `POST /send` → body is raw text (one line) forwarded to Codex stdin
  - **TCP** for interactive sessions (multiple clients). Every client sees Codex stdout, and any client’s line goes to stdin.
- You can run multiple script clients concurrently (e.g., a GUI + a batch job).

> Images: The CLI doesn’t take binary image payloads. When you need to “send an image,” the bridge prints a markdown reference such as `![image](C:/path/to.png)`. Your higher-level app should bucket files and pass markdown to Codex.

---

## Authority / Safety

- This folder manages binaries and can launch child processes. Use it with **Agent Manager** approvals enabled.
- The **Always Allow** policy should be used only for trusted workflows.
- Logs write to `./logs/` for audit; adjust as needed.

---

## Upgrading

- Edit `codex_installer.py` constants (`RELEASE_TAG`, `ASSET_SHA256`) if a newer release ships.
- Re-run `codex_installer.py` without `--force` to **skip** if already present; use `--force` to reinstall.

---

## Troubleshooting

- **Ollama not reachable** → Start Ollama: `ollama serve`
- **SHA mismatch** → The asset changed; update `ASSET_SHA256` or use a new release tag.
- **Bridge port busy** → Use `--port=NNNN`.
- **No models** → `ollama pull qwen3:8b` or another entry in the preference list.
