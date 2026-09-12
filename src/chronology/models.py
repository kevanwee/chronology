"""Chronology schema. `schema/chronology.schema.json` is generated from this file."""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class Precision(StrEnum):
    DAY = "day"
    MONTH = "month"  # `date` is the 1st of the month
    YEAR = "year"  # `date` is 1 January
    APPROX = "approx"  # "circa"; `date` is the best estimate


_PREC_ORDER = {Precision.DAY: 0, Precision.APPROX: 1, Precision.MONTH: 2, Precision.YEAR: 3}


class Source(BaseModel):
    doc: str = Field(description="document title or bundle tab, e.g. 'Email Tan to Lim'")
    pincite: str | None = Field(default=None, description="page/para, e.g. 'p 2' or '[14]'")
    bundle_ref: str | None = Field(default=None, description="bundle page, e.g. 'AB-123'")
    url: str | None = None

    def label(self) -> str:
        parts = [self.doc]
        if self.bundle_ref:
            parts.append(self.bundle_ref)
        elif self.pincite:
            parts.append(self.pincite)
        return ", ".join(parts)


class Entry(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    date: dt.date
    precision: Precision = Precision.DAY
    time: dt.time | None = None
    event: str = Field(min_length=8, description="one dated fact, past tense, neutral")
    actors: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(min_length=1)
    category: str | None = Field(default=None,
                                 description="correspondence, payment, meeting, filing ...")
    disputed: bool = False
    asserted_by: str | None = Field(default=None, description="party whose account this is")
    event_key: str | None = Field(
        default=None,
        description="same real-world event across sources; differing dates are conflicts",
    )
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def _precision_shape(self) -> Entry:
        if self.precision is Precision.MONTH and self.date.day != 1:
            raise ValueError(f"{self.id}: month precision requires date on the 1st")
        if self.precision is Precision.YEAR and (self.date.month, self.date.day) != (1, 1):
            raise ValueError(f"{self.id}: year precision requires 1 January")
        if self.time and self.precision is not Precision.DAY:
            raise ValueError(f"{self.id}: a time is only meaningful with day precision")
        return self

    def sort_key(self) -> tuple:
        return (self.date, _PREC_ORDER[self.precision], self.time or dt.time.min, self.id)

    def date_label(self) -> str:
        if self.precision is Precision.DAY:
            s = self.date.strftime("%d %b %Y")
            return f"{s} {self.time.strftime('%H:%M')}" if self.time else s
        if self.precision is Precision.MONTH:
            return self.date.strftime("%b %Y")
        if self.precision is Precision.YEAR:
            return self.date.strftime("%Y")
        return "c. " + self.date.strftime("%d %b %Y")


class Chronology(BaseModel):
    matter: str
    parties: list[str] = Field(default_factory=list)
    entries: list[Entry]

    @model_validator(mode="after")
    def _unique_ids(self) -> Chronology:
        ids = [e.id for e in self.entries]
        if len(ids) != len(set(ids)):
            dup = next(i for i in ids if ids.count(i) > 1)
            raise ValueError(f"duplicate entry id {dup!r}")
        return self

    def sorted(self) -> Chronology:
        return self.model_copy(update={"entries": sorted(self.entries, key=Entry.sort_key)})


def load_chronology(path: str | Path) -> Chronology:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Chronology.model_validate(raw)


def json_schema() -> dict:
    return Chronology.model_json_schema()
