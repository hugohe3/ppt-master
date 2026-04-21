# build_slides.py Contract

> A single Python file is the project's **source of truth**; the SVGs under `svg_output/` and `notes/total.md` are reproducible artifacts of it.
> To change an SVG, change the .py file — hand-edits to SVG files get overwritten on the next run.

## 1. File Location and Run

- Location: `<project_path>/build_slides.py`
- Run: `python3 <project_path>/build_slides.py`
- Outputs:
  - `<project_path>/svg_output/<NN>_<page_name>.svg`
  - `<project_path>/notes/total.md`
- Dependencies: pure stdlib (`html`, `textwrap`, `pathlib`); no third-party packages

## 2. File Structure

```python
from __future__ import annotations
from html import escape           # escape page text
from textwrap import dedent       # keep source indentation clean
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_DIR = ROOT / "svg_output"
NOTES_DIR = ROOT / "notes"

# ── Top-level constants: style spec + asset registry ──
PRIMARY = "#0B4EA2"               # primary color (from design_spec.md III. Visual Theme)
ACCENT  = "#18A572"
BG      = "#F5F8FC"
TEXT    = "#182433"
# ... other colors

STYLE = {
    "title_font":      "'Microsoft YaHei', Arial, sans-serif",
    "body_font":       "'Microsoft YaHei', Arial, sans-serif",
    "title_size":      30,
    "body_size":       18,
    "annotation_size": 14,
}

ICONS = {
    "arrow_right": "chunk/arrow-right",       # from design_spec.md VI. Icon Usage
    "checkmark":   "chunk/circle-checkmark",
    # All icons used by any page are registered here. Hard-coding icon names
    # inside page_*() functions is forbidden.
}

IMAGES = {
    "cover_bg": "images/cover_bg.png",        # path relative to build_slides.py
    # from design_spec.md VIII. Image Resource List
}

# ── Shared SVG resources ──
def common_defs() -> str:
    """Return <defs>...</defs> with all filter / gradient definitions."""
    return dedent("""
        <defs>
          <linearGradient id="topBar" ...>...</linearGradient>
          <filter id="cardShadow" ...>...</filter>
        </defs>
    """).strip()

def svg_doc(body: str) -> str:
    """Wrap body in the <svg> shell, auto-injecting common_defs."""
    return dedent(f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
          {common_defs()}
          {body}
        </svg>
    """).strip() + "\n"

# ── Optional helpers (extract by need, not by rule) ──
# When several pages share the same structure (e.g. content-page chrome,
# card, left-image-right-text template), extract a helper.
# When a page has a unique layout (cover, TOC, chapter, special pages),
# write it inline in the page_*() function.

# ── Page functions ──
def page_01_cover() -> str:
    body = dedent(f"""
        <rect x="0" y="0" width="1280" height="720" fill="{PRIMARY}"/>
        <text x="640" y="360" text-anchor="middle"
              font-family="{STYLE['title_font']}" font-size="60" fill="#FFFFFF">
          <tspan>{escape("Presentation Title")}</tspan>
        </text>
    """).strip()
    return svg_doc(body)

# ... page_02_toc, page_03_chapter, ..., page_NN_ending

# ── Speaker notes generation ──
def notes_total() -> str:
    """Generate notes/total.md following executor-base.md §8 format."""
    sections = [
        ("01_Cover", "Opening script...", "Key points ① ② ③", "1 min"),
        # ... one record per page
    ]
    parts = []
    for heading, script, points, duration in sections:
        parts.append(dedent(f"""
            # {heading}

            {script}

            Key points: {points}
            Duration: {duration}
        """).strip())
    return "\n\n---\n\n".join(parts) + "\n"

# ── Single entry point ──
def generate() -> None:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    pages = {
        "01_cover.svg":   page_01_cover(),
        "02_toc.svg":     page_02_toc(),
        # ...
    }
    for filename, content in pages.items():
        (SVG_DIR / filename).write_text(content, encoding="utf-8")

    (NOTES_DIR / "total.md").write_text(notes_total(), encoding="utf-8")

if __name__ == "__main__":
    generate()
```

## 3. Authoring Discipline (Executor must read)

### 3.1 Top-level constants are the single edit surface

- Colors, fonts, font sizes, icon names, image paths **all go through top-level constants**
- Page functions **must not** contain `fill="#0B4EA2"` or `<use data-icon="chunk/home" .../>` — use `fill="{PRIMARY}"` / `<use data-icon="{ICONS['home']}" .../>` instead
- This rule is the foundation of batch-edit capability; breaking it degrades the workflow back to "writing each page by hand inside .py"

### 3.2 Helpers extracted by need, not by rule

- **Extract a helper**: when the same structure repeats across 2+ pages (typical: content-page top/bottom chrome, card, left-image-right-text template) — extract a function and call it from other pages
- **Don't extract**: layouts that appear only once (cover, TOC, chapter divider, ending, special data-viz pages) — write them inline in the `page_NN_*()` function; do not over-abstract for hypothetical reuse
- The trigger is **already-repeated**, not **expected-to-repeat**

### 3.3 SVG constraints still apply

The SVGs produced by build_slides.py must satisfy every constraint in [shared-standards.md](shared-standards.md) §1:
- No `<style>` / `class` / external CSS / `<foreignObject>` / `textPath` / `@font-face` / `<animate*>` / `<script>` / `<iframe>` / `<symbol>`
- No `rgba()` — use `fill-opacity` / `stroke-opacity`
- No `<g opacity>` — set opacity on each child element individually
- See shared-standards.md for the full ruleset

### 3.4 How to reference icons

- Register every icon in the top-level ICONS dict: `ICONS["arrow_right"] = "chunk/arrow-right"`
- In page functions, reference via `<use data-icon="{ICONS['arrow_right']}" x="..." y="..." width="48" height="48" fill="{PRIMARY}"/>`
- The `data-icon` attribute appears in the final SVG as usual; `finalize_svg.py` resolves it to actual icon content during post-processing (zero behavior change)
- A project may use only one icon library (chunk / tabler-filled / tabler-outline), consistent with design_spec.md VI

### 3.5 How to reference images

- Register every image in the top-level IMAGES dict with its relative path
- In page functions: `<image href="../images/{Path(IMAGES['cover_bg']).name}" ... />`
  - Note the `../images/` prefix: the final SVG lives in `svg_output/`, and `finalize_svg.py` resolves images by this relative path then base64-embeds them
- Fully compatible with the existing `finalize_svg.py` — no script changes needed

### 3.6 Text and indentation

- Wrap every user-facing text string with `escape(...)` to prevent SVG injection
- Use `textwrap.dedent(...)` on source blocks so .py indentation stays clean without polluting output

## 4. Workflow: Phase A → User Review → Phase B

### Phase A: first 5 pages (01–05)

The Executor writes build_slides.py per design_spec.md and produces **the first 5 pages of the deck (01–05) in order** for user review. The purpose is a **preliminary style sanity check** — does the colorway / typography / icon usage / overall visual feel match the user's expectation? Phase A is **not** a layout contract: Phase B is free to introduce any new layouts the deck requires.

- Decks > 5 pages: Phase A = pages 01–05; the rest land in Phase B
- Decks ≤ 5 pages: Phase A contains all pages; Phase B is skipped entirely

Rationale for sequential 01–05 (instead of cherry-picking representative layouts): Phase B then becomes a straight append from page 06 onward — no gaps, no re-ordering, no re-numbering risk. What Phase B inherits from Phase A is the **top-level constants** (colors, fonts, icon registry, image registry) and any helpers already extracted — not the set of layouts. New layouts introduced in Phase B are expected and do not require a second approval gate.

Run `python3 build_slides.py` → SVGs land in svg_output/. Hand pages 01–05 to the user for review.

⛔ **BLOCKING**: the user must explicitly confirm the style ("OK, continue" or similar) before Phase B may begin. This gate applies even when the deck has fewer than 5 pages total.

### Phase B: append remaining pages in batches

Skip Phase B entirely if Phase A already covers every page (deck size ≤ Phase A page count).

Otherwise, **each batch is at most 5 pages**, sliced by chapter when chapters exist (if a chapter exceeds 5 pages, slice by page number); for chapter-less decks, slice by page-number ranges:

```
loop {
  1. cp build_slides.py build_slides.py.bak    # rollback point
  2. In build_slides.py:
     a. Add 5 new page_NN_*() function definitions
     b. Add the 5 entries to the pages dict in generate()
     c. Append the 5 records to notes_total()
  3. python3 build_slides.py                    # validate immediately
  4. On failure → diagnose and fix; if unfixable, mv build_slides.py.bak build_slides.py to roll back this batch
  5. On success, move to the next batch
}
```

**Important**: each batch must add page functions + pages dict entries + notes records **together** in the same edit — never split (otherwise SVGs and speaker notes drift apart).

### After Phase B

Once every page is on disk, proceed with the existing post-processing pipeline:

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
```

Post-processing is agnostic to the SVG source — same as when SVGs were hand-written.

## 5. Fault Tolerance and Rollback

| Risk | Mitigation |
|------|------------|
| One syntax error breaks the whole file | 5-page batches + a validation run after each batch |
| A batch spirals out of control | `build_slides.py.bak` saved before each batch enables one-step rollback |
| A single page is impossible to land | Temporarily comment out its entry in the `pages` dict, ship the rest, return to the hard page later |
| Will reruns destroy existing SVGs? | No — reruns are idempotent overwrites with no side effects |

Worst case: lose only the **last unvalidated batch**. Every previously validated page is safe.

## 6. Mapping to design_spec.md

design_spec.md remains the human-readable design contract; build_slides.py is its machine-readable counterpart:

| design_spec.md section | Maps to build_slides.py |
|------------------------|-------------------------|
| III. Visual Theme (color HEX table) | Top-level color constants PRIMARY / ACCENT / ... |
| IV. Typography (fonts and sizes) | STYLE dict |
| VI. Icon Usage (icon inventory) | ICONS dict |
| VIII. Image Resource List | IMAGES dict |
| IX. Content Outline | Drives page-function count, naming, and content |
| X. Speaker Notes Requirements | Implemented by notes_total() |
| XI. Technical Constraints | Satisfied by the SVG output itself, refer to shared-standards.md |

## 7. Compatibility With Existing Post-Processing Scripts

| Script | Needs change? | Notes |
|--------|---------------|-------|
| `finalize_svg.py` | ❌ No | Looks at SVG content, not its origin — icon embedding / image embedding / text flatten all unchanged |
| `total_md_split.py` | ❌ No | Reads `notes/total.md`; doesn't matter if hand-written or generated |
| `svg_to_pptx.py` | ❌ No | Reads `svg_final/`, fully decoupled from upstream source |
| `embed_icons.py` | ❌ No | Parses `data-icon` attributes; behavior identical |

**This change is a pure addition for the post-processing pipeline** — not a single line downstream needs to move.
