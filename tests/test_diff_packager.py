import json
import zipfile
from pathlib import Path

from system_tools.diff_packager import DiffPackager


def test_diff_packager_exports_bundle(tmp_path):
    base_dir = tmp_path / "diff_pkg"
    attachment_dir = tmp_path / "shots"
    attachment_dir.mkdir()
    screenshot = attachment_dir / "shot.txt"
    screenshot.write_text("demo", encoding="utf-8")

    packager = DiffPackager(base_dir=base_dir, diff_provider=lambda: "sample diff")
    bundle = packager.export_bundle(
        "Feature Patch",
        include_status=False,
        attachments=[screenshot],
        notes="All tests pass",
    )

    assert bundle.bundle_path.exists()
    with zipfile.ZipFile(bundle.bundle_path) as zf:
        members = set(zf.namelist())
        assert "README.md" in members
        assert "diff.patch" in members
        assert "comments.md" in members
        assert "attachments/shot.txt" in members
        assert zf.read("diff.patch").decode("utf-8") == "sample diff"
        assert zf.read("comments.md").decode("utf-8").strip() == "All tests pass"

    audit_entries = [
        json.loads(line)
        for line in packager.audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(entry["label"] == "Feature Patch" for entry in audit_entries)
