#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, socket, subprocess
from pathlib import Path

SCRIPT_DIR  = Path(__file__).resolve().parent
TRANSIT_DIR = SCRIPT_DIR / "Codex-Transit"
EXE_PATH    = TRANSIT_DIR / "codex-x86_64-pc-windows-msvc.exe"
OLLAMA      = "http://127.0.0.1:11434"

def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0

def main() -> int:
    ok = True
    if not EXE_PATH.exists():
        print("[x] codex exe missing:", EXE_PATH); ok = False
    else:
        out = subprocess.run([str(EXE_PATH), "--version"], capture_output=True, text=True).stdout or ""
        print("[i] codex version:", out.strip())
    try:
        import urllib.request, json as _j
        u = urllib.request.urlopen(f"{OLLAMA}/api/version", timeout=3.0)
        j = _j.loads(u.read().decode("utf-8", "replace"))
        print("[i] ollama:", j)
    except Exception as e:
        print("[x] ollama unreachable at", OLLAMA, ":", e); ok = False
    print("[i] bridge port 37915:", "BUSY (probably running)" if port_busy(37915) else "free")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
