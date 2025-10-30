#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, os, queue, socket, socketserver, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPT_DIR  = Path(__file__).resolve().parent
TRANSIT_DIR = SCRIPT_DIR / "Codex-Transit"
EXE_PATH    = TRANSIT_DIR / "codex-x86_64-pc-windows-msvc.exe"

clients_lock = threading.Lock()
clients = []
codex_proc = None
stdout_thread = None
stdin_queue = queue.Queue()
stop_flag = threading.Event()

def broadcast(line: str) -> None:
    dead = []
    with clients_lock:
        for s in clients:
            try:
                s.sendall((line + "\n").encode("utf-8", "replace"))
            except Exception:
                dead.append(s)
        for d in dead:
            try: d.close()
            except Exception: pass
            try: clients.remove(d)
            except Exception: pass

def start_codex() -> subprocess.Popen:
    exe = EXE_PATH
    if not exe.exists():
        raise SystemExit(f"Codex exe not found: {exe} — run codex_installer.py first.")
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        creationflags = 0
    p = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=creationflags, text=True, bufsize=1)
    return p

def pump_stdout() -> None:
    global codex_proc
    for ln in iter(codex_proc.stdout.readline, ""):
        ln = ln.rstrip("\r\n")
        if not ln:
            continue
        broadcast(ln)
    stop_flag.set()

def pump_stdin() -> None:
    global codex_proc
    while not stop_flag.is_set():
        try:
            line = stdin_queue.get(timeout=0.25)
        except queue.Empty:
            continue
        try:
            codex_proc.stdin.write(line + "\n")
            codex_proc.stdin.flush()
        except Exception:
            stop_flag.set()
            break

class TcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        with clients_lock:
            clients.append(self.request)
        try:
            while not stop_flag.is_set():
                data = self.request.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8", "replace").strip()
                if not text:
                    continue
                if text.startswith("IMAGE:"):
                    path = text.split(":", 1)[1].strip()
                    stdin_queue.put(f"![image]({path})")
                else:
                    stdin_queue.put(text)
        finally:
            with clients_lock:
                try: clients.remove(self.request)
                except Exception: pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, *a, **k): return
    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            payload = {"codex": "up" if (codex_proc and (codex_proc.poll() is None)) else "down", "clients": len(clients)}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path.rstrip("/") == "/send":
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8", "replace")
            line = body.strip().replace("\r", "").replace("\n", " ")
            if line:
                stdin_queue.put(line)
            self.send_response(204); self.end_headers(); return
        self.send_response(404); self.end_headers()

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=37915, help="Bridge TCP/HTTP port")
    args = ap.parse_args(argv)

    global codex_proc, stdout_thread
    codex_proc = start_codex()

    t_out = threading.Thread(target=pump_stdout, daemon=True)
    t_in  = threading.Thread(target=pump_stdin, daemon=True)
    t_out.start(); t_in.start()
    stdout_thread = t_out

    tcp = ThreadedTCPServer(("127.0.0.1", args.port), TcpHandler)
    http = HTTPServer(("127.0.0.1", args.port), HealthHandler)

    thr_tcp = threading.Thread(target=tcp.serve_forever, daemon=True)
    thr_http = threading.Thread(target=http.serve_forever, daemon=True)
    thr_tcp.start(); thr_http.start()

    print(f"[Bridge] Listening TCP+HTTP on 127.0.0.1:{args.port}", flush=True)
    print("[Bridge] GET /health  |  POST /send  |  TCP lines", flush=True)

    try:
        while codex_proc.poll() is None:
            time.sleep(0.5)
    finally:
        stop_flag.set()
        try: tcp.shutdown()
        except Exception: pass
        try: http.shutdown()
        except Exception: pass
        try:
            if codex_proc and (codex_proc.poll() is None):
                codex_proc.terminate()
        except Exception:
            pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
