# Chart Candidate Recall

`chart_recall.py` gives the Strategist a bounded deterministic shortlist, then exposes the full live catalog only when lexical confidence is `low` / `none` or the caller requests semantic review after candidate conflict. It reads `templates/charts/charts_index.json` on every invocation, so the catalog remains the only template registry.

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

`--limit` accepts 3-8 and defaults to 6. It is a maximum, not a padding target: the deterministic JSON contains only positive-scoring candidates, up to the requested limit. `low` / `none` results also contain `semantic_fallback.catalog`, allowing the Strategist to compare the page meaning against every live `Pick` / `Skip` rule without requiring lexical overlap.

When medium/high candidates all conflict with the page, rerun the same command with `--semantic-fallback`. Review the returned catalog semantically, then select one exact key or retain `no-template-match`; do not open or maintain a second keyword/category index.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `semantic_tags` | Deduplicated input tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked keys, SVG paths, verbatim catalog summaries, scores, and matched tags |
| `semantic_fallback` | Full live catalog, present only for `low` / `none` or `--semantic-fallback`; requires semantic comparison |
| `no_template_match` | Explicit fallback after the applicable lexical and semantic review finds no fit |

The scorer treats the key and the summary's Pick clause as positive evidence and the Skip clause as negative evidence. A term found only in Skip cannot make a candidate eligible, and Skip matches explicitly reduce a candidate's score. Unicode input is NFKC-normalized before matching. The Strategist still applies semantic judgment: inspect every applicable returned rule, reject candidates whose Skip clause matches, and prefer the most specific valid structure. An empty shortlist opens full semantic review; it does not authorize either a forced lexical match or immediate `no-template-match`.

## Validate selected keys

Validate every selected template key before writing `design_spec.md §VII` or `spec_lock.md page_charts`:

```bash
python3 skills/ppt-master/scripts/chart_recall.py validate line_chart quadrant_text_bullets
```

The command is read-only. It exits `0` when every key exists and `1` when any key is absent. A page recorded as `no-template-match` is not a key and must not appear in `page_charts`.

## Selection boundary

- Preserve the two-lens review: numeric/data pages and structural-information pages.
- Record the selected candidate's returned `summary` verbatim as the Section VII `summary-quote`.
- Record real returned runners-up and page-specific rejection reasons.
- Open only the selected `<key>.svg` before authoring that visualization; do not load unrelated catalog SVGs.
