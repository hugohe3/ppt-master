# `spec_review/server.py`

Local browser review of `design_spec.md`, with block comments and staged Markdown
editing. The tool writes the same spec file, keeps comments in sidecars, and does
not read or write `spec_lock.md`, invoke a model, or start generation.

## Commands

```bash
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --daemon
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --daemon --no-browser
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --port 6070 --timeout 7200
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --hold on
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --hold off
python3 skills/ppt-master/scripts/check_spec_annotations.py <project_path>
python3 skills/ppt-master/scripts/check_spec_annotations.py <project_path> --ack-edits
python3 skills/ppt-master/scripts/check_spec_annotations.py <project_path> --applied <id>
python3 skills/ppt-master/scripts/spec_review/server.py <project_path> --shutdown
```

The daemon launcher waits for `GET /api/health` and prints a compact JSON object
with the actual URL, pid, and port. Diagnostics go to stderr; detached server
output goes to `<project_path>/spec_review/server.log`.
As with other project CLIs, an existing `validation/workflow.log` receives the
launch/check command envelope through the shared console helper; detached server
requests are not copied into that workflow log.

## Lifecycle

- **Port**: bind loopback only. Without `--port`, scan 50 ports starting at `6060`;
  an explicit `--port N` binds strictly. Use the returned URL, not an assumed port.
- **Single instance**: `<project_path>/spec_review/lock.json` records pid and port.
  A second launch reuses the live instance; a different explicit port fails.
  Dead-pid locks are replaced. `service.guard` serializes concurrent launches.
- **Timeout**: `7200s` of inactivity by default; `--timeout 0` disables it.
  `/api/state` polling and `/api/health` requests do not refresh activity; other
  requests that pass the Host/Origin guard do. An idle open tab does not prevent
  timeout. Closing a tab leaves the service running. **Exit review**, `--shutdown`,
  timeout, or process termination stops it.
- **Draft lifetime**: per-block drafts live only in server memory. A tab reload
  can retrieve them; stopping or restarting the server loses unapplied drafts.
  The browser requests leave-page confirmation while it has pending work.
- **Exit review**: the button checks for unapplied drafts and unsaved comments
  before calling `POST /api/shutdown`. Pending work requires confirmation.
  Successful shutdown stops polling and replaces the review workspace with a
  static stopped message in the selected UI language; saved comments remain on disk.
- **Write handoff**: `--hold on` waits for an active Apply to finish and makes
  subsequent Apply requests return `423`. The page displays an AI-editing banner.
  `--hold off` causes automatic block/hash reload, including when both transitions
  occur between polls. Existing drafts survive and stale bases remain conflicts.
- **External changes**: the browser polls the raw-byte SHA-256 every two seconds.
  A changed hash prompts reload; reload preserves drafts. After inspecting the
  current source, **Use current disk as draft base** explicitly rebases a draft.
  A draft whose block was removed externally remains available for copying or
  discarding; it cannot be applied to a different block.
  External writers must honor hold for coordinated writes: the last hash check
  and filesystem replacement cannot form a compare-and-swap with arbitrary writers.
- **Request boundary**: Host must name loopback; a supplied Origin must match the
  request origin. Responses disable caching and carry a restrictive CSP. There
  are no remote scripts, fonts, styles, or other resources.

## Review surface

The three-column dark UI has ordered block navigation, rendered/source views,
a raw Markdown editor, and block/global comments. First/prev/next/last and
`Left`/`Right`/`Home`/`End` navigation are suppressed while typing. Four languages
(Chinese, Traditional Chinese, English, Japanese) follow `navigator.language`
and a persistent `localStorage` selection.

Blocks use each `##` section, except IX: its lead-in, each Slide heading matching
the shared `SLIDE_HEADING_RE` (levels 3–6), and every other `###` heading are
separate blocks. Non-Slide `###` headings have kind `part` and occurrence keys
`part:01`, `part:02`, etc. Each range ends immediately before the next block.
Navigation renders Parts as clickable group headings with indented Slides below.
Backtick and tilde fences hide internal headings. The preamble and all ordered ranges
reconstruct the exact source bytes. The shared `project_management/spec_blocks.py`
API exposes character offsets and corresponding UTF-8 byte offsets; malformed
duplicate keys receive occurrence suffixes.

**Apply changes** saves the selected block. The service serializes Apply and
hold, checks the supplied SHA-256 against disk (`409` on mismatch), validates the
candidate text with the existing design-spec schema, replaces only the target
byte interval using a sibling temporary file and `os.replace`, and appends edit
history. Schema errors are returned verbatim and displayed without blocking the
save. Direct editing locks the section heading, Slide level/number, and structural
boundaries; a Slide page name may change. A Part permits only title text changes:
its heading stays level 3 and its remaining content stays unchanged. Slides do
not contain the next Part heading, so appending page content does not edit a Part.
Additional unfenced `##` headings or headings matching `SLIDE_HEADING_RE` are
rejected; additional `###` headings in IX are also rejected. Page insertion,
removal, and ordering are comment requests. Changed blocks retain their newline style and terminal
whitespace; a no-op preserves even mixed line endings. Drafts on other unchanged
blocks advance to the new hash after a successful browser Apply.

The renderer uses DOM creation and text nodes for headings, paragraphs, lists
(including nesting), emphasis, inline code, tables, fenced code, quotations, and
rules. LaTeX stays monospace text; unsupported syntax falls back to literal text.
Links and image syntax do not create clickable links or loaded images.
Inline fragments over 4096 characters remain plain text to bound delimiter
backtracking. A rendering exception replaces that block's preview with its full
source in a monospace display; editing and staging remain available.

Comments are saved immediately to `spec_review/annotations.json`, separately
from Apply. Each item contains `id`, `key`, `title`, `spec_sha256` (creation-time
whole-spec hash), `body`, `created_at`, `updated_at`, and a unique `revision`.
Block comments also store `block_sha256`, the creation-time SHA-256 of that raw
block's UTF-8 bytes. Updating a comment preserves its original hashes. API and
CLI listings report `block_changed` as `true` or `false` against the current block;
legacy items without `block_sha256` report `null` (unknown). An absent block has
`block_missing: true` and `block_changed: null`; present blocks have
`block_missing: false`. The UI uses these block statuses. `global` is the global
comment slot and retains the whole-spec `base_current` comparison instead.
`annotations.jsonl` appends `saved`, `updated`, `removed`,
and `annotation_applied` events. `storage.guard` serializes browser/CLI
sidecar transactions and edit-log access across processes. `edits.jsonl` appends `ts`, `key`, `title`,
`before`, `after` (the block text), and `before_sha256` / `after_sha256` (whole-spec
hashes) for each changed block.

`check_spec_annotations.py` prints compact JSON with pending comments, their
current baseline statuses, and unread direct-edit summaries (`ts`, `key`, `title`,
plus the first 12 characters of `before_sha256` and `after_sha256`, no block bodies).
`annotations.json` stores an acknowledged byte offset in `edits_cursor` (default
`0`) and the last CLI listing's end offset in `listed_edits_cursor`. Listing does
not consume edits. `--ack-edits` advances the acknowledged cursor only to that
last listed offset; edits appended after the listing remain unread. It requires a
prior CLI listing and never rewrites `edits.jsonl`. Later listings return only
edits after the acknowledged cursor. `--ack-edits` and `--applied` are mutually exclusive.

Listing also records full-item fingerprints (including revisions) in the same
sidecar's `listed` map. `--applied ID` clears only that listed version; an unlisted or subsequently
changed comment stays pending and the command exits nonzero with stderr detail.
Browser reads do not advance this agent receipt. Updating even to identical text
creates a new revision. A fresh CLI listing replaces the previous listing receipt.

### HTTP API

JSON bodies and responses use UTF-8. Block keys are URL-encoded path components.

| Method and path | Result or request body |
| --- | --- |
| `GET /api/health` | Service identity, project path, pid |
| `GET /api/state` | `sha256`, `hold`, `hold_revision` |
| `GET /api/blocks` | Ordered metadata, annotation/draft flags, global-comment flag, draft keys, orphan drafts, state |
| `GET /api/blocks/<key>` | Original `text`, title, ranges, current hash, optional separate draft |
| `GET /api/spec` | Full raw `text` and `sha256` |
| `PUT /api/drafts/<key>` | `text`, `sha256`, `version` (`null` for a new draft); returns a new draft version |
| `DELETE /api/drafts/<key>` | `version` of the draft to discard |
| `POST /api/apply/<key>` | `sha256`, `version`; returns `saved`, new hash, `validation_errors` |
| `GET /api/annotations` | Pending items with block baseline status, or `base_current` for global comments |
| `POST /api/annotations` | `key`, `body`; returns the saved item |
| `PUT /api/annotations/<id>` | `body`, `revision` |
| `DELETE /api/annotations/<id>` | `revision` |
| `POST /api/hold` | `hold` boolean |
| `POST /api/shutdown` | Stops the service |

Stale draft or comment versions return `409`; malformed bodies and structural
edits return `400`. Request bodies are limited to 4 MiB. No approval or generation
endpoint exists.

## Frontend regression checks

There is no repository JavaScript test runner. Use a disposable project copy
with at least two editable blocks for these manual checks. Start the review
server with the commands above, open its URL, and use the browser's Network
panel to inspect request keys and bodies. To keep write responses in flight
while typing or navigating, run this temporary console snippet; reloading the
tab restores normal fetching:

```javascript
const originalFetch = window.fetch.bind(window);
window.fetch = async (...args) => {
  const response = await originalFetch(...args);
  if ((args[1]?.method || 'GET') !== 'GET') {
    await new Promise(resolve => setTimeout(resolve, 1500));
  }
  return response;
};
```

1. **Apply target and snapshot**: stage a draft in block B, return to A, and
   edit A. Within the 350 ms debounce window, click B and immediately click
   Apply while A is still displayed. Repeat after A's draft PUT has started,
   adding another character before clicking B and Apply. Expect the queued
   navigation to flush A, then Apply to target A with the text present at the
   Apply click and the version returned by staging. Only A changes on disk;
   B's draft remains. Also wait until B is displayed before clicking Apply in
   a separate run: only B should change. The editor and Apply stay disabled
   until the pending Apply finishes, including across polling responses.
2. **Typing during responses**: stage an A draft, change the disposable spec
   externally, reload its disk content, and choose the rebase action. Type
   more text while the draft PUT response is delayed. Expect all new text to
   remain in the editor and to stage using the returned version and new base.
   Separately save a new annotation and update an existing annotation, typing
   more in the same field before each response arrives. Expect the sent text
   to be saved, the newer input to remain, and a subsequent update to succeed
   with the latest revision. With no additional typing, saving a new annotation
   should still clear its input as usual.
3. **Pathological Markdown**: append a line produced by
   `'x' + String.fromCharCode(96).repeat(200000) + 'y'` to an editable block.
   Expect literal text to appear promptly and the draft PUT to proceed. Also
   try an unclosed code fence, hundreds of increasingly indented list items,
   and a table with a two-cell header and one-/three-cell body rows. Expect
   each preview to finish without throwing or looping. To exercise exception
   recovery, temporarily replace `markdown` in the console with a function
   that throws, then type: the preview must show the entire block as monospace
   source and staging must continue. Reload the tab to restore the renderer.
4. **External edit before metadata refresh**: on a fresh tab without drafts,
   run `clearInterval(pollTimer)` in the console to hold off the two-second
   poll. Change the disposable spec on disk, then save an annotation. Expect
   the reload warning immediately after metadata refresh, while the preview
   and displayed fingerprint still describe the old block. Click the in-page
   reload button: the preview/fingerprint should advance and the warning should
   clear. Reload the tab afterward to restore polling.

## Remote access

Start with `--no-browser` on the remote host. Forward the actual port `<P>` from
launch output or `spec_review/lock.json`: use the IDE's **PORTS** panel, a Termius
local rule bound to `127.0.0.1:<P>`, or
`ssh -L <P>:127.0.0.1:<P> <user>@<host>`. Open `http://localhost:<P>` locally.
