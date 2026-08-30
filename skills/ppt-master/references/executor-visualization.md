> See [`executor-base.md`](./executor-base.md) for page authoring and the Chart/Table branches for information-model construction.

# Executor Visualization Reference Branch

Conditional Executor authority for resolving one page-local Chart/Table `family/key` SVG reference and adapting it without turning the catalog preview into a page specification.

**Trigger**: Default `spec_lock.md page_visualizations` maps the current page to a canonical Chart/Table reference, a legacy `page_charts` row resolves to a live Chart/Table SVG, or Quick already selected one canonical reference in active context.

---

## 1. Canonical Reference Resolution

| Family | Canonical reference | SVG root | Construction authority |
|---|---|---|---|
| `chart` | `chart/<key>` | `templates/charts/<key>.svg` | [`executor-chart.md`](./executor-chart.md) |
| `table` | `table/<key>` | `templates/tables/<key>.svg` | [`executor-table.md`](./executor-table.md) |

| Active profile | Resolve from |
|---|---|
| Default Generate | The current `P<NN>: family/key` row in retained `spec_lock.md page_visualizations`, then that page's `Page \| Family \| Template \| Usage` row in Design Spec §VII; a legacy `page_charts` row and its §VII Usage only when the canonical row is absent |
| Quick Generate | The canonical `family/key` and page-local purpose already selected in active context before SVG authoring |

**Mandatory — shared resolution**: resolve through `visualization_recall.py validate` and consume its canonical `reference` and `path`; never guess a family or build a path from the input string. Add `--legacy-bare` only for a value read from legacy `page_charts`.

```bash
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate <family/key>
python3 ${SKILL_DIR}/scripts/visualization_recall.py validate --legacy-bare <legacy-key>
```

**Hard rule — one primary reference per page**: one page resolves at most one catalog SVG, guiding one dominant reusable Chart/Table structure; secondary objects are authored from their content through the applicable branch without another catalog SVG, keeping their §IX or Quick object keys for native/verification contracts. New `page_visualizations` and Quick selections accept only canonical `chart/<key>` or `table/<key>`; a bare key is read-compatible only from legacy `page_charts` and must resolve unambiguously, otherwise stop for upstream correction. Canonical and legacy rows for one page stop on the duplicate contract even when both resolve to the same SVG.

**Legacy Structure boundary**: a retired Structure bare key is semantic intent, not a reference — do not resolve it or load this branch; recover the relationship from §IX and apply [`executor-structure.md`](./executor-structure.md) when the per-page Structure decision is yes, or return upstream when §IX lacks meaning.

Read the resolver-returned SVG once before first use and reuse that reading until a known file change; do not reopen indexes or scan family directories during realization — the planning owner already reviewed the live registries.

---

## 2. Flexible Page-local Adaptation

**Hard rule — reference, not lock**: the selected SVG is a page-local construction reference. The §IX page block or Quick page decision plus authoritative content owns the final information structure; the preview locks no visualization type, geometry, styling, or native replacement.

| Preserve | Adapt freely |
|---|---|
| Authoritative labels, values, units, statuses, sources, relationships, hierarchy, and explanatory content | Dimensions, spacing, axes, grouping, orientation, density, and exact primitive/preset composition |
| Selected Usage and valid information encoding | Borrow, recombine, simplify, extend, or depart when another realization preserves the information more faithfully |
| Complete page content obligations | Palette, typography, container treatment, effects, background, and page chrome from project authorities |

**Forbidden — preview substitution**: copying sample labels/data as content; omitting authoritative content to fit lighter preview density; spreading one page's reference to another page without its own mapping.

The namespace selects a registry and construction authority only; it asserts no native readiness and mirrors no source PowerPoint object type — an imported table used to place duration-driven bars remains Chart semantics. Native eligibility is an independent per-object decision owned by [`native-data-interface.md`](./native-data-interface.md).
