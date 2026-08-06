#!/usr/bin/env python3
"""
PPT Master - Automatic Workflow Transcript

Internal runtime helper that records a project-scoped Python tool's command
envelope and material text outcomes in an existing project workflow log.

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import atexit
import json
import os
import sys
import threading
import time
import uuid
from collections import deque
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

WORKFLOW_LOG_RELATIVE_PATH = Path("validation/workflow.log")
PROJECT_PATH_ENV = "PPT_MASTER_PROJECT_PATH"
DISABLE_TRANSCRIPT_ENV = "PPT_MASTER_DISABLE_WORKFLOW_TRANSCRIPT"
_EXCLUDED_ENTRYPOINTS = {"workflow_log.py"}
_CRITICAL_MARKERS = ("[ERROR]", "[FAIL]")
_ALWAYS_RETAIN_MARKERS = (
    "[POSTFLIGHT]",
    "[PPTX]",
    "[REPORT]",
    "[Done]",
    "[OK] Done",
)
_SUMMARY_MARKER = "[SUMMARY]"
_SUMMARY_STOP_MARKERS = ("[TIP]",)
_WARNING_MARKERS = ("[WARN]", "[WARNING]")
_OK_MARKER = "[OK]"
_WARNING_SAMPLE_LIMIT = 4
_OK_SAMPLE_LIMIT = 1
_STDERR_SAMPLE_LIMIT = 8
_STDERR_TAIL_LIMIT = 4
_CRITICAL_CONTEXT_LIMIT = 4
_SUMMARY_CONTEXT_LIMIT = 12
_ACTIVE_TRANSCRIPT: _AutomaticTranscript | None = None


def _utc_timestamp() -> str:
    """Return a compact UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _candidate_directory(value: str) -> Path | None:
    """Resolve one CLI value to an existing directory candidate."""
    if not value or value.startswith("-") or "://" in value:
        return None
    try:
        raw_path = Path(value)
    except (OSError, ValueError):
        return None
    if not raw_path.exists() and raw_path.parent == Path("."):
        return None
    path = raw_path
    if not path.is_absolute():
        path = Path.cwd() / path
    while not path.exists() and path != path.parent:
        path = path.parent
    if path.is_file():
        path = path.parent
    return path.resolve()


def _find_project_root(argv: list[str]) -> Path | None:
    """Find the first ancestor that already owns a workflow log."""
    explicit_project = os.environ.get(PROJECT_PATH_ENV, "").strip()
    values = [explicit_project, *argv[1:], str(Path.cwd())]
    for value in values:
        directory = _candidate_directory(value)
        if directory is None:
            continue
        for candidate in (directory, *directory.parents):
            if (candidate / WORKFLOW_LOG_RELATIVE_PATH).is_file():
                return candidate
    return None


class _AutomaticTranscript:
    """Append a bounded command/outcome audit without changing the owning tool."""

    def __init__(
        self,
        handle: TextIO,
        original_stderr: TextIO,
        argv: list[str],
    ) -> None:
        self.handle = handle
        self.original_stderr = original_stderr
        self.argv = argv
        self.run_id = uuid.uuid4().hex[:12]
        self.started_clock = time.monotonic()
        self.pending = {"stdout": "", "stderr": ""}
        self.observed_lines = 0
        self.retained_lines = 0
        self.omitted_lines = 0
        self.warning_samples = 0
        self.ok_samples = 0
        self.stderr_samples = 0
        self.stderr_tail: deque[str] = deque(maxlen=_STDERR_TAIL_LIMIT)
        self.critical_context_remaining = 0
        self.summary_context_remaining = 0
        self.current_record_stream: str | None = None
        self.lock = threading.RLock()
        self.enabled = True

    def _disable(self, exc: OSError | UnicodeError | ValueError) -> None:
        """Stop transcript writes without changing tool execution."""
        self.enabled = False
        try:
            self.original_stderr.write(
                f"[WARN] Workflow audit recording stopped: {exc}\n"
            )
            self.original_stderr.flush()
        except (OSError, ValueError):
            pass

    def _write(self, text: str) -> None:
        """Append and flush one complete audit record."""
        if not self.enabled:
            return
        try:
            self.handle.write(text)
            self.handle.flush()
        except (OSError, UnicodeError, ValueError) as exc:
            self._disable(exc)

    def start(self) -> None:
        """Write the Python-command envelope."""
        self._write(
            f"\n=== {_utc_timestamp()} PYTHON run={self.run_id} ===\n"
            f"cwd: {Path.cwd()}\n"
            f"argv: {json.dumps(self.argv, ensure_ascii=False)}\n"
        )

    @staticmethod
    def _is_decoration(line: str) -> bool:
        """Return whether a non-empty line is only visual separator glyphs."""
        stripped = line.strip()
        return bool(stripped) and set(stripped) <= {"-", "=", "_"}

    def _should_retain(self, stream_name: str, line: str) -> bool:
        """Select a bounded set of explicit outcomes for the cold audit log."""
        stripped = line.strip()
        if not stripped or self._is_decoration(stripped):
            return False

        if _SUMMARY_MARKER in stripped:
            self.summary_context_remaining = _SUMMARY_CONTEXT_LIMIT
            return True
        if any(marker in stripped for marker in _SUMMARY_STOP_MARKERS):
            self.summary_context_remaining = 0
            return False
        if self.summary_context_remaining > 0:
            self.summary_context_remaining -= 1
            return True
        if any(marker in stripped for marker in _CRITICAL_MARKERS):
            self.critical_context_remaining = _CRITICAL_CONTEXT_LIMIT
            return True
        if self.critical_context_remaining > 0:
            self.critical_context_remaining -= 1
            return True
        if any(marker in stripped for marker in _ALWAYS_RETAIN_MARKERS):
            return True
        if any(marker in stripped for marker in _WARNING_MARKERS):
            if self.warning_samples < _WARNING_SAMPLE_LIMIT:
                self.warning_samples += 1
                return True
            return False
        if _OK_MARKER in stripped:
            if self.ok_samples < _OK_SAMPLE_LIMIT:
                self.ok_samples += 1
                return True
            return False
        if stream_name == "stderr" and self.stderr_samples < _STDERR_SAMPLE_LIMIT:
            self.stderr_samples += 1
            return True
        return False

    def _record_line(self, stream_name: str, line: str) -> None:
        """Record one material logical line or account for its omission."""
        if not line.strip():
            return
        self.observed_lines += 1
        if not self._should_retain(stream_name, line):
            self.omitted_lines += 1
            if stream_name == "stderr" and not self._is_decoration(line):
                self.stderr_tail.append(line)
            return
        if stream_name == "stderr":
            self.stderr_tail.clear()
        self.retained_lines += 1
        if self.current_record_stream != stream_name:
            self._write(f"{stream_name}:\n")
            self.current_record_stream = stream_name
        self._write(f"  {line}\n")

    def write_stream(self, stream_name: str, text: str) -> None:
        """Buffer fragments and write complete logical lines."""
        if not text or not self.enabled:
            return
        with self.lock:
            pending = self.pending[stream_name] + text
            while "\n" in pending:
                line, pending = pending.split("\n", 1)
                self._record_line(stream_name, line)
            self.pending[stream_name] = pending

    def flush_stream(self, stream_name: str) -> None:
        """Flush a partial logical line when the owning stream flushes."""
        with self.lock:
            if not self.enabled:
                self.pending[stream_name] = ""
                return
            pending = self.pending[stream_name]
            if pending:
                self._record_line(stream_name, pending)
                self.pending[stream_name] = ""

    def close(self) -> None:
        """Flush pending output and close the command envelope."""
        with self.lock:
            if not self.enabled:
                return
            self.flush_stream("stdout")
            self.flush_stream("stderr")
            if self.stderr_tail:
                self._write("stderr-tail:\n")
                for line in self.stderr_tail:
                    self._write(f"  {line}\n")
                self.retained_lines += len(self.stderr_tail)
                self.omitted_lines -= len(self.stderr_tail)
            elapsed_ms = int((time.monotonic() - self.started_clock) * 1000)
            self._write(
                f"=== {_utc_timestamp()} END run={self.run_id} "
                f"elapsed_ms={elapsed_ms} output_lines={self.observed_lines} "
                f"retained={self.retained_lines} omitted={self.omitted_lines} ===\n"
            )
            self.enabled = False
            try:
                self.handle.close()
            except (OSError, ValueError) as exc:
                self._disable(exc)


class _TeeTextIO:
    """Forward text writes while offering them to the audit recorder."""

    def __init__(
        self,
        primary: TextIO,
        transcript: _AutomaticTranscript,
        stream_name: str,
    ) -> None:
        self.primary = primary
        self.transcript = transcript
        self.stream_name = stream_name
        self.lock = threading.RLock()

    def write(self, text: str) -> int:
        """Write to the original stream, then mirror the same text."""
        with self.lock:
            written = self.primary.write(text)
            self.transcript.write_stream(self.stream_name, text)
        return written

    def writelines(self, lines: Iterable[str]) -> None:
        """Forward a sequence through the ordinary write path."""
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        """Flush the original stream without splitting a logical log line."""
        with self.lock:
            self.primary.flush()

    def __getattr__(self, name: str) -> object:
        """Delegate the remaining text-stream interface."""
        return getattr(self.primary, name)


def install_auto_transcript(argv: list[str] | None = None) -> Path | None:
    """Record a project-scoped Python command when its project log exists."""
    global _ACTIVE_TRANSCRIPT

    effective_argv = list(sys.argv if argv is None else argv)
    if _ACTIVE_TRANSCRIPT is not None:
        return None
    if os.environ.get(DISABLE_TRANSCRIPT_ENV):
        return None
    if Path(effective_argv[0]).name in _EXCLUDED_ENTRYPOINTS:
        return None

    project_root = _find_project_root(effective_argv)
    if project_root is None:
        return None
    log_path = project_root / WORKFLOW_LOG_RELATIVE_PATH
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    try:
        handle = log_path.open(
            "a",
            encoding="utf-8",
            errors="replace",
            newline="",
        )
    except OSError as exc:
        try:
            original_stderr.write(
                f"[WARN] Workflow audit unavailable ({log_path}): {exc}\n"
            )
            original_stderr.flush()
        except (OSError, ValueError):
            pass
        return None

    transcript = _AutomaticTranscript(
        handle,
        original_stderr,
        [sys.executable, *effective_argv],
    )
    transcript.start()
    _ACTIVE_TRANSCRIPT = transcript
    sys.stdout = _TeeTextIO(original_stdout, transcript, "stdout")
    sys.stderr = _TeeTextIO(original_stderr, transcript, "stderr")
    atexit.register(transcript.close)
    return log_path
