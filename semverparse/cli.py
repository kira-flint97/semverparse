"""Command-line checker: validate every version in a file, one per line."""

from __future__ import annotations

import sys
from typing import Iterator, Tuple

from .parser import SemverSyntaxError, format_version, parse_version


def _entries(text: str) -> Iterator[Tuple[int, str]]:
    for line_no, raw in enumerate(text.splitlines(), start=1):
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        yield line_no, entry


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if not argv or argv[0] == "-":
        source_text = sys.stdin.read()
        label = "<stdin>"
    else:
        label = argv[0]
        with open(label, "r", encoding="utf-8") as handle:
            source_text = handle.read()

    exit_code = 0
    for line_no, entry in _entries(source_text):
        try:
            version = parse_version(entry)
        except SemverSyntaxError as err:
            exit_code = 1
            print(err.render(line=line_no, filename=label), file=sys.stderr)
        else:
            print(format_version(version))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
