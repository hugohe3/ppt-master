# Native Preset Shape Vocabulary

This is Executor's complete authoring-side map of the 187 registered DrawingML
preset names. Read it once, completely, with the executor core before the first page
(Generate) or at authored-mode entry (Create Template). The Office categories and family descriptions expose what exists and
what each contour objectively depicts; the current page's meaning, visual
system, and composition determine whether and how to use it.

**Reference — not a constraint**: the order and families are browse aids, not
rankings, recommendations, whitelists, quotas, or automatic selections. A
primitive, compound construction, necessary freeform, or no drawn carrier may
still be the best result.

**Hard rule — registered identities and behavior boundaries**:

- `flowChart*` names carry conventional flowchart meanings; they are not generic decorative nodes.
- `actionButton*` names provide visual button geometry only; they create no action, hyperlink, or navigation target.
- `bentConnector*` and `curvedConnector*` are connector contours, but newly authored instances have no endpoint attachment.
- `chartX`, `chartStar`, and `chartPlus` are partition symbols, not data charts.
- Literal pictograms and mathematical operators retain the identity named here.

**When to run**: run `preset_shape_svg.py describe <name> --compact` only when
an exact candidate needs objective adjustment, connector, path,
connection-site, or text rectangle facts. Authoring syntax and fragment
contracts remain in
[`native-shape-authoring.md`](./native-shape-authoring.md).

## 1. Lines

Straight, bent, and curved relationship contours.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Straight lines and connectors | Two diagonal orientations plus one straight connector contour. | `line`, `lineInv`, `straightConnector1` |
| Bent connectors | Orthogonal connector contours with one through four bends. | `bentConnector2`, `bentConnector3`, `bentConnector4`, `bentConnector5` |
| Curved connectors | Curved connector contours with increasing segment complexity. | `curvedConnector2`, `curvedConnector3`, `curvedConnector4`, `curvedConnector5` |

## 2. Rectangles

Neutral and corner-inflected rectangular carriers.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Neutral rectangular carriers | Square-corner and uniformly rounded rectangular contours. | `rect`, `roundRect` |
| Corner-inflected rectangles | Rectangles with one-sided, paired, diagonal, rounded, clipped, or mixed corner treatments. | `round1Rect`, `round2SameRect`, `round2DiagRect`, `snipRoundRect`, `snip1Rect`, `snip2SameRect`, `snip2DiagRect` |

## 3. Basic Shapes

Geometric bodies, boundaries, radial contours, and literal symbols.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Triangular bodies | Symmetric and right-triangle contours. | `triangle`, `rtTriangle` |
| Slanted quadrilaterals | Diamond, parallelogram, symmetric trapezoid, and asymmetric trapezoid contours. | `diamond`, `parallelogram`, `trapezoid`, `nonIsoscelesTrapezoid` |
| Regular polygon bodies | Five-, six-, seven-, eight-, ten-, and twelve-sided polygon contours. | `pentagon`, `hexagon`, `heptagon`, `octagon`, `decagon`, `dodecagon` |
| Organic carriers | Oval and teardrop contours. | `ellipse`, `teardrop` |
| Ornamental carriers | Concave-corner plaque and beveled rectangle contours. | `plaque`, `bevel` |
| Radial contours and segments | Wedge, partial circle, thick arc, ring, chord, and open arc contours. | `pieWedge`, `pie`, `blockArc`, `donut`, `chord`, `arc` |
| Frames, corners, and edge pieces | Folded corner, closed/open frames, L-corner, and diagonal stripe contours. | `foldedCorner`, `frame`, `halfFrame`, `corner`, `diagStripe` |
| Brackets | Left, right, and paired square-bracket contours. | `leftBracket`, `rightBracket`, `bracketPair` |
| Braces | Left, right, and paired curly-brace contours. | `leftBrace`, `rightBrace`, `bracePair` |
| Literal pictograms | Named object, weather, emotion, prohibition, and cloud symbols. | `cube`, `can`, `lightningBolt`, `heart`, `sun`, `moon`, `smileyFace`, `noSmoking`, `cloud` |
| Functional pictograms | Six- and nine-tooth gears plus a funnel symbol. | `gear6`, `gear9`, `funnel` |
| Plus symbol | Broad plus/cross body. | `plus` |
| Corner and edge tabs | Four corner or edge tabs that imply a rectangular field. | `cornerTabs`, `squareTabs`, `plaqueTabs` |
| Partition symbols | Rectangles divided into four or six internal regions. | `chartX`, `chartStar`, `chartPlus` |

## 4. Block Arrows

Filled directional bodies for movement, sequence, return, exchange, and route
emphasis.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Arrow-shaped carriers | A pointed pentagonal stage body and a V-notched directional stage. | `homePlate`, `chevron` |
| Cardinal block arrows | Filled arrows pointing right, left, up, or down. | `rightArrow`, `leftArrow`, `upArrow`, `downArrow` |
| Stylized forward arrows | Rightward arrows with tail stripes or an inward tail notch. | `stripedRightArrow`, `notchedRightArrow` |
| Multi-axis arrows | Two-, three-, and four-direction arrow bodies. | `leftRightArrow`, `upDownArrow`, `leftUpArrow`, `leftRightUpArrow`, `quadArrow` |
| Bent and return arrows | Sharp or rounded turns plus an explicit U-turn contour. | `bentUpArrow`, `bentArrow`, `uturnArrow` |
| Circular arrows | One-way, counter-oriented, and two-way circular arrow contours. | `circularArrow`, `leftCircularArrow`, `leftRightCircularArrow` |
| Curved and swoosh arrows | Curved arrows ending on each cardinal side plus a tapered swoosh. | `curvedRightArrow`, `curvedLeftArrow`, `curvedUpArrow`, `curvedDownArrow`, `swooshArrow` |
| Arrow callout bodies | Text-bearing directional callouts in one-, two-, or four-way variants. | `leftArrowCallout`, `rightArrowCallout`, `upArrowCallout`, `downArrowCallout`, `leftRightArrowCallout`, `upDownArrowCallout`, `quadArrowCallout` |

## 5. Equation Shapes

Literal mathematical operators.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Equation operators | Addition, subtraction, multiplication, division, equality, and inequality symbols. | `mathPlus`, `mathMinus`, `mathMultiply`, `mathDivide`, `mathEqual`, `mathNotEqual` |

## 6. Flowchart

Conventional flowchart notation for explicit process diagrams.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Flowchart operations | Process, subprocess, alternate process, preparation, manual operation, and delay symbols. | `flowChartProcess`, `flowChartPredefinedProcess`, `flowChartAlternateProcess`, `flowChartPreparation`, `flowChartManualOperation`, `flowChartDelay` |
| Flowchart decisions and routing | Decision, continuation, junction, collation, sorting, extraction, and merge symbols. | `flowChartDecision`, `flowChartConnector`, `flowChartOffpageConnector`, `flowChartSummingJunction`, `flowChartOr`, `flowChartCollate`, `flowChartSort`, `flowChartExtract`, `flowChartMerge` |
| Flowchart input and output | General, manual, historical punched-media, and display input/output symbols. | `flowChartInputOutput`, `flowChartManualInput`, `flowChartPunchedCard`, `flowChartPunchedTape`, `flowChartDisplay` |
| Flowchart documents | Single-document and multidocument symbols. | `flowChartDocument`, `flowChartMultidocument` |
| Flowchart storage | Internal, offline, online, tape, disk, and drum storage symbols. | `flowChartInternalStorage`, `flowChartOfflineStorage`, `flowChartOnlineStorage`, `flowChartMagneticTape`, `flowChartMagneticDisk`, `flowChartMagneticDrum` |
| Flowchart terminator | Start/end terminal symbol. | `flowChartTerminator` |

## 7. Stars and Banners

Emblems, bursts, banners, scrolls, and wave contours.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Stars | Four- through thirty-two-point star and burst contours. | `star4`, `star5`, `star6`, `star7`, `star8`, `star10`, `star12`, `star16`, `star24`, `star32` |
| Irregular seals and explosions | Two irregular burst contours with different edge density. | `irregularSeal1`, `irregularSeal2` |
| Straight ribbons | Raised, lowered, and outward-tailed straight banner contours. | `ribbon`, `ribbon2`, `leftRightRibbon` |
| Curved ribbons | Upward- and downward-arcing ribbon contours. | `ellipseRibbon`, `ellipseRibbon2` |
| Scrolls | Vertical and horizontal rolled-document contours. | `verticalScroll`, `horizontalScroll` |
| Waves | Single and double undulating bands. | `wave`, `doubleWave` |

## 8. Callouts

Annotation bodies and leaders that point to another object or region.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Leader-line callouts | Unbordered, accent-bar, bordered, and accent-bordered bodies with straight, one-bend, or two-bend leaders. | `callout1`, `callout2`, `callout3`, `accentCallout1`, `accentCallout2`, `accentCallout3`, `borderCallout1`, `borderCallout2`, `borderCallout3`, `accentBorderCallout1`, `accentBorderCallout2`, `accentBorderCallout3` |
| Wedge and thought callouts | Rectangular, rounded, oval, and cloud annotation bodies with wedge or thought tails. | `wedgeRectCallout`, `wedgeRoundRectCallout`, `wedgeEllipseCallout`, `cloudCallout` |

## 9. Action Buttons

Visual navigation-control shapes whose behavior must be assigned separately.

| Family | Objective identity | Exact preset names |
|---|---|---|
| Action-button controls | Blank, home, help, information, directional, boundary, return, document, sound, and movie button faces. | `actionButtonBlank`, `actionButtonHome`, `actionButtonHelp`, `actionButtonInformation`, `actionButtonForwardNext`, `actionButtonBackPrevious`, `actionButtonEnd`, `actionButtonBeginning`, `actionButtonReturn`, `actionButtonDocument`, `actionButtonSound`, `actionButtonMovie` |
