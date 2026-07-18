---
description: Main-pipeline editor stage for starting live preview and applying submitted annotations.
---

# Live Preview Stage

> **Purpose**: (1) start/reopen the browser SVG editor when no preview service is currently running, and (2) apply user-submitted annotations after Step 7 export completes.
>
> **Not in scope**: Executor's mandatory auto-startup — that lives in [`generate-pptx`](../generate-pptx.md) Step 6. Do not re-launch a preview that is already running.

## When to Run

- **Start (Step 1)** — preview service is not currently running and the user wants to look at the deck or click an element. Typical cases: post-export re-entry in a fresh chat, or the user clicked **Exit preview** earlier and now wants it back.
- **Apply annotations (Step 2)** — Step 7 has produced at least one PPTX, and the user signals that submitted annotations should now be applied. Triggers include:
  - quoting the browser prompt (`Changes saved to svg_output...` / `修改已保存到 svg_output...`)
  - saying `apply my annotations` / `apply my edits` / `应用注解` / `开始应用` / 等价表达

## When NOT to Run

- The preview service is already running → just give the user the URL; do not restart.
- The user gave a precise chat edit ("change page 3 title to X") → edit the SVG directly.
- The user wants a full regeneration → use the main workflow.
- Step 7 has never run for this project → annotations cannot be applied yet; finish the main pipeline first.

---

## Step 1: Start / reopen the editor

**Precondition**: no preview service running on this project.

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --daemon
```

(Plain mode — no `--live`. The `--live` flag is reserved for Step 6's auto-startup.)

The launcher binds `127.0.0.1:5050` (or the next free port), starts the server in the background, waits for `GET /api/health` to prove the server is accepting requests, writes runtime files under `<project_path>/live_preview/`, opens the browser on a local desktop when possible, and edits `<project_path>/svg_output/` in place. After it prints the running URL, tell the user in their language, in one short message:

- editor is at the URL reported by the launcher, e.g. `http://127.0.0.1:5050`
- **Direct edit** (deterministic tweaks — wording, color, coordinates, SVG attributes): select an element → change the controls in the right panel → preview updates immediately, but nothing is written to `svg_output/` until **Apply changes**. `Ctrl+Z` or the **Undo** button drops staged edits step by step; applied changes are logged to `<project>/live_preview/edits.jsonl`. Re-export stays chat-driven and separate: say "re-export" / "重新导出" to refresh the PPTX.
- **Annotate** (changes that need AI judgement / re-layout): select an element → write the instruction, optionally starting from a quick type such as move / resize / replace image / copy / relayout → click **Add annotation** to stage it → click **Apply changes** to write annotation markers → return to the chat and say `apply my annotations` (or quote the browser prompt)
- to skip the editor, just describe the change in chat

Do not wait for confirmation before launching — the user already asked for preview, so launching is the response. If another project already holds the port, the launcher auto-advances to the next free one — report the actual URL from the launch log (`--port <other>` still forces a specific port). Remote access → see the appendix.

---

## Step 2: Apply submitted annotations

🚧 **GATE**: `<project_path>/exports/` contains at least one `*.pptx` (Step 7 has completed). If not, do not apply annotations — tell the user to finish the main pipeline first.

Triggered by the user signals listed in "When to Run".

1. Discover annotations:
   ```bash
   python3 ${SKILL_DIR}/scripts/check_annotations.py <project_path>
   ```
   The output already lists each pending change as `file → element_id → annotation text → content preview`. Use it directly as the to-do list; no need to re-parse SVG attributes yourself.
2. If the output says no annotations: tell the user, stop.
3. For each listed annotation:
   - Edit the targeted element in `<project_path>/svg_output/<file>` per the annotation text.
   - Remove `data-edit-target` and `data-edit-annotation` from that element.
   - Append one `annotation_applied` JSONL record to `<project_path>/live_preview/annotations.jsonl` with `ts`, `file`, `element_id`, and the original annotation text.
4. Re-enter [`generate-pptx`](../generate-pptx.md) Step 7.2, wait for its success criterion, then run Step 7.3. Do not rerun Step 7.1 unless speaker notes changed.
5. Tell the user (in their language): annotations applied, new PPTX exported, preview is still running. If the browser still shows the old slide, refresh or reselect the page.
6. Loop: more annotations submitted → repeat from step 1. User signals done or "stop preview" → end.

---

## Notes (editor invariants — referenced from Generate Step 6)

- **UI**: trilingual (中文 / English / 日本語); auto-detects from `navigator.language`, persists in `localStorage`, switched via the language dropdown on the right panel. The right panel is an **Edit / Annotate** surface: direct SVG edits and AI-needed annotations are visually separated, with a pending-status strip showing staged direct edits and pages with unsaved annotations. Slide navigation: first/prev/next/last buttons at the top of the center panel, plus `←` / `→` / `Home` / `End` (suppressed while typing in the annotation textarea).
- **Buttons**: `Add annotation` stages annotation text in memory; `Apply changes` writes staged direct edits plus annotation markers to disk and keeps the service running; `Exit preview` is the only UI action that stops Flask.
- **Direct edit (no AI)**: selection mode determines the right-panel surface. Single element = full object inspector (geometry, safe text content, computed text styles for the selected text node or descendant text inside a selected textbox/group, raw SVG attributes except protected fields like `id`, UI `class`, event handlers, and hrefs). SVG `<g>` group = group-level edit surface; select via `Alt/Option` + click or **Select parent group** from a child element. Multi-select = limited batch editor over top-level selected objects only: shared x/y plus `fill` / `stroke` / `opacity`; text style fields (`font-size` / `font-family` / `font-weight` / `text-anchor`) appear only when every selected object is `text`/`tspan`. Preview updates immediately; disk writes wait for **Apply changes**.
- **Drag to move**: press and drag an already-selected element on the canvas to reposition it (selection stays a separate click, so the background is never dragged by accident); the whole selection moves together under multi-select. The pointer delta is mapped through each element's own CTM, so moves track the cursor regardless of viewport scale or group transforms. Each release stages one direct edit per moved element (the same `x`/`y`-or-`transform` write the geometry inputs produce), previewed live and written only on **Apply changes**; dragging on empty canvas is still rubber-band selection. A failed stage rolls the canvas back to the pre-drag position.
- **Arrow-key nudge**: with one or more elements selected, `↑ ↓ ← →` moves the selection 1px and `Shift + arrow` moves 10px (suppressed while typing in the annotation box). Arrow keys navigate slides only when nothing is selected. Same staging/coalescing path as drag, so a burst of nudges collapses to one undo step.
- **Overlap picker**: right-click anywhere on the canvas to list every selectable element under the pointer (top→bottom), so stacked shapes can be reached without blind cycling. Left-click is unchanged (selects the topmost). Hovering a row highlights that element; clicking it selects it; `Esc` or an outside click closes the list. With exactly one element under the pointer, right-click selects it directly.
- **Undo**: `Ctrl+Z` or the **Undo** button drops the last staged direct edit on the current slide (per-slide LIFO, this session). Consecutive edits to the *same element and same field set* (e.g. nudging one color or coordinate several times) coalesce into a single undo step, keeping the original pre-edit value; switching element or field starts a new step. Applied old→new history is appended to `<project>/live_preview/edits.jsonl`; annotation save/update/remove history is appended to `<project>/live_preview/annotations.jsonl`; un-applied staged edits are in-memory only.
- **Unsaved-work guard**: staged direct edits and annotation changes (added or removed) live in server memory until **Apply changes**; closing the tab triggers the browser's native "leave site?" prompt while any are unapplied, since an idle timeout or process kill would drop them.
- **Re-export is chat-driven**: applying changes updates `svg_output/` only. Refreshing the PPTX (finalize + svg_to_pptx) stays a chat step — the editor never runs the export pipeline or presents browser-side export as part of applying edits.
- **Stop conditions**: the service stops when the user clicks **Exit preview** in the browser, asks in chat to stop it, the idle timeout fires, or the process is killed externally.
- **Port**: default `5050`, auto-advancing to the next free port when another project already holds it (report the actual URL from the launch log); force a specific port with `--port <other>`.
- **Idle timeout**: plain mode `900s`, `--live` mode `7200s`; override with `--timeout <seconds>` (`0` disables).
- **Single instance per project**: `<project_path>/live_preview/lock.json` records the running pid + port. A second launch against the same project refuses to start and prints the existing URL; stale locks (dead pid) are overwritten on the next launch. Legacy root locks at `<project_path>/.live_preview.lock` are still detected when they point to a live process.
- **Transient ids**: each element gets a temporary `_edit_N` id while the editor is running. On save, only annotated elements keep their id; unannotated `_edit_N` ids are stripped before write-back.
- **Browser preview**: the server inlines `<use data-icon>` placeholders and serves `images/*` so SVG renders correctly; the on-disk SVG is unchanged by this preview.

---

## Appendix: Remote access

If the project lives on a remote Linux server, run with `--no-browser`:

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --daemon --no-browser
# or for Step 6's auto-startup on a remote host:
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --daemon --no-browser
```

- **VS Code / Cursor Remote-SSH**: open the **PORTS** panel (`Ctrl+Shift+P` → `Ports: Focus on Ports View`), click **Forward a Port**, enter `5050`. The workspace remembers it.
- **Termius**: open the **Port Forwarding** module from the left sidebar (top-level, not nested). Add a rule with **Type = Local**, Host = your remote, Binding `127.0.0.1:5050`, Destination `127.0.0.1:5050`. Save, then start the rule (▶ button).
- **Plain SSH**: `ssh -L 5050:127.0.0.1:5050 <user>@<host>` (or add `LocalForward 5050 127.0.0.1:5050` to `~/.ssh/config`).

Then open `http://localhost:5050` in your local browser.
