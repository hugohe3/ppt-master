# AI Image Comparison — Three-Dimension Reference Gallery

PPT Master's AI images are governed by three orthogonal dimensions: **rendering (visual style) × palette (color behavior) × type (internal composition)**.
This directory uses **controlled-variable comparison** — vary one dimension while holding the other two fixed — so you can see exactly what each dimension contributes.

> This is **not** an example project (see `examples/` for those). It is a dimension-selection reference for the Strategist role and end users when picking AI image parameters.

## The three comparison sets

| Subdirectory | Count | Variable | Fixed baseline |
|---|---|---|---|
| [`rendering/`](./rendering/) | 16 | rendering (16 styles) | type=hero, palette=cool-corporate |
| [`palette/`](./palette/) | 10 | palette (10 color behaviors) | type=hero, rendering=vector-illustration |
| [`type/`](./type/) | 9 | type (9 internal compositions) | rendering=vector-illustration, palette=cool-corporate |

Each subdirectory contains:

- `_subject.md` — the controlled variables and the subject used for this set
- `_manifest.json` — generation manifest (status=Pending), runnable via `image_gen.py --manifest`
- `<dimension>.png` — the generated image for each rendering / palette / type

## Why these baselines

| Choice | Reason |
|---|---|
| rendering=`vector-illustration` | Most versatile in the catalog; ✓✓ compatible with all 10 palettes; minimal interference when used as the "origin" for palette / type comparisons |
| palette=`cool-corporate` | Most neutral and most common; simple color behavior (HEX 60-30-10 applied directly) so it doesn't overpower the dimension under comparison |
| type=`hero` | Single dominant subject (60-70% of canvas); most visually representative composition; differences in rendering / palette show up most clearly |

## How the images were generated

> Reference images were generated with the **OpenAI gpt-image-2** backend. Other backends (gemini / doubao / qwen / etc.) will produce visually different results — this reflects model-level differences, not differences in PPT Master's dimension system.

To reproduce or regenerate:

```bash
python3 skills/ppt-master/scripts/image_gen.py \
    --manifest ai-image-comparison/rendering/_manifest.json \
    -o ai-image-comparison/rendering/ \
    --backend openai

python3 skills/ppt-master/scripts/image_gen.py \
    --manifest ai-image-comparison/palette/_manifest.json \
    -o ai-image-comparison/palette/ \
    --backend openai

python3 skills/ppt-master/scripts/image_gen.py \
    --manifest ai-image-comparison/type/_manifest.json \
    -o ai-image-comparison/type/ \
    --backend openai
```

Generated images land in the corresponding subdirectory. Each item's `status` in the manifest is updated in place to `Generated` / `Failed` / `Needs-Manual`. Re-running only retries `Pending` and `Failed` items — `Generated` items are skipped.

## How to use

| If you are deciding... | Look at |
|---|---|
| Which rendering to lock in Strategist h.5 | `rendering/` — scan all 16 side by side; pick the visual temperament that matches the deck |
| Which palette pairs best with your chosen rendering | `palette/` — see how color behavior shifts the same subject |
| Which type fits a specific image's purpose | `type/` — match the internal composition to the page's content shape |

> The three sets are intentionally independent. When deciding rendering, do not look at the palette set — its varying colors will distort your judgment of pure rendering style.
