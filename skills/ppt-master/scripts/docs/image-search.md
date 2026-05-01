# Web Image Search Tools

## `image_search.py`

Search legally reusable web images, filter them by license, download them into `project/images/`, and write `image_sources.json`.

```bash
python3 scripts/image_search.py "offshore wind farm" --provider openverse -o projects/demo/images --filename cover_bg.jpg --slide 01_cover --purpose "Cover background" --orientation landscape
python3 scripts/image_search.py "executive team meeting" --provider wikimedia -o projects/demo/images --filename team.jpg --slide 03_team --purpose "Leadership photo" --orientation landscape
```

## Providers

Zero-config (no API key required):

- `openverse` — Openverse, openly licensed images from across the web
- `wikimedia` — Wikimedia Commons, educational, scientific, geographic, historical imagery

Optional keyed (better quality for commercial presentations):

- `pexels` — Pexels (requires `PEXELS_API_KEY`)
- `pixabay` — Pixabay (requires `PIXABAY_API_KEY`)

## License Policy

Allowed by default: Public Domain, CC0, CC BY, CC BY-SA, Pexels License, Pixabay Content License.

Rejected by default: CC BY-NC, CC BY-ND, CC BY-NC-SA, CC BY-NC-ND, Unknown license.

## Output

- Image file saved to the specified output directory
- `image_sources.json` manifest with full acquisition metadata
- Attribution text written into the corresponding slide notes file (when `--slide` is provided)
