# Image Palettes Legacy Reference

Compatibility tombstone for retired `image_palette` fields and historical palette comparison assets.

## 1. Current Generation Contract

**Hard rule**: Current deck generation never presents, selects, authors, or consumes `image_palette` or `image_palette_behavior`.

| Input | Current behavior |
|---|---|
| `spec_lock.md colors` | Sole source of generated-image color roles and exact HEX values |
| `image_rendering` | Controls rendering treatment only; it does not create a second color decision |
| Legacy `image_palette` row | Ignore it; it cannot override the deck color lock |
| No palette row | Expected; do not synthesize a preset or `custom` fallback |

**Forbidden — legacy activation**:

- Do not load sibling palette preset files while planning or generating a current deck.
- Do not use the historical auto-selection table, compatibility matrix, or prompt snippets.
- Do not write `image_palette: custom` or `image_palette_behavior`.

---

## 2. Legacy Interpretation and Maintenance

The sibling preset files remain archived in place for diagnosing historical locks and maintaining the legacy palette comparison assets documented by [`README.md`](../ai-image-comparison/README.md). They are not a runtime catalog.

| Legacy row | Historical meaning |
|---|---|
| `image_palette: <preset>` | Selects the named sibling preset as the archived color-behavior definition. |
| `image_palette: custom` | Declares that no preset owns the behavior; the required sibling `image_palette_behavior` row is the complete definition. |
| `image_palette_behavior: <prose>` | With `custom`, records a 2–5 sentence mapping from the lock's HEX roles to intended proportion and temperament. It must not name a competing preset or invent another HEX value. |

A historical `custom` row without a non-empty `image_palette_behavior` is incomplete. Report the missing legacy definition; do not reconstruct it.

When that maintenance is explicitly requested, read only the named historical asset or preset. Keep its palette behavior inside the historical fixture; do not copy it into current recommendations, `design_spec.md`, `spec_lock.md`, or generated-image prompts.
