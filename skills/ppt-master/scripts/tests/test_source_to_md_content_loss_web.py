#!/usr/bin/env python3
"""PPT Master - Offline web content preservation regressions.

Usage: python3 -m unittest tests.test_source_to_md_content_loss_web
Dependencies: beautifulsoup4, requests
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / 'source_to_md'))
import web_to_md  # noqa: E402


class WebContentLossTests(unittest.TestCase):
    def _convert(self, body, head='<title>Test page</title>'):
        html = '<html><head>' + head + '</head><body>' + body + '</body></html>'
        response = SimpleNamespace(url='https://example.invalid/page', content=html.encode(),
            headers={'Content-Type': 'text/html; charset=utf-8'}, text=html,
            encoding='utf-8', apparent_encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            output = Path(tmp) / 'page.md'
            with patch.object(web_to_md, 'fetch_response', return_value=response):
                result = web_to_md.process_url(response.url, str(output), download_images=False)
            self.assertTrue(result[0], result)
            return output.read_text(encoding='utf-8')

    def test_f06_article_semantic_content_survives_shell_cleanup(self) -> None:
        for container in ('article', 'main', 'div class="article-content"'):
            with self.subTest(container=container):
                tag = container.split()[0]
                md = self._convert('<header>SITE_HEADER</header><nav>SITE_NAV</nav><' + container + '>'
                    '<header><h1>ARTICLE_TITLE</h1></header><p>' + 'Body text. ' * 30 + '</p><aside>BODY_NOTE</aside>'
                    '<footer>AUTHOR_SIGNATURE</footer><nav>ARTICLE_NAV</nav></' + tag + '>'
                    '<footer>SITE_FOOTER</footer><aside>SITE_AD</aside>')
                for text in ('ARTICLE_TITLE', 'BODY_NOTE', 'AUTHOR_SIGNATURE'):
                    self.assertIn(text, md)
                for text in ('SITE_HEADER', 'SITE_NAV', 'SITE_FOOTER', 'SITE_AD', 'ARTICLE_NAV'):
                    self.assertNotIn(text, md)

    def test_f07_parallel_articles_are_retained_in_source_order(self) -> None:
        md = self._convert('<article><p>' + 'First body. ' * 40 + '</p></article>'
                          '<article><p>' + 'SECOND_BODY ' * 30 + '</p></article>')
        self.assertIn('SECOND_BODY', md)
        self.assertLess(md.index('First body.'), md.index('SECOND_BODY'))

    def test_f07_parallel_identified_content_blocks_are_retained(self) -> None:
        md = self._convert('<div class="article-content"><p>' + 'First body. ' * 40 + '</p></div>'
                          '<div class="article-content"><p>' + 'SECOND_BODY ' * 30 + '</p></div>')
        self.assertIn('SECOND_BODY', md)

    def test_f08_title_is_not_cut_by_site_keyword(self) -> None:
        md = self._convert('<p>Body</p>', '<title>预算-政府补贴3000000元方案</title>')
        self.assertIn('# 预算-政府补贴3000000元方案', md)

    def test_f08_only_verified_site_suffix_is_removed(self) -> None:
        md = self._convert('<p>Body</p>', '<title>Budget | Example Portal</title>'
                          '<meta property="og:site_name" content="Example Portal">')
        self.assertIn('# Budget\n', md)
        self.assertNotIn('# Budget |', md)

    def test_f26_ordered_list_start_and_value_are_preserved(self) -> None:
        md = self._convert('<ol start="5"><li>Fifth</li><li value="9">Ninth</li></ol>')
        # Markdown renderers renumber discontinuous lists; retain HTML for jumps.
        self.assertIn('<ol start="5">', md)
        self.assertIn('<li value="9">', md)
        self.assertIn('Fifth', md)
        self.assertIn('Ninth', md)

    def test_f26_continuous_and_nested_lists_keep_numbers_and_links(self) -> None:
        md = self._convert('<ol start="5"><li><a href="/proof">Fifth</a>'
                          '<ul><li>Child</li></ul></li><li>Sixth</li></ol>')
        self.assertIn('5. [Fifth](https://example.invalid/proof)', md)
        self.assertIn('6. Sixth', md)
        self.assertIn('  - Child', md)

    def test_short_selector_matches_fall_back_to_dense_body(self) -> None:
        body = ''.join(f'<p>Paragraph {i}: ' + 'Project investment details. ' * 12 + '</p>' for i in range(8))
        for clutter in ('<div class="content">当前位置：首页 &gt; 新闻</div>',
                        '<div class="related"><article>Related story</article><article>Another story</article></div>'):
            with self.subTest(clutter=clutter):
                md = self._convert(clutter + '<div class="article-body">' + body + '</div>')
                self.assertIn('Paragraph 7:', md)
                self.assertNotIn('Related story', md)
                self.assertNotIn('当前位置', md)

    def test_selector_score_gate_and_nested_bodies(self) -> None:
        md = self._convert('<article><p>' + 'x' * 150 + '</p></article>'
                           '<div><p>' + 'DENSE_BODY ' * 40 + '</p></div>')
        self.assertIn('DENSE_BODY', md)
        md = self._convert('<main><article><p>' + 'NESTED_BODY ' * 40 + '</p></article></main>')
        self.assertEqual(md.count('NESTED_BODY'), 40)
