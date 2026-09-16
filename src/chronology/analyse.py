"""Things a good paralegal notices and a tired one does not."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import Chronology, Entry, Precision


@dataclass
class Conflict:
    event_key: str
    entries: list[Entry]

    def describe(self) -> str:
        versions = "; ".join(
            f"{e.date_label()} per {e.asserted_by or e.sources[0].label()} ({e.id})"
            for e in self.entries)
        return f"{self.event_key}: {versions}"


@dataclass
class Gap:
    before: Entry
    after: Entry
    days: int


def conflicts(c: Chronology) -> list[Conflict]:
    groups: dict[str, list[Entry]] = defaultdict(list)
    for e in c.entries:
        if e.event_key:
            groups[e.event_key].append(e)
    out = []
    for key, es in groups.items():
        if len({(e.date, e.precision, e.time, e.event, e.asserted_by) for e in es}) > 1:
            out.append(Conflict(key, sorted(es, key=Entry.sort_key)))
    return out


def gaps(c: Chronology, *, days: int) -> list[Gap]:
    es = sorted((e for e in c.entries if e.precision is Precision.DAY), key=Entry.sort_key)
    out = []
    for a, b in zip(es, es[1:], strict=False):
        d = (b.date - a.date).days
        if d >= days:
            out.append(Gap(a, b, d))
    return out


def lint(c: Chronology) -> list[str]:
    warnings = []
    for e in c.entries:
        for s in e.sources:
            if not s.pincite and not s.bundle_ref:
                warnings.append(f"{e.id}: source '{s.doc}' has no pincite or bundle ref")
        if e.disputed and not e.asserted_by:
            warnings.append(f"{e.id}: disputed but `asserted_by` is empty")
        if e.precision is Precision.APPROX and not e.notes:
            warnings.append(f"{e.id}: approximate date with no note explaining the estimate")
        if not e.actors:
            warnings.append(f"{e.id}: no actors")
        if e.event.rstrip().endswith("?"):
            warnings.append(f"{e.id}: event text is a question; chronologies state facts")
    # near-duplicates: same date, events sharing the first 40 chars
    by_day: dict = defaultdict(list)
    for e in c.entries:
        by_day[e.date].append(e)
    for d, es in by_day.items():
        seen: dict[str, str] = {}
        for e in es:
            k = e.event.lower()[:40]
            if k in seen:
                warnings.append(f"{e.id} and {seen[k]} on {d} look like the same entry")
            seen[k] = e.id
    return warnings
