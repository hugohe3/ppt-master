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

- Python 3.10+
- Node.js 18+ (optional, for WeChat page conversion)
- Pandoc (optional, for DOCX/EPUB conversion)

### Setup

```bash
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

## Contribution Workflow

1. **Fork** the repository and create a branch from `main`
2. **Make your changes** — keep commits focused and descriptive
3. **Test** your changes locally before submitting
4. **Open a Pull Request** with a clear description of what you changed and why

## SVG Guidelines

If your contribution involves SVG files, follow the technical constraints documented in [CLAUDE.md](./CLAUDE.md):

- Do not use: `clipPath`, `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `<animate*>`, `<script>`, `<symbol>+<use>`
- Use `fill-opacity` / `stroke-opacity` instead of `rgba()`
- `marker-start` / `marker-end` are conditionally allowed — see `shared-standards.md` §1.1 for the constraints (must live in `<defs>`, `orient="auto"`, shape must be triangle / diamond / oval)
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
