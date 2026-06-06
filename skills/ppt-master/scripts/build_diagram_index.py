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

# Pack-level constants (the depth is a content-presentation choice, NOT a deck
# style gate — these drop into any deck as an element once recolored).
META = {
    "pack": "solid3d_bluegreen",
    "look": ("Dimensional 3D — glossy nodes, layered platforms, gradient depth. "
             "The depth conveys the content relationship (layers / hierarchy / "
             "convergence); it is NOT a deck-wide style lock. Recolor the base "
             "hexes to the deck palette so it blends into any deck."),
    "usage": ("Use full-slide OR scale into an in-page region via "
              "data-native-diagram (x/y/w/h). `density` says how small it can "
              "shrink and stay legible: low = fine as a small element, "
              "high = needs most of the slide."),
    "recolor_base": {"primary": "558C5A", "accent": "122B87"},
    "select_by": ("content relationship (type/use) x item count (slots) x "
                  "content-per-slot (holds); place full-slide or as a region "
                  "within the density limit."),
    "conf_note": ("type = visual pass (reliable); slots = coarse range; refine "
                  "during curation. conf: high = studied/unambiguous, "
                  "approx = contact-sheet read."),
}


def _density(shape_count: int) -> str:
    """How small the diagram can shrink and stay legible (from real shape count)."""
    if shape_count <= 15:
        return "low"      # simple — works as a small in-page element
    if shape_count <= 50:
        return "medium"   # half-slide / large region
    return "high"         # detailed — needs most of the slide

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
    "bowtie":           ("convergence",  "3-5", "stages",     "label+short-desc", "funnel",     "an hourglass/bowtie — converges to a center then diverges (many-in, many-out)"),
    "flowchart":        ("process",      "3-6", "steps",      "label+short-desc", "flowchart",  "sequential blocks connected left-to-right (input -> process -> output)"),
}
NON_DIAGRAM = {"cover", "notice", "table"}

# Content scenarios per type — the "what business content is this for" bridge a
# PPT expert selects by (mirrors image-type-templates "Typical use"). Type-level
# default; refined/reviewed entries may give a more specific list.
SCENARIO = {
    "framework":        "capability map / system architecture / methodology / org or relationship model",
    "funnel":           "conversion / sales pipeline / screening / data refinement",
    "pyramid":          "maturity model / value hierarchy / capability tiers / priority levels",
    "layered-platform": "platform or tech stack / layered architecture / service tiers",
    "isometric-stack":  "technical architecture (layers) / platform stack",
    "matrix":           "capability matrix / module-or-product portfolio / 2-axis classification (SWOT/BCG)",
    "cycle":            "PDCA / closed-loop process / continuous improvement / flywheel",
    "list-row":         "parallel options / N-column comparison / step list / pillars",
    "timeline":         "roadmap / history / evolution / milestones",
    "bowtie":           "two-sided platform (supply<->demand) / intermediary / converge-then-distribute",
    "flowchart":        "process / workflow / pipeline / input-process-output",
}

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


# P3 — hand-written distinguishing descriptors for studied diagrams. These show
# the target quality: precise node count + subform + a pick that differentiates
# WITHIN a type (the gap P4 exposed). Survivors of curation get the same treatment.
OVERRIDES = {
    "solid3d_bluegreen_003": dict(type="framework", subform="top-row cards + central node",
        slots=6, footprint="centered-compact", text_load="light", motif="mixed",
        scenario="data-governance / security model / inputs feeding a central platform (top-down)",
        distinct="A row of labeled cards across the top feeds a central node — top-down intake, not a radial ring.",
        pick="Pick for several inputs/categories feeding one concept from above (top-down). Skip if radial hub (031) or convergence-to-platform (066)."),
    "solid3d_bluegreen_031": dict(type="framework", subform="central sphere + orbiting satellites",
        slots=6, footprint="centered-compact", text_load="light", motif="sphere",
        scenario="one-core-many-aspects model / capability hub / concept breakdown",
        distinct="One large central sphere ringed by small satellite nodes — the classic even hub-spoke.",
        pick="Pick for one core concept with ~5-6 surrounding aspects (even radial hub). Skip if many-to-one convergence (066) or top-down feed (003)."),
    "solid3d_bluegreen_066": dict(type="framework", subform="convergence vortex hub",
        slots=7, footprint="full-bleed", text_load="medium", motif="sphere",
        scenario="capability hub / data or middle platform / ecosystem convergence / resource integration",
        distinct="7 labeled spheres arc into a central vortex that fans down to base labels — many sources converging into one platform.",
        pick="Pick for 6-8 sources/channels converging into one core platform (capability hub, data hub). Skip if a plain radial hub (031)."),
    "solid3d_bluegreen_012": dict(type="pyramid", subform="solid 3-tier pyramid on platform",
        slots=3, footprint="tall-center", text_load="light", motif="pyramid",
        scenario="maturity model / value hierarchy / 3-tier capability or priority",
        distinct="A solid upward 3-tier pyramid seated on a platform.",
        pick="Pick for a 3-level hierarchy / precedence / maturity. Skip if >4 levels or nested layers (013)."),
    "solid3d_bluegreen_013": dict(type="layered-platform", subform="concentric nested rings",
        slots=4, slot_of="rings", holds="label+items", footprint="centered-compact", text_load="medium", motif="ring",
        scenario="platform / tech stack (core -> ecosystem) / layered architecture",
        distinct="Concentric nested ellipse rings; each ring is a layer that wraps the inner one (core -> ecosystem).",
        pick="Pick for a platform where each layer envelops the inner (core -> capabilities -> ecosystem). Skip if flat stacked tiers (pyramid)."),
    "solid3d_bluegreen_024": dict(type="framework", subform="orbital ring around a central value",
        slots=5, footprint="centered-compact", text_load="medium", motif="sphere",
        scenario="value-centric model / factors revolving around one goal / marketing model",
        distinct="Labeled nodes orbit a central value pair on a 3D platform, with side annotation columns.",
        pick="Pick for several factors revolving around one central value/goal. Skip if many-to-one convergence (066)."),
    "solid3d_bluegreen_036": dict(type="matrix", subform="module-card grid on platform",
        slots=6, slot_of="cells", holds="label+desc", footprint="wide-band", text_load="medium", motif="card",
        scenario="capability matrix / module or product portfolio / parallel feature set",
        distinct="6 module cards laid out in a grid on a platform — parallel capabilities, not quadrants.",
        pick="Pick for 6-8 parallel modules/capabilities of equal weight. Skip if 2-axis quadrants or a hierarchy."),
    "solid3d_bluegreen_160": dict(type="isometric-stack", subform="isometric descending layers",
        slots=4, holds="label+items", footprint="full-bleed", text_load="heavy", motif="card",
        scenario="technical architecture (layers) / data platform stack",
        distinct="4 isometric platform layers descending (application/presentation/analysis/data), each holding tiles.",
        pick="Pick for a 4-layer technical architecture shown with isometric depth. Skip if a flat hierarchy (pyramid)."),
    "solid3d_bluegreen_216": dict(type="isometric-stack", subform="stacked platforms with icon-card rows",
        slots=3, holds="label+items", footprint="full-bleed", text_load="heavy", motif="card",
        scenario="PaaS platform stack / multi-layer service architecture",
        distinct="3 stacked platforms (PaaS application/capability/base), each holding a row of icon cards.",
        pick="Pick for a 3-layer platform stack (PaaS-style) with many sub-items per layer. Skip if few items per layer (pyramid)."),
}


# P3 curation grind — per-diagram visual review at full size (6/sheet, 900px),
# correcting the coarse contact-sheet types and filling footprint/text_load/motif
# + precise slots. conf:"reviewed". Grows one batch at a time. OVERRIDES (the
# fully hand-written `distinct`+`pick` entries) still win where both exist.
REVIEW = {
    # ---- batch 1: keys 4-23 (1,2 non-diagram; 3,12,13,24 already in OVERRIDES) ----
    4:  dict(type="pyramid",          slots=4, footprint="tall-center",      text_load="light",  motif="mixed"),
    5:  dict(type="funnel",           slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    6:  dict(type="pyramid",          slots=3, footprint="tall-center",      text_load="light",  motif="mixed"),
    7:  dict(type="bowtie",           slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    8:  dict(type="pyramid",          slots=4, footprint="tall-center",      text_load="medium", motif="mixed"),
    9:  dict(type="layered-platform", slots=3, footprint="centered-compact", text_load="medium", motif="ring",  subform="concentric nested rings"),
    10: dict(type="layered-platform", slots=3, footprint="centered-compact", text_load="medium", motif="mixed"),
    11: dict(type="bowtie",           slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    14: dict(type="layered-platform", slots=8, footprint="full-bleed",       text_load="heavy",  motif="card",  subform="wide platform holding many item tiles"),
    15: dict(type="bowtie",           slots=4, footprint="centered-compact", text_load="medium", motif="sphere"),
    16: dict(type="layered-platform", slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    17: dict(type="framework",        slots=5, footprint="wide-band",        text_load="light",  motif="sphere", subform="central sphere on a platform with a top node arc"),
    18: dict(type="list-row",         slots=3, slot_of="columns", footprint="wide-band", text_load="medium", motif="card", scenario="3-column parallel comparison / digital-ops matrix"),
    19: dict(type="layered-platform", slots=4, footprint="wide-band",        text_load="medium", motif="card"),
    20: dict(type="framework",        slots=4, footprint="wide-band",        text_load="light",  motif="mixed", subform="two-entity relationship on an angled platform"),
    21: dict(type="framework",        slots=4, footprint="centered-compact", text_load="medium", motif="tower", subform="central 3D object (5G) with side callouts"),
    22: dict(type="pyramid",          slots=4, footprint="tall-center",      text_load="medium", motif="mixed"),
    23: dict(type="framework",        slots=5, footprint="wide-band",        text_load="medium", motif="sphere", subform="central command hub + surrounding nodes on a platform"),
    # ---- batch 2: keys 25-48 (31,36 in OVERRIDES) ----
    25: dict(type="framework",        slots=5, footprint="centered-compact", text_load="medium", motif="mixed"),
    26: dict(type="layered-platform", slots=3, footprint="centered-compact", text_load="medium", motif="mixed", subform="top nodes feeding a layered base"),
    27: dict(type="framework",        slots=6, footprint="centered-compact", text_load="medium", motif="sphere", subform="radial ring of nodes with arrows"),
    28: dict(type="layered-platform", slots=4, footprint="wide-band",        text_load="medium", motif="card"),
    29: dict(type="funnel",           slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    30: dict(type="list-row",         slots=3, slot_of="columns", footprint="wide-band", text_load="medium", motif="card", scenario="short-video / content operations strategy"),
    32: dict(type="framework",        slots=5, footprint="wide-band",        text_load="medium", motif="mixed", scenario="talent / HR management platform"),
    33: dict(type="isometric-stack",  slots=4, footprint="wide-band",        text_load="medium", motif="mixed", subform="input -> central isometric stack -> output"),
    34: dict(type="framework",        slots=4, footprint="wide-band",        text_load="medium", motif="mixed"),
    35: dict(type="framework",        slots=5, footprint="wide-band",        text_load="medium", motif="mixed"),
    37: dict(type="layered-platform", slots=4, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="fan/arc panorama"),
    38: dict(type="framework",        slots=4, footprint="centered-compact", text_load="medium", motif="sphere", subform="radial hub with stat callouts"),
    39: dict(type="layered-platform", slots=5, footprint="wide-band",        text_load="heavy",  motif="card"),
    40: dict(type="list-row",         slots=6, footprint="wide-band",        text_load="medium", motif="sphere", subform="value-chain row", scenario="industry / value chain"),
    41: dict(type="layered-platform", slots=8, footprint="full-bleed",       text_load="heavy",  motif="card"),
    42: dict(type="bowtie",           slots=4, footprint="centered-compact", text_load="medium", motif="sphere"),
    43: dict(type="list-row",         slots=5, footprint="wide-band",        text_load="medium", motif="cube", subform="row of 3D cube nodes (SaaS/PaaS tiers on the side)"),
    44: dict(type="framework",        slots=4, footprint="centered-compact", text_load="medium", motif="tower", subform="central tower/building + side callouts"),
    45: dict(type="layered-platform", slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    46: dict(type="framework",        slots=8, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="full-slide capability panorama"),
    47: dict(type="cycle",            slots=8, footprint="full-bleed",       text_load="heavy",  motif="sphere", subform="concentric radial panorama"),
    48: dict(type="layered-platform", slots=5, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="service-system panorama"),
    # ---- batch 3: keys 49-72 (66 in OVERRIDES) ----
    49: dict(type="framework",        slots=8, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="full-slide software-platform panorama"),
    50: dict(type="layered-platform", slots=6, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="super-workbench panorama"),
    51: dict(type="framework",        slots=5, footprint="full-bleed",       text_load="heavy",  motif="cube",  subform="central data-store stack + side modules"),
    52: dict(type="layered-platform", slots=4, footprint="centered-compact", text_load="medium", motif="ring",  subform="fan/arc layered rings"),
    53: dict(type="matrix",           slots=8, footprint="full-bleed",       text_load="heavy",  motif="card",  subform="architecture grid (management platform)"),
    54: dict(type="layered-platform", slots=4, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="fan/arc panorama"),
    55: dict(type="layered-platform", slots=4, footprint="full-bleed",       text_load="heavy",  motif="mixed", subform="fan/arc panorama"),
    56: dict(type="layered-platform", slots=5, footprint="full-bleed",       text_load="heavy",  motif="card",  subform="layered product-system architecture"),
    57: dict(type="matrix",           slots=8, footprint="full-bleed",       text_load="heavy",  motif="card",  subform="security-governance architecture grid"),
    58: dict(type="isometric-stack",  slots=4, footprint="wide-band",        text_load="heavy",  motif="card",  subform="top cards + central isometric stack"),
    59: dict(type="isometric-stack",  slots=5, footprint="centered-compact", text_load="medium", motif="card",  subform="stacked transparent layers"),
    60: dict(type="isometric-stack",  slots=5, footprint="wide-band",        text_load="medium", motif="card",  subform="dual isometric stacks"),
    61: dict(type="framework",        slots=2, footprint="wide-band",        text_load="medium", motif="sphere", subform="two overlapping circles (venn/relationship)", scenario="two-entity relationship / overlap"),
    62: dict(type="framework",        slots=3, footprint="centered-compact", text_load="light",  motif="sphere", subform="big stat circle + metric callouts", scenario="metric / KPI highlight"),
    63: dict(type="bowtie",           slots=3, footprint="centered-compact", text_load="medium", motif="sphere"),
    64: dict(type="cycle",            slots=5, footprint="centered-compact", text_load="medium", motif="card"),
    65: dict(type="layered-platform", slots=4, footprint="centered-compact", text_load="medium", motif="mixed", subform="fan/arc banner over layers"),
    67: dict(type="pyramid",          slots=4, footprint="tall-center",      text_load="medium", motif="mixed"),
    68: dict(type="layered-platform", slots=4, footprint="wide-band",        text_load="medium", motif="mixed", subform="side timeline + layered platform"),
    69: dict(type="layered-platform", slots=4, footprint="centered-compact", text_load="medium", motif="ring",  subform="concentric rings"),
    70: dict(type="framework",        slots=5, footprint="wide-band",        text_load="medium", motif="sphere", subform="central hub + top node row"),
    71: dict(type="bowtie",           slots=4, footprint="centered-compact", text_load="medium", motif="mixed"),
    72: dict(type="layered-platform", slots=4, footprint="wide-band",        text_load="medium", motif="mixed"),
}


def entry(t_full: str, slide: int, shape_count: int) -> dict:
    if t_full in NON_DIAGRAM:
        return {"selectable": False, "kind": t_full, "slide": slide}
    use, slots, slot_of, holds, _svg_alt, blurb = TYPE_DEF[t_full]
    scenario = SCENARIO.get(t_full, "")
    pick = (f"Pick for {scenario} — {blurb}: ~{slots} {slot_of}, each holds {holds}. "
            f"Skip if not a {use} structure, or item count far from {slots}.")
    return {
        "type": t_full, "use": use, "scenario": scenario,
        "slots": slots, "slot_of": slot_of, "holds": holds,
        "density": _density(shape_count), "aspect": "16:9",
        "pick": pick,
    }


def _shape_count(key: str) -> int:
    mp = LIB / key / "meta.json"
    if mp.exists():
        try:
            return int(json.loads(mp.read_text(encoding="utf-8")).get("shape_count", 30))
        except Exception:
            pass
    return 30


def main() -> int:
    idx_path = LIB / "diagrams_index.json"
    old_raw = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}
    old = old_raw.get("diagrams", old_raw)  # tolerate both old flat and new wrapped form

    diagrams: dict[str, dict] = {}
    for n in range(1, 224):
        key = f"solid3d_bluegreen_{n:03d}"
        rv = REVIEW.get(n)
        # A reviewed entry's corrected type drives the base build (incl. pick).
        t_full = rv["type"] if rv else CODE[T.get(n, "lp")]
        e = entry(t_full, n, _shape_count(key))
        if "selectable" not in e:
            e["conf"] = "high" if n in HIGH else "approx"
        if rv:                               # P3 grind: fill verified visual attrs
            for f in ("slots", "slot_of", "footprint", "text_load", "motif",
                      "subform", "holds", "scenario"):
                if f in rv:
                    e[f] = rv[f]
            e["conf"] = "reviewed"
        if key in OVERRIDES:                 # fully hand-written entry wins
            e.update(OVERRIDES[key])
            e["conf"] = "refined"
        diagrams[key] = e

    # composed asset — same lean schema (no style gate)
    combo = old.get("combo_product_system", {})
    diagrams["combo_product_system"] = {
        "type": "composite", "use": "comparison",
        "slots": "2", "slot_of": "models", "holds": "diagram-each",
        "density": "high", "aspect": "16:9",
        "composed_from": combo.get("composed_from", ["solid3d_bluegreen_013", "solid3d_bluegreen_024"]),
        "pick": "Pick to show two whole models side by side under one title (composed 013+024).",
        "conf": "high",
    }

    diagrams = {k: diagrams[k] for k in sorted(diagrams)}
    out = {"meta": META, "diagrams": diagrams}
    idx_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # report
    from collections import Counter
    c = Counter(v.get("type", v.get("kind", "?")) for v in diagrams.values())
    hi = sum(1 for v in diagrams.values() if v.get("conf") == "high")
    ap = sum(1 for v in diagrams.values() if v.get("conf") == "approx")
    ns = sum(1 for v in diagrams.values() if v.get("selectable") is False)
    dens = Counter(v.get("density") for v in diagrams.values() if v.get("density"))
    print(f"diagrams: {len(diagrams)} | type dist: {dict(c)}")
    print(f"density: {dict(dens)} | conf high: {hi} | approx: {ap} | non-selectable: {ns}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
