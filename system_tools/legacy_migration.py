"""Legacy project migration assistant for Required-Updates.md §135."""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_MIGRATE_DIR = Path(os.environ.get("CODEX_MIGRATE_DIR", ".codex_local_agent/migrate_legacy")).expanduser()


@dataclass
class MigrationOutcome:
    """Summary of one migration pass."""

    source: Path
    destination: Path
    copied: List[str]
    skipped: List[str]
    overwritten: List[str]
    timestamp: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "source": str(self.source),
            "destination": str(self.destination),
            "copied": self.copied,
            "skipped": self.skipped,
            "overwritten": self.overwritten,
            "timestamp": self.timestamp,
        }


class LegacyMigrationAssistant:
    """Copy artifacts from legacy agent trees into the new layout."""

    def __init__(self, base_dir: Path = DEFAULT_MIGRATE_DIR):
        self.base_dir = base_dir.expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.mappings_path = self.base_dir / "mappings.json"
        self.runs_path = self.base_dir / "runs.jsonl"
        self.audit_path = self.base_dir / "audit_migrate_legacy.jsonl"
        self.mappings_path.touch(exist_ok=True)
        self.runs_path.touch(exist_ok=True)
        self.audit_path.touch(exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_mappings(self) -> List[Dict[str, str]]:
        if not self.mappings_path.exists():
            return []
        raw = self.mappings_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        return data.get("mappings", [])

    def migrate(
        self,
        source_root: Path,
        dest_root: Path,
        *,
        overwrite: bool = False,
        selected_keys: Optional[Iterable[str]] = None,
    ) -> MigrationOutcome:
        mappings = self.load_mappings()
        if not mappings:
            raise RuntimeError("No mappings defined in migrate_legacy/mappings.json")

        source_root = source_root.expanduser().resolve()
        dest_root = dest_root.expanduser().resolve()
        if not source_root.exists():
            raise FileNotFoundError(f"Legacy source path not found: {source_root}")

        allow = set(selected_keys or [])
        copied: List[str] = []
        skipped: List[str] = []
        overwritten: List[str] = []

        for entry in mappings:
            key = entry.get("source")
            if not key:
                continue
            if allow and key not in allow:
                continue
            src_path = source_root / key
            if not src_path.exists():
                skipped.append(key)
                continue
            target_rel = entry.get("target", key)
            target_type = entry.get("type", "file")
            dest_path = dest_root / target_rel

            if dest_path.exists():
                if not overwrite:
                    skipped.append(key)
                    continue
                overwritten.append(target_rel)
                if dest_path.is_dir() and target_type == "dir":
                    shutil.rmtree(dest_path)
                elif dest_path.is_file():
                    dest_path.unlink()

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if target_type == "dir":
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_path)
            copied.append(target_rel)

        outcome = MigrationOutcome(
            source=source_root,
            destination=dest_root,
            copied=copied,
            skipped=skipped,
            overwritten=overwritten,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._record(outcome)
        return outcome

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record(self, outcome: MigrationOutcome) -> None:
        payload = outcome.as_dict()
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")


__all__ = ["LegacyMigrationAssistant", "MigrationOutcome"]
