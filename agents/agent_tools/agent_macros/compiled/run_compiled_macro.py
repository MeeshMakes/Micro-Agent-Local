#!/usr/bin/env python3
"""
Minimal runner for compiled macros.
- Parses YAML
- --dry-run prints the plan
- Does not execute destructive commands
"""
import argparse, sys, json
from pathlib import Path
try:
    import yaml
except Exception:
    print("[runner] pyyaml missing. pip install pyyaml", file=sys.stderr); sys.exit(2)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--macro", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--params", default="{}")
    a = ap.parse_args()
    path = Path(a.macro)
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    params = json.loads(a.params)
    def fill(s):
        for k,v in params.items(): s = s.replace("{"+k+"}", str(v))
        return s
    def emit(title, seq):
        if not seq: return
        print(title+":")
        for i, cmd in enumerate(seq,1): print(f"  {i:02d}. "+fill(cmd))
        print()
    print("=== COMPILED MACRO PLAN ===")
    print("macro_id:", spec.get("macro_id"))
    print("title   :", spec.get("title"))
    print()
    emit("preflight", spec.get("preflight"))
    emit("steps", spec.get("steps"))
    emit("success", spec.get("success"))
    emit("rollback", spec.get("rollback"))
    if not a.dry_run:
        print("[runner] printing only. wire to execution harness to run.")
if __name__ == "__main__":
    main()
