# Getting Started

[English](./getting-started.md) | [Chinese](./zh/getting-started.md)

---

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

**Optional.** By default PPT Master uses **free design** — you don't need a template, and you can skip to the next section. Reach for one when a deck must reuse a brand identity, a communication/design method, a fixed layout set, or a recurring deck application.

**Two ways to reuse an existing `.pptx`, depending on what you want back:**

| You want… | Route | What happens |
|---|---|---|
| **Use this deck's native slide shells with new content** | Fill Native PPTX | Clones the selected source slides and patches text / table / chart data directly in OOXML. The source design remains native; output is a new filled deck bound to the available slide shells. |
| **Build a reusable design system, then generate a new deck** | Create Template → Generate PPTX | Creates a validated Brand, Style, Layout, or Deck workspace from the reference, then authors a fresh deck. The new story, structure, and page count can differ from the source. |

For the first, give the AI your `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" — see the [template-fill workflow](../skills/ppt-master/workflows/template-fill-pptx.md). The rest of this section covers create-template.

**To build a reusable workspace from an existing PowerPoint, explicitly request the Create Template route.** A raw `.pptx` plus new material otherwise belongs to Fill Native PPTX; it is not a Generate template workspace. Create the workspace first:

```
You: Create a reusable Deck template from projects/brand/our_deck.pptx via /create-template
```

Create Template analyzes the reference, confirms whether the result is a Brand, Style, Layout, or Deck, and then authors or materializes a new validated workspace. The importer supplies source evidence; the final workspace owns `templates/design_spec.md` plus any prototypes and assets required by its kind. Brand and Style are roster-free; Layout and Deck own structured SVG prototypes. If you want a PowerPoint review file for Layout or Deck, run the optional preview export; it creates `exports/<id>_template_preview.pptx` on demand. The workspace root is what you point to at generation time.

During the create-template brief, choose `library` (the existing default) or `project`. Both require `templates/` and use optional `images/`, `icons/`, and on-demand `exports/`; empty optional directories are omitted. Project scope requires an initialized target project; library scope alone adds global registration.

A created template lives in one of two places:

| Location | Path | Notes |
|---|---|---|
| **Registered in the skill library** | `skills/ppt-master/templates/<kind>/<id>/` | Portable workspace plus global registration, so it appears when you ask "what templates are available?" |
| **Under projects** | `projects/<name>/` | The same portable workspace without global registration |

Default Generate shows the template choice inside Stage 1, beside the communication contract. The initial communication recommendation is written without reading any template. Ordinary requests start with free design; explicit template intent or any exact root starts in template mode, and the user can always switch. To offer another result, supply its exact **workspace-root path** in chat: an unregistered root appears in the specified-root dropdown, while an exact registered match resolves back to its kind dropdown. Exactly one supplied root may be preselected; multiple supplied roots remain unselected candidates. One confirmation closes communication and template choice together. Only then are selected workspaces validated and installed; template-aware planning begins in final Stage 2. A bare template name never resolves to a workspace. The complete workspace can be copied or migrated between the library and `projects/` without restructuring it; only library registration changes.

```
You: Make a deck from sources/report.pdf with template skills/ppt-master/templates/layouts/presentation_core/
```

Full guide → [Templates Guide](./templates-guide.md)

---

## Generate your first deck

The whole loop is three steps. Install first — you only need Python; see [Quick Start](../README.md#quick-start).

1. **Drop your source material** into `projects/` — a PDF, DOCX, Markdown file, a URL, or just text you'll paste.
2. **Tell the AI in chat** what to turn into a deck. Stage 1 then lets you confirm the communication contract together with free design or template use; add one exact workspace root when you want template mode and that path preselected:
   ```
   You: Make a deck from projects/q3-report/sources/report.pdf
   You: Turn this text into a deck: <paste your text>
   ```
3. **Get an editable `.pptx`** at `exports/<name>_<timestamp>.pptx` — real DrawingML shapes, text boxes, and charts you can click and edit in PowerPoint, Keynote, WPS, or LibreOffice.

Before generation, Stage 1 confirms the communication contract, canvas/format, and free-design/template choice together. The AI then installs any selected workspace; final Stage 2 reads that installed state and confirms page count, the visual system, template application, and production choices. From there it handles content analysis, layout, image acquisition, SVG generation, and export — the core loop everything else builds on. To skip interactive confirmation, see [Quick mode](#quick-mode) below.

---

## Quick mode

The default flow runs its combined Stage-1 communication/template choice followed by final Stage 2. To skip that interaction, explicitly ask for **quick generation**:

```
You: Quickly generate a deck from sources/report.pdf — no need to confirm with me
You: Turn this into a deck, skip the confirmation, about 8 pages, dark corporate look
```

**Whatever you state explicitly is followed; whatever you leave unspecified the agent decides directly, without coming back to ask.** The page count and the look in the second example still hold — quick mode drops the round trip, not your say. State nothing, and the agent decides everything.

Quick mode never opens the Confirm UI template selector. Give it up to one exact
Brand / Style / Layout / Deck workspace root per kind and it validates,
installs, and uses them directly; give it no exact root and it uses free design.
A bare template name or style phrase is still only a design brief. Quick keeps
its lockless flat export, so Layout / Deck prototypes guide the authored pages
but do not compile into reusable native Master / Layout objects.

It does not skip capabilities: source conversion, research on identified factual gaps, shared aesthetic guidance, image / icon preparation, and native-shape / chart / table authoring still run as needed. Structural formulas are authored directly as native PowerPoint markers rather than prepared as image assets. If a required asset is missing, it still stops and asks you for it instead of substituting unrelated material.

Quick is a one-pass profile, not a shortened resumable workflow. It creates no Strategist record, `design_spec.md`, `spec_lock.md`, or substitute page plan; its content/design/resource decisions exist only in the active AI context. If that context is lost before delivery, start Quick again. Operational manifests, quality reports, postflight, and the cold Python audit log may remain, but they cannot reconstruct why the AI designed the deck that way. The profile reduces interaction and durable planning, not the available presentation toolbox or the intended quality bar.

Full guide → [quick-generate profile](../skills/ppt-master/workflows/profiles/quick-generate.md)

---

## Live preview & visual edits

A browser preview opens at the URL reported by the launcher while the deck is being generated. It prefers `http://localhost:5050` and uses the next free port when `5050` is occupied.

- **Watch pages render live** as the AI produces them.
- **Edit directly, no AI** — select an element to change its text, color, font, or size in the side panel; drag it to reposition, or nudge with the arrow keys (`Shift` = 10px). `Ctrl+Z` undoes. Edits preview instantly and write to `svg_output/` when you click **Apply changes**.
- **Or annotate for the AI** — click an element, type what you want changed, hit **Submit annotations**, then say "apply my annotations" in chat and the AI rewrites that region and re-exports the PPTX.

PPT Master was chat-only by design; visual editing was folded in after enough users asked for it (built on [@WodenJay](https://github.com/WodenJay)'s [PR #85](https://github.com/hugohe3/ppt-master/pull/85)).

Full guide → [Live Preview Stage](../skills/ppt-master/workflows/stages/live-preview.md)

---

## Animations & transitions

Exported decks carry page transitions and optional per-element object animations
as real OOXML—not embedded video. The default is a `fade` page transition with
**no element animation**; opt in with `-a auto`, one of the 203 native
`entrance_*` / `emphasis_*` / `path_*` / `exit_*` presets, or an
`animations.json` sidecar. The 29 former short names remain accepted only as
compatibility inputs; new animation choices use canonical prefixed names.

Animation settings are strict: unknown effects or Start modes, invalid timing values, and missing sidecar targets fail instead of silently becoming another effect. Before the result replaces an existing output, PPT Master reads the candidate package back and checks timing placement, IDs, shape targets, effects, durations, and Start modes. Microsoft PowerPoint is the primary motion-validation target; other presentation apps can open the PPTX but may map individual animation effects differently.

Full guide → [Animations & Transitions](./animations.md)

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
| The AI drifts or forgets a step | Ask it to re-read `skills/ppt-master/SKILL.md`, `skills/ppt-master/workflows/routing.md`, and the selected route authority. |
| Visual quality disappoints | Switch to a large-context Claude model + `gpt-image-2` — the harness sets the floor, the model sets the ceiling. |
| Text overflows or elements overlap | Re-run that page, or fix it in live preview; see the [FAQ](./faq.md). |
| No image-generation API key | Use the host's native image tool when available; otherwise zero-config web search still works. See the [FAQ](./faq.md). |
| Animations or some effects look off in another app | Microsoft PowerPoint is the primary motion-validation target. Keynote / WPS / LibreOffice can open the `.pptx`, but may remap or omit individual effects or Start semantics; validate motion-critical delivery in PowerPoint. |
| A long deck might blow the context window | Generation can run in split mode; details in the [FAQ](./faq.md). |

For model choice, cost, chart editability, custom templates, and more, the [FAQ](./faq.md) is the place to look.
