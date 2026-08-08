import csv as _csv
import os

import pytest

from pyjhora_batch.engine import (_output_name, _prepare, _slugify, run_batch,
                                  default_worker_count)
from pyjhora_batch.readers.csv_reader import RawRow
from pyjhora_batch.wrapper import BirthRecord


def _raw(n, data):
    return RawRow(row_number=n, line_number=n + 1, data=data)


def _valid(name="A", dob="1985,6,15", **over):
    d = {"name": name, "date_of_birth": dob, "time_of_birth": "10:30:00",
         "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75,
         "timezone": 5.5, "gender": "male"}
    d.update(over)
    return d


# --- naming ------------------------------------------------------------------

def test_slugify():
    assert _slugify("Test Person") == "Test_Person"
    assert _slugify("  a/b:c  ") == "a_b_c"
    assert _slugify("") == "chart"


def test_output_name_from_name_and_dob():
    rec = BirthRecord.from_dict(_valid("Jane Doe"))
    assert _output_name(rec, {}) == "Jane_Doe_1985-6-15"


def test_output_name_explicit_column():
    rec = BirthRecord.from_dict(_valid("Jane"))
    assert _output_name(rec, {"output": "custom.pdf"}) == "custom"
    assert _output_name(rec, {"filename": "x/y"}) == "y"


# --- _prepare ----------------------------------------------------------------

def test_prepare_collision_suffix(tmp_path):
    rows = [_raw(1, _valid("Same")), _raw(2, _valid("Same")), _raw(3, _valid("Same"))]
    jobs, invalids = _prepare(rows, tmp_path)
    assert invalids == []
    names = [j.pdf_path.stem for j in jobs]
    assert names == ["Same_1985-6-15", "Same_1985-6-15_2", "Same_1985-6-15_3"]


def test_prepare_isolates_invalid(tmp_path):
    rows = [_raw(1, _valid("Good")),
            _raw(2, {"name": "Bad", "date_of_birth": "1990,1,1"})]  # missing most fields
    jobs, invalids = _prepare(rows, tmp_path)
    assert len(jobs) == 1 and jobs[0].rec.name == "Good"
    assert len(invalids) == 1 and invalids[0].status == "invalid"
    assert invalids[0].row_number == 2


# --- run_batch (JHD-only: fast, no Qt render) --------------------------------

def test_run_batch_jhd_only(tmp_path):
    rows = [_raw(1, _valid("One")), _raw(2, _valid("Two", dob="1985,11,2")),
            _raw(3, {"name": "NoCoords", "date_of_birth": "2000,1,1",
                     "time_of_birth": "06:00:00", "place_name": "Nowhere"})]
    summary = run_batch(rows, tmp_path, write_pdf=False, write_txt=False, verbose=False)

    assert summary.total == 3 and summary.succeeded == 2 and summary.failed == 1
    assert (tmp_path / "One_1985-6-15.jhd").is_file()
    assert (tmp_path / "Two_1985-11-2.jhd").is_file()
    # results are sorted by row number
    assert [r.row_number for r in summary.results] == [1, 2, 3]
    # log + failures artifacts written
    assert (tmp_path / "batch.log").is_file()
    assert (tmp_path / "failures.csv").is_file()


def test_failures_csv_contents(tmp_path):
    rows = [_raw(1, _valid("Good")),
            _raw(2, {"name": "Bad", "date_of_birth": "2000,1,1",
                     "time_of_birth": "06:00:00", "place_name": "Nowhere"})]
    run_batch(rows, tmp_path, write_pdf=False, write_txt=False, verbose=False)
    with (tmp_path / "failures.csv").open() as fh:
        rows_out = list(_csv.DictReader(fh))
    assert len(rows_out) == 1
    row = rows_out[0]
    assert row["_row"] == "2" and row["_status"] == "invalid"
    assert "missing required field" in row["_error"]
    assert row["name"] == "Bad"          # original columns preserved


def test_run_batch_writes_all_three_outputs(tmp_path):
    """One valid row -> a vector .pdf, a .jhd and a .txt, with no Qt involved."""
    summary = run_batch([_raw(1, _valid("Trio"))], tmp_path, verbose=False)
    assert summary.succeeded == 1

    base = tmp_path / "Trio_1985-6-15"
    pdf, jhd, txt = base.with_suffix(".pdf"), base.with_suffix(".jhd"), base.with_suffix(".txt")
    assert pdf.is_file() and jhd.is_file() and txt.is_file()

    result = summary.results[0]
    assert result.output == str(pdf) and result.jhd == str(jhd) and result.txt == str(txt)
    # the vector PDF is orders of magnitude smaller than the screenshot one
    assert pdf.stat().st_size < 1_000_000
    assert pdf.read_bytes().startswith(b"%PDF")
    assert "HOROSCOPE REPORT" in txt.read_text(encoding="utf-8")


def test_run_batch_rejects_unknown_pdf_mode(tmp_path):
    with pytest.raises(ValueError, match="pdf_mode"):
        run_batch([], tmp_path, pdf_mode="screenshots", verbose=False)


def test_txt_only_run_skips_the_pdf(tmp_path):
    run_batch([_raw(1, _valid("TxtOnly"))], tmp_path, write_pdf=False,
              write_jhd_file=False, verbose=False)
    assert (tmp_path / "TxtOnly_1985-6-15.txt").is_file()
    assert not (tmp_path / "TxtOnly_1985-6-15.pdf").exists()


def test_default_worker_count_at_least_one():
    assert default_worker_count() >= 1


@pytest.mark.skipif(os.environ.get("PYJHORA_TEST_PARALLEL") != "1",
                    reason="set PYJHORA_TEST_PARALLEL=1 to run the slow spawn-pool test")
def test_run_batch_parallel_jhd_only(tmp_path):
    rows = [_raw(i, _valid(f"P{i}", dob=f"199{i},1,1")) for i in range(1, 5)]
    summary = run_batch(rows, tmp_path, write_pdf=False, verbose=False, workers=2)
    assert summary.succeeded == 4 and summary.failed == 0
    assert [r.row_number for r in summary.results] == [1, 2, 3, 4]  # re-sorted
    for r in summary.results:
        assert r.jhd is not None and __import__("pathlib").Path(r.jhd).is_file()
