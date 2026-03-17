from __future__ import annotations

import asyncio

from kiraclaw_agentd.proactive_models import CheckerEvent
from kiraclaw_agentd.proactive_service import ProactiveService
from kiraclaw_agentd.settings import KiraClawSettings


def _make_settings(tmp_path, **overrides) -> KiraClawSettings:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        **overrides,
    )
    settings.ensure_directories()
    return settings


def test_proactive_service_records_queued_suggestion(tmp_path) -> None:
    settings = _make_settings(tmp_path)
    service = ProactiveService(settings)
    event = CheckerEvent(
        source="jira",
        title="Assigned issue updated",
        summary="PROJ-123 moved to In Review.",
        suggestion_text="I can summarize the review impact for PROJ-123.",
        dedupe_key="jira:PROJ-123",
    )

    service.enqueue_event(event)
    processed = asyncio.run(service.process_now())

    assert len(processed) == 1
    assert processed[0].state == "queued"
    assert service.list_suggestions(limit=5)[0].state == "queued"


def test_proactive_service_marks_duplicate_events(tmp_path) -> None:
    settings = _make_settings(tmp_path)
    service = ProactiveService(settings)

    first = CheckerEvent(
        source="jira",
        title="Assigned issue updated",
        summary="PROJ-123 moved to In Review.",
        suggestion_text="I can summarize the review impact for PROJ-123.",
        dedupe_key="jira:PROJ-123",
    )
    duplicate = CheckerEvent(
        source="jira",
        title="Assigned issue updated",
        summary="PROJ-123 moved to In Review.",
        suggestion_text="I can summarize the review impact for PROJ-123.",
        dedupe_key="jira:PROJ-123",
    )

    service.enqueue_event(first)
    asyncio.run(service.process_now())
    service.enqueue_event(duplicate)
    processed = asyncio.run(service.process_now())

    assert len(processed) == 1
    assert processed[0].state == "skipped_duplicate"
    suggestions = service.list_suggestions(limit=5)
    assert suggestions[0].state == "skipped_duplicate"
    assert suggestions[1].state == "queued"
