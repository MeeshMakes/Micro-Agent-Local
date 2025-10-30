#!/usr/bin/env python3
"""
loop.py — Micro‑Agent runtime loop

High-contrast UI rule (UI relying on this loop must keep readable contrast).

Drives the Trifecta workflow:
  Required-Updates.md  -> (plan) -> approvals -> (do) -> Implemented-Updates.md
and reconciles README.md to the current state. Manages approvals, macros, datasets,
and agent profiles.

Usage:
  python loop.py --mode ask --prompt "What's next?"
  python loop.py --mode plan
  python loop.py --mode do --auto-allow true
  python loop.py --watch
"""
from __future__ import annotations

import argparse, dataclasses as dc, datetime as dt, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def append_md(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t = read_text(p)
    if t and not t.endswith("\n"):
        t += "\n"
    write_text(p, (t or "") + s.rstrip() + "\n")

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def json_load(p: Path, default: Any) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def json_dump(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

@dc.dataclass
class Paths:
    root: Path
    agents_dir: Path
    default_agent_dir: Path
    roster_dir: Path
    archived_agents_dir: Path
    datasets_dir: Path
    logs_dir: Path
    macros_dir: Path
    runtime_state: Path
    required_updates: Path
    implemented_updates: Path
    quarantined_updates: Path
    missing_updates: Path
    readme: Path
    chat_history: Path

    @classmethod
    def from_root(cls, root: Path) -> "Paths":
        return cls(
            root=root,
            agents_dir=root/"agents",
            default_agent_dir=root/"agents"/"default",
            roster_dir=root/"agent_roster",
            archived_agents_dir=root/"Archived_Agents",
            datasets_dir=root/"datasets",
            logs_dir=root/"logs",
            macros_dir=root/"system_tools"/"system_macros",
            runtime_state=root/"logs"/"runtime_state.json",
            required_updates=root/"Required-Updates.md",
            implemented_updates=root/"Implemented-Updates.md",
            quarantined_updates=root/"Quarantined-Updates.md",
            missing_updates=root/"Missing-Updates.md",
            readme=root/"README.md",
            chat_history=root/"chat_history.md",
        )

def ensure_pyyaml():
    try:
        import yaml  # type: ignore
        return yaml
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
            import yaml  # type: ignore
            return yaml
        except Exception as e:
            print(f"[warn] PyYAML not available ({e}). Continuing with defaults.")
            return None

@dc.dataclass
class AgentProfile:
    name: str = "default"
    provider: str = "ollama"  # or "openai_compatible"
    model: str = "gpt-oss:20b"
    endpoint: str = "http://127.0.0.1:11434"
    api_key_env: str = "OPENAI_API_KEY"
    safety_write_outside_repo: bool = False
    require_command_allow: bool = True
    macros_retention_hours: int = 24
    try_harder_prompt: str = "Re-evaluate the same task with more rigor and safer commands."

    @classmethod
    def load(cls, paths: Paths, override: Optional[Path]) -> "AgentProfile":
        yaml = ensure_pyyaml()
        cfg_path = override if override else (paths.default_agent_dir/"agent.yaml")
        if yaml and cfg_path.exists():
            try:
                data = yaml.safe_load(read_text(cfg_path)) or {}
                return cls(
                    name=data.get("name", "default"),
                    provider=data.get("llm", {}).get("provider", "ollama"),
                    model=data.get("llm", {}).get("model", "gpt-oss:20b"),
                    endpoint=data.get("llm", {}).get("endpoint", "http://127.0.0.1:11434"),
                    api_key_env=data.get("llm", {}).get("api_key_env", "OPENAI_API_KEY"),
                    safety_write_outside_repo=bool(data.get("safety", {}).get("write_outside_repo", False)),
                    require_command_allow=bool(data.get("safety", {}).get("require_command_allow", True)),
                    macros_retention_hours=int(data.get("retention", {}).get("macros_hours", 24)),
                    try_harder_prompt=data.get("prompts", {}).get("try_harder", cls.try_harder_prompt),
                )
            except Exception as e:
                print(f"[warn] Failed to parse {cfg_path}: {e}")
        return cls()

@dc.dataclass
class State:
    pending: List[Dict[str, Any]]
    allow_list: Dict[str, Dict[str, Any]]
    last_session_at: str

    @classmethod
    def load(cls, path: Path) -> "State":
        data = json_load(path, default={})
        return cls(
            pending=data.get("pending", []),
            allow_list=data.get("allow_list", {}),
            last_session_at=data.get("last_session_at", now_iso()),
        )

    def save(self, path: Path) -> None:
        json_dump(path, dataclasses.asdict(self))  # type: ignore

class LLMClient:
    def __init__(self, profile: AgentProfile):
        self.profile = profile

    def chat(self, messages: List[Dict[str, str]]) -> str:
        import urllib.request, urllib.error, json as _json
        # OpenAI-compatible
        try:
            url = self.profile.endpoint.rstrip("/") + "/v1/chat/completions"
            req = urllib.request.Request(
                url,
                data=_json.dumps({"model": self.profile.model, "messages": messages}).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.getenv(self.profile.api_key_env,'')}",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                payload = _json.loads(r.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"]
        except Exception:
            pass
        # Ollama native
        try:
            url = self.profile.endpoint.rstrip("/") + "/api/chat"
            req = urllib.request.Request(
                url,
                data=_json.dumps({"model": self.profile.model, "messages": messages, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                payload = _json.loads(r.read().decode("utf-8"))
                return payload.get("message", {}).get("content", "")
        except Exception as e:
            return f"[offline-mode] LLM unavailable ({e}). Safe placeholder."

TASK_RE = re.compile(r'^\s*-\s*\[\s*\]\s*(.+)$')

def parse_required_updates(text: str) -> List[Dict[str, Any]]:
    tasks = []
    section = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        m = TASK_RE.match(line)
        if m:
            body = m.group(1).strip()
            tasks.append({"section": section, "title": body, "raw": line})
    return tasks

class MacroManager:
    def __init__(self, paths: Paths, retention_h: int):
        self.paths = paths
        self.index_path = paths.macros_dir/"index.json"
        self.retention_h = retention_h
        self.index = json_load(self.index_path, default={"macros": {}, "last_cleanup": None})

    def touch(self, name: str) -> Path:
        p = self.paths.macros_dir/f"{name}.py"
        if not p.exists():
            write_text(p, f"# macro: {name}\n")
        self.index["macros"][name] = {"last_used_at": now_iso()}
        self.save()
        return p

    def save(self):
        json_dump(self.index_path, self.index)

    def cleanup(self, last_session_at_iso: str):
        try:
            last_session = dt.datetime.fromisoformat(last_session_at_iso)
        except Exception:
            last_session = dt.datetime.now(dt.timezone.utc).astimezone()
        now = dt.datetime.now(dt.timezone.utc).astimezone()
        idle = (now - last_session).total_seconds() > 3600  # treat >1h as idle gap proxy
        if idle:
            return  # don't purge if app wasn't used
        removed = []
        for name, meta in list(self.index.get("macros", {}).items()):
            try:
                t = dt.datetime.fromisoformat(meta.get("last_used_at"))
            except Exception:
                t = now
            if (now - t).total_seconds() > self.retention_h * 3600:
                (self.paths.macros_dir/f"{name}.py").unlink(missing_ok=True)
                removed.append(name)
                self.index["macros"].pop(name, None)
        if removed:
            append_md(self.paths.quarantined_updates, f"- [{now_iso()}] Macro cleanup removed: {', '.join(removed)}")
            self.save()

class Planner:
    def __init__(self, paths: Paths, profile: AgentProfile, llm: LLMClient):
        self.paths = paths; self.profile = profile; self.llm = llm

    def plan(self) -> List[Dict[str, Any]]:
        text = read_text(self.paths.required_updates)
        tasks = parse_required_updates(text)
        if not tasks:
            append_md(self.paths.missing_updates, f"- [{now_iso()}] No parseable tasks in Required-Updates.md")
        proposals = []
        for t in tasks:
            title = t["title"]
            why = f"From Required-Updates section={t['section'] or 'root'}"
            action = f"implement: {title}"
            h = sha1(action + "|" + why)
            proposals.append({"action": action, "why": why, "files": [], "risk_tag": "low", "effort": 1, "hash": h})
        return proposals

class Executor:
    def __init__(self, paths: Paths, profile: AgentProfile):
        self.paths = paths; self.profile = profile

    def _safe_write(self, path: Path, content: str):
        if not self.profile.safety_write_outside_repo and not str(path.resolve()).startswith(str(self.paths.root.resolve())):
            raise RuntimeError(f"Refusing to write outside repo: {path}")
        write_text(path, content)

    def run(self, cmd: Dict[str, Any]) -> Tuple[bool, str]:
        action = cmd.get("action","")
        m = re.search(r"create file ([\\w./\\\\-]+)", action, flags=re.IGNORECASE)
        if m:
            target = (self.paths.root / m.group(1)).resolve()
            self._safe_write(target, f"# created by agent at {now_iso()}\n")
            return True, f"created {target}"
        return False, "no-op (executor requires richer mappings)"

@dc.dataclass
class PendingResult:
    ok: bool
    note: str

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ask","plan","do"], default="ask")
    ap.add_argument("--agent", type=str, default="")
    ap.add_argument("--auto-allow", type=str, default="false")
    ap.add_argument("--prompt", type=str, default="")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--effort", type=int, default=1)
    args = ap.parse_args(argv)

    root = Path.cwd()
    paths = Paths.from_root(root)
    profile = AgentProfile.load(paths, Path(args.agent) if args.agent else None)
    if args.strict:
        profile.safety_write_outside_repo = False

    state = State.load(paths.runtime_state)
    # touch session
    state.last_session_at = now_iso()
    state.save(paths.runtime_state)

    llm = LLMClient(profile)
    planner = Planner(paths, profile, llm)
    executor = Executor(paths, profile)
    macros = MacroManager(paths, profile.macros_retention_hours)

    auto_allow = str(args.auto_allow).lower() in ("1","true","yes","on")

    def enqueue(proposals: List[Dict[str, Any]]):
        for p in proposals:
            if "hash" not in p or not p["hash"]:
                p["hash"] = sha1(json.dumps(p, sort_keys=True))
            state.pending.append(p)
        state.save(paths.runtime_state)

    def approve(item: Dict[str,Any]) -> bool:
        h = item.get("hash") or ""
        if h in state.allow_list:
            return True
        return auto_allow and not profile.require_command_allow

    def run_once():
        # macro retention
        macros.cleanup(state.last_session_at)

        if args.mode == "ask":
            prompt = args.prompt or "Summarize current repo state and next steps."
            reply = llm.chat([{"role":"user","content":prompt}])
            append_md(paths.chat_history, f"### [{now_iso()}] Ask\n\n{reply}\n")
            print(reply)

        elif args.mode == "plan":
            props = planner.plan()
            enqueue(props)
            append_md(paths.quarantined_updates, f"- [{now_iso()}] Staged {len(props)} proposals for approval.")

        elif args.mode == "do":
            remaining = []
            for item in list(state.pending):
                if approve(item):
                    ok, note = executor.run(item)
                    stamp = now_iso()
                    if ok:
                        append_md(paths.implemented_updates, f"- [{stamp}] OK: {item.get('action')} -> {note}")
                    else:
                        append_md(paths.quarantined_updates, f"- [{stamp}] NO-OP: {item.get('action')} -> {note}")
                else:
                    remaining.append(item)
            state.pending = remaining
            state.save(paths.runtime_state)

    if args.watch:
        print("[watch] Monitoring Required-Updates.md. Ctrl+C to exit.")
        last = read_text(paths.required_updates)
        try:
            while True:
                cur = read_text(paths.required_updates)
                if cur != last:
                    last = cur
                    argv2 = dict(vars(args)); argv2["mode"]="plan"; argv2["watch"]=False
                    run_once()
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
    else:
        run_once()

if __name__ == "__main__":
    main()
