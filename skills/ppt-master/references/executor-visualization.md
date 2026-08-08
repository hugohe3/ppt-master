> See [`executor-base.md`](./executor-base.md) for page authoring and the family branches for actual information-model construction.

# Executor Visualization Reference Branch

Conditional Executor authority for resolving one page-local `family/key` SVG reference and adapting it without turning the catalog preview into a page specification.

**Trigger**: load only when Default `spec_lock.md page_visualizations` maps the current page to a canonical reference, a legacy project supplies a current-page `page_charts` row, or Quick already selected one canonical reference in active context.

---

## 1. Canonical Reference Resolution

| Family | Canonical reference | SVG root | Construction authority |
|---|---|---|---|
| `chart` | `chart/<key>` | `templates/charts/<key>.svg` | [`executor-chart.md`](./executor-chart.md) |
| `structure` | `structure/<key>` | `templates/structures/<key>.svg` | [`executor-structure.md`](./executor-structure.md) |
| `table` | `table/<key>` | `templates/tables/<key>.svg` | [`executor-table.md`](./executor-table.md) |

**Per-page selection authority**:

| Active profile | Resolve from |
|---|---|
| Default Generate | Prefer the current `P<NN>: family/key` row from retained `spec_lock.md page_visualizations`, then read that page's `Page | Family | Template | Usage` row in Design Spec §VII; use a legacy `page_charts` row and its legacy §VII Usage only when the canonical row is absent |
| Quick Generate | Use the canonical `family/key` and page-local purpose already selected in active context before SVG authoring |

**Hard rule — one primary reference per page**: one page resolves at most one catalog SVG. The reference guides the page's dominant reusable information structure; secondary objects are authored from their actual content through the applicable family branch without loading another catalog SVG. Independent Chart/Table children retain their §IX or Quick semantic object keys for scoped native/verification contracts. A page may still activate several family branches when it genuinely contains several information models.

**Mandatory — shared resolution**: resolve the selected value through `visualization_recall.py validate`; consume its canonical `reference` and `path` instead of guessing a family or constructing a path from the input string. Add `--legacy-bare` only for a value read from legacy `page_charts`.

```bash
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate <family/key>
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate \
  --legacy-bare <legacy-key>
```

New `page_visualizations` and Quick selections accept only canonical `chart/<key>`, `structure/<key>`, or `table/<key>`. A bare key is read-compatible only from legacy `page_charts`: the shared resolver must produce exactly one canonical entry, otherwise stop for upstream correction. Never write the normalized result back into the legacy lock or silently choose among ambiguous families. If canonical and legacy rows both exist for one page, stop on the duplicate contract even when both values resolve to the same SVG.

Read the resolver-returned SVG once before its first use in the valid active context and reuse that reading until a known file change or context invalidation. Do not manually open indexes or scan family directories during Executor realization; the shared resolver owns live-catalog reads. Selection and bounded recall belong before this branch; this branch only resolves the already-selected reference.

---

## 2. Flexible Page-local Adaptation

**Hard rule — reference, not lock**: the selected SVG is a page-local construction reference. The current §IX page block or Quick page decision plus authoritative source content owns the final information structure; the preview does not lock visualization type, geometry, styling, or native replacement.

| Preserve | Adapt freely |
|---|---|
| Authoritative labels, values, units, statuses, sources, relationships, hierarchy, and explanatory content | Dimensions, spacing, axes, grouping, orientation, density, and exact primitive/preset composition |
| The selected page-local Usage and any information encoding that remains valid for the actual content | Borrow, recombine, simplify, extend, or depart from the preview when another realization preserves the same information more faithfully |
| The active page's complete content obligations | Palette, typography, container treatment, effects, background, and page chrome from the project authorities |

**Forbidden — preview substitution**:

- Do not copy the preview verbatim or treat its sample labels/data as content.
- Do not omit authoritative content to fit the preview's lighter density.
- Do not spread one page's reference to another page without that page's own selected mapping.

The `family` namespace selects a reference registry and its construction authority only. It does not assert that an object is native-ready; native eligibility is an independent per-object decision owned exclusively by [`native-data-interface.md`](./native-data-interface.md).
