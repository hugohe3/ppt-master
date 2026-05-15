# Rendering: pixel-art

8-bit / 16-bit retro game aesthetic. Sharp pixel grid, limited palette, no anti-aliasing. Used for gaming decks, retro tech decks, nostalgic content, and game-flavored education/entertainment.

## 1. Style paragraph (paste-ready, 90 words)

> 8-bit pixel art style with strict pixel-grid alignment and no anti-aliasing. All elements are constructed from discrete colored pixels — visible chunky pixel edges, sharp transitions between color blocks, no soft gradients. Color palette is limited and intentionally retro (often 16-32 distinct colors total). Forms are simplified to fit a low-resolution grid — small character sprites, blocky environments, iconic items. Optional 1-pixel-wide outlines in darker shades of the fill color add definition. Composition often references classic NES / SNES / arcade game framing. Overall feel is nostalgic, playful, retro-game — instantly recognizable.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Pixel-stepped — outlines built from individual pixels, no smooth lines |
| Texture | None beyond the pixel grid itself |
| Depth | Achieved through palette layering (lighter top pixels, darker bottom for shading) |
| Material | Pixel grid |
| Mood | Nostalgic, retro-game, playful |

---

## 3. Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Hero retro banner | 1200×500 | 2.4:1 | 12% |
| Half-page sprite scene | 600×500 | ~1.2 | 14% |
| Square scene | 700×700 | 1:1 | 14% |
| Spot pixel icon | 320×320 | 1:1 | 14% |

---

## 4. Using the deck's HEX values

pixel-art uses HEX values as **palette slots**:

- Primary HEX: dominant character / object color
- Secondary HEX: background or terrain
- Accent HEX: highlight items, important markers, magical effects
- Optional 4th: a darker shade of primary used as outline pixels (typically 25% darker)

---

## 5. Fewshot prompt snippets

**Snippet A — hero retro banner, text_policy: none**

> 8-bit pixel art hero banner with strict pixel-grid alignment and no anti-aliasing. A retro-game-style scene — small pixel character sprite standing on a tile floor in the foreground center, with a stylized pixel-art mountain in the background and a pixel sun in the upper right. Character outfit in primary deep blue `#1E40AF`, with 1-pixel outlines in a darker shade of the same blue. Background mountain in muted gray pixel blocks. Sky in soft secondary peach `#FED7AA`. Sun in accent gold `#D4AF37` rendered as a chunky pixel circle. All elements visibly pixel-stepped — no smooth curves. Limited color palette (around 12-16 distinct colors total). Composed for a 1200×500 hero band with 12% inner padding. Simplified pixel character — no detailed face. NO text or labels. Color values are rendering guidance only.

**Snippet B — half-page retro tech scene, text_policy: none**

> 8-bit pixel art half-page scene. A retro-game-style tech laboratory — pixel computer monitors arranged on pixel desks, with a pixel character sprite working at one of them. All elements built from discrete colored pixels with visible chunky edges. Monitors in primary deep navy `#1E3A5F` with bright accent cyan `#06B6D4` screens. Desks in warm wood-tone secondary pixels `#A16207`. Walls and floor in restrained gray pixels. Small pixel decorations — a coffee cup, a plant — add warmth. 1-pixel outlines in darker shades of each fill color. Limited palette (~16 colors total). Composed as a 600×500 half-page block with 14% inner padding. Pixel character simplified, no realistic face. NO text or labels. Color values are rendering guidance only.

---

## 6. Forbidden

- Anti-aliasing or smooth gradients (defeats the pixel identity)
- Modern photo-realistic detail
- Too high resolution per element (pixel art is intentionally low-res)
- More than 32 distinct colors in one image
- Mixing pixel art with other rendering styles

---

## 7. When to switch away

- For modern flat → `flat` or `vector-illustration`
- For 3D tech aesthetic → `3d-isometric`
- For dashboard / UI surfaces → `digital-dashboard`
