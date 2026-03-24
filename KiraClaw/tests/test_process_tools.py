from __future__ import annotations

import json
import sys
import time

from kiraclaw_agentd.process_manager import BackgroundProcessManager
from kiraclaw_agentd.process_tools import build_process_tools
from kiraclaw_agentd.settings import KiraClawSettings


def _python_command(code: str) -> str:
    escaped = code.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{sys.executable}" -c "{escaped}"'


def _build_manager(settings: KiraClawSettings) -> BackgroundProcessManager:
    return BackgroundProcessManager(
        workspace_dir=settings.workspace_dir,
        deny_patterns=settings.deny_patterns,
        allow_commands=settings.allow_commands,
        ask_by_default=settings.ask_by_default,
        max_output_chars=settings.max_output_chars,
    )


def _build_tools(settings: KiraClawSettings) -> dict[str, object]:
    manager = _build_manager(settings)
    tools = {
        tool.name: tool
        for tool in build_process_tools(
            settings,
            tool_context={
                "__process_manager__": manager,
                "session_id": "desktop:local",
            },
        )
    }
    return tools


def test_build_process_tools_requires_process_manager(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()

    assert build_process_tools(settings) == []
    tools = build_process_tools(
        settings,
        tool_context={"__process_manager__": _build_manager(settings), "session_id": "desktop:local"},
    )
    assert [tool.name for tool in tools] == ["exec", "process"]


def test_exec_tool_returns_completed_result_for_short_command(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    tools = _build_tools(settings)

    result = json.loads(tools["exec"].run(command=_python_command("print('done')"), yield_ms=500))

    assert result["success"] is True
    assert result["completed"] is True
    assert result["status"] == "completed"
    assert result["exit_code"] == 0
    assert "done" in result["output"]

    sessions = json.loads(tools["process"].run(action="list"))
    assert sessions["success"] is True
    assert sessions["sessions"] == []


def test_exec_tool_can_start_background_session_and_process_can_poll_log_and_clear(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    tools = _build_tools(settings)

    result = json.loads(
        tools["exec"].run(
            command=_python_command("import time; print('start'); time.sleep(0.3); print('end')"),
            yield_ms=10,
        )
    )

    assert result["success"] is True
    assert result["completed"] is False
    assert result["status"] == "running"
    session_id = result["session_id"]

    poll_running = json.loads(tools["process"].run(action="poll", session_id=session_id))
    assert poll_running["success"] is True
    assert poll_running["session"]["session_id"] == session_id

    time.sleep(0.45)

    log_result = json.loads(tools["process"].run(action="log", session_id=session_id))
    assert log_result["success"] is True
    assert log_result["session"]["status"] == "completed"
    assert log_result["session"]["exit_code"] == 0
    assert "start" in log_result["session"]["output"]
    assert "end" in log_result["session"]["output"]

    clear_result = json.loads(tools["process"].run(action="clear", session_id=session_id))
    assert clear_result == {
        "success": True,
        "action": "clear",
        "session_id": session_id,
    }


def test_exec_tool_resolves_relative_cwd_from_workspace(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    subdir = settings.workspace_dir / "nested"
    subdir.mkdir(parents=True, exist_ok=True)
    tools = _build_tools(settings)

    result = json.loads(
        tools["exec"].run(
            command=_python_command("from pathlib import Path; print(Path.cwd())"),
            cwd="nested",
            yield_ms=500,
        )
    )

    assert result["success"] is True
    assert result["completed"] is True
    assert str(subdir) in result["output"]


def test_exec_tool_applies_bash_safety_rules(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    tools = _build_tools(settings)

    result = json.loads(tools["exec"].run(command="rm -rf /", yield_ms=1))

    assert result["success"] is False
    assert "command denied by safety rules" in result["error"]


def test_process_manager_emits_started_and_finished_events(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    events: list[tuple[str, dict[str, object]]] = []
    manager = BackgroundProcessManager(
        workspace_dir=settings.workspace_dir,
        deny_patterns=settings.deny_patterns,
        allow_commands=settings.allow_commands,
        ask_by_default=settings.ask_by_default,
        max_output_chars=settings.max_output_chars,
        observer=lambda action, snapshot: events.append((action, snapshot)),
    )

    session = manager.start(
        command=_python_command("import time; print('hi'); time.sleep(0.1)"),
        owner_session_id="desktop:local",
    )
    manager.wait_briefly(session.session_id, 10)
    time.sleep(0.2)
    manager.poll(session.session_id)

    actions = [action for action, _snapshot in events]
    assert "started" in actions
    assert "finished" in actions


def test_process_tool_is_scoped_to_the_current_owner_session(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
    )
    settings.ensure_directories()
    manager = _build_manager(settings)

    tools_a = {
        tool.name: tool
        for tool in build_process_tools(
            settings,
            tool_context={
                "__process_manager__": manager,
                "session_id": "desktop:alpha",
            },
        )
    }
    tools_b = {
        tool.name: tool
        for tool in build_process_tools(
            settings,
            tool_context={
                "__process_manager__": manager,
                "session_id": "desktop:beta",
            },
        )
    }

    started = json.loads(
        tools_a["exec"].run(
            command=_python_command("import time; print('secret'); time.sleep(0.2)"),
            yield_ms=10,
        )
    )
    session_id = started["session_id"]

    listed = json.loads(tools_b["process"].run(action="list"))
    assert listed["success"] is True
    assert listed["sessions"] == []

    polled = json.loads(tools_b["process"].run(action="poll", session_id=session_id))
    assert polled["success"] is False
    assert "unknown_session_id" in polled["error"]
