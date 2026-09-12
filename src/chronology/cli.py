"""CLI: validate, schema, lint, merge, render, gaps, conflicts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from .analyse import conflicts, gaps, lint
from .merge import merge
from .models import json_schema, load_chronology
from .render import render_csv, render_markdown


def _load(path: Path):
    try:
        return load_chronology(path)
    except ValidationError as e:
        print(f"invalid chronology {path}:\n{e}", file=sys.stderr)
        sys.exit(2)


def _load_many(paths: list[Path]):
    cs = [_load(p) for p in paths]
    return cs[0] if len(cs) == 1 else merge(*cs)


def cmd_validate(a):
    for p in a.chronology:
        c = _load(p)
        print(f"ok  {p}  ({c.matter}, {len(c.entries)} entries)")
    return 0


def cmd_schema(a):
    print(json.dumps(json_schema(), indent=2))
    return 0


def cmd_lint(a):
    c = _load_many(a.chronology)
    ws = lint(c)
    for w in ws:
        print(f"warn: {w}")
    cf = conflicts(c)
    for x in cf:
        print(f"CONFLICT: {x.describe()}")
    print(f"{len(ws)} warning(s), {len(cf)} conflict(s)")
    return 1 if (cf or (ws and a.strict)) else 0


def cmd_merge(a):
    c = merge(*[_load(p) for p in a.chronology], matter=a.matter)
    text = yaml.safe_dump(c.model_dump(mode="json", exclude_none=True), sort_keys=False,
                          allow_unicode=True, width=100)
    if a.output:
        a.output.write_text(text, encoding="utf-8")
        print(f"wrote {a.output} ({len(c.entries)} entries)")
    else:
        print(text)
    return 0


def cmd_render(a):
    c = _load_many(a.chronology)
    print(render_csv(c) if a.format == "csv" else render_markdown(c, show_ids=a.ids))
    return 0


def cmd_gaps(a):
    c = _load_many(a.chronology)
    for g in gaps(c, days=a.days):
        print(f"{g.days:4} days  {g.before.date} ({g.before.id}) -> {g.after.date} ({g.after.id})")
    return 0


def cmd_conflicts(a):
    c = _load_many(a.chronology)
    cf = conflicts(c)
    for x in cf:
        print(x.describe())
    return 1 if cf else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chronology", description="Litigation chronologies as data.")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("chronology", type=Path, nargs="+")
    v.set_defaults(fn=cmd_validate)

    s = sub.add_parser("schema")
    s.set_defaults(fn=cmd_schema)

    li = sub.add_parser("lint", help="pincites, disputed flags, near-duplicates, conflicts")
    li.add_argument("chronology", type=Path, nargs="+")
    li.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    li.set_defaults(fn=cmd_lint)

    m = sub.add_parser("merge", help="merge several files into one")
    m.add_argument("chronology", type=Path, nargs="+")
    m.add_argument("-o", "--output", type=Path)
    m.add_argument("--matter")
    m.set_defaults(fn=cmd_merge)

    r = sub.add_parser("render")
    r.add_argument("chronology", type=Path, nargs="+")
    r.add_argument("--format", choices=["md", "csv"], default="md")
    r.add_argument("--ids", action="store_true", help="show entry ids in markdown")
    r.set_defaults(fn=cmd_render)

    g = sub.add_parser("gaps", help="periods with no day-precision entries")
    g.add_argument("chronology", type=Path, nargs="+")
    g.add_argument("--days", type=int, default=60)
    g.set_defaults(fn=cmd_gaps)

    cf = sub.add_parser("conflicts", help="same event_key, different dates")
    cf.add_argument("chronology", type=Path, nargs="+")
    cf.set_defaults(fn=cmd_conflicts)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
