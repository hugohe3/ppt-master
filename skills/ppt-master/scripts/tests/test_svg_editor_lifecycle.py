#!/usr/bin/env python3
"""Check preview ownership before launcher reuse and shutdown.

Run with: python3 -m unittest tests.test_svg_editor_lifecycle
Dependencies: standard library and the editor's Flask dependency.
"""

import io
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from svg_editor import server


class PreviewIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        (self.project / 'svg_output').mkdir()
        self.lock = {'pid': 12345, 'port': 6060}
        self.lock_file = server._lock_file(self.project)
        self.lock_file.parent.mkdir()
        self.lock_file.write_text(json.dumps(self.lock), encoding='utf-8')
        self.health = {
            'service': 'live_preview', 'project': str(self.project), 'pid': 12345,
        }

    def _response(self, request, **kwargs):
        url = request.full_url if hasattr(request, 'full_url') else request
        body = self.health if url.endswith('/api/health') else {'status': 'ok'}
        response = io.BytesIO(json.dumps(body).encode('utf-8'))
        response.status = 200
        return response

    def _run(self, flags, *, health=None, network_error=None):
        if health is not None:
            self.health = health
        with ExitStack() as stack:
            request = stack.enter_context(patch.object(
                server.urllib.request, 'urlopen', side_effect=network_error or self._response,
            ))
            kill = stack.enter_context(patch.object(server.os, 'kill'))
            browser = stack.enter_context(patch.object(server, '_open_browser'))
            stack.enter_context(patch.object(server, '_find_free_port', return_value=6061))
            stack.enter_context(patch.object(server, '_claim_lock', return_value=self.lock))
            stack.enter_context(patch.object(
                server, '_process_alive', side_effect=[True, False, False],
            ))
            result = server.main([str(self.project), *flags])
        return result, request, kill, browser

    def test_copied_lock_refuses_reuse_in_all_launch_paths(self) -> None:
        self.health['project'] = str(self.project / 'other')
        for flags in ([], ['--daemon'], ['--port', '6060']):
            with self.subTest(flags=flags):
                result, request, kill, browser = self._run(flags)
                self.assertEqual(result, 1)
                browser.assert_not_called()
                kill.assert_not_called()
                self.assertTrue(self.lock_file.exists())
                self.assertEqual(request.call_count, 1)

    def test_copied_legacy_lock_refuses_reuse(self) -> None:
        self.health['project'] = str(self.project / 'other')
        legacy = self.project / server.LEGACY_LOCK_FILE_NAME
        legacy.write_text(json.dumps(self.lock), encoding='utf-8')
        result, _, kill, browser = self._run([])
        self.assertEqual(result, 1)
        self.assertTrue(legacy.exists())
        kill.assert_not_called()
        browser.assert_not_called()

    def test_shutdown_requires_project_service_and_pid_identity(self) -> None:
        for field, value in (
            ('project', str(self.project / 'other')),
            ('service', 'confirm_ui'),
            ('pid', 54321),
        ):
            with self.subTest(field=field):
                health = {**self.health, field: value}
                result, request, kill, _ = self._run(['--shutdown'], health=health)
                self.assertEqual(result, 1)
                self.assertEqual(request.call_count, 1)
                self.assertTrue(request.call_args.args[0].endswith('/api/health'))
                kill.assert_not_called()
                self.assertTrue(self.lock_file.exists())
                self.health = {
                    'service': 'live_preview', 'project': str(self.project), 'pid': 12345,
                }

    def test_unavailable_health_never_reuses_or_signals(self) -> None:
        for flags in (['--daemon'], ['--shutdown']):
            with self.subTest(flags=flags):
                result, _, kill, browser = self._run(flags, network_error=OSError('offline'))
                self.assertEqual(result, 1)
                kill.assert_not_called()
                browser.assert_not_called()
                self.assertTrue(self.lock_file.exists())

    def test_same_project_reuses_and_stops_normally(self) -> None:
        result, request, kill, browser = self._run(['--daemon'])
        self.assertEqual(result, 0)
        self.assertEqual(request.call_count, 1)
        browser.assert_called_once_with(server._server_url(6060))
        kill.assert_not_called()
        result, request, kill, _ = self._run(['--shutdown'])
        self.assertEqual(result, 0)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args[0].method, 'POST')
        kill.assert_not_called()
        self.assertFalse(self.lock_file.exists())

    def test_explicit_other_port_still_refuses_reuse(self) -> None:
        result, _, kill, browser = self._run(['--daemon', '--port', '6061'])
        self.assertEqual(result, 1)
        browser.assert_not_called()
        kill.assert_not_called()

    def test_stale_lock_is_cleared_without_contacting_service(self) -> None:
        with patch.object(server, '_process_alive', return_value=False), patch.object(
            server.urllib.request, 'urlopen',
        ) as request, patch.object(server.os, 'kill') as kill:
            self.assertEqual(server.main([str(self.project), '--shutdown']), 0)
        request.assert_not_called()
        kill.assert_not_called()
        self.assertFalse(self.lock_file.exists())
