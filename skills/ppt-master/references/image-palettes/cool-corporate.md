# Palette: cool-corporate

Stable, professional, restrained. The default palette for consulting / finance / B2B / corporate decks where credibility is the primary visual signal.

> This file describes **color behavior**, not HEX values. The deck's HEX triplet comes from `design_spec.colors` (set by Strategist). cool-corporate tells the model **how to use** those HEX values.

## 1. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ vector-illustration | Default pairing — flat shapes carry the restraint |
| ✓✓ flat | Similar feel, slightly more decorative |
| ✓✓ 3d-isometric | Works well — keep shadows soft and 8% opacity |
| ✓✓ digital-dashboard | Natural fit for data products |
| ✓✓ blueprint | Good for technical architecture |
| ✓✓ corporate-photo | Photography with cool color grading |
| ✓✓ editorial | Magazine restraint matches palette restraint |
| ✗ sketch-notes / fantasy-animation / pixel-art | Temperament conflict — choose `warm-earth` or `macaron` for those renderings |
| ✗ dark-cinematic combinations | Dark-cinematic is a different palette — don't try to merge |

---

## 2. Fewshot prompt snippets

**Snippet A — applied to a vector-illustration background**

> [...rendering paragraph...] Color behavior is restrained-corporate: secondary light gray `#F8F9FA` carries 65% of the canvas as calm breathing space across the upper two-thirds; primary deep navy `#1E3A5F` forms a confident diagonal block across the lower portion (about 28% area); accent gold `#D4AF37` appears only as one thin horizontal line and a single small geometric dot, together under 5% of the area. No additional colors. [...container guidance...]