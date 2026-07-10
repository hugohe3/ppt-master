# Contributing to PPT Master

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

- **Templates** — New layout templates or visual styles
- **Charts** — Additional chart types or SVG chart templates
- **Icons** — Vector icons for the icon library
- **Scripts** — Improvements to conversion or post-processing scripts
- **Docs** — Substantive guides or corrections that materially improve project usage
- **Bug reports** — Reproducible issues with clear descriptions
- **Ideas** — Feature requests and design suggestions

## Getting Started

### Prerequisites

- **Python 3.10+** — the only required dependency
- **Node.js 18+** and **Pandoc** are edge-case fallbacks that 99% of contributors never need; install only if you're working on the specific paths that require them. See the [README Quick Start](./README.md#1-prerequisites) for when each applies.

### Setup

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

## Before You Open a PR

PPT Master is solo-maintained with limited review bandwidth. To keep things healthy for everyone:

- **Tiny fixes** (typos, one-line usage/doc corrections, obvious small inconsistencies) — please open an issue instead of a PR. A clear report is usually faster for the maintainer to apply directly
- **Translations & wording-only edits** — please open an issue rather than a PR. Like other tiny fixes, these are faster for the maintainer to apply directly, and unrequested translation files add ongoing sync burden without a clear owner. Translated governance docs (CONTRIBUTING, Code of Conduct) are intentionally not maintained as separate `_CN` files
- **Focused bug fixes** — PRs are welcome when the fix is self-contained, has clear reproduction steps, and includes local verification
- **Code-only changes** — self-contained fixes to scripts or script behavior, with no edits to prompt/instruction text, can go straight to a PR as long as they meet the focused-bug-fix bar above
- **Prompt / instruction changes require a prior issue** — edits to `SKILL.md`, `references/*.md`, `workflows/*.md`, or any other agent-facing instruction text **must be discussed and agreed in an issue *before* you open a PR**. These files steer AI behavior deck-wide, sit close to a fixed prompt-token budget, and restating a rule the docs already state rarely fixes a non-compliant agent — the fix usually belongs in the agent, not in more prompt text. PRs that touch prompt/instruction files without a prior agreed issue may be closed without detailed review
- **Substantial features, new backends, or new abstractions** — please open an issue first to discuss fit and direction. PRs submitted without prior discussion may be closed without detailed review
- **Refactors, structural changes, broad cleanup, or workflow changes** — open an issue first. The project deliberately stays close to its current shape

This isn't gatekeeping — it protects your time. A PR should be a meaningful, independently reviewable change, not just a few lines the maintainer could patch faster from an issue report. A 500-line PR that doesn't match the project direction is worse for you than a 10-line issue comment that clarifies it upfront.

### AI-assisted PRs

AI assistance is welcome — this project is itself AI-driven. But an AI-drafted PR you haven't personally reviewed is not a contribution; it's an unreviewed code dump:

- **Purely AI-generated PRs submitted without human review will be closed unmerged.** Before opening a PR, read the full diff yourself, run the affected scripts, and confirm the problem described actually exists in this repository — not just that it sounds plausible.
- **Every factual claim in the PR description is yours, not the AI's.** A description that asserts failures in code paths the repository doesn't actually have (an AI-invented problem narrative) gets the PR closed regardless of diff quality.
- Read this file in full before opening a PR; the PR template asks you to confirm the points above. **The template has three confirmation checkboxes — if any one of them is left unchecked, the PR is closed without review.**

## What We Accept / What We Don't

**Welcome:**

- Bug fixes with clear reproduction
- New layout templates, chart templates, icons
- Documentation updates that materially improve an existing workflow, installation path, or troubleshooting path
- Additional image backends that follow the existing `image_backends/` pattern
- SVG quality improvements that stay within the declared constraints

**Not a fit (please don't open PRs for these):**

- Introducing `uv`, `poetry`, or other tools as required dependencies — `pip + requirements.txt` is the only official install path
- Adding CI, test frameworks, pre-commit hooks, or linting infrastructure — deliberately out of scope for a solo-maintained project
- Repackaging the skill as a CLI, SaaS, desktop app, or installer — PPT Master is a chat-driven skill for AI IDEs by design
- Architectural refactors or large-scale renames — incremental cleanup only
- "Drive-by" cosmetic reformatting unrelated to a real fix
- Pure translations or wording-only edits that were not requested or discussed first
- Changing a foundational setting — the MIT license, or DrawingML component reuse / template-fill in place of AI-generated shapes. These are deliberate founding choices and won't change midway
- Fixed numeric quotas to constrain generation (`max_cards` / `max_bullets` / `max_table_rows` and similar) — density is governed by narrative rhythm and one primary focus per page, not hard caps
- Post-processing that is quality smoothing rather than compatibility — we fix things that are broken/unusable if not done (e.g. AI-image size/format/alpha); "nicer if done" polish (loudness normalization, kerning) stays out. If a model or service falls short, the fix is to switch it, not to make the project adapt to it
- A new backend, path, or option that duplicates a capability the repo already provides — check current behavior first (e.g. OpenAI-compatible providers already run under `IMAGE_BACKEND=openai`)

If you're unsure, open an issue to ask — that's always welcome.

## Contribution Workflow

1. **Fork** the repository and create a branch from `main`
2. **One PR, one thing** — keep each PR focused on a single concern. If you notice unrelated improvements, open a separate PR
3. **Write a useful PR description** — explain *what* changed and *why*, not just a diff summary. If your change fixes a bug, include reproduction steps
4. **Test locally** before submitting — run the affected scripts and verify output
5. **Don't overstate** — if your PR description claims tests or behavior changes, make sure the diff actually contains them

## Review Process

- Reviews are best-effort, usually within a few days. Ping the PR if it's been a week without response
- Review feedback will be specific: what to change, and whether it's a blocker. If a PR needs more than ~2 rounds to converge, it may be closed with a note — reopening is fine once the direction is clearer
- Focused fixes may be merged as-is; larger contributions will usually be squash-merged to keep history readable

## SVG Guidelines

If your contribution involves SVG files, follow the canonical authoring and
PPTX-compatibility contract in
[`shared-standards.md`](./skills/ppt-master/references/shared-standards.md).
This guide does not duplicate its required, forbidden, or conditional entries.

Validate the affected SVG file or directory before submitting:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py <file_or_directory>
```

## Reporting Bugs

Open an issue on [GitHub Issues](https://github.com/hugohe3/ppt-master/issues) and include:

- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, AI editor used)

## Code of Conduct

Please read and follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
