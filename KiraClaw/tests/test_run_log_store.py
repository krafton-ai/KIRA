from __future__ import annotations

from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.run_log_store import RunLogStore, build_run_log_entry
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import KiraClawSettings


def test_build_run_log_entry_keeps_internal_and_spoken_outputs_separate(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    record = RunRecord(
        run_id="run-1",
        session_id="telegram:-1:main",
        state="completed",
        prompt="Recent room messages:\n- Jiho: update?",
        created_at="2026-01-01T00:00:00Z",
        started_at="2026-01-01T00:00:01Z",
        finished_at="2026-01-01T00:00:02Z",
        result=RunResult(
            final_response="internal summary",
            streamed_text="",
            spoken_messages=["external reply"],
            tool_events=[
                {"phase": "start", "name": "read", "args": {}},
                {"phase": "end", "name": "read", "result": "ok"},
            ],
        ),
        metadata={"source": "telegram-group"},
    )

    row = build_run_log_entry(record)

    assert row["internal_summary"] == "internal summary"
    assert row["spoken_messages"] == ["external reply"]
    assert row["external_text"] == "external reply"
    assert row["tool_summary"] == "Used: read"
    assert row["silent_reason"] is None


def test_run_log_store_appends_and_tails_recent_entries(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    store = RunLogStore(settings)

    first = RunRecord(
        run_id="run-1",
        session_id="desktop:local",
        state="completed",
        prompt="hello",
        created_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:01Z",
        result=RunResult(final_response="internal one", streamed_text=""),
        metadata={"source": "api"},
    )
    second = RunRecord(
        run_id="run-2",
        session_id="slack:C1:main",
        state="completed",
        prompt="room prompt",
        created_at="2026-01-01T00:01:00Z",
        finished_at="2026-01-01T00:01:01Z",
        result=RunResult(final_response="internal two", streamed_text="", spoken_messages=["spoken two"]),
        metadata={"source": "slack-group"},
    )

    store.append(first)
    store.append(second)

    rows = store.tail(limit=2)
    assert [row["run_id"] for row in rows] == ["run-2", "run-1"]
    assert rows[1]["silent_reason"] == "no_speak"

    filtered = store.tail(limit=5, session_id="slack:C1:main")
    assert [row["run_id"] for row in filtered] == ["run-2"]
