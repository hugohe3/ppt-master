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
- Write in the **register of a Hong Kong corporate announcement**, not generic AI English or Mainland policy-slogan Chinese. The public newsrooms of HSBC Hong Kong, Cathay Pacific, and the Hong Kong Jockey Club are the register reference: one actor, one named action, one number or date. This fork does not copy those organisations' house styles, marks, or slogans.

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

## Voice

Harbour Professional's Voice & Tone is the copy contract. A line should survive as a Hong Kong listed-company headline: actor + action + number or date.

| Reject | Prefer |
|---|---|
| Unlock a seamless digital journey | Launch the service for eligible corporate clients in Hong Kong on 23 October 2026 |
| Empower stakeholders to leverage synergies | The Board is asked to approve HK$12 million for the 90-day pilot |
| `賦能數字化轉型，打造一站式生態` | `建議批准九十萬港元，於九十日內完成試點` |
| `開啟智能新篇章` | `本季旅客量較去年同期升百分之十二` |

English is British (`organisation`, `programme`, `per cent` in IR running text). Chinese is 港式書面語 (`今天宣布`, `本集團`, `本港`, `客戶`, `港元`, `較去年同期`, `截至`, `董事會建議`) in Traditional characters. Drop stacked intensifiers (`leverage`, `empower`, `cutting-edge`, `our journey`) and Mainland slogan Chinese (`賦能`, `抓手`, `落地`, `閉環`, `打造生態`, `全方位`, `一站式`) unless the source quotes a named product or policy.
