> Load after [`executor-image.md`](./executor-image.md).

# Executor Web-image Attribution Branch

Conditional Executor authority for inline attribution on web-sourced images.

**Trigger**: load when at least one placed image has `Status: Sourced`.

## 1. Inline Attribution for Sourced Images

Whenever the slide uses an image with `Status: Sourced`, look up the corresponding entry in `project/images/image_sources.json` and act on `license_tier`:

| `license_tier` | Action on this slide |
|---|---|
| `no-attribution` | Embed the `<image>` element only. **No credit element needed.** |
| `attribution-required` | Embed the `<image>` element **plus** a visible inline credit that preserves the asset-specific legal content in [image-searcher.md §7](./image-searcher.md). |
| `manual` | Embed the `<image>` element only. **No credit element** — a user-supplied `--from-url` replacement; verifying usage rights / any required credit is the user's responsibility. |

The credit is **not** rendered by post-processing or export — it must be present in the SVG you produce. Preserve that asset's author, source/provider, and CC BY / CC BY-SA license facts. Size, position, color, per-image versus combined treatment, labels, and any contrast scrim/gradient are Executor-owned as long as the credit stays readable and unambiguously bound to the correct image.

Use `attribution_text` from the manifest entry as the **starting point**. You may omit the filename and full URL when the visible source/provider remains clear, but retain that image's author and CC BY / CC BY-SA license so the quality checker can bind the credit to the referenced asset. For CC0/PD images that landed in the `attribution-required` tier only because of upstream metadata quirks (rare), credits are still safe to render.

`svg_quality_checker.py` treats a missing image-specific author + license credit as an **error**; one generic CC token does not cover multiple files. An unreadable/missing manifest or missing per-file provenance is also blocking. Fix the manifest or SVG before post-processing.

**The manifest is the single source of truth for credits.** Do not duplicate license info into speaker notes or any other artifact.
