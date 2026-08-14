# Template Authoring & Validation

[English](./template-authoring.md) | [中文](./zh/template-authoring.md)

Custom `.pptx` templates are supported, but there is no single placeholder contract for every workflow. PPT Master has two PPTX routes. Choose the route first, then validate the file with the matching read-only report.

> This repository does not provide a `python -m ppt_master` CLI. Use the script entry points below or the chat-driven skill workflow.

## Choose the route

| Route | When to use | What the `.pptx` means | Validation aid |
|---|---|---|---|
| Fill Native PPTX | Replace content in an existing deck or slide library | Existing slide shapes are analyzed and reused | `pptx_intake.py` |
| Create Template → Generate | Import a PPTX as a reusable template workspace | The imported manifest describes detected slots | `pptx_template_import.py --manifest-only` |

There is no universal placeholder schema shared by both routes. A generic `check-template` command would hide that difference.

## Fill Native PPTX checklist

1. Keep the shape you want filled on the slide. A styled plain text box can be a fillable slot even when it is not a real PowerPoint placeholder.
2. Prefer one obvious text frame for each piece of content.
3. Keep tables and charts as native objects if you want them treated as data-bearing objects.
4. Use the normal notes text frame if speaker notes matter.
5. Run the read-only intake report before generation:

```bash
python3 skills/ppt-master/scripts/pptx_intake.py your.pptx
```

If the intended title, body, table, chart, or notes region is absent from the report, do not expect generation to target it reliably.

## Create Template → Generate checklist

1. Decide which slide/layout represents each page type.
2. Use real PowerPoint placeholders for title and body where possible.
3. If a body area is only a styled text box, check the manifest to see whether it is detected as a usable slot.
4. Keep tables and charts as native objects or clearly represented placeholder areas.
5. Generate the manifest without running a full import:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py your.pptx --manifest-only
```

The manifest is the authority for what the template route detected. Do not infer behavior from shape names alone.

## Recommended layout habits

| Content | Practical habit |
|---|---|
| Title | Use a real title placeholder or a single top-level title text box |
| Body/bullets | Use a real body placeholder, or one clearly primary text box |
| Charts | Keep native chart objects; avoid flattening charts into pictures |
| Tables | Keep native table objects; avoid outlining tables into text boxes |
| Speaker notes | Use the normal notes slide text frame |
| Decorative labels | Keep them separate from content areas; name shapes clearly for debugging |

## Troubleshooting

| Symptom | First check |
|---|---|
| Content lands in an unexpected shape | Compare the visible text frames with the intake/manifest report |
| Bullets appear on a default/fallback slide | In Create Template, the intended body slot was not detected; use a real body placeholder or simplify the text box |
| Notes are missing | Confirm the source slide has a notes text frame and the report sees it |
| Chart/table is not reused | Confirm it is a native chart/table, not a picture or grouped vector |
| Two routes behave differently | Confirm which route you are using; they do not share one placeholder schema |

## Related

- [FAQ](./faq.md)
- [Templates Guide](./templates-guide.md)
- [Templates Architecture](./templates-architecture.md)
