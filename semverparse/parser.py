"""Strict parser for SemVer 2.0.0 version strings.

The grammar and precedence rules follow https://semver.org/ exactly: a
leading "v", a missing patch number, or an underscore in an identifier
are all rejected rather than tolerated. When a string is rejected the
error carries the offset of the first offending character, which is
what lets us print a caret under it.
"""

from __future__ import annotations

from .model import Version

_DIGITS = frozenset("0123456789")
_IDENT_CHARS = frozenset(
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "-"
)


class SemverSyntaxError(ValueError):
    """Raised when a string does not conform to the SemVer 2.0.0 grammar.

    `pos` is the zero-based offset into `source` of the first offending
    character; `column` is the same position as a 1-based column, which
    is what a diagnostic should actually show a person.
    """

    def __init__(self, message: str, source: str, pos: int) -> None:
        self.message = message
        self.source = source
        self.pos = pos
        self.column = pos + 1
        super().__init__(message)

    def render(self, line: int = 1, filename: str | None = None) -> str:
        """Render a diagnostic with the source line and a caret under the failure."""
        if filename:
            where = f"{filename}:{line}:{self.column}"
        else:
            where = f"line {line}, column {self.column}"
        caret = " " * self.pos + "^"
        return f"{where}: {self.message}\n  {self.source}\n  {caret}"

    def __str__(self) -> str:  # pragma: no cover - trivial delegation
        return self.render()


class _Cursor:
    __slots__ = ("text", "pos")

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self) -> str:
        ch = self.peek()
        self.pos += 1
        return ch

    def eof(self) -> bool:
        return self.pos >= len(self.text)


def parse_version(text: str) -> Version:
    """Parse `text` as a SemVer 2.0.0 version string.

    Raises SemverSyntaxError, with `source`/`pos`/`column` set, at the
    first grammar violation encountered.
    """
    cursor = _Cursor(text)
    major = _parse_numeric_component(cursor, "major")
    _expect(cursor, ".", "after major version number")
    minor = _parse_numeric_component(cursor, "minor")
    _expect(cursor, ".", "after minor version number")
    patch = _parse_numeric_component(cursor, "patch")

    prerelease: tuple[str, ...] = ()
    if cursor.peek() == "-":
        cursor.advance()
        prerelease = _parse_dotted_identifiers(
            cursor, "prerelease", numeric_leading_zero_ok=False, terminators={".", "+"}
        )

    build: tuple[str, ...] = ()
    if cursor.peek() == "+":
        cursor.advance()
        build = _parse_dotted_identifiers(
            cursor, "build metadata", numeric_leading_zero_ok=True, terminators={"."}
        )

    if not cursor.eof():
        raise SemverSyntaxError(
            f"unexpected character {cursor.peek()!r} after a complete version",
            text,
            cursor.pos,
        )

    return Version(major=major, minor=minor, patch=patch, prerelease=prerelease, build=build)


def _parse_numeric_component(cursor: _Cursor, name: str) -> int:
    start = cursor.pos
    digits = []
    while cursor.peek() in _DIGITS:
        digits.append(cursor.advance())
    if not digits:
        found = f"{cursor.peek()!r}" if not cursor.eof() else "end of input"
        raise SemverSyntaxError(
            f"expected the {name} version number, found {found}", cursor.text, start
        )
    value = "".join(digits)
    if len(value) > 1 and value[0] == "0":
        raise SemverSyntaxError(
            f"the {name} version number must not have a leading zero (found {value!r})",
            cursor.text,
            start,
        )
    return int(value)


def _expect(cursor: _Cursor, char: str, context: str) -> None:
    if cursor.peek() != char:
        found = f"{cursor.peek()!r}" if not cursor.eof() else "end of input"
        raise SemverSyntaxError(
            f"expected {char!r} {context}, found {found}", cursor.text, cursor.pos
        )
    cursor.advance()


def _scan_identifier(cursor: _Cursor) -> str:
    chars = []
    while cursor.peek() in _IDENT_CHARS:
        chars.append(cursor.advance())
    return "".join(chars)


def _parse_dotted_identifiers(
    cursor: _Cursor, label: str, *, numeric_leading_zero_ok: bool, terminators: set
) -> tuple[str, ...]:
    identifiers = []
    while True:
        start = cursor.pos
        identifier = _scan_identifier(cursor)
        if not identifier:
            stop = cursor.peek()
            if stop and stop not in terminators:
                raise SemverSyntaxError(
                    f"invalid character {stop!r} in {label} identifier", cursor.text, start
                )
            raise SemverSyntaxError(f"{label} identifiers must not be empty", cursor.text, start)
        if (
            not numeric_leading_zero_ok
            and identifier.isdigit()
            and len(identifier) > 1
            and identifier[0] == "0"
        ):
            raise SemverSyntaxError(
                f"numeric {label} identifiers must not have leading zeros (found {identifier!r})",
                cursor.text,
                start,
            )
        identifiers.append(identifier)
        if cursor.peek() == ".":
            cursor.advance()
            continue
        break
    return tuple(identifiers)


def format_version(version: Version) -> str:
    """Render `version` back to its canonical SemVer 2.0.0 string form."""
    core = f"{version.major}.{version.minor}.{version.patch}"
    if version.prerelease:
        core += "-" + ".".join(version.prerelease)
    if version.build:
        core += "+" + ".".join(version.build)
    return core
