#!/usr/bin/env python3
"""Regression tests for local preview browser dispatch across Windows and WSL."""

import base64
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import server_common as common  # noqa: E402
from svg_editor import server as editor  # noqa: E402

URL = 'http://127.0.0.1:6060'


class PreviewBrowserTests(unittest.TestCase):
    """Default fixture: WSL2 with powershell.exe on PATH and no BROWSER override."""

    def setUp(self) -> None:
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop('BROWSER', None)
        for target, value in (
            ('server_common.platform.release', '6.18-microsoft-standard-WSL2'),
            ('server_common.shutil.which', '/windows/powershell.exe'),
        ):
            mock = patch(target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def test_wsl_uses_windows_browser_and_encodes_url_as_data(self) -> None:
        url = "http://127.0.0.1:6060/?q=';&name=演示"
        ok = subprocess.CompletedProcess([], 0)
        with patch.object(common.subprocess, 'run', return_value=ok) as run:
            with patch.object(common.webbrowser, 'open') as browser:
                self.assertTrue(editor._open_browser(url))
        browser.assert_not_called()
        args = run.call_args.args[0]
        self.assertEqual(
            args[:4], ['/windows/powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand'],
        )
        script = base64.b64decode(args[4]).decode('utf-16le')
        self.assertIn(base64.b64encode(url.encode()).decode(), script)
        self.assertNotIn(url, script)
        self.assertIn('Start-Process -FilePath $u', script)
        self.assertEqual(run.call_args.kwargs['timeout'], 15)

    def test_wsl_probes_mounted_powershell_when_path_lacks_windows_dirs(self) -> None:
        ok = subprocess.CompletedProcess([], 0)
        with patch.object(common.shutil, 'which', return_value=None):
            with patch.object(common.os, 'access', return_value=True):
                with patch.object(common.subprocess, 'run', return_value=ok) as run:
                    with patch.object(common.webbrowser, 'open') as browser:
                        self.assertTrue(common.open_preview_browser(URL))
        browser.assert_not_called()
        self.assertEqual(run.call_args.args[0][0], common.WSL_POWERSHELL)

    def test_browser_env_keeps_webbrowser_dispatch_on_wsl(self) -> None:
        os.environ['BROWSER'] = 'wslview'
        with patch.object(common.subprocess, 'run') as run:
            with patch.object(common.webbrowser, 'open', return_value=True) as browser:
                self.assertTrue(common.open_preview_browser(URL))
        run.assert_not_called()
        browser.assert_called_once_with(URL)

    def test_windows_keeps_webbrowser_dispatch(self) -> None:
        with patch.object(common.platform, 'release', return_value='10'):
            with patch.object(common.subprocess, 'run') as run:
                with patch.object(common.webbrowser, 'open', return_value=True) as browser:
                    self.assertTrue(common.open_preview_browser(URL))
        run.assert_not_called()
        browser.assert_called_once_with(URL)

    def test_linux_keeps_webbrowser_dispatch(self) -> None:
        with patch.object(common.platform, 'release', return_value='6.8-linux'):
            with patch.object(common.webbrowser, 'open', return_value=True) as browser:
                self.assertTrue(common.open_preview_browser(URL))
                browser.assert_called_once()

    def test_wsl_without_powershell_keeps_webbrowser_fallback(self) -> None:
        with patch.object(common.shutil, 'which', return_value=None):
            with patch.object(common.os, 'access', return_value=False):
                with patch.object(common.webbrowser, 'open', return_value=True) as browser:
                    self.assertTrue(common.open_preview_browser(URL))
        browser.assert_called_once_with(URL)

    def test_powershell_failures_preserve_manual_url(self) -> None:
        failures = [
            OSError('interop unavailable'),
            subprocess.TimeoutExpired('powershell.exe', 15),
        ]
        for error in failures:
            run = patch.object(common.subprocess, 'run', side_effect=error)
            with self.subTest(error=error), run:
                with self.assertLogs('server_common', level='WARNING') as logs:
                    self.assertFalse(common.open_preview_browser(URL))
                self.assertIn(f'open {URL} manually', logs.output[0])

    def test_nonzero_powershell_exit_is_failure(self) -> None:
        result = subprocess.CompletedProcess([], 1, b'', b'no application')
        with patch.object(common.subprocess, 'run', return_value=result):
            with self.assertLogs('server_common', level='WARNING'):
                self.assertFalse(common.open_preview_browser(URL))

    def test_webbrowser_false_is_failure(self) -> None:
        with patch.object(common.platform, 'release', return_value='6.8-linux'):
            with patch.object(common.webbrowser, 'open', return_value=False):
                with self.assertLogs('server_common', level='WARNING'):
                    self.assertFalse(common.open_preview_browser(URL))

