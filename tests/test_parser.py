import pytest

from semverparse import SemverSyntaxError, Version, format_version, parse_version


VALID = [
    "0.0.4",
    "1.2.3",
    "10.20.30",
    "1.1.2-prerelease+meta",
    "1.1.2+meta",
    "1.1.2+meta-valid",
    "1.0.0-alpha",
    "1.0.0-beta",
    "1.0.0-alpha.beta",
    "1.0.0-alpha.beta.1",
    "1.0.0-alpha.1",
    "1.0.0-alpha0.valid",
    "1.0.0-alpha.0valid",
    "1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay",
    "1.0.0-rc.1+build.1",
    "1.0.0-0",
    "1.0.0-0a",
    "1.0.0-01a",
    "1.0.0-x-y-z.--",
    "1.0.0+0.build.1-rc.10000aaa-kk-0.1",
    "1.0.0+001",
    "1.0.0+21AF26D3--117B344092BD",
    "99999999999999999999999.999999999999999999.99999999999999999",
]


@pytest.mark.parametrize("text", VALID)
def test_valid_versions_round_trip(text):
    assert format_version(parse_version(text)) == text


def test_components_are_split():
    v = parse_version("1.2.3-alpha.1+build.5")
    assert (v.major, v.minor, v.patch) == (1, 2, 3)
    assert v.prerelease == ("alpha", "1")
    assert v.build == ("build", "5")


# (text, zero-based offset of the first offending character)
INVALID = [
    ("", 0),
    ("1", 1),
    ("1.2", 3),
    ("1.2.", 4),
    ("1..2", 2),
    ("v1.0.0", 0),
    ("1.0.x", 4),
    ("01.0.0", 0),
    ("1.01.0", 2),
    ("1.0.00", 4),
    ("-1.0.0", 0),
    ("1.0.0.0", 5),
    ("1.0.0 ", 5),
    (" 1.0.0", 0),
    ("1.0.0-", 6),
    ("1.0.0-01", 6),
    ("1.0.0-alpha.01", 12),
    ("1.0.0-a..b", 8),
    ("1.0.0-a.", 8),
    ("1.0.0-_", 6),
    ("1.0.0-a_b", 7),
    ("1.0.0-alpha!", 11),
    ("1.0.0+", 6),
    ("1.0.0+a..b", 8),
    ("1.0.0+a_b", 7),
    ("1.0.0-a+b+c", 9),
]


@pytest.mark.parametrize("text,pos", INVALID)
def test_invalid_versions_report_position(text, pos):
    with pytest.raises(SemverSyntaxError) as info:
        parse_version(text)
    assert info.value.pos == pos
    assert info.value.column == pos + 1
    assert info.value.source == text


def test_error_is_a_value_error():
    with pytest.raises(ValueError):
        parse_version("nope")


def test_non_ascii_digits_are_rejected():
    with pytest.raises(SemverSyntaxError) as info:
        parse_version("１.0.0")
    assert info.value.pos == 0


def test_render_with_filename_points_at_failure():
    with pytest.raises(SemverSyntaxError) as info:
        parse_version("1.2")
    lines = info.value.render(line=3, filename="versions.txt").split("\n")
    assert lines[0].startswith("versions.txt:3:4: ")
    assert lines[1] == "  1.2"
    assert lines[2] == "     ^"


def test_render_without_filename():
    with pytest.raises(SemverSyntaxError) as info:
        parse_version("v1.0.0")
    assert info.value.render().startswith("line 1, column 1: ")


def test_spec_precedence_chain():
    chain = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "2.0.0",
        "2.1.0",
        "2.1.1",
    ]
    versions = [parse_version(s) for s in chain]
    for lower, higher in zip(versions, versions[1:]):
        assert lower < higher
        assert higher > lower
        assert lower != higher
    assert sorted(reversed(versions)) == versions


def test_numeric_components_compare_as_numbers():
    assert parse_version("1.9.0") < parse_version("1.10.0")
    assert parse_version("1.0.0-rc.9") < parse_version("1.0.0-rc.10")


def test_numeric_identifiers_sort_below_alphanumeric():
    assert parse_version("1.0.0-99") < parse_version("1.0.0-a")


def test_build_metadata_is_ignored_for_precedence():
    a = parse_version("1.0.0+a")
    b = parse_version("1.0.0+b")
    assert a == b
    assert hash(a) == hash(b)
    assert not a < b and not b < a
    assert format_version(a) != format_version(b)


def test_compare_with_other_types():
    v = parse_version("1.0.0")
    assert v != "1.0.0"
    with pytest.raises(TypeError):
        v < "1.0.0"


def test_version_can_be_built_directly():
    assert format_version(Version(1, 2, 3, ("rc", "1"), ("x",))) == "1.2.3-rc.1+x"
