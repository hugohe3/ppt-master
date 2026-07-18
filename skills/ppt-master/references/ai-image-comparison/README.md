# AI Image Comparison — Reference Gallery

This directory preserves rendering, legacy palette, and type comparison assets. The current Confirm UI displays **rendering only**; deck colors come directly from the selected PPT color system. The palette gallery remains for legacy diagnostics and must not become a second confirmation control.
This directory uses **controlled-variable comparison** — vary one dimension while holding the other two fixed — so you can see exactly what each dimension contributes.

> This is **not** an example project. The rendering set remains a selection reference; the palette set is legacy diagnostic material, and the type set is an internal composition reference.

## The three comparison sets

| Subdirectory | Count | Variable | Fixed baseline |
|---|---|---|---|
| [`rendering/`](./rendering/) | 20 | rendering (20 styles) | single-subject hero composition (§4.1 Primitive A), palette=cool-corporate |
| [`palette/`](./palette/) | 14 | palette (14 color behaviors) | single-subject hero composition (§4.1 Primitive A), rendering=vector-illustration |
| [`type/`](./type/) | 11 | type (11 internal compositions for `page_role: local`) | rendering=vector-illustration, palette=cool-corporate |

Each subdirectory contains:

- `_subject.md` — the controlled variables and the subject used for this set
- `_manifest.json` — generation manifest (status=Pending), runnable via `image_gen.py --manifest`
- `<dimension>.png` — the generated image for each rendering / palette / type

> `page_role: hero_page` images don't pick an `image_type` — they use the four composition primitives in [`image-generator.md`](../image-generator.md) §4.1 directly (single-subject / portrait / typographic / atmospheric). The 11 types in `type/` are for local infographic blocks only.

## Why these baselines

| Choice | Reason |
|---|---|
| rendering=`vector-illustration` | Most versatile in the catalog; ✓✓ compatible with all 14 palettes; minimal interference when used as the "origin" for palette / type comparisons |
| palette=`cool-corporate` | Most neutral and most common; simple color behavior (HEX 60-30-10 applied directly) so it doesn't overpower the dimension under comparison |
| composition=single-subject hero (§4.1 Primitive A) | One dominant subject (60-70% of canvas) — the most visually representative shape, so rendering / palette differences show up most clearly |

## How the images were generated

> Reference images were generated with the **OpenAI gpt-image-2** backend. Other backends (gemini / doubao / qwen / etc.) will produce visually different results — this reflects model-level differences, not differences in PPT Master's dimension system.

To reproduce or regenerate:

```bash
python3 skills/ppt-master/scripts/image_gen.py \
    --manifest skills/ppt-master/references/ai-image-comparison/rendering/_manifest.json \
    -o skills/ppt-master/references/ai-image-comparison/rendering/ \
    --backend openai

python3 skills/ppt-master/scripts/image_gen.py \
    --manifest skills/ppt-master/references/ai-image-comparison/palette/_manifest.json \
    -o skills/ppt-master/references/ai-image-comparison/palette/ \
    --backend openai

python3 skills/ppt-master/scripts/image_gen.py \
    --manifest skills/ppt-master/references/ai-image-comparison/type/_manifest.json \
    -o skills/ppt-master/references/ai-image-comparison/type/ \
    --backend openai
```

Generated images land in the corresponding subdirectory. Each item's `status` in the manifest is updated in place to `Generated` / `Failed` / `Needs-Manual`. Re-running only retries `Pending` and `Failed` items — `Generated` items are skipped.

## How to use

| If you are deciding... | Look at |
|---|---|
| Which rendering to lock in [`strategist-image.md`](../strategist-image.md) §2 | `rendering/` — scan all 20 side by side; pick the visual temperament that matches the deck |
| Diagnosing a legacy palette lock or comparison asset | `palette/` — see how historical color behaviors shift the same subject; do not expose it as a new-flow choice |
| Which type fits a specific image's purpose | `type/` — match the internal composition to the page's content shape |

> The three sets are intentionally independent. When deciding rendering in the current flow, use only `rendering/`; the legacy palette set must not influence or reintroduce a separate color decision.
