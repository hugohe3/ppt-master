# Python Code Style Guide

> Style rules for Python code under `skills/ppt-master/scripts/` and any Python that ships with the skill. Derived from the de facto patterns in the existing codebase.

These rules are pragmatic, not exhaustive. They capture the conventions readers actually encounter — anything PEP 8 hands you for free is assumed.

---

## 1. File Header

Every script under `scripts/` starts with:

```python
#!/usr/bin/env python3
"""
PPT Master - Short Tool Name

One-paragraph description of what this script does.

Usage:
    python3 scripts/<name>.py <required_arg> [options]

Examples:
    python3 scripts/<name>.py projects/<project_name> -o output_dir

Dependencies:
    None (only uses standard library)        <-- or list third-party deps
"""
```

| Element | Rule |
|---|---|
| Shebang | `#!/usr/bin/env python3` (always — even for non-CLI helper modules) |
| Module docstring | Tool name + purpose + Usage + Examples + Dependencies |
| Internal helper modules | May add an early `--help` short-circuit (see §4) |

---

## 2. Imports

```python
# 1. Standard library
import os
import sys
import argparse
import re
from pathlib import Path
from typing import Optional

# 2. Third-party
import requests

# 3. Local — sometimes need sys.path injection first (see §3)
from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
)
```

| Rule | Note |
|---|---|
| Group order | std → third-party → local, blank line between groups |
| Within a group | Sorted by length when short; alphabetical when ≥ 4 imports |
| `from x import` lists | One name per line if ≥ 4 names, with trailing comma |
| `from __future__ import annotations` | Add at top when the file uses `X \| Y` union syntax (PEP 604) and may run on Python < 3.10 |

---

## 3. sys.path Injection (Project Convention)

`scripts/` is **not a Python package** — it's a flat directory of scripts. Each entry-point script that imports a sibling module injects `scripts/` onto `sys.path` itself:

```python
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from image_backends.backend_common import download_image  # noqa: E402
```

| Rule | Why |
|---|---|
| Inject only in entry-points | Library modules under `image_sources/` / `image_backends/` import each other normally |
| Use `Path(__file__).resolve().parent` | Robust under symlinks and aliasing |
| Annotate post-injection imports with `# noqa: E402` | Suppress the lint warning honestly, not via per-file noqa |

---

## 4. CLI Entry Points

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="One-line description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="...")
    parser.add_argument("-o", "--output", default=".", help="...")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # ... do the thing ...
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

| Rule | Note |
|---|---|
| `main(argv=None) -> int` | Returns exit code; testable by passing `argv` |
| `raise SystemExit(main())` | Preferred over `sys.exit(main())` |
| `formatter_class=argparse.RawDescriptionHelpFormatter` | Preserves docstring formatting in `--help` |
| Internal helpers `--help` | Module-level: `if __name__ == "__main__" and any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]): print(__doc__); raise SystemExit(0)` |
| Output | Progress / status to **stderr**; the script's primary output (if any) to stdout |

---

## 5. Type Hints

Required for all new public functions; optional for internal `_helpers`.

| Pattern | Use |
|---|---|
| `def f(x: str, *, y: int = 0) -> bool:` | Public functions |
| `tuple[int, int] \| None` | PEP 604 unions (with `from __future__ import annotations` if needed for compat) |
| `Optional[X]` from `typing` | Acceptable alternative to `X \| None` |
| `list[X]`, `dict[K, V]` | Built-in generics (Python 3.9+) |
| `Any` | Sparingly — only when interfacing with truly heterogeneous data (`raw: Any` in dataclasses for upstream JSON) |

**Forbidden — over-specification**:

- `Callable[[int, str], dict[str, list[Optional[Union[int, str]]]]]` — break this into typed dataclasses
- `Literal["a", "b", "c"]` everywhere — use a constant + plain `str` unless the type itself is the API

---

## 6. Naming

| Kind | Convention | Examples |
|---|---|---|
| Module file | `snake_case.py` | `image_search.py`, `svg_to_pptx.py` |
| Script entrypoint | verb or noun phrase | `finalize_svg.py`, `notes_to_audio.py` |
| Public function | `snake_case` | `download_image`, `parse_results` |
| Private helper | `_snake_case` | `_load_dotenv_if_available`, `_measure_actual_image` |
| Constant | `UPPER_SNAKE_CASE` | `API_URL`, `DEFAULT_PAGE_SIZE`, `LICENSE_TIER_NO_ATTRIBUTION` |
| Class | `PascalCase` | `AssetCandidate`, `SVGQualityChecker` |
| Dataclass field | `snake_case` | `license_tier`, `download_url` |
| Module-private regex | `_PATTERN_RE` (private + `_RE` suffix) | `_TAG_RE`, `HEADING_RE` |

---

## 7. Error Handling

| Situation | Pattern |
|---|---|
| Optional dependency | `try: import x; HAS_X = True\nexcept ImportError: HAS_X = False` |
| Optional sibling module | `try: from project_utils import CANVAS_FORMATS\nexcept ImportError: CANVAS_FORMATS = {}; print("Warning: ...")` |
| Recoverable runtime failure | Catch specific exceptions, log to stderr, return / continue — do NOT halt the pipeline |
| User-facing error | `print("...", file=sys.stderr); return 1` from `main()` |
| Programming error | Raise — don't paper over a bug |

**Hard rule**: never bare-`except:`. Always name the exception class.

**Forbidden — silent fallbacks for security-relevant code**:

- Disabling SSL verification without a domain whitelist + WARNING
- Catching all exceptions in a download path without logging the cause

---

## 8. Dependencies

| Tier | Where it can be required |
|---|---|
| Standard library | Anywhere |
| `requests`, `Pillow`, `lxml` | Common dependencies; safe to require in main scripts |
| Provider SDKs (`google-genai`, `openai`, `anthropic`, etc.) | **Lazy import inside the function that uses it**; soft-fail with `ImportError` → `RuntimeError` containing install instructions |
| `python-dotenv` | Optional — wrap the import in try/except, no-op if unavailable |

```python
def _require_api_key() -> str:
    key = os.environ.get("PEXELS_API_KEY") or ""
    if not key:
        raise RuntimeError(
            "PEXELS_API_KEY is not set. Add it to your environment or .env file. "
            "Get one at https://www.pexels.com/api/"
        )
    return key
```

Error messages **must include the fix** — "what env var to set", "where to get a key", "which package to install".

---

## 9. Shared Helpers Layer

Common functionality lives in two designated submodules. New scripts use these, not their own copies:

| Module | Owns |
|---|---|
| [`image_backends/backend_common.py`](../skills/ppt-master/scripts/image_backends/backend_common.py) | HTTP download, retry, image format detection, save-with-Pillow-transcode |
| [`image_sources/provider_common.py`](../skills/ppt-master/scripts/image_sources/provider_common.py) | License classification, query simplification, scoring, attribution text, dataclasses |
| [`project_utils.py`](../skills/ppt-master/scripts/project_utils.py) | Canvas formats, project path conventions |
| [`error_helper.py`](../skills/ppt-master/scripts/error_helper.py) | User-facing error message templates |

**Forbidden — duplicating logic that exists in a shared helper**. If a helper is missing a feature, extend the helper, don't fork it inside your new script.

---

## 10. Docstrings

Short and imperative. No Args/Returns/Raises sections unless the signature is genuinely complex.

```python
def classify_license(
    license_name: str,
    license_url: str = "",
    provider: str = "",
) -> Optional[str]:
    """Classify a license string into one of the two tiers, or reject it.

    Returns:
        ``"no-attribution"`` / ``"attribution-required"`` / ``None``.

    The provider hint lets us treat Pexels and Pixabay's own licenses as
    ``no-attribution`` even when the upstream API only returns a short
    label like ``"Pexels"``.
    """
```

| Use a Google/Sphinx-style block | Skip the block |
|---|---|
| Function returns multiple branches with semantic differences | One-liner that explains itself in the function name |
| Has more than 3 parameters with non-obvious roles | Single-purpose helper |
| Maintains a non-trivial invariant | Pure formatter / accessor |

---

## 11. Testing

**Hard rule**: this repository does **not** ship automated tests.

**Forbidden**:

- `tests/` directories
- `test_*.py` files
- `unittest` / `pytest` imports
- `if __name__ == "__main__":` blocks that run a self-test suite

**Use instead**:

- Inline smoke commands via `python3 -c "..."` against real project samples; show the output in the conversation / PR description
- Manual verification steps in the runbook
- Live-API smoke runs against `projects/_smoke_*` directories (gitignored)

This is a deliberate project convention. When external contributors include tests, ask them to remove tests in PR review (see [`docs/rules/prompt-style.md`](./prompt-style.md) §11 for the parallel rule on reference docs).

---

## 12. Dataclasses

Prefer plain `@dataclass` over `pydantic` / `attrs` for value types. Keep them simple:

```python
@dataclass
class AssetCandidate:
    provider: str
    title: str
    asset_id: str = ""
    license_tier: str = ""
    width: int = 0
    height: int = 0
    raw: Any = None
```

| Rule | Note |
|---|---|
| `@dataclass` | Default; no need for `frozen=True` unless mutation is a real risk |
| Fields | All required fields first, then optional with defaults |
| `field(default_factory=...)` | Only when the default needs to be a new container per instance |
| No legacy positional-arg shims | New dataclass = keyword-arg API. YAGNI on positional support |
| Methods | Keep dataclasses dumb; computation goes in module-level functions |

---

## 13. File Encoding & Line Endings

| Property | Value |
|---|---|
| Encoding | UTF-8 |
| Line endings | LF |
| Final newline | Always present |
| BOM | Forbidden |
| Indentation | 4 spaces (no tabs) |
| Max line length | Soft 100; hard 120. Prose in docstrings can flow longer |

---

## 14. Cross-references

When a Python file mirrors a reference doc, cross-link both ways:

- The script's docstring mentions the reference: `See references/image-searcher.md for the on-slide attribution rules.`
- The reference doc cites the script with a backticked relative link

This keeps `prompt-style.md` and `code-style.md` (this file) operating as a pair — neither layer drifts away from the other.

---

## 15. When This Guide Conflicts With Existing Files

Existing files take precedence. If a current script contradicts a rule here, decide whether to (a) update this guide, or (b) refactor the script. The canonical exemplars to model new scripts after:

| If you're writing... | Model after |
|---|---|
| A small CLI utility | [`total_md_split.py`](../skills/ppt-master/scripts/total_md_split.py), [`gemini_watermark_remover.py`](../skills/ppt-master/scripts/gemini_watermark_remover.py) |
| A multi-backend / dispatcher CLI | [`image_search.py`](../skills/ppt-master/scripts/image_search.py), [`image_gen.py`](../skills/ppt-master/scripts/image_gen.py) |
| A library / shared helper | [`image_sources/provider_common.py`](../skills/ppt-master/scripts/image_sources/provider_common.py), [`image_backends/backend_common.py`](../skills/ppt-master/scripts/image_backends/backend_common.py) |
| A class-based checker / validator | [`svg_quality_checker.py`](../skills/ppt-master/scripts/svg_quality_checker.py) |
