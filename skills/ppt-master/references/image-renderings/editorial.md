# Rendering: editorial

Magazine-style infographic look — sophisticated layout, refined type-as-shape elements, restrained color, editorial pacing. The default choice for finance, journalism, explainers, opinion pieces, sophisticated B2B content.

## Style paragraph (paste-ready, 100 words)

> Magazine-style editorial illustration with sophisticated visual hierarchy and confident negative space. Elements are arranged with editorial pacing — one dominant focal area, deliberate alignment to invisible columns, generous gutters between blocks. Color is restrained and balanced — typically one rich brand tone, one neutral, one subtle accent. Geometric forms are simple but rendered with editorial confidence: bold blocks, refined dividers, accent rules. Optional duotone or limited-color treatment reinforces the magazine feel. Composition feels like a thoughtful magazine spread — not loud, not minimal, but considered. Overall mood is intelligent, premium, restrained, suitable for analytical and opinion content.

## Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Refined — thin precise rules as dividers; clean filled shapes |
| Texture | Minimal — optional very subtle paper grain at 5-10% opacity |
| Depth | Flat with intentional layering; no shadows |
| Material | None — abstract editorial composition |
| Mood | Refined, intelligent, premium-restrained |

## Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page editorial visual | 600×500 | ~1.2 | 15% (editorial wants breathing room) |
| Hero spread | 1200×600 | 2:1 | 14% |
| Square explainer | 700×700 | 1:1 | 15% |
| Spot illustration | 400×500 | 4:5 | 12% |

## Using the deck's HEX values

- Primary HEX: dominant block or background field if a saturated editorial mood is wanted
- Secondary HEX: gutters, dividers, background field (usually neutral)
- Accent HEX: one accent rule, one highlighted element

## Fewshot prompt snippets

**Snippet A — half-page financial explainer, text_policy: none**

> Magazine-style editorial illustration. The canvas is divided into a deliberate two-column composition — a tall block on the left occupying 40% of the width filled with primary deep navy `#0F2C4C`, and the right 60% as a calm secondary cream `#FAF7F2` field. Within the cream field, three stylized bar-chart elements rise from a baseline, each bar a different height, rendered in primary navy with thin uniform width. A thin accent rule in burnt orange `#C2410C` runs horizontally across the lower third connecting the navy block to the bars. One small circular accent marker in the same orange sits at the peak of the tallest bar. Subtle paper grain at 8% opacity across the canvas. Composed as a 600×500 half-page block with 15% inner padding. NO text, no labels, no numbers anywhere. Color values are rendering guidance only.

**Snippet B — hero opinion-piece spread, text_policy: none**

> Magazine-style editorial hero illustration. Wide canvas divided into three vertical bands at roughly 25%/50%/25% — the left band a saturated deep teal `#0F766E` filled solid, the center band a neutral cream `#FEFCE8` field, the right band a soft warm gray `#D4D4D8`. Centered in the cream field is a large simple geometric form — a circle with a single thin accent line in orange `#F97316` cutting horizontally across it. A thin editorial rule in deep teal runs vertically separating the bands. Subtle paper grain at 6% opacity. Composed for a 1200×600 hero band with 14% inner padding. NO text or labels. Color values are rendering guidance only.

## What to avoid

- Decorative ornament (editorial is restrained, not Victorian)
- Vibrant accent dominating the composition
- Cluttered multi-element compositions
- More than 3 colors

## When to switch away

- For approachable / friendly visuals → `sketch-notes`, `warm-scene`
- For dashboard / product surfaces → `digital-dashboard`
- For technical schematic → `blueprint`
