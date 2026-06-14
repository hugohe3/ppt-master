# Mode: briefing

Neutral information delivery. Lay the facts out plainly and completely, organized for scanning and lookup — no thesis to argue, no story to tell, no lesson to build, no spectacle. For status updates, reference decks, catalogs, meeting packs, FAQs, data references.

---

## 1. Narrative skeleton

**No thesis, by design**: the deck informs rather than argues. Don't manufacture a conclusion-first claim (that's `pyramid`) or a turn (that's `narrative`) where the material is simply "here is what's true".

**Topic titles, not assertions**: the page title names its subject plainly ("Q3 headcount by team", "Supported file formats") — clarity for lookup beats a persuasive finding. This is the deliberate inverse of `pyramid`'s assertion titles.

**`core_message` states coverage, not a claim**: when filling `design_spec.md §IX`, write each page's `core_message` as what the page lays out ("Q3 headcount across teams"), not what it proves ("headcount is concentrating in engineering"). The §IX field reads as an assertion under the other modes; under `briefing` it names scope.

**Complete over selective**: include the full reference set the audience needs to scan, not only the points that support a case. Coverage is the value here.

**Parallel, even treatment**: sibling items get the same shape and weight so they can be compared and located quickly; nothing is dramatized over its peers unless it genuinely differs.

**Sectioned for navigation**: group related facts, label the groups, keep order predictable (chronological / categorical / alphabetical) so the reader can jump to what they need.

---

## 2. Page-structure tendencies

- Tables, definition lists, status cards, reference grids, dashboards — scannable structures over hero compositions.
- Even hierarchy within a section; consistent layout across sibling pages so the eye always knows where to look.
- Where one figure genuinely matters (a total, a status flag, an exception), surface it — but don't invent a punchline the content doesn't have.

> Table / list / dashboard / status-card geometry lives in [`templates/charts/`](../../templates/charts/); this mode decides *that the page informs completely and neutrally*, not pixel positions.

## 3. Speaker-notes register

Even, factual, plain. State what the page shows without building tension or pressing a "so what". No rhetorical questions, no suspense — a clear read-out the listener can follow or skim. Numbers stated plainly. (Common framework: [`executor-base.md §8`](../executor-base.md).)

## 4. Page skeleton example

```
Title: "Q3 deliverables by workstream"        ← a topic label, not a claim
Body:  status table — workstream | owner | status | due — rows at equal weight
Notes: "Three workstreams are on track; payments is at risk on the integration." (plain read-out)
```
