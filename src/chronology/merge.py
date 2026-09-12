"""Merge chronologies built from different sources into one.

Two entries are the *same* entry if they share an id, or share a date and a normalised
event text. Merging unions their sources and keeps the longer notes. Entries that describe
the same real-world event on *different* dates are not merged; they share an `event_key`
and are surfaced by `analyse.conflicts`.
"""

from __future__ import annotations

import re

from .models import Chronology, Entry


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _combine(a: Entry, b: Entry) -> Entry:
    seen = {(s.doc, s.pincite, s.bundle_ref) for s in a.sources}
    sources = list(a.sources) + [s for s in b.sources
                                 if (s.doc, s.pincite, s.bundle_ref) not in seen]
    notes = max(filter(None, [a.notes, b.notes]), key=len, default=None)
    return a.model_copy(update={
        "sources": sources,
        "actors": sorted(set(a.actors) | set(b.actors)),
        "tags": sorted(set(a.tags) | set(b.tags)),
        "notes": notes,
        "disputed": a.disputed or b.disputed,
        "event_key": a.event_key or b.event_key,
        "asserted_by": a.asserted_by or b.asserted_by,
    })


def merge(*chronos: Chronology, matter: str | None = None) -> Chronology:
    if not chronos:
        raise ValueError("nothing to merge")
    by_id: dict[str, Entry] = {}
    by_fact: dict[tuple, str] = {}  # (date, norm event) -> id
    for c in chronos:
        for e in c.entries:
            fact = (e.date, _norm(e.event))
            target = e.id if e.id in by_id else by_fact.get(fact)
            if target is None:
                by_id[e.id] = e
                by_fact[fact] = e.id
            else:
                by_id[target] = _combine(by_id[target], e)
    parties = sorted({p for c in chronos for p in c.parties})
    return Chronology(matter=matter or chronos[0].matter, parties=parties,
                      entries=sorted(by_id.values(), key=Entry.sort_key))
