> See [`executor-base.md`](./executor-base.md) for page authoring and the Chart/Table branches for information-model construction.

# Executor Visualization Reference Branch

Conditional Executor authority for resolving one page-local Chart/Table `family/key` SVG reference and adapting it without turning the catalog preview into a page specification.

**Trigger**: load only when Default `spec_lock.md page_visualizations` maps the current page to a canonical Chart/Table reference, a legacy `page_charts` row resolves to a live Chart/Table SVG, or Quick already selected one canonical Chart/Table reference in active context.

---

## 1. Canonical Reference Resolution

| Family | Canonical reference | SVG root | Construction authority |
|---|---|---|---|
| `chart` | `chart/<key>` | `templates/charts/<key>.svg` | [`executor-chart.md`](./executor-chart.md) |
| `table` | `table/<key>` | `templates/tables/<key>.svg` | [`executor-table.md`](./executor-table.md) |

| Active profile | Resolve from |
|---|---|
| Default Generate | Prefer the current `P<NN>: family/key` row from retained `spec_lock.md page_visualizations`, then read that page's `Page | Family | Template | Usage` row in Design Spec §VII; use a legacy `page_charts` row and its legacy §VII Usage only when the canonical row is absent |
| Quick Generate | Use the canonical Chart/Table `family/key` and page-local purpose already selected in active context before SVG authoring |

**Hard rule — one primary reference per page**: one page resolves at most one catalog SVG. The reference guides one dominant reusable Chart/Table information structure; secondary objects are authored from their actual content through the applicable branch without loading another catalog SVG. Independent Chart/Table children retain their §IX or Quick semantic object keys for scoped native/verification contracts.

**Mandatory — shared resolution**: resolve the selected value through `visualization_recall.py validate`; consume its canonical `reference` and `path` instead of guessing a family or constructing a path from the input string. Add `--legacy-bare` only for a value read from legacy `page_charts`.

```bash
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate <family/key>
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate \
  --legacy-bare <legacy-key>
```

New `page_visualizations` and Quick selections accept only canonical `chart/<key>` or `table/<key>`. A bare key is read-compatible only from legacy `page_charts`: it must resolve unambiguously to one live Chart/Table entry, otherwise stop for upstream correction. If canonical and legacy rows both exist for one page, stop on the duplicate contract even when both resolve to the same SVG.

**Legacy Structure boundary**: a retired Structure bare key is semantic intent, not a live visualization reference. Do not resolve it to an SVG or load this branch; recover the qualitative relationship from §IX and apply [`executor-structure.md`](./executor-structure.md) when the mandatory per-page Structure decision is yes. If §IX lacks enough meaning, return upstream for Design Spec repair.

Read the resolver-returned SVG once before its first use in the valid active context and reuse that reading until a known file change or context invalidation. Do not manually open indexes or scan family directories during Executor realization; the shared resolver owns live-catalog reads. Selection and bounded recall belong before this branch.

---

## 2. Flexible Page-local Adaptation

**Hard rule — reference, not lock**: the selected SVG is a page-local construction reference. The current §IX page block or Quick page decision plus authoritative source content owns the final information structure; the preview does not lock visualization type, geometry, styling, or native replacement.

| Preserve | Adapt freely |
|---|---|
| Authoritative labels, values, units, statuses, sources, relationships, hierarchy, and explanatory content | Dimensions, spacing, axes, grouping, orientation, density, and exact primitive/preset composition |
| Selected Usage and valid information encoding | Borrow, recombine, simplify, extend, or depart when another realization preserves the information more faithfully |
| Complete page content obligations | Palette, typography, container treatment, effects, background, and page chrome from project authorities |

**Forbidden — preview substitution**:

- Do not copy sample labels/data as content.
- Do not omit authoritative content to fit lighter preview density.
- Do not spread one page's reference to another page without its own mapping.

The namespace selects a reference registry and construction authority only; it does not assert native readiness or mirror a source PowerPoint object type. An imported table used to place duration-driven bars remains Chart semantics. Native eligibility is an independent per-object decision owned by [`native-data-interface.md`](./native-data-interface.md).
