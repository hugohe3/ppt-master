"""Shared constants for the pptx_to_svg package."""

# URL schemes that are silently dropped during hyperlink conversion.
# javascript:, data:, vbscript:, file: are blocked; http:, https:,
# mailto:, tel:, and other schemes are accepted.
# Single source of truth: scripts/_shared.py.
from _shared import UNSUPPORTED_URL_SCHEMES

# OOXML ppaction:// schemes that indicate internal slide navigation.
# NOTE: hlinkshowjump (custom shows) is listed as a placeholder — the
# target points to customShows/customShowN.xml instead of slideN.xml,
# so the regex in slide_to_svg / txbody_to_svg can't extract a slide
# number. Custom show jumps are silently degraded to no hyperlink.
KNOWN_SLIDE_ACTIONS = ('ppaction://hlinksldjump', 'ppaction://hlinkshowjump')

# OOXML ppaction:// schemes (or empty) that indicate external hyperlinks.
KNOWN_EXTERNAL_ACTIONS = ('', 'ppaction://hlinkurl', 'ppaction://hlinkfile')
