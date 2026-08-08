import argparse

import pytest

from pyjhora_batch import cli
from pyjhora_batch.engine import default_worker_count


# --- argument parsing --------------------------------------------------------

def test_parse_workers_auto():
    assert cli._parse_workers("auto") == default_worker_count()


def test_parse_workers_int():
    assert cli._parse_workers("4") == 4


@pytest.mark.parametrize("bad", ["0", "-1", "two", "1.5"])
def test_parse_workers_invalid(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        cli._parse_workers(bad)


def test_parser_defaults(tmp_path):
    args = cli.build_parser().parse_args(["in.csv"])
    assert args.workers == 1 and args.out_dir.name == "reports"
    assert not args.no_pdf and not args.no_jhd


# --- main() exit codes (JHD-only for speed) ---------------------------------

def _csv(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


_HEADER = "name,date_of_birth,time_of_birth,place,latitude,longitude,timezone,gender\n"
_GOOD = _HEADER + 'A,"1985,6,15",10:30:00,Ujjain,23.5,75.75,5.5,male\n'
_MIXED = _GOOD + 'Bad,"2000,1,1",06:00:00,Nowhere,,,5.5,male\n'


def test_main_all_valid_exit_0(tmp_path):
    src = _csv(tmp_path, "good.csv", _GOOD)
    code = cli.main([str(src), "-o", str(tmp_path / "out"), "--no-pdf", "-q"])
    assert code == 0
    assert (tmp_path / "out" / "A_1985-6-15.jhd").is_file()


def test_main_failures_exit_1(tmp_path):
    src = _csv(tmp_path, "mixed.csv", _MIXED)
    code = cli.main([str(src), "-o", str(tmp_path / "out"), "--no-pdf", "-q"])
    assert code == 1


def test_main_allow_failures_exit_0(tmp_path):
    src = _csv(tmp_path, "mixed.csv", _MIXED)
    code = cli.main([str(src), "-o", str(tmp_path / "out"), "--no-pdf", "-q",
                     "--allow-failures"])
    assert code == 0


def test_main_missing_input_exit_2(tmp_path):
    code = cli.main([str(tmp_path / "nope.csv"), "-o", str(tmp_path / "out"), "-q"])
    assert code == 2


def test_main_no_outputs_exit_2(tmp_path):
    src = _csv(tmp_path, "good.csv", _GOOD)
    code = cli.main([str(src), "-o", str(tmp_path / "out"),
                     "--no-pdf", "--no-jhd", "--no-txt", "-q"])
    assert code == 2


def test_main_txt_alone_is_a_valid_output(tmp_path):
    """Suppressing the PDF and JHD is fine as long as the text report remains."""
    src = _csv(tmp_path, "good.csv", _GOOD)
    out = tmp_path / "out"
    code = cli.main([str(src), "-o", str(out), "--no-pdf", "--no-jhd", "-q"])
    assert code == 0
    assert list(out.glob("*.txt"))


def test_main_unsupported_extension_exit_2(tmp_path):
    src = _csv(tmp_path, "data.json", "{}")
    code = cli.main([str(src), "-o", str(tmp_path / "out"), "-q"])
    assert code == 2
