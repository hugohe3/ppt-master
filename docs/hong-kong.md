# Hong Kong fork

This fork keeps upstream PPT Master intact and adds a Hong Kong working default: Traditional Chinese with English, key-message-first structure, and a professional navy-paper identity that is **not** Brand Hong Kong or any government mark.

English is canonical here. Deck copy still follows the user's language and sources.

## What was missing

The bundled catalog is strong on global consulting brands and Mainland SOE decks (`中国电信`, `中汽研`, `中国电建`). Language aliases treat bare `中文` as Simplified (`zh-Hans`). Bare `zh-Hant` becomes Office `zh-TW`. None of that is wrong for the upstream project; it is the wrong default for Hong Kong rooms.

Hong Kong professional decks in 2025–2026 tend to:

- Run **two written languages and three spoken ones** (Traditional Chinese and English on the page; Cantonese, English, or Putonghua in the room).
- Put the **key message first** (BLUF), then one to three supports — not a long preamble.
- Declare a **time box**. A 30-minute meeting is asked what it will cover, not given 60 pages.
- Keep **one language dominant**. The second language is a smaller subtitle, label, or caption — not a 50/50 left-right translation.
- Use **business navy, charcoal, and white**. Mainland government / SOE red-gold chrome reads as the wrong register.
- Set Chinese on a Traditional-safe face (`Microsoft JhengHei`, `PingFang HK`) and keep Latin on a separate object or a CJK-safe unified face.
- Close with **owned action items** and a real Q&A window.

Official Brand Hong Kong (flying dragon, ribbon spectrum, "Asia's world city") and the HKSAR regional flag / emblem are protected. This fork does not copy them.

## What this fork adds

| Kind | ID | Workspace | Use when |
|---|---|---|---|
| Brand | `harbour-professional` | `skills/ppt-master/templates/brands/harbour-professional/` | No client brand is supplied; identity should read as Hong Kong professional |
| Style | `hk-bilingual-board` | `skills/ppt-master/templates/styles/hk-bilingual-board/` | Board papers, IR / results, committee decision notes, operating readouts |
| Style | `hk-client-pitch` | `skills/ppt-master/templates/styles/hk-client-pitch/` | Client proposals and 30–45 minute live pitches |

A client-supplied brand, an official manual, or an existing PPTX identity always wins over Harbour Professional. Pair either Style with [`report_core`](../skills/ppt-master/templates/layouts/report_core/) when Master/Layout structure is wanted; otherwise Brand + Style stay slide-local (`flat`).

Language aliases such as `Cantonese`, `港式中文`, and `香港中文` now normalize to `zh-HK` so Office proofing, EA fonts (`Microsoft JhengHei`), and Cantonese neural voices line up.

## How to ask for a deck

Exact workspace roots, not bare names. Routing never treats a brand or style label as a selection.

Board / IR:

```text
Make a board paper from <sources>.
Primary language: zh-HK.
Brand workspace: skills/ppt-master/templates/brands/harbour-professional/
Style workspace: skills/ppt-master/templates/styles/hk-bilingual-board/
```

Client pitch:

```text
Make a client pitch from <sources>.
Primary language: zh-HK.
Brand workspace: skills/ppt-master/templates/brands/harbour-professional/
Style workspace: skills/ppt-master/templates/styles/hk-client-pitch/
```

Existing PPTX (notes, beautify, or surgical page edits) still follows the normal routes: Edit Native PPTX when the look must stay; Beautify when content is frozen and layout is rebuilt; Generate when the argument is new.

When the audience is Mainland, say so and use Simplified / the relevant client brand instead of this default.
