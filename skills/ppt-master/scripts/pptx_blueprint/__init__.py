"""pptx_blueprint — PPTX to reusable SVG template package.

Pipeline:
    PPTX (ZIP + DrawingML XML)
      -> Blueprint IR (pure dataclasses, no external app required)
      -> Compliant SVG (obeys shared-standards.md)
      -> layouts/<name>/ directory (clustered layout variants + design_spec.md)

Public API (populated as phases P1-P5 land):
    - ir: Blueprint / SlideBlueprint / Shape / Theme dataclasses
    - xml_parser: parse_pptx(path) -> Blueprint
    - svg_emitter: emit_svg(slide_bp) -> str
    - cli: main() for `python3 -m pptx_blueprint.cli <pptx>`
"""
