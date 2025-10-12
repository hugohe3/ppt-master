# Repository Guidelines
**[EN]** This contributor guide summarizes working rules; read `docs/workflow_tutorial.md` for the full Chinese workflow narrative.

## Project Structure & Module Organization
Core assets follow agent responsibilities. `roles/` houses the four main role briefs; add new ones as `RoleName.md` and append the index in `roles/README.md`. Process notes, patterns, and cheat-sheets live in `docs/`, with supporting raw material stored inside adjacent subdirectories. Slides are organised into `examples/sample_input/` and `examples/sample_output/`; keep filenames in the `yh_slide_0X_topic.svg` pattern and pair them with the matching spec document. Experimental case studies reside under `projects/<case>/` and every iteration log belongs in `logs/`.

## Build, Test, and Development Commands
- `python3 -m http.server --directory examples/sample_output 8000` – spin up a quick SVG preview server.
- `npx markdownlint "**/*.md"` – align Markdown spacing and headings before a PR.
- `grep -R 'viewBox="0 0 1280 720"' examples` – confirm every slide keeps the enforced canvas size.

## Coding Style & Naming Conventions
Markdown uses ATX headings, two-level lists, and concise paragraphs; emphasise critical steps with bold text only when necessary. Name role definitions `RoleName.md`, keep sample outputs in snake_case themes (for example `yh_slide_02_methodology.svg`), and align SVG attributes with inline comments marking layout anchors. Default copy to Chinese unless you flag an English section at the start of a paragraph and provide matching reference links.

## Testing Guidelines
Pair every new layout or automation strategy with input/output pairs in `examples/` and review the rendered slides page by page in a browser. Validate colours, fonts, and measurements against `docs/design_guidelines.md`, and attach side-by-side screenshots when visuals change. When a role brief shifts, produce a minimal “剧情脚本” demonstrating the agents’ collaboration and store it in `logs/` or a focused `projects/` subfolder.

## Commit & Pull Request Guidelines
Adopt Conventional Commits such as `feat(Strategist): refine intake checklist`, keeping each message scoped to one change. Fill the PR template with scope, tests, and linked issues; include key slide screenshots for UI or SVG updates and list affected directories (e.g. `examples/sample_output/`). Confirm Markdown linting and SVG checks pass before requesting review.

## Agent Workflow Notes
The Strategist must confirm page range, target audience, and visual style before advising changes to any role file and then synchronise updates across `docs/workflow_tutorial.md` and the design guidelines. Place automation prompts or parameter files inside `projects/<agent-name>/` and document usage and dependencies within the PR.
