"""The Version value type and SemVer 2.0.0 precedence ordering."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering


def _sort_key(identifier: str):
    # Per the spec, numeric identifiers always sort below alphanumeric
    # ones, and are compared as integers rather than as text.
    return (0, int(identifier)) if identifier.isdigit() else (1, identifier)


@total_ordering
@dataclass(frozen=True)
class Version:
    """A parsed semantic version.

    Equality and ordering follow SemVer 2.0.0 precedence rules, which
    means build metadata is ignored: `1.0.0+a` and `1.0.0+b` compare
    equal even though they round-trip to different strings.
    """

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    def _precedence_key(self):
        core = (self.major, self.minor, self.patch)
        if not self.prerelease:
            # a release with no prerelease outranks any prerelease of
            # the same major.minor.patch
            return core, (1,)
        return core, (0, tuple(_sort_key(part) for part in self.prerelease))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._precedence_key() == other._precedence_key()

    def __lt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._precedence_key() < other._precedence_key()

    def __hash__(self) -> int:
        return hash(self._precedence_key())
