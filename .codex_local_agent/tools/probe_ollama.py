#!/usr/bin/env python3
import urllib.request
BASE = "http://127.0.0.1:11434"
for path in ("/api/version", "/api/tags"):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=3.0) as r:
            print(path, "=>", r.read().decode("utf-8"))
    except Exception as e:
        print(path, "=> ERROR:", e)
