# Sound Effect Library

This directory is PPT Master's global sound-effect library. It contains 186
CC0 sound effects prepared as PowerPoint-compatible WAV files:

| Namespace | Source | Files | Primary use |
|---|---|---:|---|
| `kenney-interface` | Kenney Interface Sounds | 100 | Interface and object-animation cues |
| `kenney-ui` | Kenney UI Audio | 51 | Click, rollover, and state-change cues |
| `bigsoundbank` | BigSoundBank selection | 35 | Whoosh, notification, chime, and pencil cues |

Source snapshots, license declarations, and modifications are recorded in
[THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md). Machine-readable metadata
for every sound lives in [sounds_index.json](./sounds_index.json). The complete
planning-side identity map is [sound-vocabulary.md](./sound-vocabulary.md).

## Project-local selection

The files here are a discovery library, not project inputs. Project creation
does not create a `sounds/` directory or copy the library. Copy only the sounds
explicitly selected for a deck:

```bash
python3 skills/ppt-master/scripts/sound_sync.py projects/deck bigsoundbank/1797 kenney-interface/click_001
```

The command copies only those files to:

```text
projects/deck/sounds/bigsoundbank/1797.wav
projects/deck/sounds/kenney-interface/click_001.wav
```

Animation and transition configuration must reference these project-relative
paths. Do not reference this global directory from a project. Unknown IDs are
reported and cause a non-zero exit before any file is copied. The same batch
preflight rejects a destination that escapes the resolved project root through
a symlink, as well as an existing project file whose content differs from the
selected library ID; the tool never silently overwrites that conflict.

## Vocabulary and optional filtering

After a resolved motion row has a concrete auditory job, read
[sound-vocabulary.md](./sound-vocabulary.md) completely. It groups all 186
canonical ids by objective cue context and includes each label, duration, and
registered context without a recommendation ranking.

Use the CLI only to locate an already-considered id, label, tag, or context:

```bash
python3 skills/ppt-master/scripts/sound_sync.py list --query transition
```

The filter is optional and never replaces complete vocabulary review or current
motion judgment. Sound remains opt-in, and silence is valid.

## Format boundary

All bundled files are PCM signed 16-bit little-endian, 44.1 kHz WAV. Original
mono or stereo channel layout is preserved. The files were not trimmed and
received no loudness processing. This normalization keeps one predictable
package format while preserving each source recording's complete duration and
channel presentation.
