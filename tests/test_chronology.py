import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from chronology import (
    Chronology,
    conflicts,
    gaps,
    lint,
    load_chronology,
    merge,
    render_csv,
    render_markdown,
)
from chronology.cli import main
from chronology.models import json_schema

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"


@pytest.fixture
def corr():
    return load_chronology(EX / "from-correspondence.yaml")


@pytest.fixture
def aff():
    return load_chronology(EX / "from-affidavit.yaml")


def test_examples_validate(corr, aff):
    assert len(corr.entries) == 6 and len(aff.entries) == 4


def test_schema_matches():
    committed = json.loads((ROOT / "schema" / "chronology.schema.json").read_text("utf-8"))
    assert committed == json_schema(), "run: chronology schema > schema/chronology.schema.json"


def test_precision_rules():
    base = {"id": "x", "event": "Something happened here.", "sources": [{"doc": "d"}]}
    with pytest.raises(ValidationError, match="month precision"):
        Chronology(matter="m", entries=[{**base, "date": "2024-05-02", "precision": "month"}])
    with pytest.raises(ValidationError, match="1 January"):
        Chronology(matter="m", entries=[{**base, "date": "2024-05-01", "precision": "year"}])
    with pytest.raises(ValidationError, match="time is only meaningful"):
        Chronology(matter="m", entries=[{**base, "date": "2024-05-01", "precision": "month",
                                         "time": "10:00"}])
    with pytest.raises(ValidationError):
        Chronology(matter="m", entries=[{**base, "date": "2024-05-01", "sources": []}])


def test_date_labels(corr, aff):
    by = {e.id: e for e in corr.entries + aff.entries}
    assert by["complaint-email"].date_label() == "19 Aug 2024 16:42"
    assert by["verbal-assurance"].date_label() == "May 2024"


def test_merge_unions_sources_and_sorts(corr, aff):
    m = merge(corr, aff)
    assert len(m.entries) == 6 + 4 - 1  # msa-signed appears in both
    signed = next(e for e in m.entries if e.id == "msa-signed")
    assert [s.label() for s in signed.sources] == ["MSA, AB-1", "Lim affidavit (1st), [6]"]
    assert [e.id for e in m.entries][:3] == ["msa-signed", "verbal-assurance", "po-issued"]
    # month-precision May sorts after 1 Mar and before 14 Jun
    assert m.entries[1].date == date(2024, 5, 1)


def test_merge_dedupes_by_fact_when_ids_differ(corr):
    other = Chronology(matter=corr.matter, entries=[{
        "id": "different-id", "date": "2024-06-14",
        "event": "Beta issued Purchase Order 4471 for 2,000 units.",
        "actors": ["Beta Pte Ltd"], "sources": [{"doc": "Lim affidavit (1st)", "pincite": "[9]"}]}])
    m = merge(corr, other)
    po = [e for e in m.entries if "4471" in e.event]
    assert len(po) == 1 and len(po[0].sources) == 2 and po[0].id == "po-issued"


def test_conflicts(corr, aff):
    cf = conflicts(merge(corr, aff))
    assert len(cf) == 1
    assert cf[0].event_key == "tuas-inspection"
    assert [e.date for e in cf[0].entries] == [date(2024, 9, 3), date(2024, 9, 5)]
    assert "03 Sep 2024" in cf[0].describe() and "Beta Pte Ltd" in cf[0].describe()
    assert conflicts(corr) == []  # msa-execution key agrees across sources


def test_gaps(corr, aff):
    g = gaps(merge(corr, aff), days=300)
    assert len(g) == 1
    assert (g[0].before.id, g[0].after.id) == ("stop-payment", "lod")
    assert g[0].days == (date(2025, 11, 14) - date(2024, 9, 30)).days


def test_lint(corr, aff):
    ws = lint(merge(corr, aff))
    assert ws == []  # the examples are clean
    dirty = Chronology(matter="m", entries=[
        {"id": "a", "date": "2024-01-01",
         "event": "Meeting between Tan and Lim at the Tuas facility took place?",
         "sources": [{"doc": "d"}], "disputed": True},
        {"id": "b", "date": "2024-01-01", "precision": "approx",
         "event": "Meeting between Tan and Lim at the Tuas facility took place, per Lim.",
         "actors": ["x"], "sources": [{"doc": "d", "pincite": "p1"}]},
    ])
    ws = lint(dirty)
    assert any("no pincite" in w for w in ws)
    assert any("asserted_by" in w for w in ws)
    assert any("question" in w for w in ws)
    assert any("approximate date" in w for w in ws)
    assert any("look like the same entry" in w for w in ws)


def test_render(corr, aff):
    md = render_markdown(merge(corr, aff))
    assert "| May 2024 | **[DISPUTED: Beta Pte Ltd]** Tan allegedly" in md
    assert "| Notes |" in md
    csv_text = render_csv(corr)
    assert csv_text.splitlines()[0].startswith("id,date,precision")
    assert "complaint-email,2024-08-19,day,16:42" in csv_text


def test_cli(tmp_path, capsys):
    a, b = str(EX / "from-correspondence.yaml"), str(EX / "from-affidavit.yaml")
    assert main(["validate", a, b]) == 0
    assert main(["conflicts", a, b]) == 1
    assert main(["lint", a, b]) == 1  # conflict present
    assert main(["lint", a]) == 0
    out = tmp_path / "merged.yaml"
    assert main(["merge", a, b, "-o", str(out)]) == 0
    merged = load_chronology(out)
    assert len(merged.entries) == 9
    assert main(["render", str(out), "--format", "csv"]) == 0
    assert main(["gaps", str(out), "--days", "300"]) == 0
    assert "stop-payment" in capsys.readouterr().out
