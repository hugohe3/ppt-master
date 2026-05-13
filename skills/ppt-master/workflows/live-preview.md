---
description: Start or reopen the browser-based live preview editor; AI applies submitted annotations, re-exports, and loops until the user is done
---

# Live Preview Workflow

> Unified entry point for the browser-based SVG editor. Run this workflow any time the user mentions "live preview", "preview", "看一下效果", "visual edit", "改一下某个元素", or similar — whether the deck is mid-generation or already exported.

This workflow is **independent**: it operates on `<project_path>/svg_output/`, applies submitted annotations, and re-runs the same post-processing scripts the main pipeline uses. Safe to invoke at any stage as long as `svg_output/` contains at least one SVG file.

## When to Run

- **During Executor**: automatically, right after quality check passes — the main pipeline launches this via `--live` mode so the user can preview slides as they're generated.
- **Finished-deck re-entry**: the deck has been exported at least once (Steps 1–7 complete), or the editor was closed after generation, and the user wants to refine specific visual elements.
- Trigger phrases (any of these): "live preview", "preview", "看效果", "visual edit", "改一下", "打开编辑器", "看一下", "能不能看看", or the user describes clicking/selecting a slide element.

## When NOT to Run

- The user gave a precise edit you can apply right now ("change page 3 title font-size to 32") — just edit the SVG directly.
- The user wants a full regeneration ("redo this slide", "换个风格") — use the main workflow.
- Truly headless with no port-forwarding option: skip and apply edits via conversation instead.

---

## Step 1: Start the editor

**During Executor (live mode):**
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live
```

**Finished-deck / re-entry:**
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path>
```

The server binds to `127.0.0.1:5050`, opens the browser automatically on local desktop environments, and edits `<project_path>/svg_output/` in place. **Submit annotations** writes annotations to disk; it never stops the server. **Exit preview** closes the Flask server without saving pending annotations. `svg_to_pptx` snapshots `svg_output` into `backup/<timestamp>/` on every export, so prior versions are recoverable.

### Remote Linux access

If the project lives on a remote Linux server, run with `--no-browser`:

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --no-browser
# or with --live during generation:
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --no-browser
```

- **VS Code / Cursor Remote-SSH**: open the **PORTS** panel (`Ctrl+Shift+P` → `Ports: Focus on Ports View`), click **Forward a Port**, enter `5050`. The workspace remembers it.
- **Termius**: open the **Port Forwarding** module from the left sidebar (top-level, not nested). Add a rule with **Type = Local**, Host = your remote, Binding `127.0.0.1:5050`, Destination `127.0.0.1:5050`. Save, then **start the rule** (▶ button).
- **Plain SSH**: `ssh -L 5050:127.0.0.1:5050 <user>@<host>` (or add `LocalForward 5050 127.0.0.1:5050` to `~/.ssh/config`).

Then open `http://localhost:5050` in your local browser.

After the server prints `SVG Editor running at http://localhost:5050`, tell the user (in their language) in a single message:

- the editor is running at `http://localhost:5050`
- they should open it in a browser, click the element they want changed, write the change as a short instruction, then click **Submit annotations**
- after submitting, they should return to the conversation; the server stays open until they click **Exit preview**
- if they'd rather just describe the edit in chat, they can say so and you'll apply it directly without the editor

Do **not** wait for user confirmation before launching — they already signalled preview intent, so launching is the response. The "describe in chat" line is the escape hatch.

## Step 2: Apply annotations (Edit Loop)

Triggered when the user signals (in any wording) that they have submitted annotations and want them applied.

1. Leave the preview server running unless the user clicked **Exit preview**.
2. Discover annotations:
   ```bash
   python3 ${SKILL_DIR}/scripts/check_annotations.py <project_path>
   ```
3. If no annotations are found, tell the user and stop.
4. For each annotated SVG in `<project_path>/svg_output/`:
   - Read the file.
   - For each element with `data-edit-target="true"`, apply the change described in `data-edit-annotation`.
   - Strip `data-edit-target` and `data-edit-annotation` from the modified element.
5. Re-run post-processing:
   ```bash
   python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
   python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
   ```
6. If the preview server is still running, keep using it; if it was closed, restart with the Step 1 command.
7. Tell the user (in their language) that annotations have been applied, the PPT is updated, and the editor is at `http://localhost:5050`. If their browser shows an old slide, ask them to refresh or reselect the slide.
8. Wait for the user's next message:
   - If they indicate they're done, the loop ends.
   - If they submit more annotations, return to step 2.

---

## Notes

- **Browser preview**: the server inlines `<use data-icon>` placeholders and serves `images/*` so the SVG renders correctly in the browser. The on-disk SVG is unchanged by these previews.
- **Element targeting**: each element gets a transient `_edit_N` id assigned by the server while previewing. After save, only annotated elements keep their id; unannotated `_edit_N` ids are stripped before writing back to disk.
- **Port conflict**: if `5050` is taken, pass `--port <other>` and update the URL you tell the user.
- **Idle timeout**: the server self-terminates after 15 minutes of inactivity in standard mode (override with `--timeout <seconds>`). In `--live` mode, timeout is disabled by default.
