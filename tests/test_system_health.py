import json

from system_tools.system_health import SystemHealthMonitor


def test_system_health_collects_and_persists(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    agent_dir = repo_root / ".codex_local_agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text("model: offline", encoding="utf-8")

    monitor = SystemHealthMonitor(base_dir=tmp_path / "health")

    cards = monitor.collect(
        repo_root,
        task_statuses=["pending", "error"],
        pending_command=True,
    )
    monitor.persist(cards)

    by_key = {card.key: card for card in cards}
    assert by_key["models"].status == "green"
    assert by_key["errors"].status in {"red", "yellow"}
    assert by_key["queue"].status == "red"

    saved = json.loads(monitor.cards_path.read_text(encoding="utf-8"))
    assert saved["cards"]
    assert saved["cards"][0]["title"]
