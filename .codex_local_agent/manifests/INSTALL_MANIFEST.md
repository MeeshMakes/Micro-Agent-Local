# INSTALL_MANIFEST — Codex Local Bridge

## Steps
1. Create `./Codex-Transit/`
2. Ensure Ollama at `http://127.0.0.1:11434`
3. Select model (prefers `qwen3:8b`)
4. Write `~/.codex/config.toml` (Ollama Chat API)
5. Download:
   - URL: `https://github.com/openai/codex/releases/download/rust-v0.34.0/codex-x86_64-pc-windows-msvc.exe.zip`
   - SHA-256: `789563e58e6126de96329c8e154718409378831abcef3856c8b46527b20c08ac`
6. Extract into `./Codex-Transit/`
7. Start bridge (TCP/HTTP `127.0.0.1:37915`):
   - `GET /health`, `POST /send`
