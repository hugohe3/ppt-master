from dataclasses import dataclass
from pathlib import Path


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
    orientation: str = ""
    use_case: str = ""


@dataclass
class AssetCandidate:
    provider: str
    asset_id: str
    title: str
    width: int
    height: int
    license_name: str = ""
    license_url: str = ""


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
    score = 10000 if allowed else -10000

    candidate_orientation = normalize_orientation(candidate.width, candidate.height)
    requested_orientation = (request.orientation or "").strip().lower()
    if requested_orientation:
        if candidate_orientation == requested_orientation:
            score += 1000
        else:
            score -= 250

    if (request.use_case or "").strip().lower() == "background":
        if requested_orientation == "landscape" and candidate_orientation == "landscape":
            score += 250

    score += max(candidate.width, 0) * max(candidate.height, 0) / 1000.0
    return score


def ensure_json_parent(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
