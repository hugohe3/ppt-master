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


@dataclass(init=False)
class ImageSearchRequest:
    query: str
    purpose: str = ""
    orientation: str = ""
    min_width: int = 0
    min_height: int = 0
    filename: str = ""
    slide: str = ""

    def __init__(
        self,
        query,
        purpose="",
        orientation="",
        min_width=0,
        min_height=0,
        filename="",
        slide="",
        use_case=None,
    ):
        if use_case is not None:
            if purpose and use_case != purpose:
                raise TypeError("purpose and use_case must match when both are provided")
            purpose = use_case

        self.query = query
        self.purpose = purpose
        self.orientation = orientation
        self.min_width = min_width
        self.min_height = min_height
        self.filename = filename
        self.slide = slide

    @property
    def use_case(self):
        return self.purpose

    @use_case.setter
    def use_case(self, value):
        self.purpose = value


@dataclass(init=False)
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

    def __init__(
        self,
        *args,
        provider=None,
        title=None,
        source_page_url="",
        license_name="",
        license_url="",
        width=0,
        height=0,
        download_url="",
        author="",
        attribution_required=False,
        raw=None,
        asset_id="",
    ):
        if args:
            if len(args) < 5 or len(args) > 7:
                raise TypeError(
                    "legacy AssetCandidate positional construction requires 5 to 7 arguments"
                )
            if any(
                value is not None and value != default
                for value, default in (
                    (provider, None),
                    (title, None),
                    (source_page_url, ""),
                    (license_name, ""),
                    (license_url, ""),
                    (width, 0),
                    (height, 0),
                    (download_url, ""),
                    (author, ""),
                    (attribution_required, False),
                    (raw, None),
                    (asset_id, ""),
                )
            ):
                raise TypeError(
                    "cannot mix legacy positional AssetCandidate arguments with new metadata keywords"
                )

            provider, asset_id, title, width, height = args[:5]
            if len(args) >= 6:
                license_name = args[5]
            if len(args) == 7:
                license_url = args[6]

        if provider is None or title is None:
            raise TypeError("provider and title are required")

        self.provider = provider
        self.title = title
        self.source_page_url = source_page_url
        self.license_name = license_name
        self.license_url = license_url
        self.width = width
        self.height = height
        self.download_url = download_url
        self.author = author
        self.attribution_required = attribution_required
        self.raw = raw
        self.asset_id = asset_id


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
