# Multilingual Text Maintenance Smoke

Run this manual smoke from the repository root after changing Confirm UI
language handling, DrawingML text export, native tables/charts, notes, or
document metadata. It uses only temporary files and does not add an automated
test suite.

```bash
PYTHONPATH="skills/ppt-master/scripts:skills/ppt-master/scripts/confirm_ui" python3 - <<'PY'
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

from pptx import Presentation

from confirm_ui.server import create_app
from language_tags import (
    LanguageTagError,
    language_uses_rtl,
    normalize_language_tag,
)
from svg_to_pptx.drawingml.context import ConvertContext
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.native_objects import _build_native_chart
from svg_to_pptx.native_objects.table import _build_native_table
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import _declared_primary_language
from svg_to_pptx.pptx_package.notes import create_notes_slide_xml


def reject_language(value):
    try:
        normalize_language_tag(value)
    except LanguageTagError:
        return
    raise AssertionError(f"invalid language accepted: {value}")


canonical = {
    "ES_mx": "es-MX",
    "RU_ru": "ru-RU",
    "AR_sa": "ar-SA",
    "HE_il": "he-IL",
    "HI_in": "hi-IN",
    "TH_th": "th-TH",
    "KO_kr": "ko-KR",
    "fil_ph": "fil-PH",
    "zh_hans": "zh-Hans",
    "de-CH-1901": "de-CH-1901",
    "en-u-nu-latn": "en-u-nu-latn",
}
for raw, expected in canonical.items():
    assert normalize_language_tag(raw) == expected
for raw in ("und", "zh", "en--US", "Arabic", "x-private"):
    reject_language(raw)
assert language_uses_rtl("ar-Arab-SA")
assert not language_uses_rtl("ar-Latn-SA")
assert language_uses_rtl("en-Arab-US")

samples = {
    "en-US": "Summary 2026",
    "zh-Hans": "年度总结 2026",
    "ja-JP": "年間まとめ 2026",
    "ko-KR": "연간 요약 2026",
    "es-ES": "Resumen 2026",
    "ru-RU": "Итоги 2026",
    "ar-SA": "ملخص 2026",
    "he-IL": "סיכום 2026",
    "hi-IN": "सारांश 2026",
    "th-TH": "สรุป 2026",
}
rtl_languages = {"ar-SA", "he-IL"}

with TemporaryDirectory(prefix="ppt-master-multilingual-smoke-") as tmp:
    root = Path(tmp)

    # Confirm UI canonicalizes Stage 1 and persists the same project language.
    project = root / "confirm-project"
    confirm = project / "confirm_ui"
    confirm.mkdir(parents=True)
    recommendation = {
        "stage": "stage1",
        "lang": "en",
        "primary_language": "AR_sa",
        "audience": {"value": "Team"},
        "communication_intent": {"value": "Explain"},
        "audience_outcome": {"value": "Understand"},
        "core_message": {"value": "Result"},
        "delivery_context": {"value": "Meeting"},
        "artifact_afterlife": {"value": ""},
        "content_divergence": {"value": ""},
        "recommend": {"canvas": "ppt169"},
    }
    (confirm / "recommendations.stage1.json").write_text(
        json.dumps(recommendation),
        encoding="utf-8",
    )
    (confirm / "template_options.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "phase": "template",
                "default_mode": "free_design",
                "explicit_workspace_roots": [],
            }
        ),
        encoding="utf-8",
    )
    app = create_app(str(project), idle_timeout=0)
    app.testing = True
    client = app.test_client()
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    assert response.get_json()["primary_language"] == "ar-SA"
    response = client.post(
        "/api/confirm",
        json={
            "stage": "stage1",
            "template_selection": {
                "mode": "free_design",
                "selection_keys": [],
            },
            "primary_language": "ar-SA",
            "canvas": "ppt169",
            "audience": "Team",
            "communication_intent": "Explain",
            "audience_outcome": "Understand",
            "core_message": "Result",
            "delivery_context": "Meeting",
            "artifact_afterlife": "",
            "content_divergence": "",
        },
    )
    assert response.status_code == 200
    result = json.loads((confirm / "result.json").read_text(encoding="utf-8"))
    assert result["primary_language"] == "ar-SA"

    # The execution lock is the only export-time project-language source.
    lock_project = root / "lock-project"
    lock_project.mkdir()
    lock_template = """# Execution Lock

## communication
{language}- audience: team
- objective: explain
- core_message: result
"""
    lock = lock_project / "spec_lock.md"
    lock.write_text(
        lock_template.format(language="- primary_language: ES_mx\n"),
        encoding="utf-8",
    )
    assert _declared_primary_language(lock_project) == "es-MX"
    lock.write_text(lock_template.format(language=""), encoding="utf-8")
    assert _declared_primary_language(lock_project) is None

    for index, (language, sample) in enumerate(samples.items(), 1):
        stem = f"slide-{index}"
        svg = root / f"{stem}.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'viewBox="0 0 1280 720">'
            '<rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>'
            f'<text x="100" y="140" font-size="42" '
            f'font-family="Arial" fill="#111111">{sample}</text>'
            "</svg>",
            encoding="utf-8",
        )

        slide_xml, *_ = convert_svg_to_slide_shapes(
            svg,
            index,
            verbose=False,
            primary_language=language,
        )
        assert f'lang="{language}"' in slide_xml
        assert ("rtl=\"1\"" in slide_xml) == (language in rtl_languages)
        assert ("<a:rtl val=\"1\"/>" in slide_xml) == (
            language in rtl_languages
        )

        ascii_svg = root / f"{stem}-ascii.svg"
        ascii_svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'viewBox="0 0 1280 720">'
            '<text x="100" y="140" font-size="42">2026 AI</text>'
            "</svg>",
            encoding="utf-8",
        )
        ascii_xml, *_ = convert_svg_to_slide_shapes(
            ascii_svg,
            index + 20,
            verbose=False,
            primary_language=language,
        )
        assert f'lang="{language}"' in ascii_xml
        assert 'rtl="1"' not in ascii_xml
        assert "<a:rtl val=\"1\"/>" not in ascii_xml

        context = ConvertContext(primary_language=language)
        marker = ET.Element("g")
        table = _build_native_table(
            marker,
            context,
            {
                "schema": "ppt-master.semantic-table.v2",
                "x": 10,
                "y": 10,
                "width": 600,
                "height": 180,
                "columns": [sample, "2026 AI"],
                "rows": [["A", "B"]],
                "style": {"font_family": "Arial"},
            },
        )
        assert f'lang="{language}"' in table.xml
        assert all(slot in table.xml for slot in ("<a:latin ", "<a:ea ", "<a:cs "))

        chart_context = ConvertContext(primary_language=language)
        _build_native_chart(
            marker,
            chart_context,
            {
                "x": 10,
                "y": 220,
                "width": 600,
                "height": 300,
                "type": "column",
                "title": sample,
                "categories": ["A", "B"],
                "series": [{"name": sample, "values": [1, 2]}],
                "style": {"font_family": "Arial"},
                "show_legend": True,
            },
        )
        chart_xml = next(
            value.decode("utf-8")
            for part, value in chart_context.package_files.items()
            if part.startswith("ppt/charts/chart") and not part.endswith(".rels")
        )
        assert f'<c:lang val="{language}"/>' in chart_xml
        assert f'lang="{language}"' in chart_xml

        notes_xml = create_notes_slide_xml(
            1,
            sample + "\n2026 AI",
            language,
        )
        assert f'lang="{language}"' in notes_xml
        assert ("rtl=\"1\"" in notes_xml) == (language in rtl_languages)

        output = root / f"{index}.pptx"
        assert create_pptx_with_native_svg(
            [svg],
            output,
            canvas_format="ppt169",
            verbose=False,
            transition=None,
            notes={stem: sample + "\n2026 AI"},
            pptx_structure="flat",
            structure_name="multilingual-smoke",
            primary_language=language,
        )
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            packaged_slide = archive.read(
                "ppt/slides/slide1.xml"
            ).decode("utf-8")
            packaged_notes = archive.read(
                "ppt/notesSlides/notesSlide1.xml"
            ).decode("utf-8")
            core = archive.read("docProps/core.xml").decode("utf-8")
            assert f'lang="{language}"' in packaged_slide
            assert f'lang="{language}"' in packaged_notes
            assert f"<dc:language>{language}</dc:language>" in core
        assert len(Presentation(str(output)).slides) == 1

    # A legacy lock with no language field keeps the previous per-run path.
    legacy_svg = root / "legacy.svg"
    legacy_svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 1280 720">'
        '<text x="100" y="140" font-size="42">한국어 2026</text>'
        "</svg>",
        encoding="utf-8",
    )
    legacy_output = root / "legacy.pptx"
    assert create_pptx_with_native_svg(
        [legacy_svg],
        legacy_output,
        canvas_format="ppt169",
        verbose=False,
        transition=None,
        pptx_structure="flat",
        structure_name="legacy-smoke",
    )
    with zipfile.ZipFile(legacy_output) as archive:
        assert archive.testzip() is None
        legacy_slide = archive.read(
            "ppt/slides/slide1.xml"
        ).decode("utf-8")
        assert 'lang="ko-KR"' in legacy_slide

print("Multilingual text smoke: passed")
PY
```

Expected output:

```text
Multilingual text smoke: passed
```

The RTL contract is paragraph `a:pPr rtl="1"` plus run-level `a:rtl` only
when the run contains strong RTL characters. Do not use `rtlCol`; it controls
column order, not paragraph direction.
