# Getting Started

The short path to your first deck, how to use everything around it — templates, live preview, animations, narration, voice cloning — and where to look when something goes wrong. Sections follow roughly the order you meet them in a real run. Each is the quick version; follow the **Full guide →** link for depth.

- [Start from a template](#start-from-a-template)
- [Generate your first deck](#generate-your-first-deck)
- [Live preview & visual edits](#live-preview--visual-edits)
- [Animations & transitions](#animations--transitions)
- [Narration & video](#narration--video)
- [Use a cloned voice](#use-a-cloned-voice)
- [When something goes wrong](#when-something-goes-wrong)

---

## Start from a template

**Optional.** By default PPT Master uses **free design** — you don't need a template, and you can skip to the next section. Reach for one only when a deck must reuse a fixed layout set or brand identity.

**Two ways to reuse an existing `.pptx`, depending on what you want back:**

| You want… | Route | What happens |
|---|---|---|
| **This exact deck, with new content** | Template fill | Picks the pages that fit (a page can be reused for several output slides), swaps text / table / chart data straight in the original file. Design, layouts, images, animations preserved; output is the same deck, natively editable. Fastest; bound to the existing layouts. |
| **A new deck in this deck's style** | create-template | Parses the `.pptx` into a reusable style bundle, then generates a fresh deck through the SVG pipeline — new structure, any page count. More flexible; full regeneration. |

For the first, give the AI your `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" — see the [template-fill workflow](../skills/ppt-master/workflows/template-fill-pptx.md). The rest of this section covers create-template.

**To generate a new deck in an existing PowerPoint's style, you must explicitly run the create-template flow — don't just hand over a `.pptx` and expect the AI to handle it.** The AI defaults to free design and won't switch into the template flow on its own; without an explicit trigger, generation easily goes off the rails. First turn that `.pptx` into a PPT Master template via create-template:

```
You: Replicate this as a template via /create-template: projects/brand/our_deck.pptx
```

That runs `pptx_template_import.py` and rebuilds the file into a reusable workspace — layout SVGs + `design_spec.md` + extracted theme colors, fonts, and images. If you want a PowerPoint review file, run the optional preview export; it creates `exports/<id>_template_preview.pptx` on demand. The workspace root is what you point to at generation time.

During the create-template brief, choose `library` (the existing default) or `project`. Both require `templates/` and use optional `images/`, `icons/`, and on-demand `exports/`; empty optional directories are omitted. Project scope requires an initialized target project; library scope alone adds global registration.

A created template lives in one of two places:

| Location | Path | Notes |
|---|---|---|
| **Registered in the skill library** | `skills/ppt-master/templates/<kind>/<id>/` | Portable workspace plus global registration, so it appears when you ask "what templates are available?" |
| **Under projects** | `projects/<name>/` | The same portable workspace without global registration |

Invoke either result by giving its **workspace-root path** in chat. Step 3 resolves `templates/design_spec.md`; for compatibility it also accepts older flat packages whose `design_spec.md` is directly at the supplied root. A create-template run may hand its exact validated workspace root directly to Step 3 in the same conversation. Both cases stay path-based; a bare template name never triggers. The complete workspace can be copied or migrated between the library and `projects/` without restructuring it; only library registration changes.

```
You: Make a deck from sources/report.pdf with template skills/ppt-master/templates/layouts/presentation_core/
```

Full guide → [Templates Guide](./templates-guide.md)

---

## Generate your first deck

The whole loop is three steps. Install first — you only need Python; see [Quick Start](../README.md#quick-start).

1. **Drop your source material** into `projects/` — a PDF, DOCX, Markdown file, a URL, or just text you'll paste.
2. **Tell the AI in chat** what to turn into a deck (add a template path if you set one up above; otherwise it's free design):
   ```
   You: Make a deck from projects/q3-report/sources/report.pdf
   You: Turn this text into a deck: <paste your text>
   ```
3. **Get an editable `.pptx`** at `exports/<name>_<timestamp>.pptx` — real DrawingML shapes, text boxes, and charts you can click and edit in PowerPoint, Keynote, WPS, or LibreOffice.

Before it starts, the AI confirms a short design spec (template, format, page count, …); from there it handles content analysis, layout, image acquisition, SVG generation, and export — the core loop everything else builds on.

---

## Live preview & visual edits

A browser preview opens at `http://localhost:5050` while the deck is being generated.

- **Watch pages render live** as the AI produces them.
- **Edit directly, no AI** — select an element to change its text, color, font, or size in the side panel; drag it to reposition, or nudge with the arrow keys (`Shift` = 10px). `Ctrl+Z` undoes. Edits preview instantly and write to `svg_output/` when you click **Apply changes**.
- **Or annotate for the AI** — click an element, type what you want changed, hit **Submit annotations**, then say "apply my annotations" in chat and the AI rewrites that region and re-exports the PPTX.

PPT Master was chat-only by design; visual editing was folded in after enough users asked for it (built on [@WodenJay](https://github.com/WodenJay)'s [PR #85](https://github.com/hugohe3/ppt-master/pull/85)).

Full guide → [Live Preview Stage](../skills/ppt-master/workflows/stages/live-preview.md)

---

## Animations & transitions

Exported decks carry page transitions and optional per-element entrance animations as real OOXML — not embedded video. The default is a `fade` page transition with **no element animation**; opt in with `-a auto`, a named effect, or an `animations.json` sidecar when you want a reveal sequence.

Animation settings are strict: unknown effects or Start modes, invalid timing values, and missing sidecar targets fail instead of silently becoming another effect. Before the result replaces an existing output, PPT Master reads the candidate package back and checks timing placement, IDs, shape targets, effects, durations, and Start modes. Microsoft PowerPoint is the primary motion-validation target; other presentation apps can open the PPTX but may map individual animation effects differently.

Full guide → [Animations & Transitions](../skills/ppt-master/references/animations.md)

---

## Narration & video

Turn the speaker notes into per-slide voice narration, embed the audio back into the PPTX, and let PowerPoint export the deck as a synced-narration MP4 — no third-party tools.

```
You: Generate narration for this deck and re-export with audio embedded.
You: Generate narration audio for this deck
```

Narration defaults to `edge-tts` (about 90 locales); optional cloud providers cover higher-quality voices. The AI recommends a voice for the deck's language and asks once before generating.

Full guide → [Audio Narration & Video Export](./audio-narration.md)

---

## Use a cloned voice

Bring your own cloned voice from ElevenLabs / MiniMax / Qwen / CosyVoice and have the whole deck narrated in *your* voice (or a presenter's, with permission). Clone once in the provider's console, then pass the `voice_id` — PPT Master reads every slide's notes in that voice and embeds the result back into the PPTX.

Full guide → [Use a cloned voice](./audio-narration.md#use-a-cloned-voice)

---

## When something goes wrong

The [FAQ](./faq.md) is the living troubleshooting reference — continuously updated from real user reports. Quick pointers for the most common situations:

| Situation | First thing to try |
|---|---|
| The AI drifts or forgets a step | Ask it to re-read `skills/ppt-master/SKILL.md`. |
| Visual quality disappoints | Switch to a large-context Claude model + `gpt-image-2` — the harness sets the floor, the model sets the ceiling. |
| Text overflows or elements overlap | Re-run that page, or fix it in live preview; see the [FAQ](./faq.md). |
| No image-generation API key | Zero-config web search still works as a fallback; see the [FAQ](./faq.md). |
| Animations or some effects look off in another app | Microsoft PowerPoint is the primary motion-validation target. Keynote / WPS / LibreOffice can open the `.pptx`, but may remap or omit individual effects or Start semantics; validate motion-critical delivery in PowerPoint. |
| A long deck might blow the context window | Generation can run in split mode; details in the [FAQ](./faq.md). |

For model choice, cost, chart editability, custom templates, and more, the [FAQ](./faq.md) is the place to look.
