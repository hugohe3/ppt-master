# -*- coding: utf-8 -*-
"""Build the structured native-diagram index (diagrams_index.json).

Per-diagram tags follow the agreed PPT-expert selection schema, aligned to the
existing image-type-templates taxonomy + charts_index `pick`-rule format:

  type        - relationship/form (the primary selector), from the 11-type taxonomy
                (+ pack forms: layered-platform / isometric-stack / list-row)
  slots/slot_of - capacity (coarse range, by design — pick rules match on ranges)
  holds       - content form a slot can carry (text budget)
  use         - content relationship intent
  footprint/aspect - layout fit
  style/idiom/fit_renderings - STYLE GATE: this pack is strong 3D-skeuomorphic,
                so it is only selectable for dimensional/3D-styled decks
  recolor_base - the 2 base hexes to remap onto the deck palette
  pick        - one-line selection rule (charts_index style)
  conf        - high (studied / unambiguous form) | approx (contact-sheet read)

`type` is a visual-pass classification; `slots` is intentionally coarse. Refine
during curation. Non-diagram slides (cover / notice / pure table) are marked
selectable:false so the AI never offers them.
"""
from __future__ import annotations

import json
from pathlib import Path

LIB = Path("skills/ppt-master/templates/native_diagrams")

STYLE = {
    "style": "3d-dimensional",
    "idiom": "strong",
    "fit_renderings": ["3d-isometric", "digital-dashboard", "glassmorphism", "flat"],
    "recolor_base": {"primary": "558C5A", "accent": "122B87"},
}

# type -> (use, slots, slot_of, holds, svg_alt, blurb)
TYPE_DEF = {
    "framework":        ("relationship", "4-8", "satellites", "short-label",      "framework",  "a central concept feeding several parts (hub-and-spoke)"),
    "funnel":           ("convergence",  "3-5", "stages",     "label+short-desc", "funnel",     "a top-wide narrowing flow / convergence to one outcome"),
    "pyramid":          ("hierarchy",    "3-5", "tiers",      "short-label",      "pyramid",    "bottom-wide hierarchical tiers"),
    "layered-platform": ("hierarchy",    "3-6", "layers",     "label+items",      "pyramid",    "stacked/concentric platforms, each layer holding several items"),
    "isometric-stack":  ("hierarchy",    "3-5", "layers",     "label+items",      "pyramid",    "3D isometric layered architecture"),
    "matrix":           ("composition",  "4-9", "cells",      "label+desc",       "matrix",     "parallel modules in a grid / quadrants"),
    "cycle":            ("cycle",        "3-6", "steps",      "short-label",      "cycle",      "a closed loop returning to start"),
    "list-row":         ("comparison",   "3-6", "items",      "label+short-desc", "infographic","parallel items on a row of platforms/pillars"),
    "timeline":         ("process",      "3-6", "milestones", "label+date",       "timeline",   "events along a linear axis"),
}
NON_DIAGRAM = {"cover", "notice", "table"}

# --- per-key visual-pass type classification (1..223), row-major over the sheets ---
# Codes: fw framework/hub · fn funnel · py pyramid · lp layered-platform ·
#        iso isometric-stack · mx matrix · cy cycle · lr list-row · tl timeline ·
#        cover / notice / table = non-selectable
T = {
 1:"cover",2:"notice",3:"fw",4:"py",5:"fn",6:"py",7:"fn",8:"fn",9:"fn",10:"fn",
 11:"fn",12:"py",13:"lp",14:"lp",15:"fn",16:"fn",17:"lp",18:"fn",19:"lp",20:"lr",
 21:"iso",22:"fn",23:"fw",24:"lr",
 25:"fn",26:"lp",27:"fw",28:"lp",29:"fw",30:"fw",31:"fw",32:"lp",33:"fn",34:"iso",
 35:"fn",36:"mx",37:"lp",38:"lp",39:"lp",40:"lr",41:"lp",42:"lp",43:"lp",44:"lp",
 45:"lr",46:"lp",47:"fw",48:"fn",
 49:"lp",50:"fw",51:"lp",52:"fw",53:"fw",54:"lp",55:"lp",56:"lp",57:"lp",58:"fw",
 59:"iso",60:"lp",61:"fw",62:"py",63:"fw",64:"cy",65:"lp",66:"fw",67:"lp",68:"lp",
 69:"fw",70:"lp",71:"lr",72:"lp",
 73:"lp",74:"fw",75:"fn",76:"lp",77:"fw",78:"lr",79:"lp",80:"lp",81:"lp",82:"fn",
 83:"fw",84:"fw",85:"lp",86:"lp",87:"lp",88:"lp",89:"lp",90:"lp",91:"cy",92:"fw",
 93:"lp",94:"lp",95:"fn",96:"lp",
 97:"py",98:"lr",99:"fw",100:"lr",101:"fw",102:"lp",103:"fn",104:"lp",105:"fw",106:"lp",
 107:"mx",108:"fw",109:"lp",110:"fn",111:"lp",112:"lp",113:"lp",114:"fn",115:"lp",116:"lp",
 117:"lr",118:"fn",119:"lp",120:"fn",
 121:"lr",122:"mx",123:"fw",124:"fw",125:"lp",126:"fw",127:"fn",128:"lp",129:"mx",130:"lp",
 131:"fw",132:"fn",133:"lp",134:"lp",135:"fw",136:"lp",137:"lp",138:"fn",139:"fw",140:"cy",
 141:"lr",142:"fn",143:"lp",144:"mx",
 145:"table",146:"mx",147:"lp",148:"fw",149:"lr",150:"mx",151:"fn",152:"py",153:"py",154:"fn",
 155:"py",156:"py",157:"fn",158:"lp",159:"iso",160:"iso",161:"py",162:"fw",163:"lp",164:"mx",
 165:"mx",166:"tl",167:"lp",168:"py",
 169:"table",170:"lp",171:"fw",172:"py",173:"fn",174:"fn",175:"fw",176:"lp",177:"lp",178:"lp",
 179:"lp",180:"fw",181:"lp",182:"lp",183:"fw",184:"fw",185:"cy",186:"lp",187:"lp",188:"lr",
 189:"lp",190:"fw",191:"fn",192:"lp",
 193:"lr",194:"fw",195:"py",196:"lr",197:"fw",198:"lr",199:"lp",200:"lp",201:"fw",202:"lp",
 203:"fn",204:"fw",205:"lp",206:"cy",207:"lp",208:"lp",209:"fw",210:"lp",211:"lp",212:"fw",
 213:"lp",214:"lp",215:"iso",216:"iso",
 217:"fw",218:"lr",219:"lp",220:"fw",221:"mx",222:"lp",223:"notice",
}
CODE = {"fw":"framework","fn":"funnel","py":"pyramid","lp":"layered-platform",
        "iso":"isometric-stack","mx":"matrix","cy":"cycle","lr":"list-row","tl":"timeline",
        "cover":"cover","notice":"notice","table":"table"}
# Keys I studied at full size / unambiguous form -> high confidence
HIGH = {3,6,9,12,13,14,20,24,31,36,40,66,160,216, 1,2,223,145,169,
        62,97,152,153,155,156,161,168,172,195, 64,91,140,185,206, 166}


def entry(key: str, t_full: str, slide: int) -> dict:
    if t_full in NON_DIAGRAM:
        return {"selectable": False, "kind": t_full, "slide": slide}
    use, slots, slot_of, holds, svg_alt, blurb = TYPE_DEF[t_full]
    pick = (f"Pick for {blurb} (~{slots} {slot_of}, each holds {holds}); full-slide, "
            f"in a dimensional/3D-styled deck; recolor the base hexes to the deck palette. "
            f"Skip if a flat/minimalist deck (use the SVG {svg_alt} template) or the "
            f"content is not a {use} structure.")
    e = {"type": t_full, "use": use, "slots": slots, "slot_of": slot_of,
         "holds": holds, "footprint": "full-slide", "aspect": "16:9"}
    e.update(STYLE)
    e["pick"] = pick
    return e


def main() -> int:
    idx_path = LIB / "diagrams_index.json"
    old = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}

    new: dict[str, dict] = {}
    for n in range(1, 224):
        key = f"solid3d_bluegreen_{n:03d}"
        code = T.get(n, "lp")
        t_full = CODE[code]
        e = entry(key, t_full, n)
        if "selectable" not in e:
            e["conf"] = "high" if n in HIGH else "approx"
        new[key] = e

    # preserve / upgrade the composed asset entry
    combo = old.get("combo_product_system", {})
    new["combo_product_system"] = {
        "type": "composite", "use": "comparison",
        "slots": "2", "slot_of": "models", "holds": "diagram-each",
        "footprint": "full-slide", "aspect": "16:9",
        **STYLE,
        "composed_from": combo.get("composed_from", ["solid3d_bluegreen_013", "solid3d_bluegreen_024"]),
        "pick": ("Pick to show two whole models side by side under one title. "
                 "Composed asset (013+024), recolored teal/coral."),
        "conf": "high",
    }

    new = {k: new[k] for k in sorted(new)}
    idx_path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # report
    from collections import Counter
    c = Counter(v.get("type", v.get("kind", "?")) for v in new.values())
    hi = sum(1 for v in new.values() if v.get("conf") == "high")
    ap = sum(1 for v in new.values() if v.get("conf") == "approx")
    ns = sum(1 for v in new.values() if v.get("selectable") is False)
    print(f"entries: {len(new)} | type dist: {dict(c)}")
    print(f"conf high: {hi} | approx: {ap} | non-selectable: {ns}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
