# Hong Kong fork

This fork exists **mainly to adopt Hong Kong tone and culture into PPT Master**. It keeps the upstream workflow intact and adds a Hong Kong working default: Traditional Chinese with English, key-message-first structure, listed-company announcement copy, and a professional navy-paper identity that is **not** Brand Hong Kong or any government mark.

English is canonical here. Deck copy still follows the user's language and sources.

## What was missing

The bundled catalog is strong on global consulting brands and Mainland SOE decks (`中国电信`, `中汽研`, `中国电建`). Language aliases treat bare `中文` as Simplified (`zh-Hans`). Bare `zh-Hant` becomes Office `zh-TW`. None of that is wrong for the upstream project; it is the wrong default for Hong Kong rooms.

Hong Kong professional decks in 2025–2026 tend to:

- Run **two written languages and three spoken ones** (Traditional Chinese and English on the page; Cantonese, English, or Putonghua in the room).
- Plan the **key message first** (BLUF), then one to three supports — not a long preamble. That sequence is how the deck is built; it is never printed as a title or body sentence.
- Declare a **time box**. A 30-minute meeting is asked what it will cover, not given 60 pages.
- Keep **one language dominant**. The second language is a smaller subtitle, label, or caption — not a 50/50 left-right translation.
- Use **business navy, charcoal, and white**. Mainland government / SOE red-gold chrome reads as the wrong register.
- Set Chinese on a Traditional-safe face (`Microsoft JhengHei`, `PingFang HK`) and keep Latin on a separate object or a CJK-safe unified face.
- Close with **owned action items** and a real Q&A window.
- Write **both** languages in the register of a Hong Kong corporate announcement — Hong Kong British business English and Hong Kong written Chinese — not US consulting English, spoken Cantonese, Taiwan lexis, or Mainland policy-slogan Chinese. The public newsrooms of HSBC Hong Kong, Cathay Pacific, and the Hong Kong Jockey Club are the register reference: one actor, one named action, one number or date. This fork does not copy those organisations' house styles, marks, or slogans.

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

Harbour Professional's Voice & Tone is the copy contract for **both** languages. Each line should survive as a Hong Kong listed-company headline in that language: actor + action + number or date. Do not machine-translate one language into the other. Style Argument Flow, BLUF, time boxes, and "Hong Kong rooms want the answer first" are planning notes. They are not slide copy. Name `the Board` / `the Committee` / `本港` / `委員會`; do not self-label the room `港式` on a slide.

**English** is Hong Kong British business English (`organisation`, `programme`, `the Group today announced`, `per cent` in IR running text) — not US spelling and not Silicon Valley filler.

| Reject (US / AI) | Prefer (Hong Kong English) |
|---|---|
| We're excited to roll out the program | The Group today announced the programme for eligible customers |
| Reach out to users to unlock value | Please contact eligible customers with effect from 28 October 2026 |
| Unlock a seamless digital journey | Launch the service for eligible corporate clients in Hong Kong on 23 October 2026 |
| Key message first / HK rooms want the answer first | Recommend the Committee adopt editable PPTX as the paper format with effect from 28 October 2026 |

**Chinese** is Hong Kong written Chinese: Traditional characters, Standard Written Chinese with Hong Kong lexicon (`今天宣布`, `本集團`, `本港`, `客戶`, `港元`, `較去年同期`, `行政總裁`, `溢利`, `數碼化`, `軟件`). It is not spoken Cantonese on the slide, not Taiwan lexis (`軟體`, `網路`, `執行長`), and not Mainland slogan Chinese.

| Reject (Mainland / Taiwan / spoken) | Prefer (Hong Kong written Chinese) |
|---|---|
| `賦能數字化轉型，打造一站式生態` | `建議批准九十萬港元，於九十日內完成試點` |
| `我們很高興推出軟體給用戶` | `本集團今天公布有關軟件，供合資格客戶使用` |
| `而家我哋好興奮宣布` | `本集團今天宣布` |
| `開啟智能新篇章` | `本季旅客量較去年同期升百分之十二` |
| `結論先行` / `先給答案，再用一至三個支撐` / `長鋪墊在港式會議室是延遲` | `建議委員會於下次會議前批准可編輯 PPTX 為文件格式` |

Spoken Cantonese belongs in narration when the spoken language is Cantonese, not in slide body copy. Drop stacked English intensifiers (`leverage`, `empower`, `our journey`) and Mainland slogan Chinese (`賦能`, `抓手`, `落地`, `閉環`, `打造生態`) unless the source quotes a named product or policy.
