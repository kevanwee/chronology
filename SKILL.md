---
name: chronology-extraction
description: Build a litigation chronology from documents (correspondence, affidavits, pleadings, contracts) as chronology-schema YAML with a pincite on every entry; then merge sources, flag date conflicts and evidential gaps, and render. Use when asked for "a chronology", "timeline of events", "what happened when", or to reconcile two accounts of events.
---

# chronology-extraction

You are producing the chronology a trial team will rely on. Every entry must be traceable
to a page. Your job is to record what the documents say happened, not to decide what
happened.

## Workflow

### 1. One file per source

Create a separate YAML (`schema/chronology.schema.json`) for each source document or
bundle section: `from-correspondence.yaml`, `from-lim-affidavit.yaml`, and so on. The
merge step reconciles them; keeping them separate preserves *who says what*.

### 2. Extraction rules

For each dated fact in the source, one entry:

| Field | Rule |
|---|---|
| `id` | kebab-case, meaningful (`complaint-email`, not `e17`) |
| `date` | the date the **event** happened, not the date of the document describing it. A letter dated 14 Nov describing a meeting on 3 Sep produces an entry dated 3 Sep sourced to the letter. |
| `precision` | `day` if the source gives a day; `month` (date = 1st) or `year` (date = 1 Jan) if vaguer; `approx` with a `notes` explanation for "around", "circa", "shortly after". Never upgrade precision. |
| `time` | only if the source gives it (emails, SMS, call logs). |
| `event` | one fact, past tense, neutral wording. Not "Beta breached the contract"; rather "Beta withheld payment of invoice 2291". |
| `actors` | people and entities who acted. |
| `sources` | **at least one, with `pincite` or `bundle_ref`.** Page, paragraph, or bundle page. An entry you cannot pin to a page does not go in. |
| `disputed` / `asserted_by` | set when the fact is one party's account (affidavits, pleadings). `asserted_by` is the party. |
| `event_key` | when you recognise the same real-world event already recorded from another source, give both the same key. The tool flags the pair if dates differ. |

If a source gives no date for something that matters, do not guess. Record it in `notes` on
the nearest dated entry, or leave it out and tell the user.

### 3. Merge, check, render

```bash
chronology validate from-*.yaml
chronology lint from-*.yaml              # pincites, disputed flags, near-duplicates, CONFLICTS
chronology merge from-*.yaml -o merged.yaml
chronology gaps merged.yaml --days 60    # stretches with no documented events
chronology render merged.yaml            # markdown table
chronology render merged.yaml --format csv
```

### 4. Report

Give the user: the rendered table; every **conflict** (same event, different dates, with
who says which); every **gap** longer than the threshold with a one-line note on what
evidence might fill it; and every lint warning you could not resolve. State how many
entries are disputed.

## Rules

- Pincite or it does not exist. No exceptions for "obvious" facts.
- Event date, not document date.
- Neutral wording. The chronology is shared with the other side and the court; adjectives
  are for submissions.
- Never merge two accounts of one event into a single entry by picking a date. Give them
  the same `event_key` and let the conflict show.
- Never infer or interpolate a date to fill a gap. Report the gap.
