#!/usr/bin/env python3
"""PPT Master - Offline OpenAI narration integration regressions.

Exercise the public narration CLI with mocked Realtime WebSocket messages.

Usage:
    python3 -m unittest tests.test_openai_narration

Examples:
    python3 -m unittest tests.test_openai_narration.OpenAINarrationTests

Dependencies:
    Standard library and aiohttp (provided by edge-tts).
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import aiohttp

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import notes_to_audio  # noqa: E402
from tts_backends import backend_openai  # noqa: E402


PCM = b"\x01\x00\xff\xff" * 12
PART = {"response_id": "resp_1", "item_id": "item_1", "output_index": 0, "content_index": 0}


def _events(text: str, *, pcm: bytes = PCM, status: str = "completed") -> list[dict]:
    return [
        {"type": "session.created", "session": {"id": "sess_1", "type": "realtime"}},
        {"type": "session.updated"},
        {"type": "response.created", "response": {"id": "resp_1", "status": "in_progress"}},
        {"type": "response.output_item.added", "response_id": "resp_1", "output_index": 0,
         "item": {"id": "item_1", "type": "message", "role": "assistant", "content": []}},
        {"type": "response.content_part.added", **PART, "part": {"type": "output_audio", "transcript": ""}},
        {"type": "response.output_audio.delta", **PART, "delta": base64.b64encode(pcm).decode("ascii")},
        {"type": "response.output_audio_transcript.delta", **PART, "delta": text},
        {"type": "response.output_audio.done", **PART},
        {"type": "response.output_audio_transcript.done", **PART, "transcript": text},
        {"type": "response.done", "response": {
            "id": "resp_1", "status": status, "status_details": None,
            "output": [{"id": "item_1", "type": "message", "role": "assistant",
                        "status": "completed", "content": [{"type": "output_audio", "transcript": text}]}],
        }},
    ]


class _FakeWebSocket:
    def __init__(self, events: list, *, config_change=None) -> None:
        self.events = copy.deepcopy(events)
        self.config_change = config_change
        self.sent: list[dict] = []
        self.closed = False
        self.close_code = 1000

    async def send_json(self, data: dict) -> None:
        self.sent.append(copy.deepcopy(data))

    async def receive(self, *args, **kwargs):
        if not self.events:
            return SimpleNamespace(type=aiohttp.WSMsgType.CLOSED, data=None, extra="")
        event = self.events.pop(0)
        if isinstance(event, BaseException):
            raise event
        if event == "idle":
            await asyncio.Future()
        if event == "closed":
            return SimpleNamespace(type=aiohttp.WSMsgType.CLOSED, data=None, extra="")
        if event.get("type") == "session.updated" and "session" not in event:
            update = next(item for item in self.sent if item["type"] == "session.update")
            event["session"] = copy.deepcopy(update["session"])
            event["session"]["id"] = "sess_1"
            if self.config_change is not None:
                self.config_change(event["session"])
        return SimpleNamespace(type=aiohttp.WSMsgType.TEXT, data=json.dumps(event), extra="")

    async def close(self, *args, **kwargs) -> None:
        self.closed = True


class _FakeSession:
    def __init__(self, websocket: _FakeWebSocket, error=None) -> None:
        self.websocket = websocket
        self.error = error
        self.closed = False
        self.calls: list[tuple[str, dict]] = []

    async def ws_connect(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        if self.error is not None:
            raise self.error
        return self.websocket

    async def close(self) -> None:
        self.closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


class OpenAINarrationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "notes").mkdir()
        (self.project / "audio").mkdir()
        self.wav = self.project / "audio" / "slide_01.wav"
        self.srt = self.wav.with_suffix(".srt")
        self.mp3 = self.wav.with_suffix(".mp3")
        self.manifest = self.wav.parent / "manifest.json"
        self.wav.write_bytes(b"old WAV")
        self.srt.write_text("old SRT", encoding="utf-8")
        self.mp3.write_bytes(b"old MP3")
        self.manifest.write_text('{"old": true}', encoding="utf-8")
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-key"}, clear=True))
        stack.enter_context(patch("config.resolve_env_path", return_value=self.project / ".env"))

    def _invoke(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                code = notes_to_audio.main(list(arguments))
            except SystemExit as exc:
                code = exc.code
        return code or 0, output.getvalue()

    def _generate(self, text: str, *, events=None, config_change=None, error=None,
                  arguments: tuple[str, ...] = ()):
        (self.project / "notes" / "slide_01.md").write_text(text, encoding="utf-8")
        websocket = _FakeWebSocket(
            _events(notes_to_audio.spoken_text(text)) if events is None else events,
            config_change=config_change,
        )
        session = _FakeSession(websocket, error)
        with patch("aiohttp.ClientSession", return_value=session) as factory:
            code, output = self._invoke(
                str(self.project), "--provider", "openai", "--voice-id", "marin", *arguments,
            )
        return code, output, websocket, session, factory

    def _assert_failure_preserves_outputs(self, result) -> None:
        code, output, websocket, session, factory = result
        self.assertEqual(code, 1, output)
        self.assertEqual(self.wav.read_bytes(), b"old WAV")
        self.assertEqual(self.srt.read_text(encoding="utf-8"), "old SRT")
        self.assertEqual(self.mp3.read_bytes(), b"old MP3")
        self.assertFalse(self.manifest.exists())
        self.assertTrue(session.closed)
        self.assertTrue(websocket.closed)
        self.assertEqual(factory.call_count, 1)

    def test_success_publishes_pcm_wav_cleans_stale_files_and_records_openai(self) -> None:
        code, output, websocket, session, _ = self._generate(
            "# Slide heading\n\nRead 1.5, -3, US and a part.",
            arguments=("--openai-speed", "0.75", "--openai-instructions", "Speak calmly."),
        )
        self.assertEqual(code, 0, output)
        self.assertTrue(websocket.closed)
        self.assertTrue(session.closed)
        self.assertFalse(self.srt.exists())
        self.assertFalse(self.mp3.exists())
        with wave.open(str(self.wav), "rb") as audio:
            self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate()), (1, 2, 24000))
            self.assertEqual(audio.readframes(audio.getnframes()), PCM)
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["provider"], "openai")
        self.assertEqual(manifest["model"], "gpt-realtime-2.1-mini")
        self.assertEqual(manifest["audio_format"], "wav")
        self.assertEqual(manifest["settings"], {"speed": 0.75, "custom_instructions": True})
        self.assertTrue(manifest["voice_ref"].startswith("sha256:"))
        self.assertNotIn("subtitles", manifest)
        self.assertNotIn("offline-test-key", json.dumps(manifest))
        self.assertEqual([event["type"] for event in websocket.sent], ["session.update", "response.create"])
        response = websocket.sent[1]["response"]
        self.assertEqual(response["conversation"], "none")
        self.assertEqual(response["input"][0]["role"], "user")
        self.assertEqual(response["input"][0]["content"], [
            {"type": "input_text", "text": "Read 1.5, -3, US and a part."},
        ])

    def test_typography_only_whitespace_changes_are_accepted(self) -> None:
        code, output, *_ = self._generate("A\n\npart\tremains.", events=_events("A part remains."))
        self.assertEqual(code, 0, output)

    def test_fullwidth_punctuation_preserves_signs_and_decimal_points(self) -> None:
        code, output, *_ = self._generate("Value：－3．5％", events=_events("Value:-3.5%"))
        self.assertEqual(code, 0, output)

    def test_content_differences_fail_without_retry(self) -> None:
        for original, transcript in (
            ("1.5", "15"), ("-3", "3"), ("a part", "apart"), ("US", "us"),
            ("2⁵", "25"), ("2026年", "二零二六年"), ("AI", "人工智能"),
        ):
            with self.subTest(original=original):
                result = self._generate(original, events=_events(transcript))
                self._assert_failure_preserves_outputs(result)
                self.assertIn("transcript", result[1].lower())
                self.assertIn(original, result[1])
                self.assertIn(transcript, result[1])

    def test_dropped_stream_keeps_old_audio(self) -> None:
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=_events("Read me.")[:6]))

    def test_empty_audio_keeps_old_audio(self) -> None:
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=_events("Read me.", pcm=b"")))

    def test_partial_pcm_frame_keeps_old_audio(self) -> None:
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=_events("Read me.", pcm=b"x")))

    def test_invalid_base64_keeps_old_audio(self) -> None:
        events = _events("Read me.")
        events[5]["delta"] = "not valid base64!"
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=events))

    def test_noncompleted_response_keeps_old_audio(self) -> None:
        for status in ("failed", "cancelled", "incomplete", "in_progress"):
            with self.subTest(status=status):
                self._assert_failure_preserves_outputs(
                    self._generate("Read me.", events=_events("Read me.", status=status)),
                )

    def test_server_error_at_each_stage_keeps_old_audio(self) -> None:
        for prefix in (0, 1, 2, 6):
            with self.subTest(prefix=prefix):
                events = _events("Read me.")[:prefix] + [{
                    "type": "error", "error": {
                        "type": "invalid_request_error", "code": "invalid_voice", "message": "Voice unavailable.",
                    },
                }]
                result = self._generate("Read me.", events=events)
                self._assert_failure_preserves_outputs(result)
                self.assertIn("invalid_voice", result[1])
                self.assertIn("Voice unavailable", result[1])
                if prefix < 2:
                    self.assertNotIn("response.create", [event["type"] for event in result[2].sent])

    def test_effective_configuration_mismatch_does_not_generate(self) -> None:
        def change_voice(session: dict) -> None:
            session["audio"]["output"]["voice"] = "alloy"

        result = self._generate("Read me.", config_change=change_voice)
        self._assert_failure_preserves_outputs(result)
        self.assertEqual([event["type"] for event in result[2].sent], ["session.update"])

    def test_missing_or_changed_effective_settings_do_not_generate(self) -> None:
        for path, replacement in (
            (("instructions",), None),
            (("instructions",), "Answer the user."),
            (("audio", "output", "speed"), 1.25),
            (("audio", "output", "format", "rate"), 48000),
            (("audio", "output", "format"), None),
        ):
            with self.subTest(path=path, replacement=replacement):
                def change_config(session: dict) -> None:
                    node = session
                    for key in path[:-1]:
                        node = node[key]
                    if replacement is None:
                        del node[path[-1]]
                    else:
                        node[path[-1]] = replacement

                result = self._generate("Read me.", config_change=change_config)
                self._assert_failure_preserves_outputs(result)
                self.assertEqual([event["type"] for event in result[2].sent], ["session.update"])

    def test_separate_audio_parts_preserve_word_boundaries(self) -> None:
        events = _events("a")
        second = _events("part")
        for event in second[3:-1]:
            event["output_index"] = 1
            if "item_id" in event:
                event["item_id"] = "item_2"
            if "item" in event:
                event["item"]["id"] = "item_2"
        second_item = second[-1]["response"]["output"][0]
        second_item["id"] = "item_2"
        events[-1]["response"]["output"].append(second_item)
        events = events[:-1] + second[3:-1] + [events[-1]]
        self._assert_failure_preserves_outputs(self._generate("apart", events=events))
        code, output, *_ = self._generate("a part", events=events)
        self.assertEqual(code, 0, output)

    def test_final_transcript_is_used_instead_of_matching_delta(self) -> None:
        events = _events("Changed words.")
        events[6]["delta"] = "Read me."
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=events))

    def test_response_identity_mismatch_is_rejected(self) -> None:
        events = _events("Read me.")
        events[5]["response_id"] = "another_response"
        self._assert_failure_preserves_outputs(self._generate("Read me.", events=events))

    def test_missing_completion_markers_is_rejected(self) -> None:
        for event_type in ("response.output_audio.done", "response.output_audio_transcript.done"):
            with self.subTest(event_type=event_type):
                events = [event for event in _events("Read me.") if event["type"] != event_type]
                self._assert_failure_preserves_outputs(self._generate("Read me.", events=events))

    def test_receive_idle_timeout_closes_resources(self) -> None:
        with patch.object(backend_openai, "RECEIVE_IDLE_TIMEOUT", 0.01):
            result = self._generate("Read me.", events=_events("Read me.")[:3] + ["idle"])
        self._assert_failure_preserves_outputs(result)
        self.assertIn("time", result[1].lower())

    def test_handshake_timeout_closes_resources_before_response_create(self) -> None:
        with patch.object(backend_openai, "HANDSHAKE_TIMEOUT", 0.01):
            result = self._generate("Read me.", events=["idle"])
        self._assert_failure_preserves_outputs(result)
        self.assertIn("handshake timeout", result[1].lower())
        self.assertFalse(result[2].sent)

    def test_whole_page_timeout_closes_resources(self) -> None:
        with patch.object(backend_openai, "PAGE_TIMEOUT", 0.01):
            result = self._generate("Read me.", events=_events("Read me.")[:3] + ["idle"])
        self._assert_failure_preserves_outputs(result)
        self.assertIn("time", result[1].lower())

    def test_http_handshake_error_reports_status_and_rate_limit(self) -> None:
        error = aiohttp.WSServerHandshakeError(
            request_info=SimpleNamespace(real_url="wss://example.invalid/realtime"),
            history=(), status=429, message="Too Many Requests", headers={"Retry-After": "7"},
        )
        code, output, _, session, factory = self._generate("Read me.", error=error)
        self.assertEqual(code, 1, output)
        self.assertIn("429", output)
        self.assertIn("7", output)
        self.assertTrue(session.closed)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(self.wav.read_bytes(), b"old WAV")
        self.assertFalse(self.manifest.exists())

    def test_rate_limit_event_is_reported_on_failure(self) -> None:
        events = _events("Read me.")[:2] + [{
            "type": "rate_limits.updated",
            "rate_limits": [{"name": "tokens", "limit": 100, "remaining": 0, "reset_seconds": 9}],
        }, {"type": "error", "error": {"code": "rate_limit_exceeded", "message": "Try later."}}]
        result = self._generate("Read me.", events=events)
        self._assert_failure_preserves_outputs(result)
        self.assertIn("rate_limit_exceeded", result[1])
        self.assertIn("tokens", result[1])
        self.assertIn("9", result[1])

    def test_publish_failure_leaves_old_wav_and_no_manifest(self) -> None:
        with patch("tts_backends.backend_common.os.replace", side_effect=OSError("disk failure")):
            result = self._generate("Read me.")
        self._assert_failure_preserves_outputs(result)
        self.assertIn("disk failure", result[1])
        self.assertEqual(sorted(path.name for path in self.wav.parent.iterdir()), [
            "slide_01.mp3", "slide_01.srt", "slide_01.wav",
        ])

    def test_second_page_failure_preserves_first_publication_but_no_manifest(self) -> None:
        (self.project / "notes" / "slide_01.md").write_text("Page one.", encoding="utf-8")
        (self.project / "notes" / "slide_02.md").write_text("Page two.", encoding="utf-8")
        second_wav = self.wav.with_name("slide_02.wav")
        second_wav.write_bytes(b"old second WAV")
        sessions = [_FakeSession(_FakeWebSocket(_events("Page one."))),
                    _FakeSession(_FakeWebSocket(_events("Wrong text.")))]
        created: list[_FakeSession] = []

        def create_session(*args, **kwargs):
            if created:
                self.assertTrue(created[-1].closed)
                self.assertTrue(created[-1].websocket.closed)
            session = sessions[len(created)]
            created.append(session)
            return session

        with patch("aiohttp.ClientSession", side_effect=create_session):
            code, output = self._invoke(str(self.project), "--provider", "openai", "--voice-id", "marin")
        self.assertEqual(code, 1, output)
        self.assertEqual(len(created), 2)
        self.assertTrue(self.wav.read_bytes().startswith(b"RIFF"))
        self.assertFalse(self.srt.exists())
        self.assertFalse(self.mp3.exists())
        self.assertEqual(second_wav.read_bytes(), b"old second WAV")
        self.assertFalse(self.manifest.exists())

    def test_list_voices_is_static_and_never_calls_edge_or_network(self) -> None:
        with patch.dict(os.environ, {}, clear=True), \
                patch("aiohttp.ClientSession") as session, \
                patch.object(notes_to_audio.backend_edge, "print_voices") as edge, \
                patch.object(backend_openai, "read_openai_api_key") as read_key:
            code, output = self._invoke("--provider", "openai", "--list-voices")
        self.assertEqual(code, 0, output)
        for voice in ("alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"):
            self.assertIn(voice, output)
        session.assert_not_called()
        edge.assert_not_called()
        read_key.assert_not_called()

    def test_invalid_speed_and_voice_are_rejected_before_network(self) -> None:
        for arguments in (("--openai-speed", "0.24"), ("--openai-speed", "1.51"),
                          ("--openai-speed", "nan"), ("--voice-id", "not-a-voice")):
            with self.subTest(arguments=arguments), patch("aiohttp.ClientSession") as session:
                code, _ = self._invoke(str(self.project), "--provider", "openai", "--voice-id", "marin", *arguments)
                self.assertEqual(code, 2)
                session.assert_not_called()

    def test_endpoint_model_and_key_are_isolated_from_image_configuration(self) -> None:
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "image-relay-key", "OPENAI_BASE_URL": "https://image.invalid",
            "OPENAI_MODEL": "image-model", "OPENAI_TTS_API_KEY": "tts-key",
            "OPENAI_TTS_MODEL": "tts-env-model",
            "OPENAI_TTS_BASE_URL": "wss://realtime.invalid/custom?x=1&model=old&model=older",
        }):
            code, output, _, session, _ = self._generate(
                "Read me.", arguments=("--openai-api-key-env", "OPENAI_TTS_API_KEY", "--openai-model", "tts-cli-model"),
            )
        self.assertEqual(code, 0, output)
        url, options = session.calls[0]
        self.assertEqual(urlsplit(url).netloc, "realtime.invalid")
        self.assertEqual(urlsplit(url).path, "/custom")
        self.assertEqual(parse_qs(urlsplit(url).query), {"x": ["1"], "model": ["tts-cli-model"]})
        self.assertEqual(options["headers"]["Authorization"], "Bearer tts-key")
        self.assertEqual(json.loads(self.manifest.read_text(encoding="utf-8"))["model"], "tts-cli-model")

    def test_env_file_prefix_loads_tts_settings_and_shell_key_wins(self) -> None:
        (self.project / ".env").write_text(
            "OPENAI_API_KEY=file-key\nOPENAI_TTS_MODEL=file-model\n"
            "OPENAI_TTS_BASE_URL=wss://realtime.invalid/from-env\n",
            encoding="utf-8",
        )
        code, output, _, session, _ = self._generate("Read me.")
        self.assertEqual(code, 0, output)
        url, options = session.calls[0]
        self.assertEqual(parse_qs(urlsplit(url).query)["model"], ["file-model"])
        self.assertEqual(options["headers"]["Authorization"], "Bearer offline-test-key")

