# Chart Candidate Recall

`chart_recall.py` gives the Strategist a bounded deterministic shortlist. It exposes the full live catalog only when the caller explicitly requests semantic review. It reads `templates/charts/charts_index.json` on every invocation, so the catalog remains the only template registry.

## Recall candidates

Describe one page's information shape with 3-8 concise English semantic tags. Translate source-language or industry terms into structural meaning before invoking the script.

```bash
python3 skills/ppt-master/scripts/chart_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time" \
  --limit 6
```

`--limit` accepts 3-8 and defaults to 6. The JSON is already bounded and must be read unfiltered: `tail`, `head`, `grep`, or another truncator can discard higher-ranked candidates. `confidence` reports lexical strength only; it never decides whether a candidate fits. At `low` / `none`, a fitting bounded candidate needs no expansion, but `no_template_match.allowed` remains false until one explicit semantic fallback review.

Semantically review the bounded candidates. At `high` / `medium`, retain `no-template-match` when none fits. At `low` / `none`, select a fitting bounded candidate directly; otherwise rerun the same command once with `--semantic-fallback`, compare the returned rules semantically, and only then retain `no-template-match`. The full-catalog review is therefore a narrow low-confidence no-match gate, not a routine recall step. Do not open or maintain a second keyword/category index. `no-template-match` is an internal recall result, not a Design Spec §VII row.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `semantic_tags` | Deduplicated input tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked keys, SVG paths, verbatim catalog summaries, scores, and matched tags |
| `semantic_fallback` | Full live catalog, present only with `--semantic-fallback`; requires semantic comparison |
| `no_template_match` | Explicit fallback; `allowed` stays false for `low` / `none` until `--semantic-fallback` is used |

The scorer treats the key and the summary's Pick clause as positive evidence and the Skip clause as negative evidence. A term found only in Skip cannot make a candidate eligible, and Skip matches explicitly reduce a candidate's score. Unicode input is NFKC-normalized before matching. The Strategist still applies semantic judgment: inspect the returned candidates, reject candidates whose Skip clause matches, and prefer the most specific valid structure. An empty or low-confidence shortlist requires one `--semantic-fallback` review only when the Strategist is about to keep `no-template-match`.

## Validate selected keys

Validate every selected template key before writing `design_spec.md §VII` or `spec_lock.md page_charts`:

```bash
python3 skills/ppt-master/scripts/chart_recall.py validate line_chart quadrant_text_bullets
```

The command is read-only. It exits `0` when every key exists and `1` when any key is absent. A `no-template-match` page appears in neither §VII nor `page_charts`; record its chosen fallback in the page's §IX `Visualization` / `Layout` instead.

## Selection boundary

- Preserve the two-lens review: numeric/data pages and structural-information pages.
- Keep §VII as a positive selection list: record `Page | Template | Usage` for each selected key, and omit the whole section when no candidate is selected.
- Make `Usage` one concise page-local purpose, not geometry or execution instructions; derive `templates/charts/<key>.svg` from the key and keep detailed adaptation in §IX.
- Never serialize `no-template-match`, an empty table, or a no-reference explanation into §VII.
- Do not serialize returned summaries, paths, or runners-up into new §VII tables. Legacy wider tables remain readable.
- Open the selected `<key>.svg` only as a reference for its mapped page; it does not lock type or geometry. Do not load unrelated catalog SVGs.
