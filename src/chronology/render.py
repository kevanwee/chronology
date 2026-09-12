"""Markdown and CSV output."""

from __future__ import annotations

import csv
import io

from .models import Chronology, Entry


def _sources(e: Entry) -> str:
    return "; ".join(s.label() for s in e.sources)


def render_markdown(c: Chronology, *, show_ids: bool = False) -> str:
    c = c.sorted()
    out = [f"# Chronology: {c.matter}", ""]
    if c.parties:
        out += [f"Parties: {', '.join(c.parties)}", ""]
    n_disp = sum(1 for e in c.entries if e.disputed)
    out += [f"{len(c.entries)} entries" + (f", {n_disp} disputed" if n_disp else ""), ""]
    with_notes = any(e.notes for e in c.entries)
    cols = ["Date", "Event", "Actors", "Source"] + (["Notes"] if with_notes else [])
    out += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for e in c.entries:
        ev = e.event.replace("|", "\\|")
        if e.disputed:
            tag = f": {e.asserted_by}" if e.asserted_by else ""
            ev = f"**[DISPUTED{tag}]** {ev}"
        if show_ids:
            ev += f" `{e.id}`"
        cells = [e.date_label(), ev, ", ".join(e.actors), _sources(e)]
        if with_notes:
            cells.append((e.notes or "").replace("|", "\\|"))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def render_csv(c: Chronology) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "date", "precision", "time", "event", "actors", "sources", "category",
                "disputed", "asserted_by", "event_key", "tags", "notes"])
    for e in c.sorted().entries:
        w.writerow([e.id, e.date.isoformat(), e.precision.value,
                    e.time.isoformat(timespec="minutes") if e.time else "",
                    e.event, "; ".join(e.actors), _sources(e), e.category or "",
                    "yes" if e.disputed else "", e.asserted_by or "", e.event_key or "",
                    "; ".join(e.tags), e.notes or ""])
    return buf.getvalue()
