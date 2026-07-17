#!/usr/bin/env python3
"""ppt-master-engine — dispatch CLI for bundled skill scripts.

Usage:
    ppt-master-engine --version
    ppt-master-engine <script_stem> [args...]

Examples:
    ppt-master-engine project_manager init demo --format ppt169 --dir work
    ppt-master-engine svg_to_pptx /path/to/project
    ppt-master-engine svg_quality_checker /path/to/project

The binary lives at:
    <pack>/bin/ppt-master-engine/ppt-master-engine
Skill scripts live at:
    <pack>/skills/ppt-master/scripts/
"""

from __future__ import annotations

# Pre-import stdlib modules that skill scripts use but the launcher does not.
# PyInstaller only freezes imports reachable from this entry — without this
# list, runpy-loaded scripts fail with ModuleNotFoundError on stdlib names.
import argparse  # noqa: F401
import base64  # noqa: F401
import copy  # noqa: F401
import csv  # noqa: F401
import dataclasses  # noqa: F401
import datetime  # noqa: F401
import filecmp  # noqa: F401
import fnmatch  # noqa: F401
import functools  # noqa: F401
import glob  # noqa: F401
import hashlib  # noqa: F401
import html  # noqa: F401
import http  # noqa: F401
import http.client  # noqa: F401
import http.server  # noqa: F401
import io  # noqa: F401
import json  # noqa: F401
import logging  # noqa: F401
import mimetypes  # noqa: F401
import os  # noqa: F401
import pathlib  # noqa: F401
import pickle  # noqa: F401
import platform  # noqa: F401
import queue  # noqa: F401
import random  # noqa: F401
import re  # noqa: F401
import runpy
import shutil  # noqa: F401
import signal  # noqa: F401
import socket  # noqa: F401
import sqlite3  # noqa: F401
import ssl  # noqa: F401
import string  # noqa: F401
import struct  # noqa: F401
import subprocess  # noqa: F401
import sys
import tempfile  # noqa: F401
import textwrap  # noqa: F401
import threading  # noqa: F401
import time  # noqa: F401
import traceback  # noqa: F401
import typing  # noqa: F401
import urllib  # noqa: F401
import urllib.error  # noqa: F401
import urllib.parse  # noqa: F401
import urllib.request  # noqa: F401
import uuid  # noqa: F401
import wave  # noqa: F401
import xml  # noqa: F401
import xml.etree.ElementTree  # noqa: F401
import zipfile  # noqa: F401
from pathlib import Path

ENGINE_VERSION = "0.1.0"

# Short names → script file under skills/ppt-master/scripts/
# (stem only; .py added)
ALIASES = {
    "project_manager": "project_manager.py",
    "svg_to_pptx": "svg_to_pptx.py",
    "svg_quality_checker": "svg_quality_checker.py",
    "finalize_svg": "finalize_svg.py",
    "total_md_split": "total_md_split.py",
    "source_to_md": "source_to_md.py",
    "icon_sync": "icon_sync.py",
    "analyze_images": "analyze_images.py",
    "image_gen": "image_gen.py",
    "image_search": "image_search.py",
    "animation_config": "animation_config.py",
    "pptx_intake": "pptx_intake.py",
    "notes_to_audio": "notes_to_audio.py",
}


def pack_root() -> Path:
    """Return the engine pack root (parent of bin/ and skills/)."""
    if getattr(sys, "frozen", False):
        # <pack>/bin/ppt-master-engine/ppt-master-engine
        return Path(sys.executable).resolve().parent.parent.parent
    # Dev: engine/launcher.py → repo root is parent of engine/
    return Path(__file__).resolve().parent.parent


def scripts_dir(root: Path) -> Path:
    return root / "skills" / "ppt-master" / "scripts"


def resolve_script(name: str, sdir: Path) -> Path:
    key = name
    if key.endswith(".py"):
        key = key[: -len(".py")]
    # strip path-like prefixes
    key = Path(key).name
    if key.endswith(".py"):
        key = key[: -len(".py")]

    filename = ALIASES.get(key, f"{key}.py")
    path = sdir / filename
    if not path.is_file():
        # also allow nested like source_to_md (dispatcher)
        nested = sdir / key
        if nested.is_dir() and (nested / "__main__.py").is_file():
            return nested / "__main__.py"
        if nested.is_file():
            return nested
        raise FileNotFoundError(
            f"unknown engine command {name!r}; expected under {sdir} "
            f"(known: {', '.join(sorted(ALIASES))})"
        )
    return path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(__doc__.strip(), file=sys.stderr)
        return 0 if argv and argv[0] in {"-h", "--help", "help"} else 2
    if argv[0] in {"-V", "--version", "version"}:
        print(f"ppt-master-engine {ENGINE_VERSION}")
        return 0

    root = pack_root()
    sdir = scripts_dir(root)
    if not sdir.is_dir():
        print(
            f"error: skill scripts not found at {sdir}\n"
            f"  pack root resolved to: {root}",
            file=sys.stderr,
        )
        return 1

    cmd = argv[0]
    rest = argv[1:]
    try:
        script = resolve_script(cmd, sdir)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Scripts expect to import siblings from the scripts directory.
    scripts_path = str(sdir)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)

    # Emulate `python script.py args...`
    sys.argv = [str(script), *rest]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
