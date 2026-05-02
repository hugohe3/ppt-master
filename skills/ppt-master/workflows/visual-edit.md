---
description: Launch a local browser-based visual editor so the user can pinpoint elements they want changed; AI applies the annotations and re-exports the PPTX
---

# Visual Edit Workflow

> Standalone post-export step. Run when the user explicitly asks for fine-grained visual edits after PPTX export — e.g. "want to tweak something specific", "this part isn't right", "调一下这里" — any wording that signals they want to refine particular elements rather than regenerate. Do NOT run as part of the default flow.

This workflow is **independent**: it operates on `<project_path>/svg_output/` and re-runs the same post-processing scripts the main pipeline uses. Safe to invoke in a fresh session as long as the project has reached Step 7.

## When to Run

- The deck has been exported once (Steps 1–7 of the main workflow are complete).
- The user explicitly requests fine-grained edits.
- A browser is available on the host (Linux headless / containers without a display cannot use this workflow — fall back to direct SVG edits via conversation).

If the user's request is broad ("regenerate", "redo this slide"), use the main workflow instead — the editor is for surgical edits, not full rewrites.

---

## Step 1: Start the editor

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --no-browser
```

The server binds to `127.0.0.1:5050` and edits `<project_path>/svg_output/` in place. `svg_to_pptx` already snapshots `svg_output` into `backup/<timestamp>/` on every export, so prior versions are recoverable from there.

After the server prints `SVG Editor running at http://localhost:5050`, tell the user (in their language) in a single message:

- the editor is running at `http://localhost:5050`
- they should open it in a browser, click the element they want changed, write the change as a short instruction, then click **保存 / Save**
- after saving, the server auto-shuts and they should return to the conversation
- if they'd rather just describe the edit in chat, they can say so and you'll apply it directly without the editor

Do **not** wait for the user to confirm before launching — they already asked for fine-grained edits, so launching is the response. The "describe in chat instead" line is the escape hatch.

## Step 2: Apply annotations (Edit Loop)

Triggered when the user signals (in any wording) that they have submitted annotations and want them applied.

1. If the server is somehow still running, kill the process.
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
   python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
   ```
6. Restart the editor (same command as Step 1).
7. Tell the user (in their language) that annotations have been applied, the PPT is updated, and the editor is running again at `http://localhost:5050`.
8. Wait for the user's next message:
   - If they indicate they're done, the loop ends.
   - If they submit more annotations, return to step 1.

---

## Notes

- **Browser preview**: the server inlines `<use data-icon>` placeholders and serves `images/*` so the SVG renders correctly in the browser. The on-disk SVG is unchanged by these previews.
- **Element targeting**: each element gets a transient `_edit_N` id assigned by the server while previewing. After save, only annotated elements keep their id; unannotated `_edit_N` ids are stripped before writing back to disk.
- **Port conflict**: if `5050` is taken, pass `--port <other>` and update the URL you tell the user.
- **Idle timeout**: the server self-terminates after 15 minutes of inactivity (override with `--timeout <seconds>`).
