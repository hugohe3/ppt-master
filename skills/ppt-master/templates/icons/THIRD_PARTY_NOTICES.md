# Third-Party Icon Notices

The SVG files under this directory include third-party assets. PPT Master's
MIT license covers PPT Master itself; it does not replace the licenses,
attribution requirements, brand guidelines, or trademark rights that apply to
these assets.

## Bundled snapshots

Snapshot date: **2026-08-09**.

| Directory | Upstream baseline | Bundled files | Compatibility boundary |
|---|---|---:|---|
| `chunk-filled` | [CHUNK Icons](https://www.figma.com/community/file/1327310800295849271/chunk-icons), versionless snapshot cross-checked against the [SVG Repo collection](https://www.svgrepo.com/collection/chunk-16px-thick-interface-icons/) and [Wikimedia Commons category](https://commons.wikimedia.org/wiki/Category:Chunk_Icons) | 641 | PPT Master-normalized files; historical local basenames remain stable |
| `tabler-filled` | [Tabler Icons v3.46.0](https://github.com/tabler/tabler-icons/releases/tag/v3.46.0), commit `8ac7d81b72ece11072ef25ea9fd92e80c6f3c9fc` | 1,055 | 1,054 upstream files plus 1 legacy spelling alias |
| `tabler-outline` | [Tabler Icons v3.46.0](https://github.com/tabler/tabler-icons/releases/tag/v3.46.0), commit `8ac7d81b72ece11072ef25ea9fd92e80c6f3c9fc` | 5,138 | 5,130 upstream files plus 8 legacy spelling aliases |
| `phosphor-duotone` | [`@phosphor-icons/core@2.1.1`](https://www.npmjs.com/package/@phosphor-icons/core/v/2.1.1), npm integrity `sha512-v4ARvrip4qBCImOE5rmPUylOEK4iiED9ZyKjcvzuezqMaiRASCHKcRIuvvxL/twvLpkfnEODCOJp5dM4eZilxQ==` | 1,518 | 1,512 upstream files plus 6 legacy aliases; upstream `-duotone` filename suffixes are removed locally |
| `simple-icons` | [Simple Icons 16.28.0](https://github.com/simple-icons/simple-icons/releases/tag/16.28.0), commit `fc91ef03ec113d06627b2d47c1f9644ca202b6f9` | 3,675 | 3,453 current files plus 222 compatibility files matching the 12.4.0 snapshot at commit `32b07a5b798b84b97f2cbbb5b69ec7cb80472f73` |

The Tabler compatibility aliases are `mood-confuzed` in `tabler-filled`, plus
`brand-adobe-after-effect`, `brand-kako-talk`, `currency-rubel`,
`gender-trasvesti`, `ikosaedr`, `mood-confuzed`, `physotherapist`, and
`sport-billard` in `tabler-outline`.

The Phosphor compatibility aliases are `archive-box`, `archive-tray`,
`folder-notch`, `folder-notch-minus`, `folder-notch-open`, and
`folder-notch-plus`. Their current upstream equivalents are respectively
`box-arrow-down`, `tray-arrow-down`, `folder`, `folder-minus`, `folder-open`,
and `folder-plus`.

Simple Icons compatibility files are retained because existing templates,
examples, and user projects may still reference removed brand IDs. Their
presence here does not mean that the current Simple Icons project still ships
or recommends those marks.

## CHUNK Icons attribution

**CHUNK Icons** by **Noah Jacobus** is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

PPT Master modifications: root dimensions were normalized to 24 by 24,
hard-coded black fills were changed to `currentColor`, SVG Repo wrapper
metadata was removed, and historical local filenames were retained. The icon
geometry remains sourced from CHUNK. The `r` glyph was restored from the
public Wikimedia mirror during the 2026-08-09 reconciliation.

## Simple Icons license and trademark notice

The Simple Icons project is released under
[CC0 1.0](https://github.com/simple-icons/simple-icons/blob/16.28.0/LICENSE.md),
but that does not imply that every individual brand icon is CC0. Brand marks
may have separate licenses, usage guidelines, or trademark restrictions.
Before using a bundled brand icon, check its current Simple Icons metadata,
the brand owner's guidelines, and the upstream
[disclaimer](https://github.com/simple-icons/simple-icons/blob/16.28.0/DISCLAIMER.md).
Neither CC0 nor inclusion in this repository grants trademark permission.

## MIT notices

The following copyright notices and MIT terms apply to the Tabler and
Phosphor assets described above.

### Tabler Icons

Copyright (c) 2020-2026 Paweł Kuna

### Phosphor Icons

Copyright (c) 2023 Phosphor Icons

### MIT License terms

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Update policy

- Pin a released upstream version, or record the audit date for a versionless
  source, before copying files.
- Overwrite files that still exist upstream, but do not automatically delete
  local-only names. Review removals and renames as compatibility changes.
- Recheck the Simple Icons disclaimer and per-brand metadata whenever that
  library is refreshed; an upstream removal is not merely a file-sync detail.
- Recount the directories and validate every SVG after each refresh. Update
  this notice and the two icon-library README tables in the same change.
