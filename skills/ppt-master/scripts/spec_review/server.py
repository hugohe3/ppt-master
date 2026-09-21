#!/usr/bin/env python3
"""
PPT Master - Spec Review Server

Serve a local Markdown review surface with staged edits and sidecar comments.
See scripts/docs/spec_review.md for commands, APIs, and runtime files.

Usage:
    python3 scripts/spec_review/server.py <project_path> [--daemon]

Examples:
    python3 scripts/spec_review/server.py projects/example --daemon --no-browser
    python3 scripts/spec_review/server.py projects/example --hold on

Dependencies:
    Flask (already used by svg_editor and confirm_ui)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from server_common import (  # noqa: E402
    claim_lock,
    clear_lock,
    find_free_port,
    lock_pid,
    open_preview_browser,
    popen_detached,
    process_alive,
    read_lock,
    release_lock,
    validate_port,
)
from spec_review.store import ReviewError, ReviewStore, file_mutex  # noqa: E402


PUBLIC_HOST = "127.0.0.1"
DEFAULT_PORT = 6060
logger = logging.getLogger("spec_review")


class _QuietPolls(logging.Filter):
    """Drop successful state polls so real requests stay findable in server.log."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not ('"GET /api/state ' in message and '" 200 ' in message)


def create_app(project_dir: str, idle_timeout: int = 7200) -> Flask:
    """Create the testable HTTP surface; lifecycle threads belong to main()."""
    store = ReviewStore(Path(project_dir))
    store.document()
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(MAX_CONTENT_LENGTH=4 * 1024 * 1024, LAST_ACTIVITY=time.monotonic(), IDLE_TIMEOUT=idle_timeout)
    app.extensions["review_store"] = store
    app.extensions["stop_event"] = threading.Event()

    @app.before_request
    def protect_local_service():
        try:
            host = urllib.parse.urlsplit("//" + request.host)
            if host.hostname not in {PUBLIC_HOST, "localhost", "::1"} or host.username or host.password:
                raise ValueError("Host")
            host_port = host.port or 80
            origin = request.headers.get("Origin")
            if origin is not None:
                parsed = urllib.parse.urlsplit(origin)
                if (parsed.scheme != request.scheme or parsed.hostname != host.hostname
                        or (parsed.port or 80) != host_port or parsed.username or parsed.password
                        or parsed.path or parsed.query or parsed.fragment):
                    raise ValueError("Origin")
        except ValueError:
            return jsonify(error="Forbidden Host or Origin header"), 403
        if request.path not in {"/api/state", "/api/health"}:
            app.config["LAST_ACTIVITY"] = time.monotonic()

    @app.after_request
    def secure_response(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
        )
        return response

    @app.errorhandler(ReviewError)
    def review_error(error):
        return jsonify(error=str(error)), error.status

    @app.errorhandler(OSError)
    @app.errorhandler(ValueError)
    def storage_error(error):
        logger.error("spec review storage: %s", error)
        return jsonify(error=str(error)), 500

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    def payload(*strings: str) -> dict:
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or any(not isinstance(data.get(key), str) for key in strings):
            raise ReviewError("Send a JSON object with string fields: " + ", ".join(strings))
        return data

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="spec_review", pid=os.getpid(), project=str(store.project))

    @app.get("/api/state")
    def state():
        return jsonify(store.state())

    @app.get("/api/blocks")
    def blocks():
        return jsonify(store.snapshot())

    @app.get("/api/spec")
    def spec():
        return jsonify(store.document())

    @app.get("/api/blocks/<path:key>")
    def block(key):
        return jsonify(store.block(key))

    @app.put("/api/drafts/<path:key>")
    def stage(key):
        data = payload("text", "sha256")
        return jsonify(store.stage(key, data["text"], data["sha256"], data.get("version")))

    @app.delete("/api/drafts/<path:key>")
    def discard(key):
        data = payload("version")
        store.discard(key, data["version"])
        return jsonify(status="ok")

    @app.post("/api/apply/<path:key>")
    def apply(key):
        data = payload("sha256", "version")
        return jsonify(store.apply(key, data["sha256"], data["version"]))

    @app.route("/api/annotations", methods=["GET", "POST"])
    def annotations():
        if request.method == "GET":
            return jsonify(annotations=store.annotations())
        data = payload("key", "body")
        return jsonify(store.save_annotation(data["key"], data["body"])), 201

    @app.route("/api/annotations/<item_id>", methods=["PUT", "DELETE"])
    def annotation(item_id):
        data = payload("revision", *( ["body"] if request.method == "PUT" else []))
        if request.method == "DELETE":
            store.remove_annotation(item_id, data["revision"])
            return jsonify(status="ok")
        return jsonify(store.save_annotation("", data["body"], item_id, data["revision"]))

    @app.post("/api/hold")
    def hold():
        data = payload()
        if not isinstance(data.get("hold"), bool):
            raise ReviewError("hold must be true or false")
        return jsonify(store.set_hold(data["hold"]))

    @app.post("/api/shutdown")
    def shutdown():
        store.set_hold(True)
        app.extensions["stop_event"].set()
        return jsonify(status="ok")

    return app


def _call(port: int, path: str, data: dict | None = None) -> dict:
    url = f"http://{PUBLIC_HOST}:{validate_port(port)}{path}"
    request_data = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=request_data, headers={"Content-Type": "application/json"})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=2) as response:
        return json.load(response)


def _running(project: Path) -> dict | None:
    lock = read_lock(project / "spec_review" / "lock.json")
    if not lock or not process_alive(lock_pid(lock)):
        return None
    health = _call(lock.get("port"), "/api/health")
    if health.get("service") != "spec_review" or health.get("project") != str(project) or (
        health.get("pid") != lock_pid(lock)
    ):
        raise ValueError("The lock does not identify this project's spec review service.")
    return lock


def _announce(lock: dict, no_browser: bool) -> None:
    url = f"http://{PUBLIC_HOST}:{lock['port']}"
    print(json.dumps({"service": "spec_review", "url": url, **lock}, separators=(",", ":")))
    if not no_browser:
        open_preview_browser(url, logger=logger)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_path")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--daemon", action="store_true")
    actions.add_argument("--shutdown", action="store_true")
    actions.add_argument("--hold", choices=("on", "off"))
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, help="Bind exactly this port; otherwise scan from 6060")
    parser.add_argument("--timeout", type=int, default=7200, help="Idle seconds; 0 disables the timeout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s spec_review: %(message)s")
    logging.getLogger("werkzeug").addFilter(_QuietPolls())
    project = Path(args.project_path).resolve()
    runtime = project / "spec_review"
    lock_file = runtime / "lock.json"
    try:
        if args.port is not None:
            validate_port(args.port)
        if args.timeout < 0:
            raise ValueError("--timeout must be nonnegative")
        existing = _running(project)
        if args.shutdown or args.hold:
            if not existing:
                if args.hold:
                    raise ValueError("Start spec review before setting --hold.")
                clear_lock(lock_file)
                print('{"status":"stopped"}')
                return 0
            path = "/api/shutdown" if args.shutdown else "/api/hold"
            result = _call(existing["port"], path, {} if args.shutdown else {"hold": args.hold == "on"})
            if args.shutdown:
                deadline = time.monotonic() + 5
                while read_lock(lock_file) == existing and time.monotonic() < deadline:
                    time.sleep(0.1)
                if read_lock(lock_file) == existing:
                    raise ValueError("Shutdown is still pending; inspect spec_review/server.log.")
            print(json.dumps(result, separators=(",", ":")))
            return 0
        if existing:
            if args.port is not None and existing["port"] != args.port:
                raise ValueError("A server is already running on a different port; use --shutdown first.")
            _announce(existing, args.no_browser)
            return 0
        if not (project / "design_spec.md").is_file():
            raise ValueError("The project must contain design_spec.md.")
        runtime.mkdir(parents=True, exist_ok=True)
        if args.daemon:
            command = [sys.executable, str(Path(__file__).resolve()), str(project),
                       "--no-browser", "--timeout", str(args.timeout)]
            if args.port is not None:
                command.extend(["--port", str(args.port)])
            with (runtime / "server.log").open("a", encoding="utf-8") as log:
                process = popen_detached(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, logger=logger)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    existing = _running(project)
                except (OSError, ValueError):
                    existing = None
                if existing:
                    if args.port is not None and existing["port"] != args.port:
                        raise ValueError("A concurrent launch claimed another port; use --shutdown first.")
                    _announce(existing, args.no_browser)
                    return 0
                if process.poll() is not None:
                    break
                time.sleep(0.2)
            if process.poll() is None:
                process.terminate()
            raise ValueError("Server failed to start; inspect spec_review/server.log.")

        # Serialize startup without changing the shared servers' lock behavior.
        with file_mutex(runtime / "service.guard"):
            existing = _running(project)
            if existing:
                if args.port is not None and args.port != existing["port"]:
                    raise ValueError("A concurrent launch claimed another port; use --shutdown first.")
                _announce(existing, args.no_browser)
                return 0
            app = create_app(str(project), args.timeout)
            port = args.port if args.port is not None else find_free_port(DEFAULT_PORT)
            httpd = make_server(PUBLIC_HOST, port, app, threaded=True)
            # Let in-flight writes finish before server_close releases the slot.
            httpd.daemon_threads = False
            if claim_lock(lock_file, port):
                httpd.server_close()
                raise ValueError("Another process claimed the project lock; launch again.")
        stop = app.extensions["stop_event"]

        def watch():
            while not stop.wait(0.25):
                with app.extensions["review_store"].mutex:
                    if args.timeout and time.monotonic() - app.config["LAST_ACTIVITY"] > args.timeout:
                        logger.info("idle timeout reached")
                        break
            httpd.shutdown()

        signal.signal(signal.SIGTERM, lambda *_: stop.set())
        threading.Thread(target=watch, daemon=True).start()
        try:
            _announce({"pid": os.getpid(), "port": port}, args.no_browser)
            httpd.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            stop.set()
        finally:
            stop.set()
            httpd.server_close()
            release_lock(lock_file)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
