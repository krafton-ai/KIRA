from __future__ import annotations


def summarize_tool_events(tool_events: list[dict] | None) -> str:
    counts: dict[str, int] = {}
    for event in tool_events or []:
        if event.get("phase") != "start":
            continue
        name = str(event.get("name") or "").strip()
        if not name or name == "submit":
            continue
        counts[name] = counts.get(name, 0) + 1

    if not counts:
        return ""

    parts = [f"{name} x{count}" if count > 1 else name for name, count in counts.items()]
    return f"Used: {', '.join(parts)}"


def append_tool_summary(text: str, tool_events: list[dict] | None) -> str:
    summary = summarize_tool_events(tool_events)
    if not summary:
        return text

    base = str(text or "").rstrip()
    if not base:
        return summary
    return f"{base}\n\n{summary}"
