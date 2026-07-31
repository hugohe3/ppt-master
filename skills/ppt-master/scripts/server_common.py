#!/usr/bin/env python3
"""
PPT Master - Local Preview Server Helpers

Shared per-project mutual-exclusion (lock) and liveness helpers for the local
Flask preview servers (`svg_editor/server.py`, `confirm_ui/server.py`). Each
server keeps its own lock filename and Flask app; this module owns only the
cross-platform process-liveness check and the claim/read/release lock logic so
the two servers cannot drift apart.

Usage:
    from server_common import find_free_port, validate_port

Dependencies:
    None (only uses standard library)
"""

import json
import logging
import os
import socket
import subprocess
from pathlib import Path
from typing import Optional


MIN_PORT = 1
MAX_PORT = 65535


def validate_port(port: int) -> int:
    """Return a valid TCP port, raising ``ValueError`` outside 1..65535."""
    if isinstance(port, bool) or not isinstance(port, int):
        raise ValueError('port must be an integer between 1 and 65535')
    if not MIN_PORT <= port <= MAX_PORT:
        raise ValueError(f'port must be between {MIN_PORT} and {MAX_PORT}: {port}')
    return port


def find_free_port(preferred: int, host: str = '127.0.0.1', span: int = 50) -> int:
    """Return the first bindable port from ``preferred`` through its scan span.

    The scan remains sequential so callers can keep 5050 as their preferred
    port and advance predictably when it is occupied. Invalid ports fail before
    probing, and an exhausted valid range raises ``RuntimeError`` instead of
    returning a port already known to be unavailable.
    """
    preferred = validate_port(preferred)
    if isinstance(span, bool) or not isinstance(span, int) or span <= 0:
        raise ValueError(f'span must be a positive integer: {span}')

    last_port = min(preferred + span - 1, MAX_PORT)
    for port in range(preferred, last_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(
        f'no free TCP port on {host} in range {preferred}..{last_port}'
    )


def popen_detached(
    args: list[str],
    *,
    logger: Optional[logging.Logger] = None,
    **kwargs: object,
) -> subprocess.Popen:
    """Start a long-running child process detached from the caller.

    Windows hosts such as terminal sandboxes may place child processes in the
    caller's Job Object. ``CREATE_BREAKAWAY_FROM_JOB`` lets the local UI server
    survive after the launcher command returns; when that flag is forbidden, the
    function falls back to the previous detached-process flags.
    """
    if os.name != 'nt':
        return subprocess.Popen(args, start_new_session=True, **kwargs)

    base_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    breakaway_flag = getattr(subprocess, 'CREATE_BREAKAWAY_FROM_JOB', 0x01000000)
    try:
        return subprocess.Popen(
            args,
            creationflags=base_flags | breakaway_flag,
            **kwargs,
        )
    except OSError as exc:
        if logger is not None:
            logger.warning(
                'Windows process breakaway failed; falling back to detached '
                'process-group launch (%s)',
                exc,
            )
        return subprocess.Popen(args, creationflags=base_flags, **kwargs)


def process_alive(pid: object) -> bool:
    """Return True if a process with this pid is reachable.

    On POSIX, ``os.kill(pid, 0)`` succeeds when the process exists even without
    permission to signal it; ``PermissionError`` therefore still counts as
    alive. On Windows there is no ``os.kill(pid, 0)`` equivalent, so probe via
    ``OpenProcess`` + ``WaitForSingleObject``.
    """
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        import ctypes.wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            ctypes.wintypes.DWORD,
            ctypes.wintypes.BOOL,
            ctypes.wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
        ]
        kernel32.WaitForSingleObject.restype = ctypes.wintypes.DWORD
        kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

        process_query_limited_information = 0x1000
        synchronize = 0x00100000
        wait_timeout = 0x00000102
        wait_object_0 = 0x00000000
        wait_failed = 0xFFFFFFFF

        handle = kernel32.OpenProcess(
            process_query_limited_information | synchronize,
            False,
            pid_int,
        )
        if not handle:
            return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED
        try:
            result = kernel32.WaitForSingleObject(handle, 0)
            if result == wait_timeout:
                return True
            if result in (wait_object_0, wait_failed):
                return False
            return False
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid_int, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_lock(lock_file: Path) -> Optional[dict]:
    """Read a lock file, returning the lock dict or None if absent/corrupt."""
    try:
        data = json.loads(lock_file.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def lock_pid(lock: Optional[dict]) -> int:
    """Return a valid pid from a lock dict, or 0 if absent/corrupt."""
    if not lock:
        return 0
    raw_pid = lock.get('pid', 0)
    if isinstance(raw_pid, bool):
        return 0
    if isinstance(raw_pid, int):
        return raw_pid if raw_pid > 0 else 0
    if isinstance(raw_pid, str) and raw_pid.strip().isdigit():
        return int(raw_pid.strip())
    return 0


def claim_lock(lock_file: Path, port: int) -> Optional[dict]:
    """Try to claim the per-project preview slot.

    Returns ``None`` on success. If another live process already holds the
    slot, returns the existing lock dict (caller surfaces it as an error).
    A stale lock (pointing at a dead pid) is silently overwritten.
    """
    existing = read_lock(lock_file)
    if existing and process_alive(lock_pid(existing)):
        return existing
    lock_file.write_text(
        json.dumps({'pid': os.getpid(), 'port': port}),
        encoding='utf-8',
    )
    return None


def release_lock(lock_file: Path) -> None:
    """Best-effort cleanup: only delete the lock if it still names *us*."""
    try:
        current = read_lock(lock_file)
        if lock_pid(current) == os.getpid():
            lock_file.unlink(missing_ok=True)
    except OSError:
        pass


def clear_lock(lock_file: Path) -> None:
    """Best-effort cleanup for a lock already proven stale by the caller."""
    try:
        lock_file.unlink(missing_ok=True)
    except OSError:
        pass
