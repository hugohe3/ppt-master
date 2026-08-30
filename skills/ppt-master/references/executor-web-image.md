> Load after [`executor-image.md`](./executor-image.md).

# Executor Web-image Attribution Branch

Conditional Executor authority for inline attribution on web-sourced images and their prepared derivatives.

**Trigger**: any placed `Status: Sourced` image, or a placed derivative whose filename has a copied `image_sources.json` record; Quick uses the same manifest without interaction.

## 1. Inline Attribution for Sourced Images

**Contract**: look up the filename entry and act on `license_tier` — the manifest is the single source of credits, and the credit is rendered in the SVG you author, never by post-processing or export.

| `license_tier` | Action on this slide |
|---|---|
| `no-attribution` | `<image>` only |
| `attribution-required` | `<image>` plus a visible inline credit preserving that asset's author, source/provider, and CC BY / CC BY-SA license ([image-searcher.md §7](./image-searcher.md)) |
| `manual` | `<image>` only — a user-supplied `--from-url` replacement whose rights and credit are the user's responsibility |

Start from the manifest's `attribution_text`; the filename and full URL may go when the source stays clear, but the author and license stay so the checker can bind the credit to the asset. Size, position, color, per-image versus combined treatment, labels, and any contrast scrim/gradient are Executor's as long as the credit is readable and unambiguously bound. `svg_quality_checker.py` errors on a missing image-specific author + license credit (one generic CC token never covers several files) and on an unreadable manifest or missing per-file provenance; fix before post-processing or Quick export. Never duplicate credits into speaker notes or any other artifact.
