#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Default Agent runtime loop (minimal scaffold)."""
import json, re, datetime, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
p = lambda *parts: ROOT.joinpath(*parts)

def sha10(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]

def load_cfg():
    with open(p("agents","default","agent.yaml"), "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    s = y["sources"]; a = y["authority"]; m = y["macros"]; r = y["runtime"]
    return {
        "required": p(s["required_updates"]),
        "impl": p(s["implemented_updates"]),
        "q": p(s["quarantined_updates"]),
        "missing": p(s["missing_updates"]),
        "inbox": p("memory","logic_inbox.jsonl"),
        "rant": p(s.get("rant_feed","rant_feed.md")),
        "ledger": p(a["ledger_path"]),
        "macro_store": p(m["store_path"]),
        "ttl_hours": int(m.get("ttl_hours",24)),
        "log_dir": p(r.get("log_dir","logs"))
    }

def ensure(cfg):
    cfg["inbox"].parent.mkdir(parents=True, exist_ok=True)
    cfg["impl"].parent.mkdir(parents=True, exist_ok=True)
    cfg["q"].parent.mkdir(parents=True, exist_ok=True)
    cfg["missing"].parent.mkdir(parents=True, exist_ok=True)
    cfg["macro_store"].parent.mkdir(parents=True, exist_ok=True)
    cfg["log_dir"].mkdir(parents=True, exist_ok=True)
    for md in [cfg["impl"], cfg["q"], cfg["missing"]]:
        if not md.exists():
            md.write_text(f"# {md.name}\n\n(Initialized {datetime.date.today().isoformat()})\n", encoding="utf-8")
    if not cfg["ledger"].exists():
        cfg["ledger"].parent.mkdir(parents=True, exist_ok=True)
        cfg["ledger"].write_text(json.dumps({"version":"1.0","approvals":[],"history":[]}, indent=2), encoding="utf-8")
    if not cfg["macro_store"].exists():
        cfg["macro_store"].write_text("", encoding="utf-8")

def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

TASK_RE = re.compile(r"^(?:[-*]|\d+\.)\s+(.*)$")

def ingest_rant(cfg):
    if not cfg["rant"].exists(): return
    rant = cfg["rant"].read_text(encoding="utf-8").strip()
    if not rant: return
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = f"\n\n## Rant {stamp}\n\n{rant}\n"
    with open(cfg["required"], "a", encoding="utf-8") as f:
        f.write(block)
    cfg["rant"].write_text("", encoding="utf-8")

def parse_required(cfg):
    if not cfg["required"].exists(): return 0
    text = cfg["required"].read_text(encoding="utf-8")
    seen = set()
    if cfg["inbox"].exists():
        with open(cfg["inbox"], "r", encoding="utf-8") as f:
            for ln in f.read().splitlines():
                if ln.strip():
                    try: seen.add(json.loads(ln).get("desc",""))
                    except: pass
    new = 0
    for line in text.splitlines():
        m = TASK_RE.match(line.strip())
        if not m: continue
        desc = m.group(1).strip()
        if desc in seen: continue
        append_jsonl(cfg["inbox"], {
            "task_id": "T-" + sha10(desc),
            "desc": desc,
            "source": "Required-Updates.md",
            "created": datetime.datetime.now().isoformat(timespec="seconds")
        })
        new += 1
    return new

def take_one(cfg):
    impl_ids = set()
    if cfg["impl"].exists():
        for line in cfg["impl"].read_text(encoding="utf-8").splitlines():
            if "] " in line and ":" in line:
                impl_ids.add(line.split("] ",1)[1].split(":",1)[0].strip())
    if not cfg["inbox"].exists(): return None
    with open(cfg["inbox"], "r", encoding="utf-8") as f:
        tasks = [json.loads(ln) for ln in f.read().splitlines() if ln.strip()]
    for t in tasks:
        if t["task_id"] not in impl_ids:
            return t
    return None

def record_impl(cfg, t):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(cfg["impl"], "a", encoding="utf-8") as f:
        f.write(f"- ✅ [{stamp}] {t['task_id']}: {t['desc']} (from Required-Updates.md)\n")

def refresh_missing(cfg):
    impl_ids = set()
    if cfg["impl"].exists():
        for line in cfg["impl"].read_text(encoding="utf-8").splitlines():
            if "] " in line and ":" in line:
                impl_ids.add(line.split("] ",1)[1].split(":",1)[0].strip())
    inbox = []
    if cfg["inbox"].exists():
        with open(cfg["inbox"], "r", encoding="utf-8") as f:
            inbox = [json.loads(ln) for ln in f.read().splitlines() if ln.strip()]
    missing = [t for t in inbox if t["task_id"] not in impl_ids]
    lines = ["# Missing-Updates.md", ""]
    for t in missing:
        lines.append(f"- ⏳ {t['task_id']}: {t['desc']} (from {t['source']})")
    cfg["missing"].write_text("\n".join(lines)+"\n", encoding="utf-8")

def main_once():
    cfg = load_cfg()
    ensure(cfg)
    ingest_rant(cfg)
    parse_required(cfg)
    t = take_one(cfg)
    if t: record_impl(cfg, t)
    refresh_missing(cfg)

if __name__ == "__main__":
    main_once()
