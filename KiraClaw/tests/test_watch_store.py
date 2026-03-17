from __future__ import annotations

from kiraclaw_agentd.watch_models import WatchRunRecord, WatchSpec, derive_watch_title
from kiraclaw_agentd.watch_store import (
    WatchStateStore,
    read_watches,
    validate_interval_minutes,
    write_watches,
)


def test_watch_store_round_trips_specs(tmp_path) -> None:
    watch_file = tmp_path / "watch_data" / "watches.json"
    spec = WatchSpec(
        interval_minutes=30,
        condition="If a blocked issue appears.",
        action="Send a Slack message.",
    )

    write_watches(watch_file, [spec])
    loaded = read_watches(watch_file)

    assert len(loaded) == 1
    assert loaded[0].watch_id == spec.watch_id
    assert loaded[0].condition == "If a blocked issue appears."


def test_watch_state_store_records_recent_runs(tmp_path) -> None:
    state_file = tmp_path / "watch_data" / "state.json"
    store = WatchStateStore(state_file, history_limit=2)

    store.record_run(
        WatchRunRecord(
            watch_id="watch-1",
            watch_name="Inbox watch",
            session_id="watch:watch-1",
            state="completed",
            summary="No action needed.",
        )
    )
    store.record_run(
        WatchRunRecord(
            watch_id="watch-1",
            watch_name="Inbox watch",
            session_id="watch:watch-1",
            state="completed",
            summary="Sent a message.",
        )
    )
    store.record_run(
        WatchRunRecord(
            watch_id="watch-2",
            watch_name="Calendar watch",
            session_id="watch:watch-2",
            state="completed",
            summary="Found a meeting change.",
        )
    )

    rows = store.list_runs(limit=10)

    assert [row.summary for row in rows] == [
        "Found a meeting change.",
        "Sent a message.",
    ]


def test_validate_interval_minutes_rejects_bad_input() -> None:
    assert validate_interval_minutes(30) is None
    assert validate_interval_minutes(0) is not None
    assert validate_interval_minutes(10_081) is not None


def test_watch_spec_requires_condition_and_action() -> None:
    try:
        WatchSpec(
            interval_minutes=30,
            condition="",
            action="",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("WatchSpec should reject blank required text fields")

    assert "Watch condition is required." in message


def test_derive_watch_title_falls_back_to_action() -> None:
    assert derive_watch_title("", "Send a concise Slack update.") == "Send a concise Slack update."
