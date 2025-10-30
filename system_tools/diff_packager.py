"""Diff packaging utilities for Required-Updates.md §134.

Provides :class:`DiffPackager` to bundle repository diffs, review notes,
attachments, and metadata into portable ZIP archives stored under
``.codex_local_agent/diff_pkg``. The module stays offline-first and logs
all activity into ``audit_diff_pkg.jsonl`` for auditing.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

DEFAULT_DIFF_PKG_DIR = Path(os.environ.get("CODEX_DIFFPKG_DIR", ".codex_local_agent/diff_pkg")).expanduser()


@dataclass
class BundleResult:
    """Represents one exported diff bundle."""

    label: str
    bundle_path: Path
    diff_bytes: int
    attachment_count: int
    notes_relpath: Optional[str]
    created_at: str

    def as_dict(self) -> dict:
        data = asdict(self)
        data["bundle_path"] = str(self.bundle_path)
        return data


class DiffPackager:
    """Create review bundles containing diffs, notes, and attachments."""

    def __init__(
        self,
        base_dir: Path = DEFAULT_DIFF_PKG_DIR,
        diff_provider: Optional[Callable[[], str]] = None,
    ) -> None:
        self.base_dir = base_dir.expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.bundles_dir = self.base_dir / "bundles"
        self.bundles_dir.mkdir(parents=True, exist_ok=True)
        self.audit_path = self.base_dir / "audit_diff_pkg.jsonl"
        self.audit_path.touch(exist_ok=True)
        self._diff_provider = diff_provider or self._default_diff_provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def export_bundle(
        self,
        label: str,
        *,
        include_status: bool = True,
        attachments: Optional[Iterable[Path]] = None,
        notes: Optional[str] = None,
        diff_text: Optional[str] = None,
    ) -> BundleResult:
        """
        Bundle the current git diff and optional attachments into a ZIP file.

        Args:
            label: Human readable name for the bundle. A slugged variant is used
                for filenames.
            include_status: If True, include ``git status --short`` output.
            attachments: Optional iterable of file paths to include inside an
                ``attachments/`` directory.
            notes: Optional markdown text with reviewer commentary.
            diff_text: Override diff text (mostly used for testing). When None we
                gather it from the diff provider.
        """

        safe_label = self._slugify(label)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        zip_name = f"{safe_label}-{timestamp}.zip"
        zip_path = self.bundles_dir / zip_name

        diff_body = diff_text if diff_text is not None else self._diff_provider()
        status_body = self._git_status() if include_status else ""

        notes_relpath: Optional[str] = None

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "README.md").write_text(
                self._build_readme(label=label, timestamp=timestamp),
                encoding="utf-8",
            )
            (tmp_root / "diff.patch").write_text(diff_body, encoding="utf-8")

            if notes:
                note_path = tmp_root / "comments.md"
                note_path.write_text(notes, encoding="utf-8")
                notes_relpath = "comments.md"

            if status_body:
                (tmp_root / "git_status.txt").write_text(status_body, encoding="utf-8")

            if attachments:
                attach_dir = tmp_root / "attachments"
                attach_dir.mkdir(parents=True, exist_ok=True)
                for src in attachments:
                    src_path = Path(src).expanduser().resolve()
                    if not src_path.exists():
                        raise FileNotFoundError(f"Attachment not found: {src_path}")
                    dest = attach_dir / src_path.name
                    if src_path.is_dir():
                        shutil.copytree(src_path, dest)
                    else:
                        shutil.copy2(src_path, dest)

            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for item in tmp_root.rglob("*"):
                    if item.is_file():
                        arcname = item.relative_to(tmp_root)
                        zf.write(item, arcname.as_posix())

        bundle = BundleResult(
            label=label,
            bundle_path=zip_path,
            diff_bytes=len(diff_body.encode("utf-8")),
            attachment_count=len(list(attachments or [])),
            notes_relpath=notes_relpath,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._append_audit(bundle, has_notes=bool(notes))
        return bundle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_diff_provider(self) -> str:
        try:
            proc = subprocess.run(
                ["git", "diff"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return proc.stdout
        except Exception:
            return ""

    def _git_status(self) -> str:
        try:
            proc = subprocess.run(
                ["git", "status", "--short"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return proc.stdout
        except Exception:
            return ""

    def _build_readme(self, *, label: str, timestamp: str) -> str:
        return (
            "# Diff Bundle\n\n"
            f"- Label: {label}\n"
            f"- Created: {timestamp}Z\n"
            "- Contents:\n"
            "  - diff.patch — git diff snapshot\n"
            "  - comments.md — reviewer notes (optional)\n"
            "  - git_status.txt — working tree summary (optional)\n"
            "  - attachments/ — screenshots or supplementary files\n\n"
            "High-contrast note: any rendered UI from these attachments must"
            " keep bright text on dark backgrounds for accessibility."
        )

    def _append_audit(self, bundle: BundleResult, *, has_notes: bool) -> None:
        entry = bundle.as_dict()
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["has_notes"] = has_notes
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    @staticmethod
    def _slugify(text: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip())
        return safe.strip("-") or "bundle"


__all__ = ["DiffPackager", "BundleResult"]
