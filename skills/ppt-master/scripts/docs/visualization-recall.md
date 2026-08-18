# Visualization Candidate Recall

Default Strategist and the Quick Generate main agent read both complete compact
registries before planning. `visualization_recall.py validate` resolves their
selected canonical references. Its `recall` command remains an optional
deterministic diagnostic across the same live Chart and Table registries; it is
not the runtime capability-discovery gate and cannot replace the complete
registry review. The tool reads these indexes on every invocation and maintains
no second category or keyword index:

- `templates/charts/charts_index.json`
- `templates/tables/tables_index.json`

Qualitative Structure does not enter recall. Default records its relationship
model in §IX; Quick keeps the same decision in active context. Both load
`executor-structure.md` and compose the shapes for the current page.

## Optional recall diagnostics

Describe one page's information shape with 3-8 concise English semantic tags.
Translate source-language or industry terms into structural meaning first.

```bash
python3 skills/ppt-master/scripts/visualization_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time" \
  --limit 6
```

Use `--family chart|table` only when the page semantics already make that
boundary certain; the default `all` preserves unified Chart/Table recall.
`--limit` accepts 3-8 and defaults to 6. Read the returned JSON unfiltered:
`tail`, `head`, `grep`, or another truncator can discard higher-ranked
candidates. `confidence` reports lexical strength only and never decides fit.

At `high` / `medium`, retain `no-template-match` when none fits. At `low` /
`none`, select a fitting bounded candidate directly; otherwise rerun the same
command once with `--semantic-fallback` to inspect its diagnostic payload. The
runtime owner still bases selection on the complete registries already loaded
before planning.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `family_filter` | Requested family or `all` |
| `semantic_tags` | Deduplicated input tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked family/key references, SVG paths, summaries, scores, and matched tags |
| `semantic_fallback` | Selected live catalogs, present only with `--semantic-fallback` |
| `no_template_match` | Explicit fallback; blocked at low/none until semantic fallback review |

The scorer treats the key and summary Pick clause as positive evidence and the
Skip clause as negative evidence. A term found only in Skip cannot make a
candidate eligible. Unicode input is NFKC-normalized before matching. The
active profile owner still applies semantic judgment and prefers the most
specific valid information structure.

## Validate selected references

Validate every selected reference before Default writes Design Spec §VII and
`spec_lock.md page_visualizations`, or before Quick opens it for immediate use:

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  chart/line_chart table/record_table
```

The command is read-only. It exits `0` when every supplied reference resolves
to a registered SVG and `1` otherwise. New planning supplies canonical
`family/key`. When validating an existing legacy mapping, opt into bare-key
resolution explicitly; every key must resolve uniquely:

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  --legacy-bare pros_cons_chart
```

A Default `no-template-match` page appears in neither §VII nor
`page_visualizations`; record its custom fallback in §IX. A qualitative
Structure is not a no-match case: describe its relationships in §IX and build
it without catalog lookup.

## Selection boundary

- Runtime selection comes from the complete loaded registries; recall output is
  optional diagnostic evidence, while `validate` resolves positive selections.
- Default records `Page | Family | Template | Usage` for each positive
  selection and projects `family/key` into `page_visualizations`.
- Usage is one concise page-local purpose; detailed adaptation remains in §IX.
- Quick keeps the selected reference and purpose only in active context.
- Structure is a separate runtime information model, never a catalog candidate
  or `page_visualizations` entry.
- Never serialize `no-template-match`, empty tables, summaries, paths, or
  runners-up into planning artifacts.
- Open only the selected SVG for its mapped page. It is a flexible reference,
  not a type, geometry, style, or native-replacement lock.

## Legacy compatibility

`chart_recall.py` remains a compatibility wrapper for existing callers. It
uses the same scorer and live Chart/Table registries, preserves bare-key
validation and the historical JSON shape, and resolves live candidates to their
current family paths. New prompts and automation use `visualization_recall.py`.

When `validate --legacy-bare` receives one of the 36 retired canonical Structure
bare keys, the shared resolver returns `kind=legacy-structure-intent`,
`family=structure`, and the original key without `path` or `reference`. This
compatibility result is a semantic hint for old `page_charts`, not a live catalog
entry, and never participates in recall.
