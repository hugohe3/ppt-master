#!/usr/bin/env python3
"""PPT Master - Local Server Security Tests

Exercise both Flask request guards without creating project files or servers.

Usage:
    python3 -m unittest discover -s skills/ppt-master/scripts/tests -p test_local_server_security.py

Dependencies:
    flask
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from confirm_ui import server as confirm_server  # noqa: E402
from svg_editor import server as editor_server  # noqa: E402


class LocalServerSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servers = []
        for server in (editor_server, confirm_server):
            with patch.object(server.threading.Thread, 'start'):
                app = server.create_app(str(SCRIPTS_DIR / '__security_test_project__'), idle_timeout=0)
            app.config['TESTING'] = True
            self.servers.append((server, app, app.test_client()))

    def test_loopback_hosts_are_accepted(self) -> None:
        for server, _, client in self.servers:
            for host in ('127.0.0.1', '127.0.0.1:6060', 'localhost', 'localhost:6060',
                         'LOCALHOST:6060', '::1', '[::1]', '[::1]:6060'):
                with self.subTest(server=server.__name__, host=host):
                    response = client.get('/api/health', headers={'Host': host})
                    self.assertEqual(response.status_code, 200)

    def test_other_hosts_are_rejected_before_activity_update(self) -> None:
        for server, app, client in self.servers:
            for host in ('evil.example:6060', '127.0.0.1.evil.example', 'localhost.evil.example',
                         '192.168.1.1', '[::2]:6060', '::1:6060', 'evil@localhost:6060', ''):
                with self.subTest(server=server.__name__, host=host):
                    app.config['LAST_REQUEST_TIME'] = 0
                    response = client.get('/api/health', headers={'Host': host})
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(app.config['LAST_REQUEST_TIME'], 0)

    def test_loopback_origins_and_missing_origin_are_accepted(self) -> None:
        for server, _, client in self.servers:
            for origin in (None, 'http://127.0.0.1:6060', 'http://localhost',
                           'https://LOCALHOST:6060', 'http://[::1]', 'http://[::1]:6060'):
                with self.subTest(server=server.__name__, origin=origin):
                    headers = {} if origin is None else {'Origin': origin}
                    self.assertEqual(client.get('/api/health', headers=headers).status_code, 200)

    def test_other_or_malformed_origins_are_rejected(self) -> None:
        for server, app, client in self.servers:
            for origin in ('http://evil.example', 'http://127.0.0.1.evil.example',
                           'http://localhost@evil.example', 'http://[::2]',
                           'http://[::1', 'null', ''):
                with self.subTest(server=server.__name__, origin=origin):
                    app.config['LAST_REQUEST_TIME'] = 0
                    response = client.get('/api/health', headers={'Origin': origin})
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(app.config['LAST_REQUEST_TIME'], 0)

    def test_internal_readiness_url_is_accepted(self) -> None:
        for server, _, client in self.servers:
            with self.subTest(server=server.__name__):
                response = client.get(server._server_url(6060, '/api/health'))
                self.assertEqual(response.status_code, 200)

    def test_guard_also_blocks_shutdown_posts(self) -> None:
        for server, _, client in self.servers:
            for headers in ({'Host': 'evil.example:6060'}, {'Origin': 'http://evil.example'}):
                with self.subTest(server=server.__name__, headers=headers):
                    with patch.object(server.threading.Thread, 'start') as start:
                        response = client.post('/api/shutdown', json={}, headers=headers)
                    self.assertEqual(response.status_code, 403)
                    start.assert_not_called()
