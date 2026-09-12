# chronology

Litigation chronologies as data. A schema where every entry carries a pincite, merge
across sources that preserves who-said-what, automatic detection of date conflicts and
evidential gaps, markdown/CSV rendering, and a Claude skill for the extraction step.

```yaml
- id: site-meeting
  date: 2024-09-03
  event: Site meeting at Tuas; Alpha's engineer inspected the rejected units.
  actors: [Tan Ah Kow, Lim Bee Hoon]
  sources:
    - { doc: Meeting minutes, bundle_ref: AB-70 }
  event_key: tuas-inspection
```

```
$ chronology lint examples/from-correspondence.yaml examples/from-affidavit.yaml
CONFLICT: tuas-inspection: 03 Sep 2024 per Meeting minutes, AB-70 (site-meeting); 05 Sep 2024 per Beta Pte Ltd (inspection-per-lim)
0 warning(s), 1 conflict(s)
```

## Why

Chronologies are built by hand, in Word tables, by the most junior person on the matter,
from several sources at once. Three things go wrong: entries lose their page references
during editing; two accounts of the same event get silently reconciled into one date; and
nobody notices the eight-month stretch with no documents. This repo makes all three
mechanical.

It is small on purpose. The schema and the three checks are the value.

## What is in the box

| Piece | What it does |
|---|---|
| `schema/chronology.schema.json` | Generated JSON Schema. Entries require at least one source; precision rules are enforced (month precision means the 1st, year means 1 Jan). |
| `chronology merge` | Unions several files. Same id, or same date + same wording, becomes one entry with all sources. Different dates for the same `event_key` are **not** merged. |
| `chronology conflicts` | Same `event_key`, different dates: shows each version and who asserts it. Exit 1 if any. |
| `chronology gaps --days N` | Stretches of N+ days with no day-precision entry. |
| `chronology lint` | Sources without a pincite or bundle ref; disputed entries without `asserted_by`; approximate dates without an explanation; events phrased as questions; near-duplicate entries on the same day. |
| `chronology render` | Markdown (disputed entries marked, dates shown at their precision: `19 Aug 2024 16:42`, `May 2024`, `c. 12 Mar 2024`) or CSV. |
| `SKILL.md` | Extraction discipline: event date not document date, one fact per entry, neutral wording, pincite mandatory, same `event_key` for rival accounts. |

## Install

```bash
pip install -e ".[dev]"
```

As a Claude skill: clone into `.claude/skills/chronology-extraction/`.

## Workflow

```bash
chronology validate from-*.yaml
chronology lint from-*.yaml
chronology merge from-*.yaml -o merged.yaml
chronology gaps merged.yaml --days 60
chronology render merged.yaml > chronology.md
```

Keep one source file per document or bundle section. The merge output is itself a valid
chronology file, so you can re-lint and re-render it, but keep the source files: they are
the audit trail for who said what.

## Schema notes

| Field | Notes |
|---|---|
| `date` + `precision` | `day` (default), `month`, `year`, `approx`. The date is the event's date, never the document's. |
| `time` | `HH:MM`, day precision only. |
| `sources[]` | `doc` plus `pincite` (`p 2`, `[14]`) or `bundle_ref` (`AB-123`). Lint warns if both are missing. |
| `disputed`, `asserted_by` | Mark one party's account. Rendered as `[DISPUTED: party]`. |
| `event_key` | Same real-world event across sources. Conflicts are detected on this key. |
| `category`, `tags`, `notes` | Free. |

## Related projects

`bundle_ref` values come from a bundle built with [bundlebuild](https://github.com/kevanwee/bundlebuild). Authorities
cited in the chronology's commentary can be checked with [citecheck](https://github.com/kevanwee/citecheck).

## License

MIT.
