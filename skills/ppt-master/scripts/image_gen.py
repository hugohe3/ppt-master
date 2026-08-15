#!/usr/bin/env python3
"""
Unified Image Generation Tool

Dispatches to the appropriate backend based on explicit provider configuration.

Backend selection (`IMAGE_BACKEND` in `.env` or the current process environment):
  IMAGE_BACKEND=gemini      -> Gemini backend (google-genai SDK)
  IMAGE_BACKEND=openai      -> OpenAI-compatible backend (raw HTTP via requests)
  IMAGE_BACKEND=minimax     -> MiniMax image backend
  IMAGE_BACKEND=stability   -> Stability AI backend
  IMAGE_BACKEND=bfl         -> Black Forest Labs FLUX backend
  IMAGE_BACKEND=ideogram    -> Ideogram backend
  IMAGE_BACKEND=qwen        -> Alibaba Qwen image backend
  IMAGE_BACKEND=zhipu       -> Zhipu GLM-Image backend
  IMAGE_BACKEND=volcengine  -> Volcengine Seedream backend
  IMAGE_BACKEND=modelscope  -> ModelScope backend
  IMAGE_BACKEND=siliconflow -> SiliconFlow backend
  IMAGE_BACKEND=fal         -> fal.ai backend
  IMAGE_BACKEND=replicate   -> Replicate backend
  IMAGE_BACKEND=openrouter  -> OpenRouter backend

Configuration source (process env wins, `.env` is the fallback layer):
  1. Current process environment variables
  2. The first `.env` found among:
     - Current working directory
     - Skill directory (e.g. `~/.agents/skills/ppt-master/.env`)
     - Repo root (when running from a clone)
     - `~/.ppt-master/.env` (user-level config)

Supported keys:
  IMAGE_BACKEND    (required) backend name

  Provider-specific keys are used for credentials and overrides, for example:
    GEMINI_API_KEY / GEMINI_MODEL / GEMINI_BASE_URL
    OPENAI_API_KEY / OPENAI_MODEL / OPENAI_BASE_URL
    QWEN_API_KEY / QWEN_MODEL / QWEN_BASE_URL
    ZHIPU_API_KEY / ZHIPU_MODEL / ZHIPU_BASE_URL

Usage:
  python3 image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o images/
  python3 image_gen.py "edit instruction" --reference-image src.png -o images/
  python3 image_gen.py --manifest project/images/image_prompts.json -o project/images/
  python3 image_gen.py --list-backends
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import tempfile
import threading
import time
from pathlib import Path

from console_encoding import configure_utf8_stdio
from config import load_prefixed_env_file, resolve_env_path

configure_utf8_stdio()

ENV_PATH = resolve_env_path()
IMAGE_ENV_PREFIXES = (
    "IMAGE_",
    "GEMINI_",
    "OPENAI_",
    "MINIMAX_",
    "STABILITY_",
    "BFL_",
    "IDEOGRAM_",
    "QWEN_",
    "DASHSCOPE_",
    "ZHIPU_",
    "BIGMODEL_",
    "VOLCENGINE_",
    "LAS_",
    "ARK_",
    "MODELSCOPE_",
    "SILICONFLOW_",
    "FAL_",
    "REPLICATE_",
    "OPENROUTER_",
)
DEPRECATED_IMAGE_KEYS = {
    "IMAGE_API_KEY",
    "IMAGE_MODEL",
    "IMAGE_BASE_URL",
}

# All aspect ratios accepted by the unified CLI
# (each backend validates its own subset internally)
ALL_ASPECT_RATIOS = [
    "1:1", "1:2", "1:3", "1:4", "1:8",
    "2:1", "2:3", "3:1", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "9:21", "10:16",
    "16:9", "16:10", "21:9",
]

ALL_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

BACKEND_REGISTRY = {
    "gemini": {
        "module": "backend_gemini",
        "tier": "core",
        "label": "Google Gemini",
        "default_model": "gemini-3.1-flash-image",
        "default_image_size": "1K",
        "key_hint": "GEMINI_API_KEY",
        "aliases": ["google"],
    },
    "openai": {
        "module": "backend_openai",
        "tier": "core",
        "label": "OpenAI / OpenAI-compatible",
        "default_model": "gpt-image-2",
        "default_image_size": "1K",
        "key_hint": "OPENAI_API_KEY",
        "aliases": ["openai-compatible", "openai_compatible"],
    },
    "minimax": {
        "module": "backend_minimax",
        "tier": "experimental",
        "label": "MiniMax Image",
        "default_model": "image-01",
        "default_image_size": "1K",
        "key_hint": "MINIMAX_API_KEY",
        "aliases": ["minimaxi"],
    },
    "qwen": {
        "module": "backend_qwen",
        "tier": "core",
        "label": "Alibaba Qwen Image",
        "default_model": "qwen-image-2.0-pro",
        "default_image_size": "1K",
        "key_hint": "QWEN_API_KEY / DASHSCOPE_API_KEY",
        "aliases": ["alibaba", "dashscope"],
    },
    "zhipu": {
        "module": "backend_zhipu",
        "tier": "core",
        "label": "Zhipu GLM-Image",
        "default_model": "glm-image",
        "default_image_size": "1K",
        "key_hint": "ZHIPU_API_KEY / BIGMODEL_API_KEY",
        "aliases": ["bigmodel", "glm", "glm-image"],
    },
    "volcengine": {
        "module": "backend_volcengine",
        "tier": "core",
        "label": "Volcengine Seedream",
        "default_model": "doubao-seedream-4-5-251128",
        "default_image_size": "2K",
        "key_hint": "LAS_API_KEY / VOLCENGINE_API_KEY / ARK_API_KEY",
        "aliases": ["ark", "doubao", "seedream"],
    },
    "modelscope": {
        "module": "backend_modelscope",
        "tier": "experimental",
        "label": "ModelScope",
        "default_model": None,
        "model_hint": "MODELSCOPE_MODEL",
        "default_image_size": "1K",
        "key_hint": "MODELSCOPE_API_KEY",
        "aliases": ["modelscope", "model-scope"]
    },
    "stability": {
        "module": "backend_stability",
        "tier": "extended",
        "label": "Stability AI",
        "default_model": "stable-image-core",
        "default_image_size": "1K",
        "key_hint": "STABILITY_API_KEY",
        "aliases": ["stabilityai", "stability-ai"],
    },
    "bfl": {
        "module": "backend_bfl",
        "tier": "extended",
        "label": "Black Forest Labs FLUX",
        "default_model": "flux-pro-1.1-ultra",
        "default_image_size": "1K",
        "key_hint": "BFL_API_KEY",
        "aliases": ["flux", "black-forest-labs", "black_forest_labs"],
    },
    "ideogram": {
        "module": "backend_ideogram",
        "tier": "extended",
        "label": "Ideogram",
        "default_model": "ideogram-v3",
        "default_image_size": "1K",
        "key_hint": "IDEOGRAM_API_KEY",
    },
    "siliconflow": {
        "module": "backend_siliconflow",
        "tier": "experimental",
        "label": "SiliconFlow",
        "default_model": "Qwen/Qwen-Image",
        "default_image_size": "1K",
        "key_hint": "SILICONFLOW_API_KEY",
        "aliases": ["silicon"],
    },
    "fal": {
        "module": "backend_fal",
        "tier": "experimental",
        "label": "fal.ai",
        "default_model": "fal-ai/nano-banana-2",
        "default_image_size": "1K",
        "key_hint": "FAL_KEY / FAL_API_KEY",
        "aliases": ["fal-ai"],
    },
    "replicate": {
        "module": "backend_replicate",
        "tier": "experimental",
        "label": "Replicate",
        "default_model": "black-forest-labs/flux-1.1-pro",
        "default_image_size": "1K",
        "key_hint": "REPLICATE_API_TOKEN / REPLICATE_API_KEY",
    },
    "openrouter": {
        "module": "backend_openrouter",
        "tier": "experimental",
        "label": "OpenRouter",
        "default_model": "google/gemini-3.1-flash-image",
        "default_image_size": "1K",
        "key_hint": "OPENROUTER_API_KEY",
    },
}

TIER_ORDER = {"core": 0, "extended": 1, "experimental": 2}
SUPPORTED_BACKENDS = tuple(sorted(BACKEND_REGISTRY))


def _load_image_env_file() -> Path | None:
    """
    Load image generation config from the resolved `.env` as a fallback layer.

    Existing process environment variables win over `.env`.
    """
    replacements = {
        "IMAGE_API_KEY": "GEMINI_API_KEY / OPENAI_API_KEY / QWEN_API_KEY / ZHIPU_API_KEY / ...",
        "IMAGE_MODEL": "GEMINI_MODEL / OPENAI_MODEL / QWEN_MODEL / ZHIPU_MODEL / ...",
        "IMAGE_BASE_URL": "GEMINI_BASE_URL / OPENAI_BASE_URL / QWEN_BASE_URL / ZHIPU_BASE_URL / ...",
    }
    deprecated_messages = {
        key: (
            "Global image config keys have been removed.\n"
            f"Use IMAGE_BACKEND plus provider-specific keys instead, such as {replacement}."
        )
        for key, replacement in replacements.items()
    }
    return load_prefixed_env_file(
        IMAGE_ENV_PREFIXES,
        deprecated_keys=deprecated_messages,
    )


def _validate_runtime_config() -> None:
    """Reject deprecated global image variables from any configuration source."""
    for key in DEPRECATED_IMAGE_KEYS:
        if key not in os.environ:
            continue
        replacement = {
            "IMAGE_API_KEY": "GEMINI_API_KEY / OPENAI_API_KEY / QWEN_API_KEY / ZHIPU_API_KEY / ...",
            "IMAGE_MODEL": "GEMINI_MODEL / OPENAI_MODEL / QWEN_MODEL / ZHIPU_MODEL / ...",
            "IMAGE_BASE_URL": "GEMINI_BASE_URL / OPENAI_BASE_URL / QWEN_BASE_URL / ZHIPU_BASE_URL / ...",
        }[key]
        raise ValueError(
            f"Unsupported image config key: {key}\n"
            "Global image config keys have been removed.\n"
            f"Use IMAGE_BACKEND plus provider-specific keys instead, such as {replacement}."
        )


def _build_backend_aliases() -> dict[str, str]:
    """Build a lookup from aliases to canonical backend names."""
    aliases = {}
    for canonical_name, config in BACKEND_REGISTRY.items():
        aliases[canonical_name] = canonical_name
        for alias in config.get("aliases", []):
            aliases[alias] = canonical_name
    return aliases


BACKEND_ALIASES = _build_backend_aliases()


_BACKEND_PIP_HINTS = {
    "gemini": "google-genai",
    "openai": "openai",
}


def _load_backend(canonical_name: str) -> tuple[object, str]:
    """Import and return the configured backend module."""
    module_name = f"image_backends.{BACKEND_REGISTRY[canonical_name]['module']}"
    try:
        module = __import__(module_name, fromlist=["*"])
    except ImportError as exc:
        pip_name = _BACKEND_PIP_HINTS.get(canonical_name, exc.name or "<dependency>")
        print(
            f"Error: backend '{canonical_name}' needs a package that is not installed.\n"
            f"Missing: {exc.name}\n"
            f"Run: pip install {pip_name}",
            file=sys.stderr,
        )
        sys.exit(1)
    return module, canonical_name


def _print_backend_resolution() -> None:
    """Print the effective Path A backend without exposing credentials."""
    backend_from_process = "IMAGE_BACKEND" in os.environ
    try:
        env_path = _load_image_env_file()
    except ValueError as exc:
        print("Resolved backend: invalid configuration")
        print(f"Configuration source: {ENV_PATH}")
        print(f"Configuration error: {exc}")
        return

    try:
        _validate_runtime_config()
    except ValueError as exc:
        print("Resolved backend: invalid configuration")
        print("Configuration source: process environment")
        print(f"Configuration error: {exc}")
        return

    backend_name = os.environ.get("IMAGE_BACKEND", "").strip().lower()
    if not backend_name:
        if backend_from_process:
            source = "process environment (empty)"
        elif env_path is not None:
            source = f"none (checked {env_path})"
        else:
            source = "none (no .env found)"
        print("Resolved backend: not configured (Path A unavailable)")
        print(f"Configuration source: {source}")
        return

    canonical = BACKEND_ALIASES.get(backend_name)
    resolved = canonical or f"invalid ({backend_name})"
    source = "process environment" if backend_from_process else str(env_path or ENV_PATH)
    print(f"Resolved backend: {resolved}")
    print(f"Configuration source: {source}")


def _print_backend_list() -> None:
    """Print supported backends grouped by support tier."""
    print("Supported image backends:\n")
    tiers = ("core", "extended", "experimental")
    for tier in tiers:
        print(f"{tier.upper()}:")
        for name, info in sorted(
            BACKEND_REGISTRY.items(),
            key=lambda item: (TIER_ORDER[item[1]["tier"]], item[0]),
        ):
            if info["tier"] != tier:
                continue
            if info["default_model"]:
                model_label = f"default={info['default_model']}"
            else:
                model_label = f"model=required via {info['model_hint']}"
            print(
                f"  {name:<12} {info['label']} | "
                f"{model_label} | "
                f"size={info['default_image_size']} | keys={info['key_hint']}"
            )
        print()
    print("Recommendation: prefer CORE backends for everyday PPT generation.")
    _print_backend_resolution()


def _resolve_backend() -> tuple[object, str]:
    """
    Determine which backend to use from explicit configuration.

    Returns:
        A backend module with a generate() function.
    """
    backend_name = os.environ.get("IMAGE_BACKEND", "").strip().lower()
    if backend_name:
        canonical = BACKEND_ALIASES.get(backend_name)
        if not canonical:
            supported = ", ".join(SUPPORTED_BACKENDS)
            print(f"Error: Unknown IMAGE_BACKEND='{backend_name}'. Supported: {supported}")
            sys.exit(1)
        return _load_backend(canonical)

    supported = ", ".join(SUPPORTED_BACKENDS)
    print(
        "Error: No image backend configured for Path A (image_gen.py).\n"
        "\n"
        "If your host (Codex / Antigravity / Claude Code / etc.) has a native image\n"
        "generation tool, do NOT run this script — switch to Path B: invoke the host's\n"
        "image tool directly with the prompts from images/image_prompts.json and save\n"
        "the outputs to images/<filename>. See references/image-generator.md §7 Path B.\n"
        "\n"
        "To use Path A instead, set IMAGE_BACKEND in one of these places:\n"
        f"  1. Current process environment\n"
        f"  2. {ENV_PATH}\n"
        "\n"
        f"Supported backends: {supported}\n"
        "\n"
        "Example:\n"
        "  IMAGE_BACKEND=openai\n"
        "  OPENAI_API_KEY=sk-xxx\n"
    )
    sys.exit(1)


_AI_IMAGE_PATH_ROW_RE = re.compile(
    r"^\s*\|\s*AI Image Acquisition Path\s*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
VALID_AI_IMAGE_ACQUISITION_PATHS = {
    "api",
    "auto",
    "host-native",
    "manual",
}


def _project_design_spec_for_manifest(manifest_path: str) -> Path | None:
    """Return a project Design Spec for an images/ manifest, when present."""
    path = Path(manifest_path).resolve()
    if path.parent.name != "images":
        return None
    design_spec = path.parent.parent / "design_spec.md"
    return design_spec if design_spec.is_file() else None


def _confirmed_image_acquisition_path_for_manifest(
    manifest_path: str,
) -> str | None:
    """Return the Design Spec's AI Image Acquisition Path, if present."""
    design_spec = _project_design_spec_for_manifest(manifest_path)
    if design_spec is None:
        return None
    try:
        text = design_spec.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _AI_IMAGE_PATH_ROW_RE.search(text)
    if not match:
        return None
    value = match.group(1).strip().lstrip("`*_ ").strip()
    token_match = re.match(
        r"^(host[\s_-]*native|api|auto|manual)(?![A-Za-z0-9_-])",
        value,
        re.IGNORECASE,
    )
    selected = token_match.group(1) if token_match else value
    return re.sub(r"[\s_]+", "-", selected.strip().lower())


def _guard_confirmed_non_api_path(manifest_path: str) -> None:
    """Allow project Path A only when its Design Spec explicitly permits it."""
    design_spec = _project_design_spec_for_manifest(manifest_path)
    if design_spec is None:
        return
    acquisition_path = _confirmed_image_acquisition_path_for_manifest(manifest_path)
    if acquisition_path not in VALID_AI_IMAGE_ACQUISITION_PATHS:
        shown = acquisition_path or "(missing)"
        valid = ", ".join(sorted(VALID_AI_IMAGE_ACQUISITION_PATHS))
        print(
            "Error: project manifest mode requires a valid "
            "AI Image Acquisition Path in design_spec.md §I.\n"
            f"Found: {shown!r}. Valid values: {valid}.\n"
            "Return to Generate Step 4 recovery and record the durable "
            "selection before running Path A."
        )
        sys.exit(1)
    if acquisition_path in {"api", "auto"}:
        return
    if acquisition_path == "host-native":
        print(
            "Error: Design Spec confirms AI Image Acquisition Path as 'host-native'.\n"
            "\n"
            "Do NOT run image_gen.py --manifest for this project. That command is Path A\n"
            "and may use the configured API/proxy backend. Use the host's native image\n"
            "generation tool with prompts from images/image_prompts.json, save outputs to\n"
            "images/<filename>, update each item status to Generated, then run:\n"
            "  python3 scripts/image_gen.py --render-md images/image_prompts.json\n"
        )
    else:
        print(
            "Error: Design Spec confirms AI Image Acquisition Path as 'manual'.\n"
            "\n"
            "Do NOT run image_gen.py --manifest for this project. Render the Markdown\n"
            "sidecar and hand images/image_prompts.md to the user for external generation:\n"
            "  python3 scripts/image_gen.py --render-md images/image_prompts.json\n"
        )
    sys.exit(1)


DEFAULT_MANIFEST_CONCURRENCY = 3
MAX_MANIFEST_RATE_LIMIT_ATTEMPTS = 3

STATUS_PENDING = "Pending"
STATUS_GENERATED = "Generated"
STATUS_FAILED = "Failed"
STATUS_NEEDS_MANUAL = "Needs-Manual"
VALID_STATUSES = {STATUS_PENDING, STATUS_GENERATED, STATUS_FAILED, STATUS_NEEDS_MANUAL}
RETRYABLE_STATUSES = {STATUS_PENDING, STATUS_FAILED}
REQUIRED_ITEM_FIELDS = ("filename", "prompt", "aspect_ratio", "status")
VALID_PAGE_ROLES = {"local", "hero_page", "full_page"}
VALID_TEXT_POLICIES = {"none", "embedded"}
STRUCTURAL_IMAGE_TYPES = {
    "infographic",
    "flowchart",
    "framework",
    "matrix",
    "cycle",
    "funnel",
    "pyramid",
    "comparison",
    "timeline",
    "map",
    "scene",
}
LEGACY_IMAGE_TYPES = {"background", "hero", "portrait", "typography"}
EARLY_LEGACY_IMAGE_TYPES = {"illustration", "photography"}
VALID_IMAGE_TYPES = (
    STRUCTURAL_IMAGE_TYPES
    | LEGACY_IMAGE_TYPES
    | EARLY_LEGACY_IMAGE_TYPES
)


def _validate_bare_output_name(
    value: str,
    *,
    field_name: str,
    require_extension: bool = False,
    reject_parent_marker: bool = False,
) -> Path:
    """Require one cross-platform-safe basename, optionally with an extension."""
    value_path = Path(value)
    if (
        not value.strip()
        or value in {".", ".."}
        or reject_parent_marker and ".." in value
        or "/" in value
        or "\\" in value
        or ":" in value
        or value_path.is_absolute()
        or value_path.name != value
    ):
        raise ValueError(
            f"{field_name} must be a bare filename without path components, "
            f"got {value!r}"
        )
    if require_extension and not value_path.suffix:
        raise ValueError(f"{field_name} must include an extension, got {value!r}")
    return value_path


def load_manifest(path: str) -> dict:
    """Load and validate an `image_prompts.json` manifest.

    Schema (top level): {"items": [ ... ]}, optionally with
    `deck_rendering`, `color_scheme`, `generated_at`.

    Each item requires: `filename`, `prompt`, `aspect_ratio`, `status`.
    Optional: `image_size`, `model`, `alt_text`, `purpose`, `type`,
    `page_role`, `text_policy`, `slice_grid`, `slice_names`, `last_error`.
    """
    from image_backends.backend_common import normalize_image_size

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc.msg} "
            f"(line {exc.lineno}, col {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top level must be a JSON object, "
            f"got {type(data).__name__}"
        )

    for field in ("project", "generated_at", "deck_rendering"):
        if field not in data:
            continue
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(
                f"{path}: field '{field}' must be a non-empty string when present"
            )
    if "deck_style_anchor" in data:
        legacy_anchor = data["deck_style_anchor"]
        if not (
            isinstance(legacy_anchor, str)
            and legacy_anchor.strip()
            or isinstance(legacy_anchor, dict)
            and legacy_anchor
        ):
            raise ValueError(
                f"{path}: legacy field 'deck_style_anchor' must be a "
                "non-empty string or object when present"
            )

    if "color_scheme" in data:
        color_scheme = data["color_scheme"]
        if not isinstance(color_scheme, dict) or not color_scheme:
            raise ValueError(
                f"{path}: field 'color_scheme' must be a non-empty object when present"
            )
        for key, value in color_scheme.items():
            if (
                not isinstance(key, str)
                or not key.strip()
                or not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    f"{path}: color_scheme keys and values must be non-empty strings"
                )

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: 'items' must be a non-empty array")

    claimed_outputs: dict[str, str] = {}
    seen_stems: set[str] = set()
    missing_page_role = 0
    missing_text_policy = 0
    for i, item in enumerate(items):
        prefix = f"{path}: items[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be an object")
        for field in REQUIRED_ITEM_FIELDS:
            if field not in item:
                raise ValueError(f"{prefix} missing required field '{field}'")
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(
                    f"{prefix} field '{field}' must be a non-empty string"
                )
        if item["status"] not in VALID_STATUSES:
            raise ValueError(
                f"{prefix} status '{item['status']}' is invalid. "
                f"Valid: {sorted(VALID_STATUSES)}"
            )
        if item["aspect_ratio"] not in ALL_ASPECT_RATIOS:
            raise ValueError(
                f"{prefix} aspect_ratio '{item['aspect_ratio']}' is invalid. "
                f"Valid: {ALL_ASPECT_RATIOS}"
            )
        if "image_size" in item:
            image_size = item["image_size"]
            if not isinstance(image_size, str) or not image_size.strip():
                raise ValueError(
                    f"{prefix} field 'image_size' must be a non-empty string"
                )
            normalized_size = normalize_image_size(image_size)
            if normalized_size not in ALL_IMAGE_SIZES:
                raise ValueError(
                    f"{prefix} image_size '{image_size}' is invalid. "
                    f"Valid: {ALL_IMAGE_SIZES}"
                )

        page_role = item.get("page_role")
        if page_role is None:
            missing_page_role += 1
        elif not isinstance(page_role, str) or page_role not in VALID_PAGE_ROLES:
            raise ValueError(
                f"{prefix} page_role '{page_role}' is invalid. "
                f"Valid: {sorted(VALID_PAGE_ROLES)}"
            )

        text_policy = item.get("text_policy")
        if text_policy is None:
            missing_text_policy += 1
        elif (
            not isinstance(text_policy, str)
            or text_policy not in VALID_TEXT_POLICIES
        ):
            raise ValueError(
                f"{prefix} text_policy '{text_policy}' is invalid. "
                f"Valid: {sorted(VALID_TEXT_POLICIES)}"
            )

        image_type = item.get("type")
        if image_type is not None:
            normalized_type = (
                image_type.strip().lower()
                if isinstance(image_type, str)
                else ""
            )
            if normalized_type not in VALID_IMAGE_TYPES:
                raise ValueError(
                    f"{prefix} type '{image_type}' is invalid. "
                    f"Valid current/legacy values: {sorted(VALID_IMAGE_TYPES)}"
                )

        for field in ("model", "alt_text", "purpose"):
            if field in item and (
                not isinstance(item[field], str) or not item[field].strip()
            ):
                raise ValueError(
                    f"{prefix} field '{field}' must be a non-empty string when present"
                )
        if "last_error" in item and not isinstance(item["last_error"], str):
            raise ValueError(f"{prefix} field 'last_error' must be a string")
        has_slice_grid = "slice_grid" in item
        has_slice_names = "slice_names" in item
        slice_outputs: list[str] = []
        if has_slice_grid != has_slice_names:
            raise ValueError(
                f"{prefix} fields 'slice_grid' and 'slice_names' must appear together"
            )
        if has_slice_grid:
            slice_grid = item["slice_grid"]
            grid_match = (
                re.fullmatch(r"([1-9]\d*)[xX]([1-9]\d*)", slice_grid.strip())
                if isinstance(slice_grid, str)
                else None
            )
            if grid_match is None:
                raise ValueError(
                    f"{prefix} field 'slice_grid' must use positive RxC notation"
                )
            slice_names = item["slice_names"]
            if not isinstance(slice_names, str) or not slice_names.strip():
                raise ValueError(
                    f"{prefix} field 'slice_names' must be a non-empty string"
                )
            names = [name.strip() for name in slice_names.split(",")]
            if any(not name for name in names):
                raise ValueError(
                    f"{prefix} field 'slice_names' contains an empty name"
                )
            rows, cols = map(int, grid_match.groups())
            if len(names) != rows * cols:
                raise ValueError(
                    f"{prefix} field 'slice_names' has {len(names)} names but "
                    f"slice_grid {rows}x{cols} requires {rows * cols}"
                )
            normalized_outputs: set[str] = set()
            for name in names:
                name_path = _validate_bare_output_name(
                    name,
                    field_name=f"{prefix} slice output name",
                    reject_parent_marker=True,
                )
                if name_path.suffix and name_path.suffix.lower() != ".png":
                    raise ValueError(
                        f"{prefix} slice output name {name!r} must omit its "
                        "extension or use .png"
                    )
                output_name = (
                    name if name_path.suffix else f"{name}.png"
                ).casefold()
                if output_name in normalized_outputs:
                    raise ValueError(
                        f"{prefix} field 'slice_names' repeats output "
                        f"{output_name!r}"
                    )
                normalized_outputs.add(output_name)
                slice_outputs.append(output_name)

        fname = item["filename"]
        filename_path = _validate_bare_output_name(
            fname,
            field_name=f"{prefix} field 'filename'",
            require_extension=True,
        )
        normalized_filename = fname.casefold()
        if normalized_filename in claimed_outputs:
            raise ValueError(
                f"{prefix} output filename {fname!r} conflicts with "
                f"{claimed_outputs[normalized_filename]} (case-insensitive)"
            )
        claimed_outputs[normalized_filename] = f"manifest output {fname!r}"

        stem = filename_path.stem.casefold()
        if stem in seen_stems:
            raise ValueError(
                f"{prefix} duplicate filename stem '{filename_path.stem}' "
                "would reuse backend output"
            )
        seen_stems.add(stem)

        for output_name in slice_outputs:
            if output_name in claimed_outputs:
                raise ValueError(
                    f"{prefix} slice output {output_name!r} conflicts with "
                    f"{claimed_outputs[output_name]} (case-insensitive)"
                )
            claimed_outputs[output_name] = (
                f"slice output {output_name!r} from items[{i}]"
            )

    legacy_parts = []
    if missing_page_role:
        legacy_parts.append(
            f"{missing_page_role} item(s) missing page_role (resolved as local)"
        )
    if missing_text_policy:
        legacy_parts.append(
            f"{missing_text_policy} item(s) missing text_policy (resolved as none)"
        )
    if legacy_parts:
        print(
            f"Warning: {path}: legacy manifest compatibility: "
            + "; ".join(legacy_parts),
            file=sys.stderr,
        )

    return data


def save_manifest(path: str, data: dict) -> None:
    """Atomically write manifest back to disk (tmp file + rename)."""
    target = Path(path)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.stem + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _materialize_manifest_image(saved_path: str, target_path: Path) -> str:
    """Validate backend output and place it at the manifest's exact target path."""
    from image_backends.backend_common import (
        save_image_bytes,
        validate_image_file,
    )

    source_path = Path(saved_path)
    validate_image_file(str(source_path))

    if source_path.resolve() != target_path.resolve():
        try:
            image_bytes = source_path.read_bytes()
        except OSError as exc:
            raise RuntimeError(
                f"Could not read image output {source_path}: {exc}"
            ) from exc
        save_image_bytes(image_bytes, str(target_path))

    validate_image_file(str(target_path))
    return str(target_path)


def _run_manifest(manifest: dict, manifest_path: str, backend_module, *,
                  initial_concurrency: int,
                  image_size: str,
                  output_dir: str,
                  model: str | None) -> tuple[int, int, int]:
    """Run Pending/Failed items through the backend with adaptive concurrency.

    Strategy:
      - Verify every `Generated` item's target before treating it as done;
        missing or unreadable output returns to `Failed` for this run.
      - Start at `initial_concurrency` workers per batch.
      - On any rate-limit error in a batch, halve concurrency (min 1) and
        requeue the rate-limited items within a fixed attempt budget.
      - A rate limit at concurrency 1 or after the budget is exhausted is
        recorded as `status: Failed` + `last_error`; the current run then stops
        without switching providers.
      - Per-item failures are recorded as `status: Failed` + `last_error`
        and not retried within this run. `Failed` remains retryable and
        non-terminal; the Step 5 gate must resolve it by rerunning this
        manifest or marking the item `Needs-Manual`.
      - Status is written back to the manifest file after each completion;
        a Ctrl-C in the middle still preserves done items.
      - `Needs-Manual` items are skipped (user processes them externally).

    Returns (ok_count, failed_count, skipped_count).
    """
    manifest_output_dir = Path(manifest_path).resolve().parent
    if Path(output_dir).resolve() != manifest_output_dir:
        raise ValueError(
            "Manifest outputs must stay beside image_prompts.json: "
            f"expected {manifest_output_dir}, got {Path(output_dir).resolve()}"
        )
    output_dir = str(manifest_output_dir)

    from image_backends.backend_common import (
        is_rate_limit_error,
        validate_image_file,
    )

    items = manifest["items"]
    repaired_generated = False
    for item in items:
        if item["status"] != STATUS_GENERATED:
            continue
        target_path = Path(output_dir) / item["filename"]
        try:
            validate_image_file(str(target_path))
        except RuntimeError as exc:
            item["status"] = STATUS_FAILED
            item["last_error"] = (
                f"Generated file validation failed: {exc}"
            )[:500]
            repaired_generated = True
            print(
                f"  [RETRY] {item['filename']} was marked Generated but its "
                f"target is invalid: {exc}"
            )
    if repaired_generated:
        save_manifest(manifest_path, manifest)

    pending_idx = [
        i for i, it in enumerate(items) if it["status"] in RETRYABLE_STATUSES
    ]
    total = len(pending_idx)
    skipped = len(items) - total

    if total == 0:
        print(
            f"[Manifest] Nothing to do — all {len(items)} items already in "
            "a terminal state (Generated / Needs-Manual)."
        )
        return 0, 0, skipped

    print(
        f"\n[Manifest] {total} item(s) to generate, "
        f"{skipped} already done. concurrency={initial_concurrency}\n"
    )

    queue: list[int] = list(pending_idx)
    ok_count = 0
    fail_count = 0
    current = max(1, initial_concurrency)
    state_lock = threading.Lock()
    rate_limit_attempts: dict[int, int] = {}
    stopped_for_rate_limit = False

    def _one(idx: int):
        item = items[idx]
        try:
            saved_path = backend_module.generate(
                prompt=item["prompt"],
                aspect_ratio=item["aspect_ratio"],
                image_size=item.get("image_size", image_size),
                output_dir=output_dir,
                filename=Path(item["filename"]).stem,
                model=item.get("model", model),
            )
            saved_path = _materialize_manifest_image(
                saved_path,
                Path(output_dir) / item["filename"],
            )
            return idx, saved_path, None
        except Exception as exc:  # noqa: BLE001 — backend raises arbitrary types
            return idx, None, exc

    while queue:
        batch_size = min(current, len(queue))
        batch_idx = queue[:batch_size]
        queue = queue[batch_size:]

        print(
            f"--- Batch of {batch_size} (concurrency={current}, "
            f"remaining_after={len(queue)}) ---"
        )

        rate_limited = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as ex:
            futures = [ex.submit(_one, i) for i in batch_idx]
            for fut in concurrent.futures.as_completed(futures):
                idx, saved_path, exc = fut.result()
                item = items[idx]
                with state_lock:
                    if exc is None:
                        item["status"] = STATUS_GENERATED
                        item.pop("last_error", None)
                        ok_count += 1
                        print(f"  [OK]   {item['filename']}")
                    elif is_rate_limit_error(exc):
                        rate_limited = True
                        attempts = rate_limit_attempts.get(idx, 0) + 1
                        rate_limit_attempts[idx] = attempts
                        if (
                            current == 1
                            or attempts >= MAX_MANIFEST_RATE_LIMIT_ATTEMPTS
                        ):
                            boundary = (
                                "serial concurrency reached"
                                if current == 1
                                else "rate-limit attempt budget exhausted"
                            )
                            item["status"] = STATUS_FAILED
                            item["last_error"] = (
                                f"Rate limit persisted ({boundary}; "
                                f"attempt {attempts}): {exc}"
                            )[:500]
                            fail_count += 1
                            stopped_for_rate_limit = True
                            print(
                                f"  [FAIL] {item['filename']}: {exc} "
                                f"({boundary}; status=Failed)"
                            )
                        else:
                            queue.append(idx)
                            print(
                                f"  [RATE] {item['filename']} — requeued "
                                f"(attempt {attempts}/"
                                f"{MAX_MANIFEST_RATE_LIMIT_ATTEMPTS})"
                            )
                    else:
                        item["status"] = STATUS_FAILED
                        item["last_error"] = str(exc)[:500]
                        fail_count += 1
                        print(
                            f"  [FAIL] {item['filename']}: {exc} "
                            "(status=Failed; retry or mark Needs-Manual before Executor)"
                        )
                    save_manifest(manifest_path, manifest)

        if stopped_for_rate_limit:
            print(
                "\n  Persistent rate limit reached the run boundary. "
                "Stopping without switching providers; untouched items remain retryable.\n"
            )
            break
        if rate_limited and current > 1 and queue:
            new_current = max(1, current // 2)
            print(
                f"\n  ⚠ Rate-limit hit — concurrency {current} → {new_current}, "
                "pausing 10s before next batch\n"
            )
            current = new_current
            time.sleep(10)
        elif queue:
            time.sleep(2)

    run_state = "Stopped" if stopped_for_rate_limit else "Done"
    remaining_note = ""
    if stopped_for_rate_limit:
        remaining = sum(
            1 for item in items if item["status"] in RETRYABLE_STATUSES
        )
        remaining_note = f"; {remaining} item(s) remain retryable"
    print(
        f"\n[Manifest] {run_state}: {ok_count} ok / {fail_count} failed "
        f"({skipped} pre-skipped{remaining_note}). "
        f"Manifest written to {manifest_path}"
    )
    if fail_count:
        print(
            "[Manifest] Failed is retryable and non-terminal. "
            "Resolve failed item(s) by rerunning this manifest or marking them "
            "Needs-Manual before entering Executor."
        )
    return ok_count, fail_count, skipped


def _resolve_concurrency(cli_value: int | None) -> int:
    """CLI value wins over IMAGE_CONCURRENCY env; default 3."""
    if cli_value is not None:
        return max(1, cli_value)
    env_val = os.environ.get("IMAGE_CONCURRENCY", "").strip()
    if env_val.isdigit():
        return max(1, int(env_val))
    return DEFAULT_MANIFEST_CONCURRENCY


def render_manifest_md(manifest: dict) -> str:
    """Render a manifest into the paste-ready Markdown view.

    The output is a read-only snapshot of the JSON manifest, intended as a
    fallback so a user can copy `Prompt` blocks into ChatGPT / Midjourney
    when `--manifest` cannot run (no key, no backend, network down).
    """
    lines: list[str] = []
    lines.append("# Image Generation Prompts")
    lines.append("")
    lines.append("> Auto-generated from `image_prompts.json` by `image_gen.py --render-md`.")
    lines.append("> Do not hand-edit — re-run the command to refresh.")
    lines.append("")

    project = manifest.get("project")
    generated_at = manifest.get("generated_at")
    color_scheme = manifest.get("color_scheme") or {}
    deck_rendering = manifest.get("deck_rendering")
    if not deck_rendering:
        legacy_anchor = manifest.get("deck_style_anchor")
        if isinstance(legacy_anchor, dict):
            deck_rendering = (
                legacy_anchor.get("visual_style")
                or json.dumps(legacy_anchor, ensure_ascii=False, sort_keys=True)
            )
        else:
            deck_rendering = legacy_anchor

    if project:
        lines.append(f"> Project: {project}")
    if generated_at:
        lines.append(f"> Generated: {generated_at}")
    if color_scheme:
        cs = " | ".join(
            f"{k.capitalize()} {v}" for k, v in color_scheme.items()
        )
        lines.append(f"> Color scheme: {cs}")
    if deck_rendering:
        lines.append(f"> Deck Rendering: {deck_rendering}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(manifest["items"], start=1):
        lines.append(f"### Image {i}: {item['filename']}")
        lines.append("")
        lines.append("| Attribute | Value |")
        lines.append("|---|---|")
        for label, key in (
            ("Purpose", "purpose"),
            ("Type", "type"),
            ("Page role", "page_role"),
            ("Text policy", "text_policy"),
            ("Aspect ratio", "aspect_ratio"),
            ("Image size", "image_size"),
            ("Model", "model"),
            ("Slice grid", "slice_grid"),
            ("Slice names", "slice_names"),
            ("Status", "status"),
        ):
            value = item.get(key)
            if not value and key == "page_role":
                value = "local (legacy default)"
            elif not value and key == "text_policy":
                value = "none (legacy default)"
            if value:
                lines.append(f"| {label} | {value} |")
        if item.get("last_error"):
            lines.append(f"| Last error | {item['last_error']} |")
        lines.append("")
        lines.append("**Prompt**:")
        lines.append("")
        lines.append(item["prompt"])
        lines.append("")
        if item.get("alt_text"):
            lines.append("**Alt Text**:")
            lines.append(f"> {item['alt_text']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_manifest_md_to_file(manifest_path: str, manifest: dict | None = None) -> str:
    """Render the manifest's Markdown sidecar next to the JSON file.

    Returns the written path. If `manifest` is omitted, it is loaded from
    `manifest_path` first.
    """
    if manifest is None:
        manifest = load_manifest(manifest_path)
    md_path = str(Path(manifest_path).with_suffix(".md"))
    Path(md_path).write_text(render_manifest_md(manifest), encoding="utf-8")
    return md_path


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate images using AI image model providers."
    )
    parser.add_argument(
        "prompt", nargs="?", default=None,
        help=(
            "The text prompt for image generation. With --reference-image, "
            "this is the edit instruction (required in that mode)."
        )
    )
    parser.add_argument(
        "--aspect_ratio", default="1:1", choices=ALL_ASPECT_RATIOS,
        help=f"Aspect ratio. Default: 1:1."
    )
    parser.add_argument(
        "--image_size", default=None,
        help=(
            f"Image size. Choices: {ALL_IMAGE_SIZES}. Default depends on the "
            "backend and is shown by --list-backends. (case-insensitive)"
        ),
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output directory. Default: current directory."
    )
    parser.add_argument(
        "--filename", "-f", default=None,
        help="Output filename (without extension). Overrides auto-naming."
    )
    parser.add_argument(
        "--model", "-m", default=None,
        help="Model name. Default depends on backend."
    )
    parser.add_argument(
        "--backend", "-b", default=None, choices=SUPPORTED_BACKENDS,
        help="Override IMAGE_BACKEND env var."
    )
    parser.add_argument(
        "--list-backends", action="store_true",
        help="List available backends grouped by support tier and exit."
    )
    parser.add_argument(
        "--manifest", default=None, metavar="IMAGE_PROMPTS_JSON",
        help=(
            "Path to image_prompts.json. Runs every Pending/Failed item in "
            "parallel; writes status back to the manifest as each completes."
        ),
    )
    parser.add_argument(
        "--concurrency", type=int, default=None,
        help=(
            "Max concurrent requests in --manifest mode. Defaults to "
            f"IMAGE_CONCURRENCY env or {DEFAULT_MANIFEST_CONCURRENCY}. "
            "Auto-halves on rate-limit; 1 is the serial fallback."
        ),
    )
    parser.add_argument(
        "--render-md", dest="render_md", default=None, metavar="IMAGE_PROMPTS_JSON",
        help=(
            "Render <json>'s read-only Markdown sidecar (image_prompts.md) "
            "next to the manifest, then exit. No backend / network needed."
        ),
    )
    parser.add_argument(
        "--reference-image", dest="reference_image", default=None, metavar="PATH",
        help=(
            "Source image for image-to-image editing (single-image mode only). "
            "When set, the prompt is used as the edit instruction. Only backends "
            "that support editing accept this (currently: openai). Not valid with "
            "--manifest / --render-md / --list-backends."
        ),
    )

    args = parser.parse_args()

    if args.filename is not None:
        try:
            _validate_bare_output_name(
                args.filename,
                field_name="--filename",
            )
        except ValueError as exc:
            parser.error(str(exc))

    if args.reference_image is not None:
        # Reference editing is a single-image-only enhancement; keep it out of
        # the manifest / sidecar / list surfaces entirely.
        conflicting = [
            name for name, val in (
                ("--manifest", args.manifest),
                ("--render-md", args.render_md),
                ("--list-backends", args.list_backends),
            ) if val
        ]
        if conflicting:
            parser.error(
                "--reference-image is single-image mode only and cannot be "
                f"combined with {', '.join(conflicting)}."
            )
        if not args.prompt or not args.prompt.strip():
            parser.error(
                "--reference-image requires a prompt to use as the edit instruction."
            )
        if not os.path.isfile(args.reference_image):
            parser.error(
                f"--reference-image file not found: {args.reference_image}"
            )

    if args.list_backends:
        _print_backend_list()
        return

    if args.render_md:
        if not os.path.isfile(args.render_md):
            print(f"Error: manifest file not found: {args.render_md}")
            sys.exit(1)
        try:
            manifest = load_manifest(args.render_md)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        md_path = render_manifest_md_to_file(args.render_md, manifest)
        print(f"Rendered Markdown sidecar: {md_path}")
        return

    manifest = None
    manifest_output_dir = None
    if args.manifest:
        if not os.path.isfile(args.manifest):
            print(f"Error: manifest file not found: {args.manifest}")
            sys.exit(1)
        _guard_confirmed_non_api_path(args.manifest)
        try:
            manifest = load_manifest(args.manifest)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        manifest_output_dir = Path(args.manifest).resolve().parent
        if args.output and Path(args.output).resolve() != manifest_output_dir:
            print(
                "Error: --output cannot redirect manifest items outside the "
                f"manifest directory ({manifest_output_dir})"
            )
            sys.exit(1)

    try:
        _load_image_env_file()
        _validate_runtime_config()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # CLI --backend overrides the value loaded from .env
    if args.backend:
        os.environ["IMAGE_BACKEND"] = args.backend

    backend, backend_name = _resolve_backend()
    image_size = (
        args.image_size
        or BACKEND_REGISTRY[backend_name]["default_image_size"]
    )
    print(f"Using backend: {backend_name}\n")

    if args.manifest:
        concurrency = _resolve_concurrency(args.concurrency)
        try:
            _, failed, _ = _run_manifest(
                manifest, args.manifest, backend,
                initial_concurrency=concurrency,
                image_size=image_size,
                output_dir=str(manifest_output_dir),
                model=args.model,
            )
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Partial progress preserved in manifest.")
            sys.exit(130)
        md_path = render_manifest_md_to_file(args.manifest, manifest)
        print(f"Rendered Markdown sidecar: {md_path}")
        sys.exit(1 if failed else 0)

    # Single-image mode. Backfill the historical default prompt only here, so
    # plain generation is byte-for-byte unchanged while edit mode still requires
    # an explicit instruction (enforced above).
    prompt = args.prompt if args.prompt is not None else "a beautiful landscape"

    gen_kwargs = {
        "prompt": prompt,
        "aspect_ratio": args.aspect_ratio,
        "image_size": image_size,
        "output_dir": args.output,
        "filename": args.filename,
        "model": args.model,
    }
    if args.reference_image is not None:
        if not getattr(backend, "SUPPORTS_REFERENCE_IMAGE", False):
            print(
                f"Error: backend '{backend_name}' does not support image editing "
                "(--reference-image). Use a backend that does (currently: openai)."
            )
            sys.exit(1)
        gen_kwargs["reference_image"] = args.reference_image

    try:
        backend.generate(**gen_kwargs)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
