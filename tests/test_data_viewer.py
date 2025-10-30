import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from system_tools.data_viewer import DataViewManager, iter_rows_as_json


def _make_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nAlice,30\nBob,25\nCara,22\n", encoding="utf-8")
    return csv_path


def test_load_and_recent(tmp_path: Path):
    base = tmp_path / "store"
    mgr = DataViewManager(base_dir=base)
    table = mgr.load_table(_make_csv(tmp_path))
    assert table.total_rows == 3
    assert table.rows[0]["name"] == "Alice"

    recent = mgr.list_recent()
    assert recent and Path(recent[0]["path"]).name == "people.csv"


def test_filter_and_sample(tmp_path: Path):
    base = tmp_path / "store"
    mgr = DataViewManager(base_dir=base)
    data = _make_csv(tmp_path)

    filtered = mgr.load_table(data, filter_text="Bob", filter_column="name")
    assert len(filtered.rows) == 1
    assert filtered.rows[0]["age"] == "25"

    sampled = mgr.load_table(data, sample=2)
    assert len(sampled.rows) == 2


def test_export_rows(tmp_path: Path):
    base = tmp_path / "store"
    mgr = DataViewManager(base_dir=base)
    table = mgr.load_table(_make_csv(tmp_path))

    dest = tmp_path / "filtered.csv"
    mgr.export_rows(table.rows[:2], table.columns, dest)
    content = dest.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "name,age"
    assert "Alice,30" in content


def test_iter_rows_as_json(tmp_path: Path):
    base = tmp_path / "store"
    mgr = DataViewManager(base_dir=base)
    table = mgr.load_table(_make_csv(tmp_path), limit=2)
    lines = list(iter_rows_as_json(table))
    header = json.loads(lines[0])
    assert header["type"] == "header"
    row = json.loads(lines[1])
    assert row["type"] == "row"


@pytest.mark.integration
def test_cli_pipeline(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = _make_csv(tmp_path)

    env = os.environ.copy()
    env["CODEX_DATA_VIEW_DIR"] = str(tmp_path / "cli_store")

    proc = subprocess.run(
        [sys.executable, str(repo_root / "agent"), "data", "view", str(csv_path)],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert proc.stdout.strip()

    proc_sample = subprocess.run(
        [sys.executable, str(repo_root / "sample"), "--n", "2", "--markdown"],
        input=proc.stdout,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert "| name |" in proc_sample.stdout
