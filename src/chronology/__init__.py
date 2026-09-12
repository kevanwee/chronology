"""chronology: litigation chronologies as data.

    load_chronology(path)   -> Chronology
    merge(*chronos)         -> Chronology   union, dedupe, sort
    conflicts(chrono)       -> list[Conflict]   same event_key, different dates
    gaps(chrono, days)      -> list[Gap]
    lint(chrono)            -> list[str]        missing pincites etc.
    render_markdown / render_csv
"""

from .analyse import Conflict, Gap, conflicts, gaps, lint
from .merge import merge
from .models import Chronology, Entry, Precision, Source, load_chronology
from .render import render_csv, render_markdown

__all__ = [
    "Chronology",
    "Entry",
    "Source",
    "Precision",
    "load_chronology",
    "merge",
    "conflicts",
    "gaps",
    "lint",
    "Conflict",
    "Gap",
    "render_markdown",
    "render_csv",
]

__version__ = "0.1.0"
