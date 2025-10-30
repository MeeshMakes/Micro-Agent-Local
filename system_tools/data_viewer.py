"""Data Viewer utilities for the local agent.

Implements the storage and data-loading layer for Required-Updates.md §133
(DataFrame Viewer & CSV Toolkit). Provides:

* :class:`DataViewManager` — load/filter/sample/export tables.
* :func:`table_to_markdown` — CLI preview rendering with high contrast text when
  printed to the console (white text on dark backgrounds).
* :func:`iter_rows_as_json` — stream rows as JSON for downstream tooling.

All artifacts are stored under ``.codex_local_agent/data_view`` keeping the
system offline-first and auditable.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

DATA_VIEW_DIR = Path(os.environ.get("CODEX_DATA_VIEW_DIR", ".codex_local_agent/data_view")).expanduser()

@dataclass
class DataTable:
    """Container for tabular data loaded by :class:`DataViewManager`."""

    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    source: str

    def as_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["row_count"] = data.pop("total_rows")
        return data


class DataViewManager:
    """Load, filter, and export tabular data with offline-friendly code."""

    def __init__(self, base_dir: Path = DATA_VIEW_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.recent_path = self.base_dir / "recent.json"
        self.presets_path = self.base_dir / "presets.json"
        self.audit_path = self.base_dir / "audit_data_view.jsonl"
        self._ensure_json(self.recent_path, {"files": []})
        self._ensure_json(self.presets_path, {"presets": []})
        self.audit_path.touch(exist_ok=True)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def load_table(
        self,
        file_path: Path,
        limit: Optional[int] = None,
        sample: Optional[int] = None,
        delimiter: Optional[str] = None,
        filter_text: str = "",
        filter_column: Optional[str] = None,
    ) -> DataTable:
        """
        Load a table from ``file_path``.

        Args:
            file_path: Target file (CSV/TSV/Parquet).
            limit: Optional cap on rows read (before sampling/filter).
            sample: Optional random sample size applied after filter.
            delimiter: Override CSV delimiter. None triggers auto sniff.
            filter_text: Case-insensitive substring filter applied to the
                stringified row (or the specified column).
            filter_column: If provided, limit filtering to this column.
        """

        file_path = file_path.expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            table = self._load_csv(file_path, delimiter, limit)
        elif suffix in {".parquet", ".pq"}:
            table = self._load_parquet(file_path, limit)
        else:
            raise ValueError(
                "Unsupported file type. Expected CSV/TSV/Parquet: "
                f"{file_path.name}"
            )

        rows = table.rows
        if filter_text:
            rows = self._filter_rows(rows, filter_text, filter_column)
        if sample and sample > 0 and len(rows) > sample:
            rows = self._sample_rows(rows, sample)
        if limit and limit > 0 and len(rows) > limit:
            rows = rows[:limit]

        filtered_table = DataTable(
            columns=table.columns,
            rows=rows,
            total_rows=table.total_rows,
            source=str(file_path),
        )

        self._record_recent(file_path, filtered_table)
        self._write_audit(
            action="load",
            file_path=file_path,
            meta={
                "rows_read": len(rows),
                "filter": filter_text,
                "filter_column": filter_column,
                "sample": sample,
            },
        )
        return filtered_table

    def export_rows(
        self,
        rows: Sequence[Dict[str, Any]],
        columns: Sequence[str],
        destination: Path,
    ) -> None:
        """Export provided rows to ``destination`` (CSV)."""

        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(columns))
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in columns})

        self._write_audit(
            action="export",
            file_path=destination,
            meta={"rows": len(rows), "columns": len(columns)},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_csv(
        self, file_path: Path, delimiter: Optional[str], limit: Optional[int]
    ) -> DataTable:
        with file_path.open("r", newline="", encoding="utf-8") as fh:
            sample_text = fh.read(2048)
            fh.seek(0)
            if delimiter:
                use_delim = delimiter
            else:
                try:
                    use_delim = csv.Sniffer().sniff(sample_text).delimiter
                except Exception:
                    use_delim = ","
            reader = csv.reader(fh, delimiter=use_delim)
            try:
                headers = next(reader)
            except StopIteration:
                return DataTable(columns=[], rows=[], total_rows=0, source=str(file_path))

            rows: List[Dict[str, Any]] = []
            total = 0
            for row in reader:
                total += 1
                if limit and len(rows) >= limit:
                    # Count continues for total_rows but we stop storing.
                    continue
                row_dict = {
                    headers[i] if i < len(headers) else f"col_{i}": value
                    for i, value in enumerate(row)
                }
                rows.append(row_dict)
        return DataTable(columns=headers, rows=rows, total_rows=total, source=str(file_path))

    def _load_parquet(self, file_path: Path, limit: Optional[int]) -> DataTable:
        try:
            import pandas as pd  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Parquet support requires pandas. Install pandas to open Parquet files."
            ) from exc

        df = pd.read_parquet(file_path)
        total_rows = int(df.shape[0])
        if limit and limit > 0:
            df = df.head(limit)
        rows = [
            {
                col: (
                    ""
                    if value is None
                    or (isinstance(value, float) and math.isnan(value))
                    else value
                )
                for col, value in record.items()
            }
            for record in df.to_dict(orient="records")
        ]
        return DataTable(
            columns=list(df.columns),
            rows=rows,
            total_rows=total_rows,
            source=str(file_path),
        )

    def _filter_rows(
        self,
        rows: Sequence[Dict[str, Any]],
        filter_text: str,
        filter_column: Optional[str],
    ) -> List[Dict[str, Any]]:
        needle = filter_text.lower()
        filtered: List[Dict[str, Any]] = []
        for row in rows:
            if filter_column:
                value = str(row.get(filter_column, ""))
                if needle in value.lower():
                    filtered.append(row)
            else:
                hay = " ".join(str(v) for v in row.values()).lower()
                if needle in hay:
                    filtered.append(row)
        return filtered

    def _sample_rows(
        self, rows: Sequence[Dict[str, Any]], sample_size: int
    ) -> List[Dict[str, Any]]:
        if sample_size >= len(rows):
            return list(rows)
        indices = random.sample(range(len(rows)), sample_size)
        return [rows[i] for i in indices]

    def list_recent(self) -> List[Dict[str, Any]]:
        data = self._read_json(self.recent_path)
        entries = data.get("files", [])
        if not isinstance(entries, list):
            return []
        return entries

    def list_presets(self) -> List[Dict[str, Any]]:
        data = self._read_json(self.presets_path)
        presets = data.get("presets", [])
        if not isinstance(presets, list):
            return []
        return presets

    def _record_recent(self, file_path: Path, table: DataTable) -> None:
        data = self._read_json(self.recent_path)
        entries = data.get("files", [])
        new_entry = {
            "path": str(file_path),
            "timestamp": self._now_iso(),
            "columns": table.columns,
            "row_count": table.total_rows,
        }
        entries = [e for e in entries if e.get("path") != str(file_path)]
        entries.insert(0, new_entry)
        data["files"] = entries[:15]
        self.recent_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _write_audit(self, action: str, file_path: Path, meta: Dict[str, Any]) -> None:
        entry = {
            "timestamp": self._now_iso(),
            "action": action,
            "path": str(file_path),
            "meta": meta,
        }
        with self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    def _ensure_json(self, path: Path, default: Dict[str, Any]) -> None:
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")

    def _read_json(self, path: Path) -> Dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


def table_to_markdown(table: DataTable, max_rows: int = 20) -> str:
    """Render a table preview as markdown for CLI output."""

    rows = table.rows[:max_rows]
    if not rows:
        return "| (empty) |\n| --- |\n| No rows available |"

    columns = table.columns
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, separator]
    for row in rows:
        line = "| " + " | ".join(str(row.get(col, "")) for col in columns) + " |"
        lines.append(line)
    if table.total_rows > len(rows):
        lines.append(
            f"| ... | {table.total_rows - len(rows)} more rows not shown |"
        )
    return "\n".join(lines)


def iter_rows_as_json(table: DataTable) -> Iterable[str]:
    """Yield JSON lines for the supplied ``DataTable``."""

    yield json.dumps(
        {"type": "header", "columns": table.columns, "source": table.source}
    )
    for row in table.rows:
        yield json.dumps({"type": "row", "data": row})

