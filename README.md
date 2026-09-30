# semverparse

A strict parser and pretty printer for Semantic Versioning 2.0.0 strings,
built for one reason: when a version string is rejected, most tools just
say "invalid" and leave you to find the typo yourself. This one points at
the exact character.

## The problem

Version strings show up everywhere as bare text: CI matrix entries, lock
files, changelog headers, a git tag pasted into a config. The SemVer spec
(https://semver.org) is precise about what's legal, but common mistakes
slip through constantly:

- a leading `v` (`v1.2.3` is a git tag convention, not a SemVer string)
- leading zeros (`1.02.3`, or `1.0.0-alpha.01`)
- empty identifiers from a stray double dot (`1.0.0-beta..1`)
- underscores or other stray punctuation (`1.0.0-beta_1`)

`semverparse` validates against the full grammar and, on failure, raises
an exception that already knows its own line and column, so you don't
have to eyeball a forty-character string looking for the problem.

## Usage as a library

    >>> from semverparse import parse_version, format_version
    >>> version = parse_version("1.4.2-rc.1+build.987")
    >>> version.major, version.minor, version.patch
    (1, 4, 2)
    >>> version.prerelease
    ('rc', '1')
    >>> format_version(version)
    '1.4.2-rc.1+build.987'

Failures raise `SemverSyntaxError`, which carries `pos` (0-based offset),
`column` (1-based), and a `.render()` method that builds the diagnostic:

    >>> from semverparse import SemverSyntaxError
    >>> try:
    ...     parse_version("v1.2.3")
    ... except SemverSyntaxError as err:
    ...     print(err.render())
    ...
    line 1, column 1: expected the major version number, found 'v'
      v1.2.3
      ^

`Version` instances compare and sort by SemVer precedence rules (build
metadata is ignored, as the spec requires):

    >>> parse_version("1.0.0-alpha") < parse_version("1.0.0-alpha.1")
    True
    >>> parse_version("1.0.0-beta") < parse_version("1.0.0")
    True
    >>> parse_version("1.0.0+build1") == parse_version("1.0.0+build2")
    True

## Command-line checker

`semverparse` also installs a small CLI that validates every version in a
file, one per line (blank lines and `#` comments are skipped), and prints
the canonical form of each valid entry:

    $ cat versions.txt
    1.0.0
    1.2.3-beta.1
    1.2.3-01
    v2.0.0

    $ python -m semverparse versions.txt
    1.0.0
    1.2.3-beta.1
    versions.txt:3:7: numeric prerelease identifiers must not have leading zeros (found '01')
      1.2.3-01
            ^
    versions.txt:4:1: expected the major version number, found 'v'
      v2.0.0
      ^

The exit code is 1 if any line failed to parse, 0 otherwise, so it works
as a CI check. Reading from stdin works with `-` or no argument at all.

## Status

Early skeleton: the parser, printer, and precedence comparison cover the
full SemVer 2.0.0 grammar and are meant to be used.

Tests live in `tests/` and run with `pytest`, which is only needed for
development; the library itself has no dependencies.

## License

MIT, see LICENSE.
