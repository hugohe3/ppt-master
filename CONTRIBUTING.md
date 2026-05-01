# Contributing to PPT Master

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

- **Templates** — New layout templates or visual styles
- **Charts** — Additional chart types or SVG chart templates
- **Icons** — Vector icons for the icon library
- **Scripts** — Improvements to conversion or post-processing scripts
- **Docs** — Clarifications, translations, or new guides
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
- **Focused bug fixes** — PRs are welcome when the fix is self-contained, has clear reproduction steps, and includes local verification
- **Substantial features, new backends, or new abstractions** — please open an issue first to discuss fit and direction. PRs submitted without prior discussion may be closed without detailed review
- **Refactors, structural changes, broad cleanup, or workflow changes** — open an issue first. The project deliberately stays close to its current shape

This isn't gatekeeping — it protects your time. A PR should be a meaningful, independently reviewable change, not just a few lines the maintainer could patch faster from an issue report. A 500-line PR that doesn't match the project direction is worse for you than a 10-line issue comment that clarifies it upfront.

## What We Accept / What We Don't

**Welcome:**
- Bug fixes with clear reproduction
- New layout templates, chart templates, icons
- Documentation clarifications and translations
- Additional image backends that follow the existing `image_backends/` pattern
- SVG quality improvements that stay within the declared constraints

**Not a fit (please don't open PRs for these):**
- Introducing `uv`, `poetry`, or other tools as required dependencies — `pip + requirements.txt` is the only official install path
- Adding CI, test frameworks, pre-commit hooks, or linting infrastructure — deliberately out of scope for a solo-maintained project
- Repackaging the skill as a CLI, SaaS, desktop app, or installer — PPT Master is a chat-driven skill for AI IDEs by design
- Architectural refactors or large-scale renames — incremental cleanup only
- "Drive-by" cosmetic reformatting unrelated to a real fix

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

If your contribution involves SVG files, follow the technical constraints documented in [CLAUDE.md](./CLAUDE.md):

- Do not use: `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `<animate*>`, `<script>`, `<symbol>+<use>`
- Use `fill-opacity` / `stroke-opacity` instead of `rgba()`
- `marker-start` / `marker-end` are conditionally allowed — see `shared-standards.md` §1.1 (must live in `<defs>`, `orient="auto"`, shape must be triangle / diamond / oval)
- `clipPath` on `<image>` is conditionally allowed — see `shared-standards.md` §1.2 (must live in `<defs>`, single shape child, only on `<image>` elements)
- All SVGs must use the correct `viewBox` for the target canvas format

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
