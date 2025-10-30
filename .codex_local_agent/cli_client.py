#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket, sys, threading

HOST = "127.0.0.1"
PORT = 37915

def reader(sock: socket.socket):
    while True:
        data = sock.recv(4096)
        if not data:
            print("[client] disconnected")
            break
        print(data.decode("utf-8", "replace"), end="\n")

def main(argv=None):
    global PORT
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except Exception:
            pass
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    t = threading.Thread(target=reader, args=(s,), daemon=True)
    t.start()
    print(f"[client] connected to {PORT}; type and press Enter. 'exit' to quit.")
    try:
        for line in sys.stdin:
            line = line.rstrip("\r\n")
            if line.lower().strip() in ("exit", "quit"):
                break
            s.sendall((line + "\n").encode("utf-8", "replace"))
    finally:
        try: s.close()
        except Exception: pass

if __name__ == "__main__":
    main()
