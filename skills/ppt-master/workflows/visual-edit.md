---
description: Reopen the browser-based visual editor for a finished/exported deck; AI applies annotations, re-exports, and reopens the editor for another pass
---

# Visual Edit Workflow

> Standalone finished-deck re-entry step. The main pipeline automatically starts the editor in live mode during Executor; use this workflow only after a deck has been generated/exported and the editor needs to be reopened for another visual edit pass.

This workflow is **independent**: it operates on `<project_path>/svg_output/`, applies submitted annotations, and re-runs the same post-processing scripts the main pipeline uses. Safe to invoke in a fresh session as long as the project has reached Step 7.

## When to Run

- The deck has been exported once (Steps 1–7 of the main workflow are complete), or the main live preview was closed after generation.
- The user wants to change one or more specific visual elements **and either can't pinpoint them in words or would benefit from clicking the slide directly**.
- A browser is reachable — either the host has a local desktop, or you can forward the port from a remote Linux server (see "Remote Linux access" below). Truly headless with no forwarding option: skip and apply edits via conversation instead.

## When NOT to Run

- The main Executor phase is still running with `--live` preview available — use that existing editor session instead.
- The user gave a precise edit you can apply right now ("change page 3 title font-size to 32") — just edit the SVG.
- The user wants a full regeneration ("redo this slide", "换个风格") — use the main workflow.

---

## Step 1: Start the editor

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path>
```

The server binds to `127.0.0.1:5050`, opens the browser automatically on local desktop environments, and edits `<project_path>/svg_output/` in place. **Submit annotations** only writes annotations to disk; it never stops the server. The preview UI includes **Exit preview** for closing the Flask server without saving pending annotations. `svg_to_pptx` already snapshots `svg_output` into `backup/<timestamp>/` on every export, so prior versions are recoverable from there.

### Remote Linux access

If the project lives on a remote Linux server, run the editor with `--no-browser`; it still listens only on `127.0.0.1` for safety. Forward port 5050 from your local machine using one of:

```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --no-browser
```

- **VS Code / Cursor Remote-SSH**: open the **PORTS** panel (`Ctrl+Shift+P` → `Ports: Focus on Ports View`), click **Forward a Port**, enter `5050`. The workspace remembers it.
- **Termius**: open the **Port Forwarding** module from the left sidebar (it's a top-level module, not nested under the host). Add a rule with **Type = Local** (not Remote — Remote forwards the opposite direction), Host = your remote, Binding `127.0.0.1:5050`, Destination `127.0.0.1:5050`. Save, then **start the rule** (▶ button) — saving alone does not activate it.
- **Plain SSH**: in a local terminal, run `ssh -L 5050:127.0.0.1:5050 <user>@<host>` (or add `LocalForward 5050 127.0.0.1:5050` to `~/.ssh/config` once).

Then open `http://localhost:5050` in your local browser.

After the server prints `SVG Editor running at http://localhost:5050`, tell the user (in their language) in a single message:

- the editor is running at `http://localhost:5050`
- they should open it in a browser, click the element they want changed, write the change as a short instruction, then click **Submit annotations**
- after submitting annotations, they should return to the conversation; the server remains open until they click **Exit preview**
- if they'd rather just describe the edit in chat, they can say so and you'll apply it directly without the editor

Do **not** wait for the user to confirm before launching — they already asked for fine-grained edits, so launching is the response. The "describe in chat instead" line is the escape hatch.

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
6. If the preview server is still running, keep using it; if it was closed, restart the editor with the Step 1 command.
7. Tell the user (in their language) that annotations have been applied, the PPT is updated, and the editor is available at `http://localhost:5050`. If their browser still shows an old slide, ask them to refresh or reselect the slide.
8. Wait for the user's next message:
   - If they indicate they're done, the loop ends.
   - If they submit more annotations, return to step 1.

---

## Notes

- **Browser preview**: the server inlines `<use data-icon>` placeholders and serves `images/*` so the SVG renders correctly in the browser. The on-disk SVG is unchanged by these previews.
- **Element targeting**: each element gets a transient `_edit_N` id assigned by the server while previewing. After save, only annotated elements keep their id; unannotated `_edit_N` ids are stripped before writing back to disk.
- **Port conflict**: if `5050` is taken, pass `--port <other>` and update the URL you tell the user.
- **Idle timeout**: the server self-terminates after 15 minutes of inactivity (override with `--timeout <seconds>`).
