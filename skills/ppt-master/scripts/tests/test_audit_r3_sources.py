#!/usr/bin/env python3
"""PPT Master - Third-Round Source Regression Tests

Exercise HTTP boundaries, archived source imports, and DOCX conversion offline.

Usage:
    python3 -m unittest discover -s skills/ppt-master/scripts/tests -p test_audit_r3_sources.py

Dependencies:
    requests, beautifulsoup4, mammoth, PyMuPDF
"""

from __future__ import annotations

import contextlib
import io
import json
import socket
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
BACKEND_DIR = SCRIPTS_DIR / "source_to_md"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import doc_to_md  # noqa: E402
import web_to_md  # noqa: E402
from _conversion_profile import profile_path_for  # noqa: E402
from project_management import cli as project_cli  # noqa: E402


@contextlib.contextmanager
def _memory_transport(routes):
    """Keep requests' redirect engine and replace only adapter transmission."""
    visited = []
    responses = []

    def send(adapter, request, **kwargs):
        visited.append(request)
        status, headers, content = routes[request.url]
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = status
        response.headers.update(headers)
        response.raw = io.BytesIO(content)
        response._content = content
        responses.append(response)
        return response

    with patch.object(requests.adapters.HTTPAdapter, "send", send):
        yield visited, responses


class SourceHttpSecurityTests(unittest.TestCase):
    START = "http://8.8.8.8/start"
    PRIVATE = "http://127.0.0.1/side-effect"
    FINAL = "http://8.8.8.8/finished"
    NON_PUBLIC = (
        "127.0.0.1", "10.0.0.1", "100.64.0.0", "100.64.0.1",
        "100.127.255.254", "100.127.255.255", "224.0.0.0", "239.255.255.255",
        "0.0.0.1", "0.255.255.255", "240.0.0.0", "255.255.255.255",
        "[ff00::]", "[ff02::1]", "[ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff]",
        "[fc00::1]", "[fdff:ffff::1]", "[fe80::1]", "[::]", "[::1]",
        "[::ffff:100.64.0.1]", "[::ffff:224.0.0.1]", "[::ffff:240.0.0.1]",
    )

    def setUp(self) -> None:
        for guard in (
            patch.dict(web_to_md.CONFIG, allow_private_hosts=False),
            patch.object(web_to_md, "curl_requests", None),
            patch.object(socket, "getaddrinfo", side_effect=AssertionError("Unexpected DNS")),
            patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network")),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    def test_a01_private_redirect_never_enters_requests_transport(self) -> None:
        for return_public in (False, True):
            routes = {
                self.START: (302, {"Location": self.PRIVATE}, b""),
                self.PRIVATE: (302, {"Location": self.FINAL}, b"") if return_public else (200, {}, b""),
                self.FINAL: (200, {}, b"ok"),
            }
            with self.subTest(return_public=return_public), _memory_transport(routes) as (visited, responses):
                with self.assertRaisesRegex(ValueError, "Refusing non-public URL target"):
                    web_to_md._http_get(self.START)
                self.assertEqual([request.url for request in visited], [self.START])
                self.assertTrue(responses[0].raw.closed)

    def test_a01_public_redirects_keep_relative_targets_and_response_history(self) -> None:
        for status in (301, 302, 303, 307, 308):
            routes = {
                self.START: (status, {"Location": "/finished"}, b""),
                self.FINAL: (200, {}, b"ok"),
            }
            with self.subTest(status=status), _memory_transport(routes) as (visited, _):
                response = web_to_md._http_get(self.START)
                self.assertEqual(response.url, self.FINAL)
                self.assertEqual(response.content, b"ok")
                self.assertEqual([entry.url for entry in response.history], [self.START])
                self.assertEqual(len(visited), 2)

    def test_a01_private_opt_in_preserves_redirect_chain(self) -> None:
        routes = {
            self.START: (302, {"Location": self.PRIVATE}, b""),
            self.PRIVATE: (302, {"Location": self.FINAL}, b""),
            self.FINAL: (200, {}, b"ok"),
        }
        with patch.dict(web_to_md.CONFIG, allow_private_hosts=True), _memory_transport(routes) as (visited, _):
            response = web_to_md._http_get(self.START)
        self.assertEqual([request.url for request in visited], [self.START, self.PRIVATE, self.FINAL])
        self.assertEqual(response.url, self.FINAL)

    def test_a01_requests_redirect_limit_remains_enforced(self) -> None:
        routes = {self.START: (302, {"Location": self.START}, b"")}
        with _memory_transport(routes) as (visited, _):
            with self.assertRaises(requests.exceptions.TooManyRedirects):
                web_to_md._http_get(self.START)
        self.assertEqual(len(visited), 31)

    def test_a01_refused_page_redirect_returns_nonzero_without_output(self) -> None:
        routes = {self.START: (302, {"Location": self.PRIVATE}, b"")}
        with tempfile.TemporaryDirectory() as tmp, _memory_transport(routes), \
                contextlib.redirect_stdout(io.StringIO()) as log, contextlib.redirect_stderr(io.StringIO()):
            output = Path(tmp) / "page.md"
            rc = web_to_md.main([self.START, "-o", str(output)])
            self.assertEqual(rc, 1)
            self.assertIn("non-public", log.getvalue())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_a17_non_public_literals_are_rejected_before_transport(self) -> None:
        for use_curl in (False, True):
            for host in self.NON_PUBLIC:
                backend = Mock()
                with self.subTest(host=host, curl=use_curl), \
                        patch.object(web_to_md, "curl_requests", backend if use_curl else None), \
                        patch.object(requests, "get", backend.get):
                    with self.assertRaisesRegex(ValueError, "non-public"):
                        web_to_md._http_get(f"http://{host}/")
                    backend.get.assert_not_called()

    def test_a17_every_dns_answer_must_be_public_before_transport(self) -> None:
        public = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))
        for host in self.NON_PUBLIC:
            address = host.strip("[]")
            family = socket.AF_INET6 if ":" in address else socket.AF_INET
            non_public = (family, socket.SOCK_STREAM, 6, "", (address, 0))
            with self.subTest(host=host), \
                    patch.object(socket, "getaddrinfo", return_value=[public, non_public]), \
                    patch.object(requests, "get") as transport:
                with self.assertRaisesRegex(ValueError, "non-public"):
                    web_to_md._http_get("https://source.example/")
                transport.assert_not_called()

    def test_a17_public_addresses_and_cgnat_neighbors_still_reach_transport(self) -> None:
        for host in ("8.8.8.8", "100.63.255.255", "100.128.0.0", "[2001:4860:4860::8888]"):
            url = f"http://{host}/"
            with self.subTest(host=host), _memory_transport({url: (200, {}, b"ok")}) as (visited, _):
                self.assertEqual(web_to_md._http_get(url).content, b"ok")
                self.assertEqual(len(visited), 1)

    def test_a17_private_opt_in_keeps_literal_targets_available(self) -> None:
        with patch.dict(web_to_md.CONFIG, allow_private_hosts=True):
            for host in self.NON_PUBLIC:
                with self.subTest(host=host):
                    url = f"http://{host}/"
                    response = Mock(url=url)
                    with patch.object(requests, "get", return_value=response) as transport:
                        self.assertIs(web_to_md._http_get(url), response)
                        transport.assert_called_once()


class RemoteDocumentRedirectTests(unittest.TestCase):
    def _convert(self, root: Path, body: bytes, suffix: str, content_type: str):
        start = "http://8.8.8.8/download?id=123"
        final = f"http://8.8.8.8/report{suffix}"
        routes = {
            start: (302, {"Location": final}, b""),
            final: (200, {"Content-Type": content_type}, body),
        }
        output = root / "converted.md"
        with patch.object(web_to_md, "curl_requests", None), \
                patch.dict(web_to_md.CONFIG, allow_private_hosts=False), \
                patch.object(socket, "getaddrinfo", side_effect=AssertionError("Unexpected DNS")), \
                patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network")), \
                _memory_transport(routes) as (visited, _), contextlib.redirect_stdout(io.StringIO()):
            result = web_to_md.process_url(start, str(output), download_images=False)
        self.assertTrue(result[0], result)
        self.assertEqual([request.url for request in visited], [start, final])
        profile = json.loads(profile_path_for(output).read_text(encoding="utf-8"))
        self.assertEqual(profile["source"]["url"], start)
        return output, profile

    def test_a05_redirected_octet_stream_docx_uses_document_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = DocxSourceRegressionTests()._docx(root)
            body = source.read_bytes()
            output, profile = self._convert(root, body, ".docx", "application/octet-stream")
            self.assertIn("Source data", output.read_text(encoding="utf-8"))
            self.assertIn("| 2026 | 54321 |", output.read_text(encoding="utf-8"))
            self.assertEqual(output.with_suffix(".docx").read_bytes(), body)
            self.assertEqual(profile["converter"], "doc_to_md.py")

    def test_a05_redirected_pdf_magic_still_uses_pdf_backend(self) -> None:
        import fitz

        with tempfile.TemporaryDirectory() as tmp, fitz.open() as document:
            page = document.new_page()
            page.insert_text((72, 72), "Expected revenue 54321")
            body = document.tobytes()
            output, profile = self._convert(Path(tmp), body, "", "application/octet-stream")
            self.assertIn("Expected revenue 54321", output.read_text(encoding="utf-8"))
            self.assertEqual(output.with_suffix(".pdf").read_bytes(), body)
            self.assertEqual(profile["converter"], "pdf_to_md.py")


class DocxSourceRegressionTests(unittest.TestCase):
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
    PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
    CHART = (
        f'<c:chartSpace xmlns:c="{C}"><c:chart><c:plotArea><c:barChart>'
        '<c:barDir val="col"/><c:grouping val="clustered"/>'
        '<c:ser><c:idx val="0"/><c:order val="0"/>'
        '<c:tx><c:v>Revenue</c:v></c:tx>'
        '<c:cat><c:strRef><c:f>Sheet1!$A$2</c:f><c:strCache><c:ptCount val="1"/>'
        '<c:pt idx="0"><c:v>2026</c:v></c:pt></c:strCache></c:strRef></c:cat>'
        '<c:val><c:numRef><c:f>Sheet1!$B$2</c:f><c:numCache><c:ptCount val="1"/>'
        '<c:pt idx="0"><c:v>54321</c:v></c:pt></c:numCache></c:numRef></c:val>'
        '</c:ser></c:barChart></c:plotArea></c:chart></c:chartSpace>'
    )

    def _docx(
        self, root: Path, *, note_type: str | None = None,
        chart_target: str = "charts/chart1.xml", include_chart: bool = True,
    ) -> Path:
        note_attr = f' w:type="{note_type}"' if note_type is not None else ""
        parts = {
            "[Content_Types].xml": (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" '
                'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
                'officedocument.wordprocessingml.document.main+xml"/>'
                '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-'
                'officedocument.wordprocessingml.footnotes+xml"/>'
                '<Override PartName="/word/charts/chart1.xml" ContentType="application/vnd.openxmlformats-'
                'officedocument.drawingml.chart+xml"/></Types>'
            ),
            "_rels/.rels": (
                f'<Relationships xmlns="{self.PKG}"><Relationship Id="document" '
                f'Type="{self.R}/officeDocument" Target="word/document.xml"/></Relationships>'
            ),
            "word/document.xml": (
                f'<w:document xmlns:w="{self.W}" xmlns:r="{self.R}" xmlns:c="{self.C}" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
                '<w:body><w:p><w:r><w:t>Source data</w:t></w:r></w:p>'
                '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Measure</w:t></w:r></w:p></w:tc></w:tr>'
                '<w:tr><w:tc><w:p><w:r><w:t>Amount</w:t></w:r>'
                '<w:r><w:footnoteReference w:id="2"/></w:r></w:p></w:tc></w:tr></w:tbl>'
                '<w:p><w:r><w:t>Chart follows</w:t></w:r>'
                '<w:r><w:drawing><wp:inline><wp:extent cx="4000000" cy="2500000"/>'
                '<wp:docPr id="1" name="Revenue"/><a:graphic>'
                f'<a:graphicData uri="{self.C}"><c:chart r:id="chart"/></a:graphicData>'
                '</a:graphic></wp:inline></w:drawing></w:r></w:p>'
                '</w:body></w:document>'
            ),
            "word/_rels/document.xml.rels": (
                f'<Relationships xmlns="{self.PKG}"><Relationship Id="notes" '
                f'Type="{self.R}/footnotes" Target="footnotes.xml"/>'
                f'<Relationship Id="chart" Type="{self.R}/chart" Target="{chart_target}"/>'
                '</Relationships>'
            ),
            "word/footnotes.xml": (
                f'<w:footnotes xmlns:w="{self.W}"><w:footnote w:id="2"{note_attr}>'
                '<w:p><w:r><w:t>Amount excludes tax.</w:t></w:r></w:p></w:footnote></w:footnotes>'
            ),
        }
        if include_chart:
            parts["word/charts/chart1.xml"] = self.CHART
        source = root / "report.docx"
        with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as package:
            for name, contents in parts.items():
                package.writestr(name, contents)
        return source

    def _convert(self, source: Path) -> tuple[str, list[str]]:
        output = source.with_suffix(".md")
        with contextlib.redirect_stdout(io.StringIO()):
            markdown = doc_to_md.convert_to_markdown(str(source), str(output))
        self.assertEqual(output.read_text(encoding="utf-8"), markdown)
        profile = json.loads(profile_path_for(output).read_text(encoding="utf-8"))
        return markdown, profile["warnings"]

    def test_a03_normal_and_omitted_footnote_types_preserve_body(self) -> None:
        outputs = []
        for note_type in (None, "normal"):
            with self.subTest(note_type=note_type), tempfile.TemporaryDirectory() as tmp:
                markdown, warnings = self._convert(self._docx(Path(tmp), note_type=note_type))
                self.assertIn("Amount[^2]", markdown)
                self.assertIn("[^2]: Amount excludes tax.", markdown)
                self.assertEqual(warnings, [])
                outputs.append(markdown)
        self.assertEqual(outputs[0], outputs[1])

    def test_a03_separator_footnote_types_are_not_body(self) -> None:
        for note_type in ("separator", "continuationSeparator", "continuationNotice"):
            with self.subTest(note_type=note_type), tempfile.TemporaryDirectory() as tmp:
                markdown, warnings = self._convert(self._docx(Path(tmp), note_type=note_type))
                self.assertNotIn("Amount excludes tax.", markdown)
                self.assertEqual(warnings, [])

    def test_a04_absolute_and_relative_chart_targets_preserve_data(self) -> None:
        outputs = []
        for target in ("charts/chart1.xml", "/word/charts/chart1.xml"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                markdown, warnings = self._convert(self._docx(Path(tmp), chart_target=target))
                self.assertIn("| 2026 | 54321 |", markdown)
                self.assertEqual(warnings, [])
                outputs.append(markdown)
        self.assertEqual(outputs[0], outputs[1])

    def test_a04_missing_chart_part_keeps_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            markdown, warnings = self._convert(self._docx(Path(tmp), include_chart=False))
        self.assertIn("Chart 1 — data unavailable (KeyError)", markdown)
        self.assertEqual(warnings, ["Chart 1 (word/charts/chart1.xml): chart data unavailable"])


class ArchivedProjectImportTests(unittest.TestCase):
    def _assert_import_behavior(
        self,
        relative: str,
        *,
        initialized: bool,
        preserved: bool,
        quick_generate: bool = False,
        move: bool = False,
        copy: bool = False,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            projects.mkdir()
            # The shared projects README must not turn scratch into a project.
            (projects / "README.md").write_text("# Projects\n", encoding="utf-8")
            manager = project_cli.ProjectManager(base_dir=projects)
            with contextlib.redirect_stdout(io.StringIO()):
                target = Path(manager.init_project("new_project", quick_generate=True))
                if initialized:
                    old = Path(manager.init_project(
                        "old_project",
                        base_dir=str(projects / relative),
                        quick_generate=quick_generate,
                    ))
                    source_dir = old / "sources" / "nested"
                else:
                    source_dir = projects / relative
            source_dir.mkdir(parents=True, exist_ok=True)
            source = source_dir / "source.md"
            content = "# Source\n\nKeep the original project intact.\n"
            source.write_text(content, encoding="utf-8")
            log = io.StringIO()
            with patch.object(project_cli, "PROJECTS_ROOT", projects), contextlib.redirect_stderr(log):
                result = manager.import_sources(str(target), [str(source)], move=move, copy=copy)
            self.assertEqual(result["skipped"], [])
            self.assertEqual(len(result["markdown"]), 1)
            self.assertEqual(Path(result["markdown"][0]).read_text(encoding="utf-8"), content)
            self.assertEqual(source.exists(), preserved)
            if initialized and not move and not copy:
                self.assertIn("belongs to another project; copied", log.getvalue())

    def test_initialized_projects_copy_sources_by_default(self) -> None:
        for relative in ("", "archive/2026-09"):
            for quick_generate in (False, True):
                with self.subTest(relative=relative, quick_generate=quick_generate):
                    self._assert_import_behavior(
                        relative,
                        initialized=True,
                        preserved=True,
                        quick_generate=quick_generate,
                    )

    def test_project_source_explicit_move_and_copy(self) -> None:
        for relative in ("", "archive/2026-09"):
            for move in (False, True):
                with self.subTest(relative=relative, move=move):
                    self._assert_import_behavior(
                        relative, initialized=True, preserved=not move, move=move, copy=not move,
                    )

    def test_scratch_sources_keep_default_move_and_explicit_copy(self) -> None:
        for relative in ("", "topic_web_sources", "archive/2026-09/topic_web_sources"):
            for copy in (False, True):
                with self.subTest(relative=relative, copy=copy):
                    self._assert_import_behavior(
                        relative, initialized=False, preserved=copy, copy=copy,
                    )


class _CurlHeaders(dict):
    """Represent repeated curl headers without importing optional curl_cffi."""

    def __init__(self, entries=()):
        self.entries = list(entries.items()) if isinstance(entries, dict) else list(entries)
        super().__init__(self.entries)

    def get_list(self, name):
        return [value for key, value in self.entries if key.lower() == name.lower()]


@contextlib.contextmanager
def _memory_curl(routes):
    visited = []
    responses = []

    def get(url, **kwargs):
        prepared = requests.Request("GET", url).prepare()
        cookies = kwargs["cookies"]
        visited.append({
            "url": url,
            "headers": dict(kwargs["headers"]),
            "cookie_header": requests.cookies.get_cookie_header(cookies, prepared) or "",
            "cookies": {(cookie.name, cookie.domain, cookie.domain_specified, cookie.path)
                        for cookie in cookies},
            "kwargs": kwargs,
        })
        status, headers = routes[url]
        response = Mock(url=url, status_code=status, headers=_CurlHeaders(headers))
        responses.append(response)
        return response

    backend = SimpleNamespace(get=Mock(side_effect=get))
    with patch.object(web_to_md, "curl_requests", backend):
        yield visited, responses


class CurlSourceRedirectTests(unittest.TestCase):
    START = "https://8.8.8.8/start"
    MIDDLE = "https://8.8.8.8/middle"
    PRIVATE = "http://127.0.0.1/side-effect"
    FINAL = "https://1.1.1.1/finished"

    def setUp(self) -> None:
        for guard in (
            patch.dict(web_to_md.CONFIG, allow_private_hosts=False),
            patch.object(socket, "getaddrinfo", side_effect=AssertionError("Unexpected DNS")),
            patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network")),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    def test_a01_curl_private_hops_never_enter_transport(self) -> None:
        for intermediate_public in (False, True):
            routes = {
                self.START: (302, {"Location": self.MIDDLE if intermediate_public else self.PRIVATE}),
                self.MIDDLE: (302, {"Location": self.PRIVATE}),
                self.PRIVATE: (302, {"Location": self.FINAL}),
                self.FINAL: (200, {}),
            }
            with self.subTest(intermediate_public=intermediate_public), _memory_curl(routes) as (visited, responses):
                with self.assertRaisesRegex(ValueError, "non-public"):
                    web_to_md._http_get(self.START)
                expected = [self.START, self.MIDDLE] if intermediate_public else [self.START]
                self.assertEqual([item["url"] for item in visited], expected)
                for response in responses:
                    response.close.assert_called_once_with()

    def test_a01_curl_follows_relative_public_redirects(self) -> None:
        for status in (301, 302, 303, 307, 308):
            routes = {self.START: (status, {"Location": "/middle"}), self.MIDDLE: (200, {})}
            with self.subTest(status=status), _memory_curl(routes) as (visited, responses):
                result = web_to_md._http_get(self.START, verify=False, stream=True)
                self.assertIs(result, responses[-1])
                self.assertEqual([item["url"] for item in visited], [self.START, self.MIDDLE])
                for item in visited:
                    self.assertIs(item["kwargs"]["allow_redirects"], False)
                    self.assertIs(item["kwargs"]["verify"], False)
                    self.assertIs(item["kwargs"]["stream"], True)
                responses[0].close.assert_called_once_with()
                responses[-1].close.assert_not_called()

    def test_a01_curl_retains_cookie_scope_and_strips_cross_host_credentials(self) -> None:
        scoped = "https://8.8.8.8/only/step"
        routes = {
            self.START: (302, [
                ("Location", "/only/step"),
                ("Set-Cookie", "host=kept; Path=/"),
                ("Set-Cookie", "domain=kept; Domain=8.8.8.8; Path=/"),
                ("Set-Cookie", "scoped=kept; Path=/only"),
                ("Set-Cookie", "expired=gone; Max-Age=0; Path=/"),
            ]),
            scoped: (302, {"Location": "/middle"}),
            self.MIDDLE: (302, {"Location": self.FINAL}),
            self.FINAL: (200, {}),
        }
        headers = {"Authorization": "secret", "Cookie": "explicit=secret", "User-Agent": "test"}
        with _memory_curl(routes) as (visited, _):
            web_to_md._http_get(self.START, headers=headers)
        self.assertIn("host=kept", visited[1]["cookie_header"])
        self.assertIn("domain=kept", visited[1]["cookie_header"])
        self.assertIn("scoped=kept", visited[1]["cookie_header"])
        self.assertNotIn("expired=", visited[1]["cookie_header"])
        self.assertIn(("host", "8.8.8.8", False, "/"), visited[1]["cookies"])
        self.assertIn(("domain", ".8.8.8.8", True, "/"), visited[1]["cookies"])
        self.assertNotIn("scoped=", visited[2]["cookie_header"])
        self.assertEqual(visited[2]["headers"]["Authorization"], "secret")
        self.assertEqual(visited[3]["cookie_header"], "")
        self.assertNotIn("Authorization", visited[3]["headers"])
        self.assertNotIn("Cookie", visited[3]["headers"])
        self.assertEqual(visited[3]["headers"]["User-Agent"], "test")
        self.assertEqual(headers["Authorization"], "secret")

    def test_a01_curl_redirect_limit_closes_last_response(self) -> None:
        routes = {self.START: (302, {"Location": self.START})}
        with _memory_curl(routes) as (visited, responses):
            with self.assertRaisesRegex(requests.exceptions.TooManyRedirects, "Exceeded 30 redirects"):
                web_to_md._http_get(self.START)
            self.assertEqual(len(visited), 31)
            for response in responses:
                response.close.assert_called_once_with()

    def test_a01_curl_private_opt_in_keeps_automatic_redirects(self) -> None:
        response = Mock(url=self.PRIVATE)
        backend = SimpleNamespace(get=Mock(return_value=response))
        with patch.dict(web_to_md.CONFIG, allow_private_hosts=True), \
                patch.object(web_to_md, "curl_requests", backend):
            self.assertIs(web_to_md._http_get(self.START), response)
        backend.get.assert_called_once()
        self.assertNotIn("allow_redirects", backend.get.call_args.kwargs)
        response.close.assert_not_called()

    def test_a01_curl_nonredirect_or_missing_location_returns_response(self) -> None:
        for status, headers in ((200, {"Location": self.PRIVATE}), (302, {})):
            with self.subTest(status=status), _memory_curl({self.START: (status, headers)}) as (visited, responses):
                self.assertIs(web_to_md._http_get(self.START), responses[0])
                self.assertEqual(len(visited), 1)
                responses[0].close.assert_not_called()
