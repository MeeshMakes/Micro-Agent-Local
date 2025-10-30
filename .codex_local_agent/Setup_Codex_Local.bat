@echo off
setlocal
cd /d "%~dp0"
py -3 codex_installer.py --bridge
