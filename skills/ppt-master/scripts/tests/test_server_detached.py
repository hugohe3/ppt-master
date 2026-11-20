#!/usr/bin/env python3
"""PPT Master - Detached Preview Server Launcher Tests

Exercise ``server_common.popen_detached()`` Windows breakaway fallback and
error handling paths for the local preview launchers.

Usage:
    cd skills/ppt-master/scripts && python3 -m unittest tests.test_server_detached

Dependencies:
    flask
"""

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import server_common as common  # noqa: E402
from confirm_ui import server as confirm_server  # noqa: E402
from svg_editor import server as editor_server  # noqa: E402


def _win_oserror(winerror: int, message: str = 'access denied') -> OSError:
    exc = OSError(message)
    exc.winerror = winerror
    return exc


class PopenDetachedTests(unittest.TestCase):
    def _patch_windows(self):
        return (
            patch.object(common.os, 'name', 'nt'),
            patch.object(common.subprocess, 'CREATE_NEW_PROCESS_GROUP', 0x200, create=True),
            patch.object(common.subprocess, 'DETACHED_PROCESS', 0x008, create=True),
            patch.object(common.subprocess, 'CREATE_BREAKAWAY_FROM_JOB', 0x01000000, create=True),
        )

    def test_windows_breakaway_success_launches_once_without_warning(self) -> None:
        proc = MagicMock()
        p_os, p_group, p_detach, p_break = self._patch_windows()
        logger = MagicMock(spec=logging.Logger)
        with p_os, p_group, p_detach, p_break:
            with patch.object(common.subprocess, 'Popen', return_value=proc) as popen:
                result = common.popen_detached(['python', 'srv.py'], logger=logger)
        self.assertIs(result, proc)
        popen.assert_called_once()
        self.assertEqual(popen.call_args.kwargs['creationflags'], 0x200 | 0x008 | 0x01000000)
        logger.warning.assert_not_called()

    def test_windows_access_denied_falls_back_and_warns_with_action(self) -> None:
        proc = MagicMock()
        p_os, p_group, p_detach, p_break = self._patch_windows()
        logger = logging.getLogger('test.popen_detached.fallback')
        with p_os, p_group, p_detach, p_break:
            with patch.object(
                common.subprocess,
                'Popen',
                side_effect=[_win_oserror(5, 'Access is denied'), proc],
            ) as popen:
                with self.assertLogs(logger, level='WARNING') as logs:
                    result = common.popen_detached(['python', 'srv.py'], logger=logger)
        self.assertIs(result, proc)
        self.assertEqual(popen.call_count, 2)
        self.assertEqual(popen.call_args_list[0].kwargs['creationflags'], 0x200 | 0x008 | 0x01000000)
        self.assertEqual(popen.call_args_list[1].kwargs['creationflags'], 0x200 | 0x008)
        msg = logs.output[0]
        self.assertIn('Windows Job Object denied process breakaway', msg)
        self.assertIn('omit --daemon', msg)
        self.assertIn('GET /api/health', msg)

    def test_windows_persistent_access_denied_raises_without_job_warning(self) -> None:
        p_os, p_group, p_detach, p_break = self._patch_windows()
        logger = MagicMock(spec=logging.Logger)
        with p_os, p_group, p_detach, p_break:
            with patch.object(
                common.subprocess,
                'Popen',
                side_effect=[_win_oserror(5, 'Access is denied'), _win_oserror(5, 'Access is denied')],
            ) as popen:
                with self.assertRaises(OSError):
                    common.popen_detached(['python', 'srv.py'], logger=logger)
        self.assertEqual(popen.call_count, 2)
        logger.warning.assert_not_called()

    def test_windows_non_access_denied_oserror_does_not_retry(self) -> None:
        p_os, p_group, p_detach, p_break = self._patch_windows()
        logger = MagicMock(spec=logging.Logger)
        with p_os, p_group, p_detach, p_break:
            with patch.object(
                common.subprocess,
                'Popen',
                side_effect=_win_oserror(2, 'The system cannot find the file specified'),
            ) as popen:
                with self.assertRaises(OSError):
                    common.popen_detached(['missing.exe'], logger=logger)
        popen.assert_called_once()
        logger.warning.assert_not_called()


class LauncherSpawnErrorTests(unittest.TestCase):
    def test_svg_editor_reports_process_start_error_distinct_from_log_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / 'svg_output').mkdir()
            with patch.object(editor_server, '_find_free_port', return_value=6060), patch.object(
                editor_server, '_popen_detached', side_effect=OSError('spawn failed'),
            ), self.assertLogs(editor_server.logger, level='ERROR') as logs:
                code = editor_server.main([str(project), '--daemon', '--no-browser'])
        self.assertEqual(code, 1)
        self.assertIn('failed to start live preview process', logs.output[0])
        self.assertNotIn('cannot write live preview log', logs.output[0])

    def test_confirm_ui_handles_oserror_from_background_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            with patch.object(confirm_server, '_confirmation_launch_error', return_value=None), patch.object(
                confirm_server, '_launch_background_server', side_effect=OSError('spawn failed'),
            ), self.assertLogs(confirm_server.logger, level='ERROR') as logs:
                code = confirm_server.main([str(project), '--daemon', '--no-browser'])
        self.assertEqual(code, 1)
        self.assertIn('spawn failed', logs.output[0])
