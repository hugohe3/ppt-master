---
brand_id: harbour-professional
kind: brand
summary: Hong Kong professional identity — harbour navy on warm paper, bilingual Traditional Chinese and English, and a listed-company announcement copy register for board, IR, client, and civic decks
primary_color: "#123B5C"
---

# Harbour Professional Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Harbour Professional |
| Use Cases | Hong Kong board papers, investor and results readouts, client proposals, internal operating reviews, and civic or professional briefings that must read as local rather than Mainland SOE or generic Western consulting |
| Tone | Formal, measured, announcement-led — Hong Kong listed-company and civic register, not a consultancy brochure or Mainland policy slogan |
| Sources | Authored for this Hong Kong fork. Visual identity from Hong Kong professional presentation practice (navy / charcoal / white field). Copy register observed from public Hong Kong corporate announcements (banks, carriers, civic institutions) as a register reference only — not a transcription of any issuer's house style, marks, or slogans. Not Brand Hong Kong, not the HKSAR regional emblem, and not an official government or listed-company identity |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#123B5C` | user | Harbour navy — titles, structure, primary series, and cover field |
| secondary | `#1F6A7A` | user | Harbour teal — secondary series and quiet structural emphasis |
| accent | `#B8860B` | user | Muted gold — one point of emphasis per page, never a fill for tables |
| bg | `#FFFFFF` | user | Default light presentation field |
| surface | `#F4F1EC` | user | Warm paper — grouped regions, implication panels, table banding |
| border | `#D5D0C8` | user | Hairline rules, dividers, and table borders |
| muted-text | `#5C6570` | user | Secondary text, unit lines, footnotes, and bilingual support lines |
| ink | `#1A1F24` | user | Body copy and headline numerals |

Every row is `user`. This is a fork-authored professional identity, not a transcription of Brand Hong Kong or any listed-company manual, so nothing here may be represented as an official civic or corporate specification. Keep navy for structure and gold for a single emphasis; never spread teal, gold, and navy as a decorative tricolour on one page, and never restyle the deck as a red-gold Mainland government or SOE template. Do not lock an invented success/warning/error trio as identity. Do not reproduce the Brand Hong Kong flying dragon, its ribbon spectrum, the regional flag, or the regional emblem.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Calibri, "Microsoft JhengHei", sans-serif` | 600–700 |
| body | `Calibri, "Microsoft JhengHei", sans-serif` | 400 |

> PPT Master does not auto-embed fonts or follow CSS tails in PowerPoint. The rows above are the default Windows/Office export for Hong Kong Traditional Chinese (`zh-HK`) with a Latin companion. Replace them only with a user-confirmed target-installed face. Never name Microsoft YaHei or SimSun as the CJK face for this identity. Prefer tabular figures so HKD columns align. When a line mixes scripts, keep Chinese and English in separate text objects, or keep both on a CJK-safe face such as Microsoft JhengHei rather than forcing Calibri to carry Chinese.

## IV. Logo

- File: `none`
- Usage: never

No logo asset is bundled. Brand Hong Kong's flying dragon and the HKSAR regional flag and emblem are protected marks and require official approval; this preset must not approximate them. Where a presenting entity must appear, set it as editable text in the deck's own typography, or install an officially supplied client or organisation asset into this workspace's `images/` directory and add its usage rules here. Never imply affiliation with the HKSAR Government, Brand Hong Kong, or any listed company.

## V. Voice & Tone

- Formality: formal
- Person: we / you (English), 我們 / 您 (Traditional Chinese)
- Emoji: forbidden
- Abbreviations: spell-out-first-use

> Presentation convention for this fork, not an official brand token and not any listed company's voice.

**Register**: Write as a Hong Kong results announcement, board paper, or client letter would be published — institutional, numbered, and dated. The test is whether a listed-company newsroom in Hong Kong could print the line; the test is not a product brochure, a Silicon Valley launch post, or a Mainland policy paper. Do not imitate any issuer's slogans or marks.

**Sentence shape**: One actor, one named action, one number or date or condition. A line with no proper noun, figure, date, or named owner is unfinished; rewrite it. Facts stay in the third person (`the Group today announced`, `本集團今天宣布`). The ask and owned next step may use we (`we recommend the Board approve`, `建議董事會批准`).

**English**: British spelling (`organisation`, `centre`, `programme`, `honour`, `analyse`). `customers` / `clients` / `passengers` / `members`, not `users`, unless the subject is an app interface. `Hong Kong`, `the Chinese Mainland`, and `Hong Kong SAR Government` in running prose. Dates as `28 October 2026` or `28/10/2026`. Currency as `HK$12 million` with Western thousand separators; `per cent` in IR running text, `%` on a KPI tile. Spell out a market abbreviation on first use (`Hong Kong Exchanges and Clearing`, then `HKEX`).

**Chinese**: 港式書面語 in Traditional characters. Prefer `今天宣布`, `本集團` / `本公司` / `本行`, `本港`, `客戶`, `港元`, `較去年同期`, `截至`, `董事會建議`, `有關`, `將於`, `惠及`. Address as `Ms Chan` / `陳女士`. Government-facing copy may use `閣下` in place of `您`. Keep English as a companion line, never a 50/50 parallel translation. Prefer `zh-HK` as the deck language tag. Do not use Simplified Chinese unless the named audience is Mainland.

**Forbidden — stacked intensifiers and policy slogan Chinese**:

| Reject | Prefer |
|---|---|
| Unlock a seamless digital journey | Launch the service for eligible corporate clients in Hong Kong on 23 October 2026 |
| Empower stakeholders to leverage synergies | The Board is asked to approve HK$12 million for the 90-day pilot |
| We're excited to dive into the landscape | The Group today released the six-month figures |
| `賦能數字化轉型，打造一站式生態` | `建議批准九十萬港元，於九十日內完成試點` |
| `開啟智能新篇章` | `本季旅客量較去年同期升百分之十二` |
| `助力高質量發展` | `建議透過慈善信託基金捐助七千二百萬港元` |

Also drop, unless the source itself uses them as a quoted product or policy name: `leverage`, `empower`, `cutting-edge`, `robust ecosystem`, `game-changer`, `harness`, `going forward`, `key takeaways`, `our journey`; and `賦能`, `抓手`, `落地`, `閉環`, `打造生態`, `全方位`, `一站式`, `痛點`, `賽道`, `破圈`, `開啟新時代`.

Keep facts, assumptions, and requests distinct, and close with owned action items rather than a decorative thank-you.

## VI. Icon Style

- Preference: linear

> Presentation convention, not an official brand token. Prefer a restrained stroke family such as `tabler-outline`, keep one family across the deck, and use an icon only where it clarifies a role, state, or relationship. Avoid ornamental seals, bauhinia devices, skyline silhouettes used as decoration, and Mainland SOE emblem styling.
