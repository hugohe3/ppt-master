# Third-Party Sound Notices

The WAV files under this directory are modified copies of third-party CC0
sound assets. PPT Master's MIT license covers PPT Master itself; the source
declarations below describe the bundled sounds.

## Bundled snapshot

Snapshot date: **2026-08-10**.

| Directory | Upstream snapshot | Bundled files | Local modification |
|---|---|---:|---|
| `kenney-interface` | [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds), archive supplied as version 1.0 | 100 | Ogg Vorbis transcoded to PCM 16-bit 44.1 kHz WAV while preserving mono/stereo layout |
| `kenney-ui` | [Kenney UI Audio](https://kenney.nl/assets/ui-audio), versionless current archive | 51 | Ogg Vorbis transcoded to PCM 16-bit 44.1 kHz WAV while preserving stereo layout; `Preview.ogg` excluded |
| `bigsoundbank` | [BigSoundBank](https://bigsoundbank.com/) sound IDs listed below | 35 | Source WAV resampled and, where needed, reduced to PCM 16-bit at 44.1 kHz while preserving mono/stereo layout |

No sound was trimmed, loudness-processed, or unnecessarily downmixed.
Final-file metadata and SHA-256 digests are recorded in `sounds_index.json`.
The Kenney archive URLs and archive digests are also recorded there.

The normalization pass is equivalent to:

```bash
ffmpeg -i <input> -map_metadata -1 -vn -c:a pcm_s16le -ar 44100 <output.wav>
```

No explicit channel-count option is used, so source mono/stereo layout remains
intact.

The UI Audio asset page reports 50 files, while the current downloaded archive
contains 51 usable files under `Audio/`. This snapshot includes all 51 and does
not count the separate preview track.

## Kenney

The source license files for both Kenney packs declare
[Creative Commons Zero (CC0 1.0)](https://creativecommons.org/publicdomain/zero/1.0/).
They permit personal, educational, and commercial use, and state that credit
to Kenney is appreciated but not mandatory.

- Interface Sounds: created and distributed by Kenney, version 1.0, source
  creation date 2020-02-11.
- UI Audio: created by Kenney Vleugels / Kenney.nl.

## BigSoundBank

BigSoundBank identifies the selected files as
“CC0 (public domain): Free and royalty-free” and links them to its
[license page](https://bigsoundbank.com/licenses.html). The individual source
pages identify Joseph Sardin as the author.

The snapshot contains exactly these sound IDs:

- Whoosh: `0572`, `0573`, `1795`–`1802`
- Notification: `2059`–`2067`
- Chime: `2079`–`2091`
- Pencil signature: `3236`–`3238`

Each entry in `sounds_index.json` records its individual BigSoundBank source
page. The library keeps the full recordings, including the two long whooshes
and longer chimes; the `recommended` flag keeps those outside the conservative
default discovery shortlist without removing them.

## CC0 terms

CC0 1.0 lets the rights holder waive copyright and related rights to the
greatest extent allowed by law. It provides the work as-is and does not grant
patent, trademark, privacy, or publicity rights. See the bundled
[CC0 1.0 legal code](./CC0-1.0.txt), sourced from Creative Commons, or the
[official copy](https://creativecommons.org/publicdomain/zero/1.0/legalcode)
for the complete terms.
