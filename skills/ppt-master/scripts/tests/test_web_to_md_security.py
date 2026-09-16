#!/usr/bin/env python3
"""PPT Master - Web Conversion Security Tests

Check URL validation, TLS defaults, and failure paths with in-memory responses.

Usage:
    python3 -m unittest discover -s skills/ppt-master/scripts/tests -p test_web_to_md_security.py

Dependencies:
    requests, beautifulsoup4
"""

import io
import socket
import ssl
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from urllib3.util.ssl_ import resolve_cert_reqs

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import source_to_md  # noqa: E402

WEB_BACKEND_DIR = SCRIPTS_DIR / 'source_to_md'
if str(WEB_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_BACKEND_DIR))

import web_to_md  # noqa: E402


PUBLIC_URL = 'https://8.8.8.8/page'


class _CurlHeaders(web_to_md.requests.structures.CaseInsensitiveDict):
    def get_list(self, name):
        return [self[name]] if name in self else []


@contextmanager
def _offline_transport(routes, use_curl):
    """Replace transmission while retaining requests' preparation and redirects."""
    visited = []
    responses = []

    def respond(url):
        visited.append(url)
        status, headers = routes[url]
        response = web_to_md.requests.Response()
        response.url = url
        response.status_code = status
        response.headers = _CurlHeaders(headers)
        response._content = b'public content'
        response.raw = io.BytesIO(response._content)
        responses.append(response)
        return response

    def send(adapter, request, **kwargs):
        response = respond(request.url)
        response.request = request
        return response

    backend = SimpleNamespace(get=Mock(side_effect=lambda url, **kwargs: respond(url)))
    with patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
            patch.object(web_to_md.requests.adapters.HTTPAdapter, 'send', send):
        yield visited, responses


def _dns_answer(address, port=0):
    family = socket.AF_INET6 if ':' in address else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, '', (address, port))]


def _http_socket():
    """Provide a socket substitute to exercise the real urllib3 connection path."""
    sock = Mock()
    sock.makefile.side_effect = lambda *args, **kwargs: io.BytesIO(
        b'HTTP/1.1 200 OK\r\nContent-Length: 6\r\nConnection: close\r\n\r\npublic'
    )
    return sock


class PublicUrlTests(unittest.TestCase):
    def setUp(self) -> None:
        dns_patch = patch.object(web_to_md.socket, 'getaddrinfo', side_effect=AssertionError('Unexpected DNS'))
        dns_patch.start()
        self.addCleanup(dns_patch.stop)
        options = patch.object(web_to_md, 'CurlOpt', SimpleNamespace(RESOLVE=10203, PROXY=10004))
        options.start()
        self.addCleanup(options.stop)

    def test_non_public_literal_addresses_are_rejected_without_dns(self) -> None:
        for host in ('169.254.169.254', '10.0.0.1', '172.16.0.1', '192.168.0.1',
                     '127.0.0.1', '0.0.0.0', '[::1]', '[::]', '[fe80::1]', '[fc00::1]',
                     '[::ffff:127.0.0.1]'):
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, 'non-public'):
                web_to_md._validate_public_url(f'http://{host}/')

    def test_public_literal_addresses_are_accepted_without_dns(self) -> None:
        for host in ('8.8.8.8', '[2001:4860:4860::8888]'):
            with self.subTest(host=host):
                url, addresses = web_to_md._validate_public_url(f'https://{host}/')
                self.assertEqual(url, f'https://{host}/')
                self.assertEqual([str(ip) for ip in addresses], [host.strip('[]')])

    def test_non_http_or_malformed_urls_are_rejected(self) -> None:
        for url in ('file:///etc/passwd', 'ftp://8.8.8.8/', 'data:text/plain,hello',
                    '//8.8.8.8/', 'http:///missing-host', 'http://[::1'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                web_to_md._validate_public_url(url)

    def test_every_dns_answer_must_be_public(self) -> None:
        public = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 0))
        private = (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('fe80::1', 0, 0, 0))
        with patch.object(web_to_md.socket, 'getaddrinfo', return_value=[public]) as resolve:
            url, addresses = web_to_md._validate_public_url('https://page.example/')
            self.assertEqual(url, 'https://page.example/')
            self.assertEqual([str(ip) for ip in addresses], ['8.8.8.8'])
            resolve.assert_called_once_with('page.example', None, type=socket.SOCK_STREAM)
        with patch.object(web_to_md.socket, 'getaddrinfo', return_value=[public, private]):
            with self.assertRaisesRegex(ValueError, 'non-public'):
                web_to_md._validate_public_url('https://page.example/')

    def test_dns_failure_or_empty_answers_fail_closed(self) -> None:
        with patch.object(web_to_md.socket, 'getaddrinfo', side_effect=socket.gaierror('unresolved')):
            with self.assertRaisesRegex(ValueError, 'Cannot validate URL hostname'):
                web_to_md._validate_public_url('https://page.example/')
        with patch.object(web_to_md.socket, 'getaddrinfo', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'Cannot resolve URL hostname'):
                web_to_md._validate_public_url('https://page.example/')

    def test_initial_url_is_checked_before_either_backend_fetches(self) -> None:
        for use_curl in (False, True):
            backend = Mock()
            with self.subTest(curl=use_curl), \
                    patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                    patch.object(web_to_md.requests.Session, 'get', backend.get):
                with self.assertRaisesRegex(ValueError, 'non-public'):
                    web_to_md._http_get('http://169.254.169.254/latest/meta-data/')
                backend.get.assert_not_called()

    def test_final_url_is_checked_and_response_closed_for_both_backends(self) -> None:
        for use_curl in (False, True):
            for final_url in ('http://10.0.0.1/private', 'file:///etc/passwd'):
                response = Mock(url=final_url)
                backend = Mock()
                backend.get.return_value = response
                with self.subTest(curl=use_curl, final_url=final_url), \
                        patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                        patch.object(web_to_md.requests.Session, 'get', backend.get):
                    with self.assertRaises(ValueError):
                        web_to_md._http_get(PUBLIC_URL)
                    response.close.assert_called_once_with()

    def test_unsafe_page_or_image_redirect_does_not_write_output(self) -> None:
        page = Mock(
            url=PUBLIC_URL,
            content=b'<html><head><title>Page</title></head><body>'
                    b'<article><p>Content</p><img src="/image.png"></article></body></html>',
            headers={'Content-Type': 'text/html; charset=utf-8'},
        )
        for unsafe_image in (False, True):
            blocked = Mock(url='http://169.254.169.254/secret')
            responses = [page, blocked] if unsafe_image else [blocked]
            with self.subTest(image=unsafe_image), \
                    patch.object(web_to_md, 'curl_requests', None), \
                    patch.object(web_to_md.requests.Session, 'get', side_effect=responses), \
                    patch.object(web_to_md.os, 'makedirs'), \
                    patch('builtins.open') as write, redirect_stdout(io.StringIO()):
                result = web_to_md.process_url(PUBLIC_URL, '/unused/result.md')
                self.assertFalse(result[0])
                self.assertIn('non-public', result[2])
                write.assert_not_called()
                blocked.close.assert_called_once_with()


class TlsVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        options = patch.object(web_to_md, 'CurlOpt', SimpleNamespace(RESOLVE=10203, PROXY=10004))
        options.start()
        self.addCleanup(options.stop)

    def test_both_http_backends_verify_by_default_and_honor_explicit_opt_out(self) -> None:
        for use_curl in (False, True):
            for kwargs, expected in (({}, True), ({'verify': False}, False)):
                backend = Mock()
                backend.get.return_value = Mock(url=PUBLIC_URL)
                with self.subTest(curl=use_curl, kwargs=kwargs), \
                        patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                        patch.object(web_to_md.requests.Session, 'get', backend.get):
                    web_to_md._http_get(PUBLIC_URL, **kwargs)
                    self.assertIs(backend.get.call_args.kwargs['verify'], expected)
                    if use_curl:
                        self.assertEqual(backend.get.call_args.kwargs['impersonate'], web_to_md._CURL_IMPERSONATE)

    def test_pages_and_images_share_the_insecure_config(self) -> None:
        response = Mock(url=PUBLIC_URL, content=b'page', headers={'Content-Type': 'text/plain; charset=utf-8'})
        for insecure in (False, True):
            with self.subTest(insecure=insecure), patch.dict(web_to_md.CONFIG, insecure=insecure):
                with patch.object(web_to_md, '_http_get', return_value=response) as fetch:
                    web_to_md.fetch_url(PUBLIC_URL)
                    self.assertIs(fetch.call_args.kwargs['verify'], not insecure)
                content = web_to_md.BeautifulSoup('<img src="/image.png">', 'html.parser')
                with patch.object(web_to_md, '_http_get', side_effect=web_to_md._UnsafeUrlError('blocked')) as fetch, \
                        patch.object(web_to_md.os, 'makedirs'):
                    with self.assertRaises(web_to_md._UnsafeUrlError):
                        web_to_md.download_and_rewrite_images(content, PUBLIC_URL, '/unused/images', 'images')
                    self.assertIs(fetch.call_args.kwargs['verify'], not insecure)

    def test_cli_insecure_is_opt_in_and_warns(self) -> None:
        with patch.dict(web_to_md.CONFIG), \
                patch.object(web_to_md, 'process_url', return_value=(True, PUBLIC_URL, None, None)), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(web_to_md.main([PUBLIC_URL, '--insecure']), 0)
            self.assertIs(web_to_md.CONFIG['insecure'], True)
            self.assertIn('TLS certificate verification disabled', errors.getvalue())
            self.assertEqual(web_to_md.main([PUBLIC_URL]), 0)
            self.assertIs(web_to_md.CONFIG['insecure'], False)

    def test_dispatcher_forwards_insecure_to_web_backend(self) -> None:
        args, unknown = source_to_md.build_parser().parse_known_args([PUBLIC_URL, '--insecure'])
        with patch.object(source_to_md, 'run_backend', return_value=1) as run:
            self.assertEqual(source_to_md.dispatch_single(PUBLIC_URL, 'web', '/unused/result.md', args, unknown), 1)
        command, script_name = run.call_args.args
        self.assertEqual(script_name, 'web_to_md.py')
        self.assertEqual(command.count('--insecure'), 1)


class TransportBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        for guard in (
            patch.dict(web_to_md.CONFIG, allow_private_hosts=False),
            patch.object(web_to_md, 'CurlOpt', SimpleNamespace(RESOLVE=10203, PROXY=10004)),
            patch.object(web_to_md.socket, 'getaddrinfo', side_effect=AssertionError('Unexpected DNS')),
            patch.object(web_to_md.socket, 'socket', side_effect=AssertionError('Unexpected socket')),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    def test_ambiguous_urls_are_refused_before_either_transport_is_created(self) -> None:
        urls = (
            'http://127.0.0.1\\@example.com/',
            'http://8.8.8.8/path\\name',
            ' http://8.8.8.8/',
            'http://8.8.8.8/a b',
            'http://8.8.8.8/\tpath',
            'http://8.8.8.8/\r\npath',
            'http://8.8.8.8/\x00path',
            'http://8.8.8.8/\x7fpath',
            'http://8.8.8.8/\x85path',
            'http://%65xample.com/',
        )
        for use_curl in (False, True):
            for allow_private in (False, True):
                for url in urls:
                    backend = Mock()
                    with self.subTest(curl=use_curl, private=allow_private, url=url), \
                            patch.dict(web_to_md.CONFIG, allow_private_hosts=allow_private), \
                            patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                            patch.object(web_to_md.requests, 'Session') as session:
                        with self.assertRaises(web_to_md._UnsafeUrlError):
                            web_to_md._http_get(url)
                        backend.get.assert_not_called()
                        session.assert_not_called()
                        socket.socket.assert_not_called()

    def test_ambiguous_image_urls_are_refused_before_transport(self) -> None:
        for use_curl in (False, True):
            for src in ('http://127.0.0.1\\@example.com/', 'http://8.8.8.8/&#9;image.png'):
                content = web_to_md.BeautifulSoup(f'<img src="{src}">', 'html.parser')
                backend = Mock()
                with self.subTest(curl=use_curl, src=src), tempfile.TemporaryDirectory() as tmp, \
                        patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                        patch.object(web_to_md.requests, 'Session') as session:
                    with self.assertRaises(web_to_md._UnsafeUrlError):
                        web_to_md.download_and_rewrite_images(content, PUBLIC_URL, tmp, 'images')
                    self.assertEqual(list(Path(tmp).iterdir()), [])
                    backend.get.assert_not_called()
                    session.assert_not_called()
                    socket.socket.assert_not_called()

    def test_every_redirect_rejects_ambiguous_locations_even_with_private_opt_in(self) -> None:
        middle = 'https://8.8.8.8/middle'
        for use_curl in (False, True):
            for allow_private in (False, True):
                for location in ('http://127.0.0.1\\@example.com/', '/\tpath', 'http://%65xample.com/'):
                    routes = {PUBLIC_URL: (302, {'Location': middle}), middle: (302, {'Location': location})}
                    with self.subTest(curl=use_curl, private=allow_private, location=location), \
                            patch.dict(web_to_md.CONFIG, allow_private_hosts=allow_private), \
                            _offline_transport(routes, use_curl) as (visited, responses):
                        with self.assertRaises(web_to_md._UnsafeUrlError):
                            web_to_md._http_get(PUBLIC_URL)
                        self.assertEqual(visited, [PUBLIC_URL, middle])
                        self.assertTrue(responses[-1].raw.closed)
                        socket.socket.assert_not_called()

    def test_both_backends_send_the_prepared_url_on_every_public_hop(self) -> None:
        start = 'http://public.example/~start'
        final = 'http://public.example/~end'
        routes = {start: (302, {'Location': '/%7eend'}), final: (200, {})}
        for use_curl in (False, True):
            with self.subTest(curl=use_curl), \
                    patch.object(socket, 'getaddrinfo', return_value=_dns_answer('8.8.8.8')), \
                    _offline_transport(routes, use_curl) as (visited, _):
                response = web_to_md._http_get('HTTP://PUBLIC.EXAMPLE/%7estart')
                self.assertEqual(response.content, b'public content')
                self.assertEqual(visited, [start, final])

    def test_requests_rebinding_is_refused_before_socket_creation(self) -> None:
        for scheme in ('http', 'https'):
            for rebound in (_dns_answer('169.254.169.254'),
                            _dns_answer('8.8.8.8') + _dns_answer('169.254.169.254')):
                with self.subTest(scheme=scheme, rebound=rebound), \
                        patch.object(web_to_md, 'curl_requests', None), \
                        patch.object(socket, 'getaddrinfo', side_effect=[_dns_answer('8.8.8.8'), rebound]) as dns:
                    with self.assertRaisesRegex(web_to_md._UnsafeUrlError, 'non-public'):
                        web_to_md._http_get(f'{scheme}://rebind.example/')
                    self.assertEqual(dns.call_count, 2)
                    socket.socket.assert_not_called()

    def test_requests_rebinding_on_a_redirect_is_refused_before_its_socket(self) -> None:
        sock = _http_socket()
        sock.makefile.side_effect = lambda *args: io.BytesIO(
            b'HTTP/1.1 302 Found\r\nLocation: http://rebind.example/private\r\n'
            b'Content-Length: 0\r\nConnection: close\r\n\r\n'
        )
        with patch.object(web_to_md, 'curl_requests', None), \
                patch.object(socket, 'socket', return_value=sock) as create_socket, \
                patch.object(socket, 'getaddrinfo', side_effect=[
                    _dns_answer('8.8.8.8'), _dns_answer('169.254.169.254'),
                ]) as dns:
            with self.assertRaisesRegex(web_to_md._UnsafeUrlError, 'non-public'):
                web_to_md._http_get('http://8.8.8.8/start')
            self.assertEqual(dns.call_count, 2)
            create_socket.assert_called_once()
            sock.connect.assert_called_once_with(('8.8.8.8', 80))

    def test_curl_rebinding_on_a_redirect_is_refused_before_transport(self) -> None:
        routes = {PUBLIC_URL: (302, {'Location': 'http://rebind.example/private'})}
        with _offline_transport(routes, True) as (visited, responses), \
                patch.object(socket, 'getaddrinfo', side_effect=[
                    _dns_answer('8.8.8.8'), _dns_answer('169.254.169.254'),
                ]) as dns:
            with self.assertRaisesRegex(web_to_md._UnsafeUrlError, 'non-public'):
                web_to_md._http_get(PUBLIC_URL)
            self.assertEqual(dns.call_count, 2)
            self.assertEqual(visited, [PUBLIC_URL])
            self.assertTrue(responses[0].raw.closed)

    def test_requests_public_connections_keep_host_and_tls_verification(self) -> None:
        for scheme in ('http', 'https'):
            sock = _http_socket()
            with self.subTest(scheme=scheme), patch.object(web_to_md, 'curl_requests', None), \
                    patch.object(socket, 'getaddrinfo', return_value=_dns_answer('8.8.8.8')), \
                    patch.object(socket, 'socket', return_value=sock), \
                    patch.dict(web_to_md.os.environ, HTTP_PROXY='http://127.0.0.1:9',
                               HTTPS_PROXY='http://127.0.0.1:9', ALL_PROXY='http://127.0.0.1:9'), \
                    patch('urllib3.connection._ssl_wrap_socket_and_match_hostname',
                          return_value=SimpleNamespace(socket=sock, is_verified=True)) as tls:
                response = web_to_md._http_get(f'{scheme}://public.example/')
                self.assertEqual(response.content, b'public')
                sock.connect.assert_called_once_with(('8.8.8.8', 443 if scheme == 'https' else 80))
                self.assertIn(b'Host: public.example\r\n', sock.sendall.call_args.args[0])
                if scheme == 'https':
                    self.assertEqual(tls.call_args.kwargs['server_hostname'], 'public.example')
                    self.assertEqual(resolve_cert_reqs(tls.call_args.kwargs['cert_reqs']), ssl.CERT_REQUIRED)
                    self.assertIsNone(tls.call_args.kwargs['assert_hostname'])

    def test_requests_connects_only_to_validated_ipv4_and_ipv6_answers(self) -> None:
        first, second = _http_socket(), _http_socket()
        first.connect.side_effect = OSError('unreachable')
        answers = _dns_answer('8.8.8.8') + _dns_answer('2001:4860:4860::8888')
        with patch.object(web_to_md, 'curl_requests', None), \
                patch.object(socket, 'getaddrinfo', return_value=answers), \
                patch.object(socket, 'socket', side_effect=[first, second]):
            response = web_to_md._http_get('http://public.example:8080/')
            self.assertEqual(response.content, b'public')
            first.connect.assert_called_once_with(('8.8.8.8', 8080))
            first.close.assert_called_once()
            second.connect.assert_called_once_with(('2001:4860:4860::8888', 8080))

    def test_curl_pins_public_addresses_despite_rebinding_at_transport(self) -> None:
        connected = []

        def get(url, **kwargs):
            # The answer available at connect time has changed. A pinned backend
            # uses RESOLVE instead of consulting it for its destination.
            rebound = socket.getaddrinfo('mp.weixin.qq.com', None, type=socket.SOCK_STREAM)
            self.assertEqual(rebound[0][4][0], '169.254.169.254')
            options = kwargs['curl_options']
            self.assertEqual(options[web_to_md.CurlOpt.RESOLVE], ['mp.weixin.qq.com:443:8.8.8.8'])
            connected.extend(options[web_to_md.CurlOpt.RESOLVE][0].split(':')[2:])
            self.assertEqual(options[web_to_md.CurlOpt.PROXY], '')
            self.assertEqual(kwargs['impersonate'], web_to_md._CURL_IMPERSONATE)
            self.assertIs(kwargs['allow_redirects'], False)
            return Mock(url=url, status_code=200)

        with patch.object(web_to_md, 'curl_requests', SimpleNamespace(get=get)), \
                patch.object(socket, 'getaddrinfo', side_effect=[
                    _dns_answer('8.8.8.8'), _dns_answer('169.254.169.254'), _dns_answer('8.8.8.8'),
                ]):
            web_to_md._http_get('https://mp.weixin.qq.com/')
        self.assertEqual(connected, ['8.8.8.8'])

    def test_curl_recomputes_pins_for_each_redirect_and_explicit_port(self) -> None:
        calls = []
        start = 'https://mp.weixin.qq.com/start'
        final = 'https://images.example:8443/photo'

        def get(url, **kwargs):
            calls.append((url, kwargs['curl_options'][web_to_md.CurlOpt.RESOLVE]))
            headers = _CurlHeaders({'Location': final}) if url == start else _CurlHeaders()
            return Mock(url=url, status_code=302 if url == start else 200, headers=headers)

        def resolve(host, *args, **kwargs):
            return _dns_answer('8.8.8.8' if host == 'mp.weixin.qq.com' else '2001:4860:4860::8888')

        with patch.object(web_to_md, 'curl_requests', SimpleNamespace(get=get)), \
                patch.object(socket, 'getaddrinfo', side_effect=resolve):
            web_to_md._http_get(start, stream=True)
        self.assertEqual(calls, [
            (start, ['mp.weixin.qq.com:443:8.8.8.8']),
            (final, ['images.example:8443:[2001:4860:4860::8888]']),
        ])

    def test_private_opt_in_uses_the_regular_requests_connection(self) -> None:
        sock = _http_socket()
        with patch.dict(web_to_md.CONFIG, allow_private_hosts=True), \
                patch.dict(web_to_md.os.environ, {'NO_PROXY': '*', 'no_proxy': '*'}), \
                patch.object(web_to_md, 'curl_requests', None), \
                patch.object(socket, 'getaddrinfo', return_value=_dns_answer('127.0.0.1', 80)), \
                patch.object(socket, 'socket', return_value=sock):
            self.assertEqual(web_to_md._http_get('http://127.0.0.1/').content, b'public')
            sock.connect.assert_called_once_with(('127.0.0.1', 80))

    def test_installed_curl_api_applies_resolve_without_network(self) -> None:
        try:
            from curl_cffi import Curl, CurlOpt, requests as curl_requests
        except ImportError:
            self.skipTest('optional curl_cffi is not installed')
        applied = {}
        original_setopt = Curl.setopt

        def setopt(curl, option, value):
            applied[option] = value
            return original_setopt(curl, option, value)

        url = 'https://mp.weixin.qq.com/'
        response = Mock(url=url, status_code=200)
        with patch.object(web_to_md, 'CurlOpt', CurlOpt), \
                patch.object(web_to_md, 'curl_requests', curl_requests), \
                patch.object(socket, 'getaddrinfo', return_value=_dns_answer('8.8.8.8')), \
                patch.object(Curl, 'setopt', setopt), patch.object(Curl, 'perform') as perform, \
                patch.object(curl_requests.Session, '_parse_response', return_value=response):
            self.assertIs(web_to_md._http_get(url), response)
            perform.assert_called_once()
        self.assertEqual(applied[CurlOpt.RESOLVE], ['mp.weixin.qq.com:443:8.8.8.8'])
        self.assertEqual(applied[CurlOpt.PROXY], '')
        socket.socket.assert_not_called()


class PreparedUrlEdgeTests(unittest.TestCase):
    """The parser-agreement check compares the prepared URL, and HTML padding is not ambiguity."""

    def test_idn_hosts_are_prepared_to_punycode_not_refused(self) -> None:
        prepared = web_to_md._prepare_url("https://例子.测试/路径")
        self.assertTrue(prepared.startswith("https://xn--fsqu00a.xn--0zwm56d/"), prepared)

    def test_padded_image_src_is_stripped_before_the_character_check(self) -> None:
        soup = web_to_md.BeautifulSoup('<img src=" https://8.8.8.8/a.png ">', "html.parser")
        self.assertEqual(
            web_to_md.resolve_content_image_url(soup.img, "https://8.8.8.8/"), "https://8.8.8.8/a.png"
        )
        soup = web_to_md.BeautifulSoup('<img src="https://8.8.8.8/a b.png">', "html.parser")
        with self.assertRaises(web_to_md._UnsafeUrlError):
            web_to_md.resolve_content_image_url(soup.img, "https://8.8.8.8/")
