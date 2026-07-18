> Load after [`executor-image.md`](./executor-image.md).

# Executor Web-image Attribution Branch

Conditional Executor authority for inline attribution on web-sourced images.

**Trigger**: load when at least one placed image has `Status: Sourced`.

## 1. Inline Attribution for Sourced Images

Whenever the slide uses an image with `Status: Sourced`, look up the corresponding entry in `project/images/image_sources.json` and act on `license_tier`:

| `license_tier` | Action on this slide |
|---|---|
| `no-attribution` | Embed the `<image>` element only. **No credit element needed.** |
| `attribution-required` | Embed the `<image>` element **plus** a small inline `<text>` credit element per the visual spec in [image-searcher.md §7](./image-searcher.md). |
| `manual` | Embed the `<image>` element only. **No credit element** — a user-supplied `--from-url` replacement; verifying usage rights / any required credit is the user's responsibility. |

The credit text is **not** rendered by post-processing or export — it must be present in the SVG you produce. The shape of the credit element (size, position, color, multi-image source line, hero gradient overlay) is specified in [image-searcher.md §7](./image-searcher.md). Do not invent a different style.

Use `attribution_text` from the manifest entry as the **starting point**, then compress for the small-text constraint (drop URL, drop filename, keep "via Provider / License"). For CC0/PD images that landed in the `attribution-required` tier only because of upstream metadata quirks (rare), credits are still safe to render.

`svg_quality_checker.py` treats missing CC BY / CC BY-SA inline attribution as an **error**. Fix the offending SVG before post-processing.

**The manifest is the single source of truth for credits.** Do not duplicate license info into speaker notes or any other artifact.
