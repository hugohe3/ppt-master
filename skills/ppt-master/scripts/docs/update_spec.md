# update_spec.py

Propagate a `spec_lock.md` value change to both the lock file and every `svg_output/*.svg`. The single edit surface for bulk style tweaks after generation.

## Usage

```bash
python3 skills/ppt-master/scripts/update_spec.py <project_path> <key>=<value>
```

One invocation = one change. The tool:

1. Reads the old value from `<project_path>/spec_lock.md`
2. Writes the new value into `spec_lock.md`
3. Replaces every occurrence of the old value with the new value across `svg_output/*.svg`
4. Prints the list of files touched

## Examples

```bash
# swap the primary color deck-wide
python3 skills/ppt-master/scripts/update_spec.py projects/acme_ppt169_20260301 primary=#0066AA

# adjust the accent color
python3 skills/ppt-master/scripts/update_spec.py projects/acme_ppt169_20260301 accent=#FF6B35
```

## v1 scope

- **Supported**: keys under `## colors` in `spec_lock.md` (bulk HEX replacement)
- **Not supported**: typography sizes, `font_family`, icons, images — these involve attribute-scoped replacements whose risk/benefit was not worth the first cut. Edit `spec_lock.md` and the affected SVGs by hand if you need to change them; re-author the page if the edit is substantial.

## When to use

- "Change the primary color across the whole deck" → one `update_spec.py` call
- "Switch an individual page's accent" → just edit that page's SVG directly; no tool needed
- "Re-design the color palette" → update `spec_lock.md` manually, then the Executor can regenerate affected pages

## Safety

- HEX values (e.g. `#005587`) are unique enough in SVG content that literal replacement is safe
- The tool refuses non-HEX inputs and unknown keys
- No backups are created — the project folder should be under git so you can diff / revert
