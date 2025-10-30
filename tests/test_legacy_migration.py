import json
from pathlib import Path

from system_tools.legacy_migration import LegacyMigrationAssistant


def test_legacy_migration_copies_files(tmp_path):
    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    (legacy_root / "agent.yaml").write_text("model: legacy", encoding="utf-8")

    dest_root = tmp_path / "dest"
    dest_root.mkdir()

    assistant = LegacyMigrationAssistant(base_dir=tmp_path / "migrate")
    assistant.mappings_path.write_text(
        json.dumps(
            {
                "mappings": [
                    {"source": "agent.yaml", "target": "new_agent/agent.yaml", "type": "file"}
                ]
            }
        ),
        encoding="utf-8",
    )

    outcome = assistant.migrate(legacy_root, dest_root)

    copied_file = dest_root / "new_agent" / "agent.yaml"
    assert copied_file.exists()
    assert copied_file.read_text(encoding="utf-8").startswith("model: legacy")
    assert "new_agent/agent.yaml" in outcome.copied

    audit_lines = assistant.audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert audit_lines
    payload = json.loads(audit_lines[-1])
    assert payload["copied"] == ["new_agent/agent.yaml"]
