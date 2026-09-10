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
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import source_to_md  # noqa: E402

WEB_BACKEND_DIR = SCRIPTS_DIR / 'source_to_md'
if str(WEB_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_BACKEND_DIR))

import web_to_md  # noqa: E402


PUBLIC_URL = 'https://8.8.8.8/page'


class PublicUrlTests(unittest.TestCase):
    def setUp(self) -> None:
        dns_patch = patch.object(web_to_md.socket, 'getaddrinfo', side_effect=AssertionError('Unexpected DNS'))
        dns_patch.start()
        self.addCleanup(dns_patch.stop)

    def test_non_public_literal_addresses_are_rejected_without_dns(self) -> None:
        for host in ('169.254.169.254', '10.0.0.1', '172.16.0.1', '192.168.0.1',
                     '127.0.0.1', '0.0.0.0', '[::1]', '[::]', '[fe80::1]', '[fc00::1]',
                     '[::ffff:127.0.0.1]'):
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, 'non-public'):
                web_to_md._validate_public_url(f'http://{host}/')

    def test_public_literal_addresses_are_accepted_without_dns(self) -> None:
        for host in ('8.8.8.8', '[2001:4860:4860::8888]'):
            with self.subTest(host=host):
                self.assertIsNone(web_to_md._validate_public_url(f'https://{host}/'))

    def test_non_http_or_malformed_urls_are_rejected(self) -> None:
        for url in ('file:///etc/passwd', 'ftp://8.8.8.8/', 'data:text/plain,hello',
                    '//8.8.8.8/', 'http:///missing-host', 'http://[::1'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                web_to_md._validate_public_url(url)

    def test_every_dns_answer_must_be_public(self) -> None:
        public = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 0))
        private = (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('fe80::1', 0, 0, 0))
        with patch.object(web_to_md.socket, 'getaddrinfo', return_value=[public]) as resolve:
            self.assertIsNone(web_to_md._validate_public_url('https://page.example/'))
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
                    patch.object(web_to_md.requests, 'get', backend.get):
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
                        patch.object(web_to_md.requests, 'get', backend.get):
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
                    patch.object(web_to_md.requests, 'get', side_effect=responses), \
                    patch.object(web_to_md.os, 'makedirs'), \
                    patch('builtins.open') as write, redirect_stdout(io.StringIO()):
                result = web_to_md.process_url(PUBLIC_URL, '/unused/result.md')
                self.assertFalse(result[0])
                self.assertIn('non-public', result[2])
                write.assert_not_called()
                blocked.close.assert_called_once_with()


class TlsVerificationTests(unittest.TestCase):
    def test_both_http_backends_verify_by_default_and_honor_explicit_opt_out(self) -> None:
        for use_curl in (False, True):
            for kwargs, expected in (({}, True), ({'verify': False}, False)):
                backend = Mock()
                backend.get.return_value = Mock(url=PUBLIC_URL)
                with self.subTest(curl=use_curl, kwargs=kwargs), \
                        patch.object(web_to_md, 'curl_requests', backend if use_curl else None), \
                        patch.object(web_to_md.requests, 'get', backend.get):
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
