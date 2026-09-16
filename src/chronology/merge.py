"""Merge chronologies built from different sources into one.

Two entries are the *same* entry if they share an id, or share a date and a normalised
event text. Merging unions their sources and keeps the longer notes. Entries that describe
the same real-world event on *different* dates are not merged; they share an `event_key`
and are surfaced by `analyse.conflicts`.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .models import Chronology, Entry


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s).casefold()).strip()


def _fact(e: Entry) -> tuple:
    return e.date, e.precision, e.time, _norm(e.event)


def _compatible(a: Entry, b: Entry) -> bool:
    return _fact(a) == _fact(b) and all(
        not x or not y or x == y
        for x, y in ((a.asserted_by, b.asserted_by), (a.event_key, b.event_key),
                     (a.category, b.category))
    )


def _combine(a: Entry, b: Entry) -> Entry:
    sources = list(a.sources)
    for source in b.sources:
        if source not in sources:
            sources.append(source)
    notes = a.notes
    if b.notes and b.notes != a.notes:
        notes = f"{a.notes}\n\n{b.notes}" if a.notes else b.notes
    return a.model_copy(deep=True, update={
        "sources": sources,
        "actors": sorted(set(a.actors) | set(b.actors)),
        "tags": sorted(set(a.tags) | set(b.tags)),
        "notes": notes,
        "category": a.category or b.category,
        "disputed": a.disputed or b.disputed,
        "event_key": a.event_key or b.event_key,
        "asserted_by": a.asserted_by or b.asserted_by,
    })


def merge(*chronos: Chronology, matter: str | None = None) -> Chronology:
    if not chronos:
        raise ValueError("nothing to merge")
    if matter is None and len({c.matter for c in chronos}) > 1:
        raise ValueError("different matters: supply an explicit merged matter name")
    by_id: dict[str, Entry] = {}
    by_fact: dict[tuple, list[str]] = {}
    for c in chronos:
        for incoming in c.entries:
            e = incoming.model_copy(deep=True)
            candidates = by_fact.get(_fact(e), [])
            target = next((i for i in candidates if _compatible(by_id[i], e)), None)
            if target is not None:
                by_id[target] = _combine(by_id[target], e)
                continue
            if e.id in by_id:
                original_id = e.id
                prior = by_id[original_id]
                group = prior.event_key or e.event_key or f"id-conflict-{original_id}"
                if not prior.event_key:
                    prior.event_key = group
                if not e.event_key:
                    e.event_key = group
                suffix = hashlib.sha256(e.model_dump_json().encode()).hexdigest()[:10]
                e.id = f"{original_id}-{suffix}"
                while e.id in by_id:
                    e.id += "-copy"
            by_id[e.id] = e
            by_fact.setdefault(_fact(e), []).append(e.id)
    parties = sorted({p for c in chronos for p in c.parties})
    return Chronology(matter=matter or chronos[0].matter, parties=parties,
                      entries=sorted(by_id.values(), key=Entry.sort_key))
