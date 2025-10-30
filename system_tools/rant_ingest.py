#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append rant_feed.md into Required-Updates.md as timestamped block."""
import datetime, pathlib

ROOT = pathlib.Path(".").resolve()
rant_path = ROOT / "rant_feed.md"
req_path = ROOT / "Required-Updates.md"

def main():
    if not rant_path.exists():
        print("No rant_feed.md found."); return
    rant = rant_path.read_text(encoding="utf-8").strip()
    if not rant:
        print("Rant feed empty."); return
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = f"\n\n## Rant {stamp}\n\n{rant}\n"
    with open(req_path, "a", encoding="utf-8") as f:
        f.write(block)
    rant_path.write_text("", encoding="utf-8")
    print(f"Ingested rant into Required-Updates.md @ {stamp}")

if __name__ == "__main__":
    main()
