---
description: Test-only Generate profile for authoring a few SVG slides and exporting one PPTX without normal planning or sidecar artifacts.
---

# Quick Test Profile

> Generate-PPTX profile, not a top-level route. Use it only for disposable
> converter/layout tests; normal presentation delivery stays on
> [`generate-pptx.md`](../generate-pptx.md) Steps 1–7.

**Trigger**: the user explicitly requests quick/fast test mode, identifies the
deck as a test, and asks for a small fixed slide roster. A small page count alone
never activates this profile.

---

## 1. Eligibility

| Condition | Required state |
|---|---|
| Intent | Explicit disposable test, not a presentation delivery |
| Page roster | Small, fixed, and named or directly inferable |
| Content | Supplied in chat and sufficient to draw without conversion or research |
| Visual inputs | Plain SVG geometry/text, or already supplied self-contained data; no asset acquisition |
| Output | Only authored SVG pages and one native PPTX |

**Missing eligibility** → use the normal Generate pipeline. Do not ask the user
to weaken a normal delivery request so it can enter this profile.

**Hard rule — explicit scope only**: this profile never activates for a factual
deck, a template-backed deck, source-file conversion, native charts/tables,
external images/icons/fonts, speaker notes, animation, narration, visual
review, or any reusable deliverable.

---

## 2. Minimal Authoring Contract

Read only [`shared-standards-core.md`](../../references/shared-standards-core.md).
Load one of its conditional modules only when the user's exact SVG test needs
that registered feature; otherwise keep the SVG surface to solid paint, basic
geometry, text, and semantic groups.

Create only:

```text
<project_path>/
├── svg_output/
│   └── <ordered-page>.svg
└── exports/
    └── <project_name>_<timestamp>.pptx
```

**Hard rule — no normal-pipeline artifacts**: do not run source conversion,
`project_manager.py init`, topic research, template application, Strategist,
Confirm UI, image/icon acquisition, Live Preview, SVG quality checker,
speaker-note generation, `finalize_svg.py`, chart verification, animation,
narration, or any supporting stage. Do not create `design_spec.md`,
`spec_lock.md`, `sources/`, `analysis/`, `images/`, `icons/`, `templates/`,
`confirm_ui/`, `notes/`, `svg_final/`, `validation/`, `backup/`, or metadata
sidecars.

**Canvas**: write `viewBox="0 0 W H"` on every page. The first SVG establishes
the test canvas; every remaining page must match it exactly.

**Structure**: author flat, Slide-local SVG only. Include the complete visible
page in each SVG; set one root `data-pptx-page-role` from `cover`, `toc`,
`section`, `content`, or `ending`, and omit Master/Layout/layer/placeholder
metadata.

**Typography**: name an installed concrete font family in the SVG; do not depend
on a lock or generated font asset.

**Generation pacing**: the current main agent hand-writes the fixed SVG roster
in order. Skip the normal first-page and final checker gates.

---

## 3. Direct Export

Run one export command after every requested SVG exists:

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-test
```

`--quick-test` reads only `svg_output/`, infers one consistent canvas, uses a
flat PowerPoint package with converter defaults, disables notes and motion,
skips lock/theme sidecars, and writes no backup, conversion trace, or validation
report. An explicit `-o <path>.pptx` may replace the default `exports/`
destination without changing the artifact boundary.

**Validation**: success requires `[QUICK-TEST] status=passed`, the authored SVG
count to equal the published Slide count, and the PPTX to pass in-memory ZIP
integrity. On failure, repair the owning SVG and rerun this command; do not
create planning or validation artifacts.

```markdown
## ✅ Quick Test Complete

- [x] Requested SVG pages exist under `svg_output/`
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No normal-pipeline artifacts were created
- [ ] **Next**: Report the PPTX path
```
