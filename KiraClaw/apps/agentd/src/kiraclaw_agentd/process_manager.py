from __future__ import annotations

import os
import signal
import subprocess
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TextIO
from uuid import uuid4

from krim_sdk.safety import Action, check_command
from krim_sdk.truncate import truncate


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_stream_chunk(stream_name: str, text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    if not cleaned:
        return ""

    if stream_name == "stderr":
        lines = cleaned.splitlines(keepends=True)
        return "".join(f"[stderr] {line}" for line in lines)
    return cleaned


@dataclass
class ProcessSession:
    session_id: str
    command: str
    cwd: str
    owner_session_id: str
    process: subprocess.Popen[str]
    started_at: str
    status: str = "running"
    finished_at: str | None = None
    exit_code: int | None = None
    kill_requested: bool = False
    output_chunks: deque[str] = field(default_factory=deque)
    output_chars: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    reader_threads: list[threading.Thread] = field(default_factory=list)

    @property
    def pid(self) -> int | None:
        return getattr(self.process, "pid", None)

    def append_output(self, text: str, *, max_chars: int) -> None:
        if not text:
            return

        with self.lock:
            self.output_chunks.append(text)
            self.output_chars += len(text)
            while self.output_chars > max_chars and self.output_chunks:
                removed = self.output_chunks.popleft()
                self.output_chars -= len(removed)

    def output_text(self) -> str:
        with self.lock:
            return "".join(self.output_chunks)


class BackgroundProcessManager:
    def __init__(
        self,
        *,
        workspace_dir: Path,
        deny_patterns: list[str],
        allow_commands: list[str],
        ask_by_default: bool,
        max_output_chars: int,
        log_buffer_chars: int | None = None,
        observer: Callable[[str, dict[str, object]], None] | None = None,
    ) -> None:
        self._workspace_dir = Path(workspace_dir)
        self._deny_patterns = list(deny_patterns)
        self._allow_commands = list(allow_commands)
        self._ask_by_default = ask_by_default
        self._max_output_chars = max(1, int(max_output_chars))
        self._log_buffer_chars = max(log_buffer_chars or (self._max_output_chars * 4), self._max_output_chars)
        self._sessions: dict[str, ProcessSession] = {}
        self._lock = threading.Lock()
        self._observer = observer

    def start(
        self,
        *,
        command: str,
        cwd: str | None = None,
        owner_session_id: str | None = None,
    ) -> ProcessSession:
        cleaned = str(command or "").strip()
        if not cleaned:
            raise ValueError("empty_command")

        action = check_command(
            cleaned,
            self._deny_patterns,
            self._allow_commands,
            self._ask_by_default,
        )
        if action == Action.DENY:
            raise ValueError(f"command denied by safety rules: {cleaned}")
        if action == Action.ASK:
            raise ValueError("command requires approval but no ask_callback configured")

        resolved_cwd = self._resolve_cwd(cwd)
        session_id = f"proc_{uuid4().hex[:12]}"
        popen_kwargs: dict[str, object] = {
            "shell": True,
            "cwd": str(resolved_cwd),
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 1,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(cleaned, **popen_kwargs)
        session = ProcessSession(
            session_id=session_id,
            command=cleaned,
            cwd=str(resolved_cwd),
            owner_session_id=str(owner_session_id or "").strip(),
            process=process,
            started_at=_timestamp(),
        )

        with self._lock:
            self._sessions[session_id] = session

        self._start_stream_reader(session_id, process.stdout, "stdout")
        self._start_stream_reader(session_id, process.stderr, "stderr")
        self._notify("started", session)
        return session

    def wait_briefly(self, session_id: str, yield_ms: int) -> bool:
        session = self._get_session(session_id)
        timeout_seconds = max(0, int(yield_ms)) / 1000
        if timeout_seconds <= 0:
            self._refresh_status(session)
            return session.status != "running"

        try:
            session.process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            self._refresh_status(session)
            return False

        self._refresh_status(session)
        return session.status != "running"

    def list_sessions(
        self,
        *,
        tail_chars: int | None = None,
        owner_session_id: str | None = None,
    ) -> list[dict[str, object]]:
        with self._lock:
            sessions = list(self._sessions.values())

        owner = str(owner_session_id or "").strip()
        if owner:
            sessions = [session for session in sessions if session.owner_session_id == owner]

        rows = [
            self._snapshot(self._refresh_status(session), tail_chars=tail_chars or min(self._max_output_chars, 4_000))
            for session in sessions
        ]
        rows.sort(key=lambda row: str(row.get("started_at") or ""), reverse=True)
        return rows

    def poll(
        self,
        session_id: str,
        *,
        tail_chars: int | None = None,
        owner_session_id: str | None = None,
    ) -> dict[str, object]:
        session = self._refresh_status(self._get_session(session_id, owner_session_id=owner_session_id))
        return self._snapshot(session, tail_chars=tail_chars or self._max_output_chars)

    def log(
        self,
        session_id: str,
        *,
        tail_chars: int | None = None,
        owner_session_id: str | None = None,
    ) -> dict[str, object]:
        session = self._refresh_status(self._get_session(session_id, owner_session_id=owner_session_id))
        return self._snapshot(session, tail_chars=tail_chars or self._max_output_chars)

    def kill(self, session_id: str, *, owner_session_id: str | None = None) -> dict[str, object]:
        session = self._get_session(session_id, owner_session_id=owner_session_id)
        session.kill_requested = True
        if session.process.poll() is None:
            self._terminate_process(session.process)
        session = self._refresh_status(session)
        return self._snapshot(session, tail_chars=self._max_output_chars)

    def clear(self, session_id: str, *, owner_session_id: str | None = None) -> None:
        session = self._refresh_status(self._get_session(session_id, owner_session_id=owner_session_id))
        if session.status == "running":
            raise ValueError("cannot_clear_running_process")
        snapshot = self._snapshot(session, tail_chars=self._max_output_chars)
        with self._lock:
            self._sessions.pop(session_id, None)
        self._notify("cleared", session, snapshot=snapshot)

    def stop_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())

        for session in sessions:
            if session.process.poll() is None:
                session.kill_requested = True
                self._terminate_process(session.process)
            self._refresh_status(session)

    def _notify(
        self,
        action: str,
        session: ProcessSession,
        *,
        snapshot: dict[str, object] | None = None,
    ) -> None:
        if self._observer is None:
            return
        try:
            self._observer(action, snapshot or self._snapshot(session, tail_chars=self._max_output_chars))
        except Exception:
            pass

    def _resolve_cwd(self, cwd: str | None) -> Path:
        if not cwd:
            return self._workspace_dir

        candidate = Path(str(cwd).strip()).expanduser()
        if not candidate.is_absolute():
            candidate = self._workspace_dir / candidate
        resolved = candidate.resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise ValueError(f"invalid_cwd: {resolved}")
        return resolved

    def _get_session(self, session_id: str, *, owner_session_id: str | None = None) -> ProcessSession:
        key = str(session_id or "").strip()
        if not key:
            raise KeyError("missing_session_id")
        with self._lock:
            session = self._sessions.get(key)
        if session is None:
            raise KeyError(f"unknown_session_id: {key}")
        owner = str(owner_session_id or "").strip()
        if owner and session.owner_session_id != owner:
            raise KeyError(f"unknown_session_id: {key}")
        return session

    def _start_stream_reader(self, session_id: str, stream: TextIO | None, stream_name: str) -> None:
        if stream is None:
            return

        def _reader() -> None:
            try:
                for chunk in iter(stream.readline, ""):
                    formatted = _format_stream_chunk(stream_name, chunk)
                    session = self._sessions.get(session_id)
                    if session is None:
                        break
                    session.append_output(formatted, max_chars=self._log_buffer_chars)
            finally:
                stream.close()

        thread = threading.Thread(target=_reader, daemon=True)
        session = self._sessions.get(session_id)
        if session is not None:
            session.reader_threads.append(thread)
        thread.start()

    def _refresh_status(self, session: ProcessSession) -> ProcessSession:
        return_code = session.process.poll()
        if return_code is None:
            session.status = "running"
            return session

        newly_finished = session.finished_at is None
        if session.finished_at is None:
            for thread in session.reader_threads:
                thread.join(timeout=0.05)
            session.exit_code = int(return_code)
            session.finished_at = _timestamp()
            if session.kill_requested:
                session.status = "killed"
            elif return_code == 0:
                session.status = "completed"
            else:
                session.status = "failed"
        if newly_finished:
            self._notify("finished", session)
        return session

    def _snapshot(self, session: ProcessSession, *, tail_chars: int) -> dict[str, object]:
        output = session.output_text()
        if tail_chars > 0:
            output = output[-tail_chars:]
        output = truncate(output.strip() or "(no output)", self._max_output_chars)
        return {
            "session_id": session.session_id,
            "owner_session_id": session.owner_session_id,
            "command": session.command,
            "cwd": session.cwd,
            "pid": session.pid,
            "status": session.status,
            "started_at": session.started_at,
            "finished_at": session.finished_at,
            "exit_code": session.exit_code,
            "output": output,
        }

    def _terminate_process(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return

        try:
            if os.name == "nt":
                process.kill()
                process.wait(timeout=2)
                return

            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=2)
        except Exception:
            try:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait(timeout=2)
            except Exception:
                pass
