# Getting Started

[English](./getting-started.md) | [Chinese](./zh/getting-started.md)

---

The short path to your first deck, how to use everything around it — templates, live preview, animations, narration, voice cloning — and where to look when something goes wrong. Sections follow roughly the order you meet them in a real run. Each is the quick version; follow the **Full guide →** link for depth.

- [Set up the installation and working folders](#set-up-the-installation-and-working-folders)
- [Start from a template](#start-from-a-template)
- [Generate your first deck](#generate-your-first-deck)
- [Live preview & visual edits](#live-preview--visual-edits)
- [Animations & transitions](#animations--transitions)
- [Narration & video](#narration--video)
- [Use a cloned voice](#use-a-cloned-voice)
- [When something goes wrong](#when-something-goes-wrong)

---

## Set up the installation and working folders

Before starting the agent, keep these three directories separate:

| Directory | What it is | Where it comes from |
|---|---|---|
| **Installed skill directory** | The PPT Master package containing `SKILL.md`, `requirements.txt`, workflows, and scripts | In a full-repository clone or repository ZIP, this is `skills/ppt-master/`; a marketplace/plugin installation or skill-only release ZIP has its own installed or extracted location |
| **Working folder** | A persistent, writable folder that you open in the agent | For a full-repository clone or repository ZIP, normally the repository root; for skill-only installation, choose your own folder—it does not have to be the installed skill directory |
| **Active project** | One generation run's sources, authored SVG, reports, backups, and exports | The agent initializes it under `<working-folder>/projects/<generated-project-name>/` and reports the exact path |

Every installation path needs Python 3.10+ and an installed, authenticated agent host that can read and write the working folder and run shell commands. For a full-repository clone or repository ZIP, install dependencies from the repository root:

```bash
python3 -m pip install -r requirements.txt
```

For a skill-only installation, first locate the installed or extracted directory that contains the skill's `SKILL.md` and `requirements.txt`, then install from that path:

```bash
python3 -m pip install -r "<installed-skill-dir>/requirements.txt"
```

The `npx skills add hugohe3/ppt-master` installation path also requires a working `npx` command, normally supplied with Node.js/npm; the repository does not specify a Node/npm minimum version. A host's own `/plugin install` command does not use that `npx` path. After installation, start the agent in the **working folder**, not in the host-managed skill cache. The execution entry point resolves the installed skill separately. Installation choices are listed in [Quick Start](../README.md#quick-start); runtime discipline is defined in [`SKILL.md`](../skills/ppt-master/SKILL.md).

---

## Start from a template

**Optional.** By default PPT Master uses **free design** — you don't need a template, and you can skip to the next section. Reach for one when a deck must reuse a brand identity, a communication/design method, a fixed layout set, or a recurring deck application.

**Two ways to reuse an existing `.pptx`, depending on what you want back:**

| You want… | Route | What happens |
|---|---|---|
| **Use this deck's native slide shells with new content** | Edit Native PPTX | Imports a round-trip workspace; unchanged pages restore byte-for-byte, `page_plan.json` may select/reorder/repeat/omit pages, and only planned pages are edited. |
| **Build a reusable design system, then generate a new deck** | Create Template → Generate PPTX | Creates a validated Brand, Style, Layout, or Deck workspace from the reference, then authors a fresh deck. The new story, structure, and page count can differ from the source. |

For the first, give the AI your `.pptx` plus your material (or a topic) and ask it to "fill this deck with the new content" — see the [Edit Native PPTX workflow](../skills/ppt-master/workflows/edit-native-pptx.md). The rest of this section covers create-template.

**To build a reusable workspace from an existing PowerPoint, explicitly request the Create Template route.** A raw `.pptx` plus new material otherwise belongs to Edit Native PPTX; it is not a Generate template workspace. Create the workspace first:

```
You: Create a reusable Deck template from projects/brand/our_deck.pptx via /create-template
```

Create Template analyzes the reference, confirms whether the result is a Brand, Style, Layout, or Deck, and then authors or materializes a new validated workspace. The importer supplies source evidence; a library workspace owns `templates/design_spec.md`, while a shared project root owns `templates/design_spec.<kind>.<id>.md`, plus any prototypes and assets required by that kind. Brand and Style are roster-free; Layout and Deck own structured SVG prototypes. If you want a PowerPoint review file for Layout or Deck, run the optional preview export; it creates `exports/<id>_template_preview.pptx` on demand. The workspace root is what you point to at generation time.

During the create-template brief, choose `library` (the existing default) or `project`. Both require `templates/` and use optional `images/`, `icons/`, and on-demand `exports/`; empty optional directories are omitted. Project scope requires an initialized target project; library scope alone adds global registration.

A created template lives in one of two places:

| Location | Path | Notes |
|---|---|---|
| **Registered in the skill library** | `skills/ppt-master/templates/<kind>/<id>/` | Portable workspace plus global registration, so it appears when you ask "what templates are available?" |
| **Under projects** | `projects/<name>/` | A shared qualified-spec root without global registration; all four kinds may coexist, with Layout taking structural precedence over Deck |

Default Generate shows the template choice inside Stage 1, beside the communication contract. The initial communication recommendation is written without reading any template. Ordinary requests start with free design; explicit template intent or any exact root starts in template mode, and the user can always switch. To offer another result, supply its exact **workspace-root path** in chat: an unregistered root appears in the specified-root dropdown, while an exact registered match resolves back to its kind dropdown. Exactly one supplied root may be preselected; multiple supplied roots remain unselected candidates. Each kind may appear once; Layout and Deck may coexist, with Layout supplying structure. A multi-kind project root is selected atomically. One confirmation closes communication and template choice together. Only then are selected roots validated and installed; template-aware planning begins in final Stage 2. A bare template name never resolves to a workspace. A project root can be reused directly by another project; moving one contribution into the library changes its spec filename placement and adds registration.

```
You: Make a deck from sources/report.pdf with template skills/ppt-master/templates/layouts/presentation_core/
```

Full guide → [Templates Guide](./templates-guide.md)

---

## Generate your first deck

Once the environment and working folder above are ready, the whole loop is three steps:

1. **Give the agent source material it can read** — a PDF, DOCX, Markdown file, a URL, or text pasted into chat. A folder such as `<working-folder>/inputs/` is fine; you do not need to pre-create the final `projects/<name>/` directory.
2. **Tell the AI in chat** what to turn into a deck. [Default Generate Step 2](../skills/ppt-master/workflows/generate-pptx.md) or [Quick initialization](../skills/ppt-master/workflows/profiles/quick-generate.md) creates the active project under the working folder's `projects/` directory and reports its exact path. File-based material is imported when present; pasted text stays in the conversation context and needs no import. Default then opens Stage 1 to confirm the communication contract together with free design or template use; Quick skips those confirmation stages. For Default, add one exact workspace root when you want template mode and that path preselected:
   ```
   You: Make a deck from <path-to-report.pdf>
   You: Turn this text into a deck: <paste your text>
   ```
3. **Get an editable `.pptx`** at `<active-project>/exports/<project-name>_<timestamp>.pptx` unless you explicitly requested another output path. For a full-repository clone or repository ZIP this is commonly `<repository-root>/projects/<generated-project-name>/exports/...`; for skill-only installation it is `<working-folder>/projects/<generated-project-name>/exports/...`. Use the exact active-project path reported by the agent rather than looking for an unqualified repository-root `exports/`.

The terms in that flow are not extra folders you must create. **Stage 1** confirms the communication contract—purpose, audience, reading situation, canvas/format—and the free-design/template choice. A **workspace root** is the root directory of an optional reusable Brand, Style, Layout, or Deck package; it is not the active project. The AI installs any selected workspace, then **Stage 2** confirms page count, the visual system, template application, and production choices. From there it handles content analysis, layout, image acquisition, SVG generation, and export. To skip interactive confirmation, see [Quick mode](#quick-mode) below.

---

## Quick mode

The default flow runs its combined Stage-1 communication/template choice followed by final Stage 2. To skip that interaction, explicitly ask for **quick generation**:

```
You: Quickly generate a deck from sources/report.pdf — no need to confirm with me
You: Turn this into a deck, skip the confirmation, about 8 pages, dark corporate look
```

**Whatever you state explicitly is followed; whatever you leave unspecified the agent decides directly, without coming back to ask.** The page count and the look in the second example still hold — quick mode drops the round trip, not your say. Instead of materializing Default's three directions, Quick directly executes the direction that Default would recommend: the strongest overall fit for free design, or the viable direction most fully expressing installed template context. State nothing, and the agent decides everything.

Quick mode never opens the Confirm UI template selector. Give it up to one exact
Brand / Style / Layout / Deck workspace root per kind and it validates,
installs, and uses them directly; give it no exact root and it uses free design.
A bare template name or style phrase is still only a design brief. Quick keeps
its lockless workflow but preserves template capability: free design and
Brand / Style-only output stays flat, while a supplied Layout / Deck workspace
keeps explicit Master / Layout / slot metadata in the authored SVGs and compiles
it into reusable native structure. Before P01, the agent reads every installed
template SVG and freezes one natural-language application paragraph in active
context; no confirmation/spec artifact is created.

It does not skip capabilities: source conversion, research on identified factual gaps, shared aesthetic guidance, image / icon preparation, and native-shape / chart / table authoring still run as needed. Structural formulas are authored directly as native PowerPoint markers rather than prepared as image assets. A missing explicitly selected manual asset or other irreplaceable file dependency blocks until you provide it. If automated AI generation or required dependent slicing is exhausted, Quick removes the failed jobs and stale manifest entries, replans with native editable text/SVG or already-prepared non-AI assets, continues the same run, and reports the replacement in its final handoff.

Quick is a one-pass profile, not a shortened resumable workflow. It creates no Strategist record, `design_spec.md`, `spec_lock.md`, or substitute page plan; its content/design/resource decisions exist only in the active AI context. If that context is lost before delivery, start Quick again. Operational manifests, quality reports, postflight, and the cold Python audit log may remain, but they cannot reconstruct why the AI designed the deck that way. The profile reduces interaction and durable planning, not the available presentation toolbox or the intended quality bar.

Full guide → [quick-generate profile](../skills/ppt-master/workflows/profiles/quick-generate.md)

---

## Live preview & visual edits

A browser preview opens at the URL reported by the launcher while the deck is being generated. It prefers `http://localhost:5050` and uses the next free port when `5050` is occupied.

- **Watch pages render live** as the AI produces them.
- **Edit directly, no AI** — select an element to change its text, color, font, or size in the side panel; drag it to reposition, or nudge with the arrow keys (`Shift` = 10px). `Ctrl+Z` undoes. Edits preview instantly and write to `svg_output/` when you click **Apply changes**.
- **Or annotate for the AI** — click an element, type what you want changed, click **Add annotation** to stage it, then click **Apply changes** to write the annotation markers to `svg_output/`. Return to chat and say "apply my annotations"; the AI rewrites that region and re-exports the PPTX.

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
