---
description: Generate profile for directly authoring a self-contained SVG deck and exporting one PPTX without Strategist planning or sidecar artifacts.
---

# Quick Generate Profile

> Generate-PPTX profile, not a top-level route. Use it when the user explicitly
> requests a direct SVG-to-PPTX shortcut and supplies enough content to author
> the deck without the default [`generate-pptx.md`](../generate-pptx.md)
> Steps 1–7.

**Trigger**: the user explicitly requests quick/fast generation or directs the
agent to skip planning/confirmation and proceed directly to SVG, and the request
contains enough content for direct authoring without conversion or research.
Page count alone never activates or blocks this profile.

---

## 1. Eligibility

| Condition | Required state |
|---|---|
| Intent | Explicit direct-generation shortcut |
| Content | Supplied in chat or directly readable text/Markdown, and sufficient without conversion or research |
| Visual inputs | Basic SVG geometry/text or already supplied self-contained data; no asset acquisition |
| Output | Only authored SVG pages and one native PPTX |

**Missing eligibility** → use the default Generate pipeline. Do not silently
discard requested capabilities to fit this profile.

**Hard rule — explicit scope only**: requests that require source conversion,
factual research, template application, external image/icon/font acquisition,
native charts/tables, speaker notes, animation, narration, or visual review stay
on the default pipeline. Supplied fact-sufficient content may use this profile;
the shortcut must not invent or externally enrich claims.

---

## 2. Minimal Authoring Contract

Always read
[`shared-standards-core.md`](../../references/shared-standards-core.md). Do not
load `executor-base.md`: its planned-project prerequisites do not apply to this
profile. Besides the conditional canvas lookup below, load a core conditional
module only when the requested SVG needs that registered feature; otherwise
keep the SVG surface to solid paint, basic geometry, text, and semantic groups.

Before writing P01, resolve the slide roster, canvas, visual direction, palette,
and typography in the active context. Do not persist a plan, invoke Strategist,
or wait for confirmation. Preserve the supplied facts and requested wording.

Use a new project path, or first verify that its `svg_output/` is empty. Never
reuse a directory containing pages from another run: the exporter publishes
every discovered SVG. Use one zero-padded width sized for the resolved roster,
such as `01_cover.svg` through `12_end.svg` or `001_cover.svg` through
`120_end.svg`.

Create only:

```text
<project_path>/
├── svg_output/
│   └── <ordered-page>.svg
└── exports/
    └── <project_name>_<timestamp>.pptx
```

**Hard rule — no default-pipeline artifacts**: do not run source conversion,
`project_manager.py init`, topic research, template application, Strategist,
Confirm UI, image/icon acquisition, Live Preview, SVG quality checker,
speaker-note generation, `finalize_svg.py`, chart verification, animation,
narration, or any supporting stage. Do not create `design_spec.md`,
`spec_lock.md`, `sources/`, `analysis/`, `images/`, `icons/`, `templates/`,
`confirm_ui/`, `notes/`, `svg_final/`, `validation/`, `backup/`, or metadata
sidecars.

**Canvas**: unless the user specifies another canvas, use `ppt169` with
`viewBox="0 0 1280 720"`. For another requested registered format, load
[`canvas-formats.md`](../../references/canvas-formats.md) and use its exact
viewBox. The first SVG establishes the export canvas; every remaining page must
match it exactly.

**Structure**: author flat, Slide-local SVG only. Include the complete visible
page in each SVG; set one root `data-pptx-page-role` from `cover`, `toc`,
`section`, `content`, or `ending`, and omit Master/Layout/layer/placeholder
metadata.

**Typography**: name an installed concrete font family in the SVG; do not depend
on a lock or generated font asset.

**Generation pacing**: the current main agent decides the page structure in the
active context, then hand-writes the SVG roster in order. Use P01 as the visual
anchor, continue directly through the remaining pages, and skip the default
first-page and final checker gates.

---

## 3. Direct Export

Run one export command after every page in the resolved SVG roster exists:

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate
```

`--quick-generate` reads only `svg_output/`, infers one consistent canvas, uses
a flat PowerPoint package with converter defaults, disables notes and motion,
skips lock/theme sidecars, and writes no backup, conversion trace, or validation
report. An explicit `-o <path>.pptx` may replace the default `exports/`
destination without changing the artifact boundary.

**Package sanity**: the standard non-quiet command succeeds only when
`[QUICK-GENERATE] status=passed`, the discovered SVG count equals the published
Slide count, and the PPTX passes in-memory ZIP integrity. This receipt does not
claim SVG-checker, visual-quality, factual-correctness, or default postflight
approval. On failure, repair the owning SVG and rerun this command; do not
create planning or validation-report artifacts.

```markdown
## ✅ Quick Generate Complete

- [x] Resolved SVG pages exist under `svg_output/`
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No default-pipeline artifacts were created
- [ ] **Next**: Report the PPTX path
```
