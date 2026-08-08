# Legacy Chart Recall Compatibility

`chart_recall.py` preserves the historical broad visualization-recall CLI for
existing projects and external callers. It delegates to
`visualization_recall.py`, reads the same live family registries, and emits the
legacy bare-key JSON shape.

```bash
python3 skills/ppt-master/scripts/chart_recall.py recall \
  --page P03 \
  --tag "process flow" \
  --tag "five stages" \
  --tag "left to right"
python3 skills/ppt-master/scripts/chart_recall.py validate process_flow
```

Do not use this wrapper in new planning prompts. See
[`visualization-recall.md`](./visualization-recall.md) for the canonical
`family/key` workflow and `page_visualizations` contract.
