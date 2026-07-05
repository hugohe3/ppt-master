# Maintainer Playbook — PR triage

Internal reference for deciding what to merge or close, and how. This is a
maintainer aid, **not an outward promise** — contributor-facing rules live in
[CONTRIBUTING.md](../CONTRIBUTING.md) and the PR template. Precedent PR numbers
are cited so a close can point at a concrete prior decision.

## Decision order

Run a PR through these gates in order. **The first gate it fails is the close
reason** — no need to keep going.

1. **Foundational** — does it change an out-of-the-box setting we don't move?
2. **Capability boundary** — is it outside the "AI-generates-PPT" main line?
3. **Already-solved** — does the repo already do this, via an existing path or on `main`?
4. **Root cause & layer** — does it fix the actual cause, at the right layer?
5. **Evidence & process** — verified against real code, human-reviewed, focused, right entry point?

Passing all five is the bar for merge. Attitude (last section) applies to every
outcome, merge or close.

## The five gates

### A. Foundational non-negotiables

Not merged regardless of implementation quality — these are the project's
factory settings.

- **License stays MIT** — a deliberate founding choice, not changed midway (#203).
- **`pip + requirements.txt` is the only official install path** — no `uv`/`poetry` as a required dependency; multiple dependency sources are a lifetime sync cost that lands on the maintainer (#92, #116).
- **No CI / test frameworks / lint infra**; `tests/` and `test_*.py` are disallowed by `docs/rules/code-style.md` §11 (#200, #203).
- **No fixed numeric quotas** (`max_cards`/`max_bullets`/`max_table_rows` …) — density is governed by narrative rhythm and one primary focus per page (#203).
- **No `_CN` (or other translated) copies of governance docs** — they drift without a sync owner (#179).
- **AI generates a deck; it does not template-fill one** — DrawingML component reuse / native-diagram is outside the current direction (#153–#168).

### B. Capability boundary

The project is a tool around the "AI generates PPT" main line, not an
everything-repo. "We know our limits" is itself the rule.

- **Post-processing is for compatibility, not quality smoothing** — we fix things that are *broken/unusable if not done* (AI-image size/format/alpha). Loudness normalization, kerning polish, etc. are quality smoothing and stay out (#194).
- **If a model/service doesn't work, switch it — don't make the project adapt to it.** A weak agent/provider is a capability gap on their side (#194; also the prompt-change rule).
- **Secondary opt-in features don't get to add heavy deps or change global defaults** — e.g. a narration sub-issue may not push tens-of-MB ffmpeg into core `requirements.txt` default-on (#194).
- **Fidelity yes, authoring deferred** — preserving existing links/structure is in scope; inventing new links/structure on the generation side waits until the core is stable (#155).
- **Personal / vertical preferences belong in the contributor's own copy** (`CLAUDE.md` / fork), so the shared skill stays general-purpose (#177).

### C. Already-solved / redundant

Verify current behavior before accepting a "fix" or "feature".

- **The capability already exists, docs were just unclear** — manual image gen was already covered by `Needs-Manual` (#88).
- **Already supported via an existing path** — Agnes runs under `IMAGE_BACKEND=openai`; a separate backend duplicates the compatibility layer (#202).
- **`main` already solves it more completely** — text-box width is handled at run level (#200).
- **Don't duplicate an existing abstraction/path** (#202, #88).

### D. Root cause & correct layer

- **Fix the root cause; don't paper over an attribute/state nobody consumes** — removing an unconsumed `width`/`height` requirement beat backfilling it (#221).
- **Checks/validation should guard only what downstream actually consumes** (#221).
- **Respect abstraction layers and the single confirmation point** — image strategy is a Step 4 (Eight Confirmations) decision; Step 5 is execution, not a place to re-decide (#88).
- **Take the valid signal, land it our way** — fold the real gain into the existing path instead of swapping an engine or adding a dependency (#207).

### E. Evidence & process

Mirrors CONTRIBUTING; these are close-on-sight.

- Every factual claim must be verified against this repo's actual code — AI-invented problem narratives are closed regardless of diff quality.
- Purely AI-generated, personally-unreviewed PRs are closed unmerged.
- **The PR template's three confirmation boxes: any one left unchecked = closed without review.**
- One PR, one thing; focused bug-fix PRs are prioritized (#206).
- **Prompt/instruction changes** (`SKILL.md`, `references/*.md`, `workflows/*.md`) require a prior agreed issue before a PR.

## How I close (applies to every outcome)

1. **Thank sincerely, and separate "not merging" from "your work is poor."** Name the gate (boundary / direction / already-solved), not the person.
2. **Take and credit the valid signal** — `Co-authored-by`, land it in our structure (#155, #207).
3. **When it's timing/direction, leave the door open** — "we can reopen and restart from here" (#168).
4. **Redirect to the right entry point** — open an issue first, use existing config, keep it in your fork (#177, #202, #206).

## Canned closes

Reusable openers — adapt specifics, keep the tone above. Fill `<…>`.

**Unchecked confirmation box**
> Thanks for the PR. Closing per CONTRIBUTING — the template's three confirmation boxes must all be checked (personal review + claim verification, and the code-only/prompt-issue line), and `<box>` is unchecked. Once you've done `<X>` and can confirm it, feel free to reopen.

**Prompt change without a prior issue**
> Thanks. This edits prompt/instruction text (`<file>`), which per CONTRIBUTING needs a prior agreed issue before a PR — these files steer AI behavior deck-wide and sit near a fixed token budget, and restating a rule the docs already state rarely fixes a non-compliant agent. Please open an issue describing the failure so we can agree the direction first.

**Already supported via existing path**
> Thanks for the contribution. Closing because `<capability>` is already available through `<existing path>` — use `<config/command>`. A separate `<thing>` duplicates the existing path and runs against the current design in `<doc>`. If `<provider/case>` later needs behavior the existing path can't express, we can revisit with a focused change.

**Already solved on main**
> Thanks — the root-cause analysis is correct and matched ours. Closing because `main` already handles this, more completely, via `<mechanism>` in `<file>`. It just landed first through a different structure. Really appreciate the issue and the PR.

**Out of scope / capability boundary**
> Thanks, and for the careful write-up 🙏 After weighing it I'm not taking this direction — it's a capability-boundary call, not an implementation-quality one. `<Reason: quality-smoothing vs compatibility / disproportionate dependency cost / belongs on the provider side>`. If `<X>` blocks you, the more reliable path is `<user-side one-liner / switch provider>` rather than welding it into the default pipeline.

**Foundational setting won't change**
> Thanks for the PR, but this isn't something I'll merge: `<setting>` is a foundational choice from the start and won't change midway. `<one line why>`. Closing that outright.

**Personal / vertical → own copy**
> Thanks for your interest! This looks meant for your own workspace/fork — the best home is your project `CLAUDE.md` or a personal fork, so you get exactly the behavior you want without changing the shared skill (which stays general-purpose). Closing here, but please don't take it as discouragement — an issue is always a great way to float an idea first.

**Tiny fix → issue**
> Thanks! For a fix this small, an issue is usually faster for me to apply directly than a PR round-trip. Closing this, but the report is genuinely useful — mind opening an issue with `<detail>`?

**Not a hard no (timing/direction)**
> Thanks for all the work here 🙏 This sits outside the project's current focus rather than being a problem with the implementation. To keep the PR list manageable I'll close it as not-planned for now — not a hard no; when we revisit this direction we can reopen and restart from here.
