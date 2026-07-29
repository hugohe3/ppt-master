#!/usr/bin/env python3
"""
PPT Master - Language Tag Helpers

Normalize and inspect the project primary-language tag shared by confirmation
and export tooling.

Usage:
    Import ``normalize_language_tag`` from another script.

Examples:
    from language_tags import normalize_language_tag
    normalize_language_tag("Chinese")

Dependencies:
    None (only uses standard library)
"""

import re


class LanguageTagError(ValueError):
    """Report an invalid or ambiguous project language tag."""


_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,8}$")
_EXTLANG_RE = re.compile(r"^[A-Za-z]{3}$")
_SCRIPT_RE = re.compile(r"^[A-Za-z]{4}$")
_REGION_RE = re.compile(r"^(?:[A-Za-z]{2}|[0-9]{3})$")
_VARIANT_RE = re.compile(r"^(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3})$")
_SINGLETON_RE = re.compile(r"^[0-9A-WY-Za-wy-z]$")
_EXTENSION_RE = re.compile(r"^[A-Za-z0-9]{2,8}$")
_PRIVATE_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")


def _alias_key(value: str) -> str:
    """Return a whitespace-stable key for legacy natural-language aliases."""
    return " ".join(value.strip().casefold().split())


_LANGUAGE_ALIASES = {
    _alias_key(alias): tag
    for tag, aliases in {
        "en-US": (
            "English",
            "英文",
            "英语",
            "英語",
        ),
        "zh-Hans": (
            "Chinese",
            "Chinese Simplified",
            "Chinese (Simplified)",
            "Simplified Chinese",
            "Mandarin",
            "中文",
            "汉语",
            "漢語",
            "普通话",
            "普通話",
            "简体",
            "簡體",
            "简体中文",
            "簡體中文",
            "简中",
        ),
        "zh-Hant": (
            "Chinese Traditional",
            "Chinese (Traditional)",
            "Traditional Chinese",
            "繁体",
            "繁體",
            "繁体中文",
            "繁體中文",
            "繁中",
        ),
        "ja-JP": (
            "Japanese",
            "日本語",
            "日文",
            "日语",
            "日語",
        ),
        "ko-KR": (
            "Korean",
            "한국어",
            "조선말",
            "韩语",
            "韓語",
            "朝鲜语",
            "朝鮮語",
        ),
    }.items()
    for alias in aliases
}

_NATURAL_LANGUAGE_NAMES = {
    "arabic",
    "bengali",
    "czech",
    "danish",
    "dutch",
    "farsi",
    "finnish",
    "french",
    "georgian",
    "german",
    "greek",
    "hebrew",
    "hindi",
    "hungarian",
    "indonesian",
    "italian",
    "malay",
    "marathi",
    "nepali",
    "norwegian",
    "persian",
    "polish",
    "portuguese",
    "romanian",
    "russian",
    "slovak",
    "spanish",
    "swedish",
    "tamil",
    "telugu",
    "thai",
    "turkish",
    "ukrainian",
    "urdu",
    "vietnamese",
}
_RTL_BASE_LANGUAGES = {
    "ar",
    "dv",
    "fa",
    "he",
    "iw",
    "ps",
    "sd",
    "ug",
    "ur",
    "yi",
}
_RTL_SCRIPTS = {
    "Adlm",
    "Arab",
    "Hebr",
    "Mand",
    "Nkoo",
    "Rohg",
    "Samr",
    "Syrc",
    "Thaa",
}


def normalize_language_tag(value: str) -> str:
    """Return one canonical, unambiguous BCP-47 language tag.

    The helper accepts the four historical natural-language aliases used by
    Confirm UI. Other language names stay invalid: callers must provide a real
    tag such as ``es-ES``, ``ru-RU``, or ``ar-SA``.
    """
    if not isinstance(value, str) or not value.strip():
        raise LanguageTagError("primary language must be a non-empty BCP-47 tag")

    raw = value.strip()
    alias = _LANGUAGE_ALIASES.get(_alias_key(raw))
    if alias:
        raw = alias
    else:
        raw = raw.replace("_", "-")

    parts = raw.split("-")
    if any(not part for part in parts):
        raise LanguageTagError(f"invalid BCP-47 language tag: {value!r}")

    language = parts[0]
    if not _LANGUAGE_RE.fullmatch(language):
        raise LanguageTagError(
            "use a BCP-47 language tag such as es-ES, ru-RU, ar-SA, or zh-Hans"
        )
    language = language.lower()
    if language in _NATURAL_LANGUAGE_NAMES:
        raise LanguageTagError(
            "use a BCP-47 language tag such as es-ES, ru-RU, ar-SA, or zh-Hans"
        )
    if language == "und":
        raise LanguageTagError(
            "und is not a usable primary language; choose the presentation language"
        )

    normalized = [language]
    index = 1

    extlang_count = 0
    while (
        len(language) <= 3
        and index < len(parts)
        and extlang_count < 3
        and _EXTLANG_RE.fullmatch(parts[index])
    ):
        normalized.append(parts[index].lower())
        index += 1
        extlang_count += 1

    has_script = False
    if index < len(parts) and _SCRIPT_RE.fullmatch(parts[index]):
        normalized.append(parts[index].title())
        index += 1
        has_script = True

    has_region = False
    if index < len(parts) and _REGION_RE.fullmatch(parts[index]):
        region = parts[index]
        normalized.append(region.upper() if region.isalpha() else region)
        index += 1
        has_region = True

    variants = set()
    while index < len(parts) and _VARIANT_RE.fullmatch(parts[index]):
        variant = parts[index].lower()
        if variant in variants:
            raise LanguageTagError(f"duplicate BCP-47 variant: {parts[index]!r}")
        variants.add(variant)
        normalized.append(variant)
        index += 1

    singletons = set()
    while index < len(parts) and _SINGLETON_RE.fullmatch(parts[index]):
        singleton = parts[index].lower()
        if singleton in singletons:
            raise LanguageTagError(f"duplicate BCP-47 extension: {parts[index]!r}")
        singletons.add(singleton)
        normalized.append(singleton)
        index += 1
        start = index
        while index < len(parts) and _EXTENSION_RE.fullmatch(parts[index]):
            normalized.append(parts[index].lower())
            index += 1
        if index == start:
            raise LanguageTagError(
                f"BCP-47 extension {singleton!r} requires a following subtag"
            )

    if index < len(parts) and parts[index].casefold() == "x":
        normalized.append("x")
        index += 1
        start = index
        while index < len(parts) and _PRIVATE_RE.fullmatch(parts[index]):
            normalized.append(parts[index].lower())
            index += 1
        if index == start:
            raise LanguageTagError("BCP-47 private use requires a following subtag")

    if index != len(parts):
        raise LanguageTagError(f"invalid BCP-47 subtag: {parts[index]!r}")
    if language == "zh" and not (has_script or has_region):
        raise LanguageTagError(
            "Chinese must declare a script or region, for example zh-Hans, "
            "zh-Hant, zh-CN, or zh-TW"
        )
    return "-".join(normalized)


def language_base(value: str) -> str:
    """Return the lower-case primary language subtag."""
    return normalize_language_tag(value).split("-", 1)[0]


def language_uses_rtl(value: str) -> bool:
    """Return whether the canonical language or explicit script is RTL."""
    tag = normalize_language_tag(value)
    parts = tag.split("-")
    index = 1
    if len(parts[0]) <= 3:
        while index < len(parts) and _EXTLANG_RE.fullmatch(parts[index]):
            index += 1
    if index < len(parts) and _SCRIPT_RE.fullmatch(parts[index]):
        return parts[index] in _RTL_SCRIPTS
    return parts[0] in _RTL_BASE_LANGUAGES
