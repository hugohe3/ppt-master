from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


OPEN_LICENSE_TOKENS = (
    "cc by",
    "cc-by",
    "cc by-sa",
    "cc-by-sa",
    "cc0",
    "public domain",
    "creativecommons.org/licenses/by/",
    "creativecommons.org/licenses/by-sa/",
    "creativecommons.org/publicdomain/",
)

REJECT_LICENSE_TOKENS = (
    "by-nc",
    "by nc",
    "noncommercial",
    "by-nd",
    "by nd",
    "no derivatives",
    "all rights reserved",
)

PROVIDER_LICENSE_TOKENS = {
    "pexels": ("pexels license",),
    "pixabay": ("pixabay content license",),
}


@dataclass
class ImageSearchRequest:
    query: str
    purpose: str = ""
    orientation: str = ""
    min_width: int = 0
    min_height: int = 0
    filename: str = ""
    slide: str = ""

    @property
    def use_case(self):
        return self.purpose

    @use_case.setter
    def use_case(self, value):
        self.purpose = value


@dataclass
class AssetCandidate:
    provider: str
    title: str
    source_page_url: str = ""
    license_name: str = ""
    license_url: str = ""
    width: int = 0
    height: int = 0
    download_url: str = ""
    author: str = ""
    attribution_required: bool = False
    raw: Any = field(default=None)
    asset_id: str = ""


def normalize_orientation(width, height):
    if width <= 0 or height <= 0:
        return "unknown"
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"


def is_allowed_license(license_name, license_url, provider=""):
    text = " ".join(
        part.strip().lower()
        for part in (license_name or "", license_url or "")
        if part
    )
    if not text:
        return False

    if any(token in text for token in REJECT_LICENSE_TOKENS):
        return False

    if any(token in text for token in OPEN_LICENSE_TOKENS):
        return True

    provider_key = (provider or "").strip().lower()
    provider_tokens = PROVIDER_LICENSE_TOKENS.get(provider_key, ())
    return any(token in text for token in provider_tokens)


def score_candidate(candidate, request):
    allowed = is_allowed_license(
        candidate.license_name,
        candidate.license_url,
        provider=candidate.provider,
    )
    if not allowed:
        return -1000000

    score = 10000

    candidate_orientation = normalize_orientation(candidate.width, candidate.height)
    requested_orientation = (request.orientation or "").strip().lower()
    if requested_orientation:
        if candidate_orientation == requested_orientation:
            score += 1000
        else:
            score -= 250

    if (request.purpose or "").strip().lower() == "background":
        if requested_orientation == "landscape" and candidate_orientation == "landscape":
            score += 250

    min_width = max(int(request.min_width or 0), 0)
    min_height = max(int(request.min_height or 0), 0)
    if min_width and candidate.width < min_width:
        score -= 500
    if min_height and candidate.height < min_height:
        score -= 500

    size_score = max(candidate.width, 0) * max(candidate.height, 0) / 1000.0
    score += min(size_score, 5000)
    return score


def ensure_json_parent(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
