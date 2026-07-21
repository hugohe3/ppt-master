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

`--limit` accepts 3-8 and defaults to 6. It is a maximum, not a padding target: the deterministic JSON contains only positive-scoring candidates, up to the requested limit. `confidence` reports lexical recall strength only; `low` / `none` never expands the result or decides whether a template should be used.

Semantically review the bounded candidates. If none fits and the page clearly needs a custom composition, retain `no-template-match`. If terminology mismatch or structural ambiguity suggests that bounded recall may have missed a catalog match, rerun the same command with `--semantic-fallback`, then compare the returned rules semantically. The flag is an uncertainty fallback, not a routine no-match gate. Do not open or maintain a second keyword/category index. `no-template-match` is an internal recall result, not a Design Spec §VII row.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `semantic_tags` | Deduplicated input tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked keys, SVG paths, verbatim catalog summaries, scores, and matched tags |
| `semantic_fallback` | Full live catalog, present only with `--semantic-fallback`; requires semantic comparison |
| `no_template_match` | Explicit fallback when the Strategist judges that no recalled reference fits |

The scorer treats the key and the summary's Pick clause as positive evidence and the Skip clause as negative evidence. A term found only in Skip cannot make a candidate eligible, and Skip matches explicitly reduce a candidate's score. Unicode input is NFKC-normalized before matching. The Strategist still applies semantic judgment: inspect the returned candidates, reject candidates whose Skip clause matches, and prefer the most specific valid structure. An empty shortlist permits `no-template-match`; use `--semantic-fallback` only when the Strategist suspects a relevant catalog structure was missed.

## Validate selected keys

Validate every selected template key before writing `design_spec.md §VII` or `spec_lock.md page_charts`:

```bash
python3 skills/ppt-master/scripts/chart_recall.py validate line_chart quadrant_text_bullets
```

The command is read-only. It exits `0` when every key exists and `1` when any key is absent. A `no-template-match` page appears in neither §VII nor `page_charts`; record its chosen fallback in the page's §IX `Visualization` / `Layout` instead.

## Selection boundary

- Preserve the two-lens review: numeric/data pages and structural-information pages.
- Record the selected candidate's returned `summary` verbatim as the Section VII `summary-quote`.
- Keep §VII as a positive inventory: every row has a real key/path, and the whole section is omitted when no candidate is selected.
- Never serialize `no-template-match`, an empty table, or a no-reference explanation into §VII.
- Record real returned runners-up and page-specific rejection reasons only for pages with a selected reference.
- Open only the selected `<key>.svg` before authoring that visualization; do not load unrelated catalog SVGs.
