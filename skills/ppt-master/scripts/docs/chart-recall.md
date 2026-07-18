# Chart Candidate Recall

`chart_recall.py` gives the Strategist a bounded, deterministic shortlist without loading the full chart catalog into the runtime prompt. It reads `templates/charts/charts_index.json` on every invocation, so the catalog remains the only template registry.

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

`--limit` accepts 3-8 and defaults to 6. It is a maximum, not a padding target: the deterministic JSON contains only positive-scoring candidates, up to the requested limit. Zero positive matches return an empty `candidates` list plus the explicit `no-template-match` option.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `semantic_tags` | Deduplicated input tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked keys, SVG paths, verbatim catalog summaries, scores, and matched tags |
| `no_template_match` | Explicit fallback option when every candidate conflicts with the page |

The scorer treats the key and the summary's Pick clause as positive evidence and the Skip clause as negative evidence. A term found only in Skip cannot make a candidate eligible, and Skip matches explicitly reduce a candidate's score. Unicode input is NFKC-normalized before matching. The Strategist still applies semantic judgment: inspect every returned summary, reject candidates whose Skip clause matches, and prefer the most specific valid structure. A low score does not authorize a forced match; when no candidate has a positive final score, the result carries an empty shortlist and the explicit fallback.

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
