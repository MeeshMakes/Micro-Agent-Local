#!/usr/bin/env python3
import argparse, sys, shutil
from pathlib import Path

def main():
  ap = argparse.ArgumentParser();
  ap.add_argument('--file', required=True); ap.add_argument('--find', required=True); ap.add_argument('--replace', required=True); ap.add_argument('--guard', action='store_true');
  a = ap.parse_args(); p = Path(a.file)
  if not p.exists(): print('RESULT: MISSING'); sys.exit(1)
  b = p.with_suffix(p.suffix+'.bak')
  if not b.exists(): shutil.copy2(p, b)
  t = p.read_text(encoding='utf-8', errors='ignore')
  nt = t.replace(a.find, a.replace)
  if nt==t: print('RESULT: NO_CHANGE'); sys.exit(0)
  p.write_text(nt, encoding='utf-8'); print('RESULT: PATCHED')
if __name__=='__main__': main()
