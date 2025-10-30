@echo off
setlocal
REM High-contrast note: make console colors legible.
cd /d "%~dp0"
py -3 start_codex_bridge.py --port 37915
