"""Shared constants used across conversion pipeline packages."""

# URL schemes that are silently dropped during hyperlink conversion.
# Blacklist approach: blocks known dangerous schemes. For user-supplied
# SVG input via standalone svg_to_pptx, consider switching to a whitelist:
#   ('http:', 'https:', 'mailto:', 'tel:')
# PowerPoint runtime also rejects unrecognized schemes at open time,
# so actual risk from unsupported schemes not listed here is low.
UNSUPPORTED_URL_SCHEMES = ('javascript:', 'data:', 'vbscript:', 'file:')
