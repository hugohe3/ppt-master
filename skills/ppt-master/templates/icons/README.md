# SVG Icon Library

**12,027 SVG icons** across five libraries, embedded directly into generated SVG. Default Strategist or the Quick main agent chooses at most one primary library from the four stylistic ones; the brand-logo library (`simple-icons`) is prepared as needed for real brands, alone or alongside it, and is never a separate Confirm UI choice. Upstream versions, licenses, attribution, and trademark boundaries: [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

| Library | Style | Count | viewBox | Prefix |
|---------|-------|-------|---------|--------|
| `chunk-filled` | fill · compact, chunky 16px silhouettes; heavy, solid | 641 | primarily `0 0 16 16` | `chunk-filled/` |
| `tabler-filled` | fill · bezier forms, smooth rounded contours; medium, approachable | 1,055 | `0 0 24 24` | `tabler-filled/` |
| `tabler-outline` | stroke / line art (default stroke-width 2); light, refined; best on screen — thin strokes weaken when printed or projected | 5,138 | `0 0 24 24` | `tabler-outline/` |
| `phosphor-duotone` | duotone · full-opacity shape plus a same-color 20% backplate; medium, layered | 1,518 | `0 0 256 256` | `phosphor-duotone/` |
| `simple-icons` | **brand logos** (real company / product marks), single-color silhouettes colored via `fill` | 3,675 | `0 0 24 24` | `simple-icons/` |

## Per-project icons folder

This directory is the global library; the resource owner copies chosen icons into `<project>/icons/<lib>/` before SVG authoring:

```bash
python3 skills/ppt-master/scripts/icon_sync.py <project_path> tabler-outline/home tabler-outline/bulb simple-icons/github
```

Missing names, or one batch mixing the four stylistic libraries, exit non-zero; `simple-icons` may coexist. Files under `<project>/icons/` form the prepared pool and combine freely with user-provided, custom, or imported icons; `finalize_svg.py --only embed-icons`, preview, validation, and native export resolve only this pool. **Custom icons**: drop `.svg` files into `<project>/icons/<lib>/` (any `<lib>`, e.g. `custom/`) and reference `data-icon="<lib>/<name>"`. **Imported vectors**: `create-template` reserves `imported/` — one copy at `<workspace>/icons/imported/<name>.svg`, referenced as `data-icon="imported/<name>"`, never duplicated under `templates/` or used as a hand-curated library.

## Usage

```xml
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#0076A8"/>
<use data-icon="phosphor-duotone/house" x="100" y="200" width="48" height="48" fill="#0076A8"/>
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>
```

`data-icon` is `<library>/<icon-name>` (filename without `.svg`), case-sensitive because it resolves a real file — bundled names are canonical lowercase (`tabler-outline/award`), custom icons keep their file case; `x`, `y` position; `width`, `height` size (32–48px recommended); `fill` color. A complete `library/name` identifier is mandatory: bare names, abbreviated namespaces, paths into `templates/icons/`, and unsynced bundled files fail rather than fall back. `finalize_svg.py` embeds every placeholder during post-processing (`scripts/svg_finalize/embed_icons.py svg_output/*.svg` runs it manually).

## Searching for Icons

For a known basename run `icon_sync.py` directly; for an uncertain one search only the chosen stylistic library (`simple-icons` only for a real brand mark):

```bash
rg --files "skills/ppt-master/templates/icons/tabler-outline" -g '*chart*.svg'
rg --files "skills/ppt-master/templates/icons/simple-icons" -g '*github*.svg'
```

**Hard rule**: search by the drawable object, not the abstract concept — these libraries store things that can be drawn (`bulb`, `target`, `trending-up`, `alert-triangle`), so `idea`, `goal`, `growth`, `warning`, `innovation` return nothing in most of them; translate the semantic into an object first. **Reference — not a constraint**: one concept usually has several valid objects, chosen per deck from page register and visual style. **Hard rule**: basenames are not portable across the four stylistic libraries — `alert-*` exists in the tabler libraries but `phosphor-duotone` uses `warning-*`; `arrow-trend-*` in `chunk-filled` is `trending-*` in `tabler-outline`. Do not load a full index or enumerate broad keyword families; re-pick from the narrow result and rerun the batch until clean; never switch stylistic libraries for a missing generic icon. An empty result → try another drawable translation in the same library; when several stay empty, let another carrier (chart, typography, shape) take that semantic rather than forcing a loose icon.

## Style Rules

**No default library — choose from the deck's visual needs** after reading the source: compact silhouettes (`chunk-filled`) vs rounded curves (`tabler-filled` / `phosphor-duotone`) vs open strokes (`tabler-outline`); visual weight heavy solid → medium solid → medium layered → light stroke. **At most one primary bundled stylistic library per deck selection**: when it lacks an exact icon, use the closest alternative within it rather than another bundled library — a catalog-selection rule, not a ban on combining assets already in the project's `icons/`. **Brand-logo exception**: `simple-icons` is not a stylistic library and does not count toward that rule; its job is brand recognition (Slack's purple, GitHub's cat), intentionally heterogeneous — prepare it only when content needs a company / product / service mark (customer or partner logos, tech-stack icons in architecture diagrams, social handles in a footer), never as a substitute for a missing generic icon or for decoration.
