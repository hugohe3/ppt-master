# Security Policy

## Supported Versions

We provide security updates for the latest version of PPT Master.

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| Older   | No        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you discover a security issue, please report it privately by emailing:

**heyug3@gmail.com**

Include in your report:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested fix, if you have one

We will acknowledge your report within **72 hours** and aim to provide a resolution timeline within **7 days**.

## Scope

This policy covers the PPT Master source code in this repository, including:

- Python scripts in `skills/ppt-master/scripts/`
- Post-processing pipeline (`total_md_split.py`, `finalize_svg.py`, `svg_to_pptx.py`)
- Project management utilities

Out of scope:

- Third-party AI editors or APIs (Claude, Cursor, GitHub Copilot, etc.)
- Generated PPTX output files
- User-provided source documents

## Disclosure Policy

We follow responsible disclosure. Once a fix is available, we will publish a GitHub Security Advisory crediting the reporter (unless they prefer to remain anonymous).
