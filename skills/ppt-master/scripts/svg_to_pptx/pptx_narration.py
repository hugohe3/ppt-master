"""Narration audio discovery and PPTX XML helpers."""

from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path


MEDIA_REL_TYPE = "http://schemas.microsoft.com/office/2007/relationships/media"
AUDIO_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

AUDIO_CONTENT_TYPES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}

NARRATION_EXTENSIONS = tuple(AUDIO_CONTENT_TYPES.keys())

TRANSPARENT_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/"
    "lBf7WQAAAABJRU5ErkJggg=="
)


def _get_audio_poster_bytes() -> bytes:
    """Return a small visible speaker-icon PNG for the audio poster frame.

    Uses Pillow to draw a rounded blue rectangle with a white speaker glyph
    when available; otherwise returns a small solid-blue square PNG as a
    minimal fallback.
    """
    try:
        from PIL import Image, ImageDraw
        import io
        size = 48
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = 2
        draw.rounded_rectangle(
            [margin, margin, size - margin - 1, size - margin - 1],
            radius=8, fill=(68, 114, 196, 230),
        )
        body_color = (255, 255, 255, 240)
        bx1, bx2 = 12, 24
        by1, by2 = 16, 32
        draw.polygon([
            (bx1, by1), (bx2, by1 - 4), (bx2, by2 + 4), (bx1, by2),
        ], fill=body_color)
        wave_color = (255, 255, 255, 220)
        for r_offset, w in [(0, 2), (4, 2), (8, 2)]:
            cx, cy = 24, 24
            r = 10 + r_offset
            draw.arc([cx - r, cy - r, cx + r, cy + r], start=-40, end=40,
                     fill=wave_color, width=w)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        pass
    # Fallback: small solid blue square (32x32, PowerPoint accent blue #4472C4)
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
        "jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAdSURBVFhH7cEBDQAAAMKg909tDjcgAAAAADBf"
        "iwABb/0BE7gAAAAASUVORK5CYII="
    )


def _normalize_title(title: str) -> str:
    # Keep alphanumerics, CJK Unified Ideographs, Japanese Kana, Korean Hangul,
    # CJK Extension A. All other characters become underscore separators.
    text = re.sub(
        r"[^0-9A-Za-z\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+",
        "_", title.strip(),
    )
    return re.sub(r"_+", "_", text).strip("_").lower()


def _leading_number(text: str) -> int | None:
    match = re.match(r"^(\d{1,3})", text.strip())
    return int(match.group(1)) if match else None


def find_narration_files(audio_dir: Path, svg_files: list[Path]) -> dict[str, Path]:
    """Return `{svg_stem: audio_path}` matched by exact stem, normalized stem, or index."""
    if not audio_dir.exists() or not audio_dir.is_dir():
        return {}

    audio_files = [
        path for path in sorted(audio_dir.iterdir())
        if path.is_file() and path.suffix.lower() in NARRATION_EXTENSIONS
    ]
    exact = {path.stem: path for path in audio_files}
    normalized: dict[str, Path] = {}
    numbered: dict[int, Path] = {}
    for path in audio_files:
        normalized.setdefault(_normalize_title(path.stem), path)
        number = _leading_number(path.stem)
        if number is not None:
            numbered.setdefault(number, path)

    matched: dict[str, Path] = {}
    for index, svg in enumerate(svg_files, 1):
        stem = svg.stem
        if stem in exact:
            matched[stem] = exact[stem]
            continue
        norm = _normalize_title(stem)
        if norm in normalized:
            matched[stem] = normalized[norm]
            continue
        if index in numbered:
            matched[stem] = numbered[index]
    return matched


def probe_audio_duration(audio_path: Path) -> float | None:
    """Return duration in seconds. Tries ffprobe, then mutagen, then stdlib wave."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        data = json.loads(result.stdout or "{}")
        duration = float(data.get("format", {}).get("duration", 0))
        if duration > 0:
            return duration
    except Exception:
        pass
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(audio_path))
        if audio is not None and getattr(audio, "info", None) is not None:
            length = getattr(audio.info, "length", 0)
            if length and length > 0:
                return float(length)
    except Exception:
        pass
    try:
        import wave
        if audio_path.suffix.lower() == ".wav":
            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return frames / float(rate)
    except Exception:
        pass
    return None


def next_shape_id(slide_xml: str) -> int:
    ids = [int(value) for value in re.findall(r'<p:cNvPr[^>]*\sid="(\d+)"', slide_xml)]
    return max(ids, default=1) + 1


def create_audio_pic_xml(
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
) -> str:
    """Create a visible speaker-icon audio shape carrying narration media.

    The icon is placed in the top-right corner so users can see audio is
    embedded and click it. Auto-play timing is still injected so audio
    plays on slide entry during slideshow mode.
    Icon size: 480000 EMU (0.5 inch, approx 36pt). Positioned 200000 EMU
    (~0.16 inch) from the top-right edge of a standard 16:9 slide.
    """
    icon_cx = 480000
    icon_cy = 480000
    icon_x = 11680000 - icon_cx - 200000
    icon_y = 200000
    return f'''<p:pic>
        <p:nvPicPr>
          <p:cNvPr id="{shape_id}" name="{shape_name}">
            <a:hlinkClick r:id="" action="ppaction://media"/>
          </p:cNvPr>
          <p:cNvPicPr>
            <a:picLocks noChangeAspect="1"/>
          </p:cNvPicPr>
          <p:nvPr>
            <a:audioFile r:link="{audio_rid}"/>
            <p:extLst>
              <p:ext uri="{{DAA4B4D4-6D71-4841-9C94-3DE7FCFB9230}}">
                <p14:media xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" r:embed="{media_rid}"/>
              </p:ext>
            </p:extLst>
          </p:nvPr>
        </p:nvPicPr>
        <p:blipFill>
          <a:blip r:embed="{poster_rid}"/>
          <a:stretch><a:fillRect/></a:stretch>
        </p:blipFill>
        <p:spPr>
          <a:xfrm>
            <a:off x="{icon_x}" y="{icon_y}"/>
            <a:ext cx="{icon_cx}" cy="{icon_cy}"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
      </p:pic>'''


def _next_timing_id(slide_xml: str) -> int:
    ids = [int(value) for value in re.findall(r'<p:cTn[^>]*\sid="(\d+)"', slide_xml)]
    return max(ids, default=1) + 1


def _create_audio_timing_xml(shape_id: int, ctn_id: int) -> str:
    return f'''<p:audio>
                <p:cMediaNode vol="80000">
                  <p:cTn id="{ctn_id}" fill="hold" display="0">
                    <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                  </p:cTn>
                  <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                </p:cMediaNode>
              </p:audio>'''


def inject_narration(
    slide_xml: str,
    *,
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
) -> str:
    """Inject a visible narration media shape and slide-entry autoplay timing.

    Uses multiple regex-based fallback strategies so timing insertion is
    robust across different PPT generators' XML layouts.
    """
    audio_pic_xml = create_audio_pic_xml(
        shape_id=shape_id,
        shape_name=shape_name,
        audio_rid=audio_rid,
        media_rid=media_rid,
        poster_rid=poster_rid,
    )
    if "</p:spTree>" in slide_xml:
        slide_xml = slide_xml.replace("</p:spTree>", audio_pic_xml + "\n    </p:spTree>", 1)

    audio_timing_xml = _create_audio_timing_xml(shape_id, _next_timing_id(slide_xml))

    if "<p:timing>" not in slide_xml:
        timing_xml = f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
          <p:childTnLst>
              {audio_timing_xml}
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''
        return slide_xml.replace("</p:sld>", timing_xml + "\n</p:sld>", 1)

    # Try multiple cTn id="1" patterns (attributes may appear in different order)
    ctn_patterns = [
        re.compile(r'(<p:cTn\s+id="1"[^>]*>\s*<p:childTnLst>)', re.S),
        re.compile(r'(<p:cTn[^>]*\s+id="1"[^>]*>\s*<p:childTnLst>)', re.S),
    ]
    for pattern in ctn_patterns:
        if pattern.search(slide_xml):
            return pattern.sub(r"\1\n              " + audio_timing_xml, slide_xml, count=1)

    # Try finding first childTnLst inside tnLst/par
    child_pattern = re.compile(r'(<p:tnLst>\s*<p:par>.*?<p:childTnLst>)', re.S)
    m = child_pattern.search(slide_xml)
    if m:
        return child_pattern.sub(r"\1\n              " + audio_timing_xml, slide_xml, count=1)

    # Last resort: insert before closing tnLst
    if "</p:tnLst>" in slide_xml:
        slide_xml = slide_xml.replace("</p:tnLst>", audio_timing_xml + "\n    </p:tnLst>", 1)
    return slide_xml


def apply_recorded_timing(
    slide_xml: str,
    *,
    advance_after: float,
    transition_duration: float,
    transition_effect: str | None = "fade",
) -> str:
    """Set slide auto-advance timing so exported video follows narration length."""
    adv_ms = max(1, int(advance_after * 1000))
    dur_ms = max(1, int(transition_duration * 1000))

    transition_match = re.search(r"<p:transition\b[^>]*>", slide_xml)
    if transition_match:
        tag = transition_match.group(0)
        is_self_closing = tag.rstrip().endswith("/>")
        base_tag = tag.rstrip()
        if is_self_closing:
            base_tag = re.sub(r"\s*/>$", ">", base_tag, count=1)
        if "advTm=" in base_tag:
            new_tag = re.sub(r'\sadvTm="[^"]*"', f' advTm="{adv_ms}"', base_tag, count=1)
        else:
            new_tag = base_tag[:-1] + f' advTm="{adv_ms}">'
        if is_self_closing:
            new_tag = new_tag[:-1] + "/>"
        return slide_xml[:transition_match.start()] + new_tag + slide_xml[transition_match.end():]

    effect = transition_effect or "fade"
    transition_xml = f'''  <p:transition p14:dur="{dur_ms}" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" advTm="{adv_ms}">
    <p:{effect}/>
  </p:transition>'''
    if "<p:timing>" in slide_xml:
        return slide_xml.replace("<p:timing>", transition_xml + "\n  <p:timing>", 1)
    return slide_xml.replace("</p:sld>", transition_xml + "\n</p:sld>", 1)
