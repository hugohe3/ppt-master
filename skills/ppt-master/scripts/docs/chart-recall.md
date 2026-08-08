# Legacy Chart Recall Compatibility

`chart_recall.py` preserves the historical broad visualization-recall CLI for
existing projects and external callers. It delegates to
`visualization_recall.py`, reads the same live Chart/Table registries, and emits
the legacy bare-key JSON shape.

```bash
python3 skills/ppt-master/scripts/chart_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time"
python3 skills/ppt-master/scripts/chart_recall.py validate process_flow
```

The validation example intentionally uses the legacy bare Structure intent `process_flow`;
the shared resolver recognizes it as a Structure intent without an SVG path.
The wrapper retains the original string in its historical `valid` list and adds
a `resolved` item with `family`, `key`, and `kind`; a Structure intent omits
`reference` and `path`. New planning describes qualitative relationships in §IX
or Quick active context; it does not write a Structure catalog key.

Do not use this wrapper in new planning prompts. See
[`visualization-recall.md`](./visualization-recall.md) for the canonical
`family/key` workflow and `page_visualizations` contract.
