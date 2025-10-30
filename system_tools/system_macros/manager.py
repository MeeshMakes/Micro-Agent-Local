#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Macro manager — persists small terminal/file automation snippets with TTL and bean counts."""
import sys, json, datetime, pathlib

STORE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "tools/macros/store.jsonl")
STORE.parent.mkdir(parents=True, exist_ok=True)

def add_macro(text):
    obj = {
        "macro": text,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "last_used": datetime.datetime.now().isoformat(timespec="seconds"),
        "beans": 1
    }
    with open(STORE, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False)+"\n")

def use_macro(text):
    rows = []
    if STORE.exists():
        with open(STORE, "r", encoding="utf-8") as f:
            for ln in f.read().splitlines():
                if not ln.strip(): continue
                obj = json.loads(ln)
                if obj.get("macro") == text:
                    obj["last_used"] = datetime.datetime.now().isoformat(timespec="seconds")
                    obj["beans"] = int(obj.get("beans",0)) + 1
                rows.append(obj)
    with open(STORE, "w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False)+"\n")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[2] == "add":
        add_macro(sys.argv[3])
    elif len(sys.argv) >= 3 and sys.argv[2] == "use":
        use_macro(sys.argv[3])
    else:
        print("Usage: manager.py <store_path> add|use \"macro text\"")
