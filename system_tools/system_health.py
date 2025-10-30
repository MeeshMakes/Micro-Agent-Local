"""System health dashboard utilities for Required-Updates.md §136."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_HEALTH_DIR = Path(os.environ.get("CODEX_HEALTH_DIR", ".codex_local_agent/health")).expanduser()


@dataclass
class HealthCard:
    """Represent one card in the dashboard."""

    key: str
    title: str
    status: str  # green / yellow / red
    summary: str
    details: Dict[str, object]

    def as_dict(self) -> Dict[str, object]:
        data = asdict(self)
        return data


class SystemHealthMonitor:
    """Collect health metrics for the local agent."""

    def __init__(self, base_dir: Path = DEFAULT_HEALTH_DIR):
        self.base_dir = base_dir.expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cards_path = self.base_dir / "cards.json"
        self.audit_path = self.base_dir / "audit_health.jsonl"
        self.cards_path.touch(exist_ok=True)
        self.audit_path.touch(exist_ok=True)

    def collect(
        self,
        repo_root: Optional[Path],
        *,
        task_statuses: Optional[Iterable[str]] = None,
        pending_command: bool = False,
    ) -> List[HealthCard]:
        repo_root = repo_root.resolve() if repo_root else Path.cwd()
        cards: List[HealthCard] = []
        cards.append(self._models_card(repo_root))
        cards.append(self._queue_card(task_statuses or []))
        cards.append(self._storage_card(repo_root))
        cards.append(self._errors_card(task_statuses or [], pending_command))
        cards.append(self._integrity_card(repo_root))
        cards.append(self._power_card())
        return cards

    def persist(self, cards: List[HealthCard]) -> None:
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "cards": [card.as_dict() for card in cards],
        }
        self.cards_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")

    # ------------------------------------------------------------------
    # Card builders
    # ------------------------------------------------------------------
    def _models_card(self, repo_root: Path) -> HealthCard:
        agent_yaml = repo_root / ".codex_local_agent" / "agent.yaml"
        if agent_yaml.exists():
            status = "green"
            summary = "agent.yaml present; offline model configured"
        else:
            status = "yellow"
            summary = "agent.yaml missing; using defaults"
        return HealthCard(
            key="models",
            title="Models",
            status=status,
            summary=summary,
            details={"agent_yaml": str(agent_yaml)},
        )

    def _queue_card(self, statuses: Iterable[str]) -> HealthCard:
        pending = sum(1 for s in statuses if s == "pending")
        running = sum(1 for s in statuses if s == "running")
        errors = sum(1 for s in statuses if s == "error")
        status = "green"
        if pending or running:
            status = "yellow"
        if errors:
            status = "red"
        summary = f"{pending} pending / {running} running / {errors} error"
        return HealthCard(
            key="queue",
            title="Queue",
            status=status,
            summary=summary,
            details={"counts": {"pending": pending, "running": running, "error": errors}},
        )

    def _storage_card(self, repo_root: Path) -> HealthCard:
        agent_dir = repo_root / ".codex_local_agent"
        size_bytes = self._dir_size(agent_dir) if agent_dir.exists() else 0
        status = "green" if size_bytes < 5 * 1024 * 1024 else "yellow"
        summary = f"{size_bytes/1024:.1f} KiB used"
        return HealthCard(
            key="storage",
            title="Storage",
            status=status,
            summary=summary,
            details={"bytes": size_bytes},
        )

    def _errors_card(self, statuses: Iterable[str], pending_command: bool) -> HealthCard:
        errors = sum(1 for s in statuses if s == "error")
        status = "green"
        notes: List[str] = []
        if errors:
            status = "red"
            notes.append(f"{errors} tasks failed")
        if pending_command:
            status = "yellow" if status != "red" else status
            notes.append("Pending command awaiting approval")
        summary = "; ".join(notes) if notes else "No active errors"
        return HealthCard(
            key="errors",
            title="Errors",
            status=status,
            summary=summary,
            details={"task_errors": errors, "pending_command": pending_command},
        )

    def _integrity_card(self, repo_root: Path) -> HealthCard:
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(repo_root),
                check=True,
            )
            dirty = bool(proc.stdout.strip())
        except Exception:
            dirty = True
        status = "green" if not dirty else "yellow"
        summary = "Working tree clean" if not dirty else "Uncommitted changes present"
        return HealthCard(
            key="integrity",
            title="Integrity",
            status=status,
            summary=summary,
            details={"dirty": dirty},
        )

    def _power_card(self) -> HealthCard:
        return HealthCard(
            key="power",
            title="Power",
            status="yellow",
            summary="Power telemetry unavailable; assume stable desktop",
            details={"telemetry": "unavailable"},
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _dir_size(self, path: Path) -> int:
        total = 0
        for root, dirs, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except FileNotFoundError:
                    continue
        return total


__all__ = ["SystemHealthMonitor", "HealthCard"]
