# CLAUDE.md — chronology

Engineering conventions for this repository. They bind AI assistants and humans equally.

## What this is

A small, deliberate tool: a schema for chronology entries with mandatory sourcing, a merge
that preserves provenance, three checks (conflicts, gaps, lint), and renderers. Resist
growth. The temptation to add "smart" features here is strong and almost always wrong.

## Non-negotiables

1. **Every entry has a source.** The schema requires `sources` with at least one item.
   Lint warns when a source lacks a pincite or bundle ref. Do not weaken either.
2. **Merge never reconciles dates.** Two accounts of one event with different dates stay
   as two entries sharing an `event_key`. `conflicts()` surfaces them. Never add a
   "prefer the documentary source" heuristic; that is a judgement for counsel.
3. **Precision is explicit and enforced.** Month precision means the 1st; year means
   1 January; `approx` needs a note. Never silently upgrade precision for sorting.
4. **Renderers are dumb.** They format; they do not filter, summarise, or reorder beyond
   the sort key.
5. **No NLP, no date parsing from prose, no model calls** in the library. The skill does
   extraction with the document in front of it.
6. **Schema drift fails a test.** `schema/chronology.schema.json` is generated
   (`chronology schema > schema/chronology.schema.json`).

## Layout

```
SKILL.md                       extraction skill (repo root is the skill directory)
schema/chronology.schema.json  generated
src/chronology/
  models.py                    Entry / Source / Chronology; precision rules; date_label()
  merge.py                     union + dedupe (id, or date+normalised event)
  analyse.py                   conflicts(), gaps(), lint()
  render.py                    markdown, csv
  cli.py                       argparse; no logic
examples/                      two source files for one fictional matter, with one planted conflict
tests/
```

## Testing discipline

- The two example files are the fixture. They must always merge to exactly one conflict
  (`tuas-inspection`) and zero lint warnings. If you change them, update the assertions
  and keep those two properties.
- Lint rules each have a test that triggers them on a deliberately dirty chronology.
- Date-label formats are tested literally.
- `python -m pytest` and `ruff check src tests` before every commit.

## Style

- Python 3.11+, type hints, pydantic v2 for the schema, dataclasses for analysis results.
- Line length 100.
- YAML examples: flow style for `sources` (`{ doc: ..., bundle_ref: ... }`) to keep entries
  scannable; block style for everything else.
- Entry ids are kebab-case and meaningful.

## Legal-content conventions

- `event` text is past tense, neutral, one fact. The skill enforces this on extraction;
  lint catches questions. Do not add a rule that rewrites wording.
- `asserted_by` is a party name as used in `parties`.
- Bundle refs follow the stamp format of the bundle they came from (e.g. `AB-123`).

## Commit hygiene

- Imperative subject, scoped: `analyse: flag approximate dates without notes`.
- No AI attribution lines or co-author trailers.

## What not to build here

- Timeline graphics. Render to CSV and use whatever charting the team already has.
- Automatic extraction from PDFs.
- Relevance scoring or "key events" detection.
- A Word exporter. Markdown pastes into Word acceptably; if that stops being true, revisit.
