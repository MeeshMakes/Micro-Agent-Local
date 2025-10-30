#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, socket, subprocess, sys, time, zipfile
from pathlib import Path
from urllib import request

RELEASE_TAG   = "rust-v0.34.0"
ASSET_ZIP     = "codex-x86_64-pc-windows-msvc.exe.zip"
ASSET_SHA256  = "789563e58e6126de96329c8e154718409378831abcef3856c8b46527b20c08ac"
ASSET_URL     = "https://github.com/openai/codex/releases/download/rust-v0.34.0/codex-x86_64-pc-windows-msvc.exe.zip"
DEFAULT_MODEL = "qwen3:8b"
OLLAMA        = "http://127.0.0.1:11434"
API_VER       = f"{OLLAMA}/api/version"
API_TAGS      = f"{OLLAMA}/api/tags"

SCRIPT_DIR    = Path(__file__).resolve().parent
TRANSIT_DIR   = SCRIPT_DIR / "Codex-Transit"
DEFAULT_EXE   = TRANSIT_DIR / "codex-x86_64-pc-windows-msvc.exe"
WIN_CFG_DIR   = Path.home() / ".codex"
WIN_CFG       = WIN_CFG_DIR / "config.toml"

PREF_LIST = [
    "gpt-oss:20b",
    "qwen3-coder:30b",
    "qwen3:30b",
    "qwen3:8b",
    "deepseek-coder-v2:16b",
    "granite-code:8b",
    "qwen3:4b",
    "mistral:7b",
    "starcoder2:latest",
    "gemma3:27b",
    "gemma3:4b",
    "phi4-mini:3.8b",
]

def _print(msg: str) -> None:
    print(msg, flush=True)

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def _http_json(url: str, timeout=5.0):
    try:
        with request.urlopen(request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return { "__error__": str(e) }

def ensure_dirs() -> None:
    TRANSIT_DIR.mkdir(parents=True, exist_ok=True)

def ensure_ollama() -> None:
    obj = _http_json(API_VER, timeout=2.0)
    if "__error__" not in obj:
        return
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["powershell", "-NoLogo", "-NoProfile", "-Command",
                 "Start-Process -WindowStyle Minimized cmd -ArgumentList '/c','ollama','serve'"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception:
            pass
    deadline = time.time() + 60
    while time.time() < deadline:
        obj = _http_json(API_VER, timeout=2.0)
        if "__error__" not in obj:
            return
        time.sleep(0.5)
    raise RuntimeError(f"Ollama not reachable at {OLLAMA}. Start it manually via 'ollama serve'.")

def list_models() -> list[str]:
    obj = _http_json(API_TAGS, timeout=5.0)
    names: list[str] = []
    if "__error__" not in obj:
        for m in obj.get("models") or []:
            n = m.get("name")
            if n:
                names.append(n)
    if names:
        return sorted(set(names))
    exe = shutil.which("ollama")
    if not exe:
        return []
    out = subprocess.run([exe, "list"], capture_output=True, text=True).stdout or ""
    for ln in out.splitlines():
        m = re.match(r"^(\S+:\S+)", ln.strip())
        if m:
            names.append(m.group(1))
    return sorted(set(names))

def auto_pick_model(requested: str|None) -> str:
    if requested:
        return requested
    avail = list_models()
    for pref in PREF_LIST:
        if pref in avail:
            return pref
    return avail[0] if avail else DEFAULT_MODEL

def warm_model(name: str) -> bool:
    import json as _json
    try:
        payload = _json.dumps({"model": name, "prompt": "ping", "stream": False}).encode("utf-8")
        req = request.Request(f"{OLLAMA}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=12.0) as resp:
            _ = resp.read()
        return True
    except Exception:
        return False

def download_codex(zip_path: Path) -> None:
    _print(f"[Info] Downloading: {ASSET_URL}")
    tmp = zip_path.with_suffix(".part")
    if tmp.exists():
        tmp.unlink()
    with request.urlopen(request.Request(ASSET_URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r, tmp.open("wb") as f:
        while True:
            buf = r.read(128 * 1024)
            if not buf:
                break
            f.write(buf)
    tmp.replace(zip_path)
    digest = _sha256_file(zip_path)
    _print(f"[Info] SHA-256: {digest}")
    if digest.lower() != ASSET_SHA256.lower():
        raise RuntimeError("SHA-256 mismatch — release may have changed. Update ASSET_SHA256.")

def extract_codex(zip_path: Path) -> Path:
    import zipfile
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(TRANSIT_DIR)
    candidate = TRANSIT_DIR / "codex-x86_64-pc-windows-msvc.exe"
    if not candidate.exists():
        for name in os.listdir(TRANSIT_DIR):
            if name.lower().endswith(".exe"):
                candidate = TRANSIT_DIR / name
                break
    if not candidate.exists():
        raise RuntimeError("Codex EXE not found after extraction.")
    return candidate

def write_win_cfg(model: str) -> None:
    WIN_CFG_DIR.mkdir(parents=True, exist_ok=True)
    txt = (
        f'model = "{model}"\\n'
        f'model_provider = "ollama"\\n\\n'
        f'[model_providers.ollama]\\n'
        f'name = "Ollama"\\n'
        f'base_url = "{OLLAMA}/v1"\\n'
        f'wire_api = "chat"\\n'
    )
    WIN_CFG.write_text(txt, encoding="utf-8")
    _print(f"[OK] Wrote config: {WIN_CFG}")

def codex_version(exe: Path) -> str:
    try:
        out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=8)
        return (out.stdout or out.stderr or "").strip()
    except Exception as e:
        return f"(version check failed: {e})"

def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="Preferred model name (Ollama)")
    ap.add_argument("--force", action="store_true", help="Force re-download and re-extract")
    ap.add_argument("--bridge", action="store_true", help="Start the Codex bridge after install")
    ap.add_argument("--port", type=int, default=37915, help="Bridge port (TCP/HTTP)")
    args = ap.parse_args(argv)

    ensure_dirs()
    ensure_ollama()

    model = auto_pick_model(args.model)
    _print(f"[Info] Using model: {model}")
    warm_model(model)

    write_win_cfg(model)

    zip_path = TRANSIT_DIR / ASSET_ZIP
    exe_path = DEFAULT_EXE
    if args.force or not exe_path.exists():
        download_codex(zip_path)
        exe_path = extract_codex(zip_path)
        _print(f"[OK] Extracted: {exe_path}")
    else:
        _print(f"[Skip] Codex already present at: {exe_path}")

    _print(f"[Info] Codex CLI: {codex_version(exe_path)}")

    if args.bridge:
        if not port_free(args.port):
            _print(f"[Warn] Port {args.port} is busy — the bridge may already be running.")
        if os.name == "nt":
            subprocess.Popen(["cmd", "/c", "start", "/min", "py", "-3", "start_codex_bridge.py", "--port", str(args.port)], cwd=str(SCRIPT_DIR))
        else:
            subprocess.Popen([sys.executable, "start_codex_bridge.py", "--port", str(args.port)], cwd=str(SCRIPT_DIR))
        _print("[OK] Bridge launch requested.")
    else:
        _print("[OK] Installation finished. Run start_codex_bridge.py to launch the bridge.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
