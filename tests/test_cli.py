import io

from semverparse.cli import main


def test_valid_file_prints_each_version(tmp_path, capsys):
    path = tmp_path / "versions.txt"
    path.write_text("# releases\n1.0.0\n\n2.1.0-rc.1+build.7\n", encoding="utf-8")
    assert main([str(path)]) == 0
    out = capsys.readouterr()
    assert out.out.splitlines() == ["1.0.0", "2.1.0-rc.1+build.7"]
    assert out.err == ""


def test_invalid_entry_reports_line_and_caret(tmp_path, capsys):
    path = tmp_path / "versions.txt"
    path.write_text("1.0.0\n1.2\n", encoding="utf-8")
    assert main([str(path)]) == 1
    out = capsys.readouterr()
    assert out.out.splitlines() == ["1.0.0"]
    err_lines = out.err.splitlines()
    assert err_lines[0].startswith(f"{path}:2:4: ")
    assert err_lines[1] == "  1.2"
    assert err_lines[2] == "     ^"


def test_every_bad_line_is_reported(tmp_path, capsys):
    path = tmp_path / "versions.txt"
    path.write_text("v1.0.0\n1.0.0\n01.0.0\n", encoding="utf-8")
    assert main([str(path)]) == 1
    err = capsys.readouterr().err
    assert f"{path}:1:1: " in err
    assert f"{path}:3:1: " in err


def test_reads_stdin_when_no_argument(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("1.0.0\nbad\n"))
    assert main([]) == 1
    out = capsys.readouterr()
    assert out.out.splitlines() == ["1.0.0"]
    assert "<stdin>:2:1: " in out.err


def test_dash_means_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("3.2.1\n"))
    assert main(["-"]) == 0
    assert capsys.readouterr().out == "3.2.1\n"
