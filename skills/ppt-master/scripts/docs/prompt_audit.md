# Prompt Audit — Budget and Governance Lint

> Maintainer-only, read-only. Audits the agent-facing Markdown corpus without modifying it and is intentionally not wired into CI or pre-commit hooks. Generation roles never load this doc, the tool, or its manifest.

## Run

```bash
python3 skills/ppt-master/scripts/prompt_audit.py            # text summary
python3 skills/ppt-master/scripts/prompt_audit.py --json     # stable JSON report
```

Requires `tiktoken` (not part of `requirements.txt` — end users never need it):

```bash
pip install 'tiktoken>=0.7.0'
```

Exit code `1` on any deterministic error; advisory duplicate/schema candidates stay warnings. With `--json`, setup failures also use a stable `AUDIT_SETUP_ERROR` JSON envelope instead of a traceback or plain-text error.

## What It Checks

| Area | Failure class |
|---|---|
| Corpus and hot-file token ceilings | error on budget overflow |
| Declared load sets (route/stage scenarios) | error on budget overflow, unknown files, selector/registry drift |
| Load coverage | error when a corpus file is in no load set and has no `coverage.exempt` entry |
| Registry claims (layout patterns, modes, styles, renderings, types, charts) | error on ID/count/index drift |
| Markdown references and declared authority edges | error on broken links or unreferenced edges |
| Cross-file exact/near duplicates | warning; intentional cases are adjudicated via `duplicates.accepted` |
| Schema multi-definition | warning when an owner field also has grammar-like text in any non-owner file |

## Manifest Maintenance — `prompt_audit_manifest.json`

The manifest is audit-only (`audit_only: true`, `runtime_consumed: false`); it is a lint fixture, never prompt context. It hand-transcribes the load rules stated in `SKILL.md` and the role/workflow docs, so **every change to read instructions in those docs must update the matching load set in the same change** — the coverage check catches unclassified files, but only humans can catch a changed read rule for an existing file.

- **New corpus file** → when no existing category exemption matches it, the audit fails with `LOAD_COVERAGE_GAP` until you add it to the load sets that read it or exempt it with a one-line reason. Exempt only material that never enters role context (for example, a legacy tombstone, generated maintenance asset, maintainer-only doc, or license notice); represent conditional runtime reads as incremental load sets.
- **Intentional duplicate** → run `--json`, copy the finding's `kind`, `fingerprint`, and `paths` into `duplicates.accepted` with a reason. The acceptance identity is all three values, so separate path pairs with identical prose remain independently reviewable. Editing either reported raw block changes its fingerprint; stale acceptance fails with `DUPLICATE_ACCEPTED_STALE`. `--skip-near-duplicates` deliberately leaves accepted near pairs unchecked because that scan did not run.
- **Schema owner** → every configured field must have a definition signal in its declared owner. One grammar-like non-owner is enough to surface a candidate; split fields into separate owner entries when they belong to different artifacts.
- **Raising a budget** (`budget_policy: current_growth_ceiling` — ceilings ratchet against the current state): legitimate only when a deliberate content addition or a corrected load-set membership moves a file or scenario past its ceiling. Bump to the new actual value plus minimal slack in the same change that causes the increase, and say why in that change's message. Never pre-raise ceilings to make room.
