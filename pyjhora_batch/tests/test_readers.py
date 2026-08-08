import datetime as dt

from openpyxl import Workbook

from pyjhora_batch.readers.csv_reader import read_csv
from pyjhora_batch.readers.excel_reader import read_excel, _stringify_cell


# --- CSV ---------------------------------------------------------------------

def _write(path, text, encoding="utf-8"):
    path.write_text(text, encoding=encoding)
    return path


def test_csv_basic_rows_and_numbers(tmp_path):
    csv = _write(tmp_path / "a.csv",
                 "name,dob\nAlice,\"1990,1,1\"\nBob,\"1991,2,3\"\n")
    rows = list(read_csv(csv))
    assert [r.row_number for r in rows] == [1, 2]
    assert rows[0].line_number == 2 and rows[1].line_number == 3
    assert rows[0].data["name"] == "Alice"


def test_csv_header_lowercased(tmp_path):
    csv = _write(tmp_path / "b.csv", "Name,DOB\nX,\"2000,1,1\"\n")
    row = next(iter(read_csv(csv)))
    assert set(row.data) == {"name", "dob"}


def test_csv_skips_blank_rows(tmp_path):
    csv = _write(tmp_path / "c.csv", "name,dob\nA,\"2000,1,1\"\n,\nB,\"2001,1,1\"\n")
    rows = list(read_csv(csv))
    assert [r.data["name"] for r in rows] == ["A", "B"]


def test_csv_strips_bom(tmp_path):
    csv = _write(tmp_path / "d.csv", "﻿name,dob\nA,\"2000,1,1\"\n")
    row = next(iter(read_csv(csv)))
    assert "name" in row.data          # BOM stripped from first header


def test_csv_missing_file(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        list(read_csv(tmp_path / "nope.csv"))


# --- Excel -------------------------------------------------------------------

def test_stringify_cell_types():
    assert _stringify_cell(dt.date(1985, 6, 15)) == "1985,6,15"
    assert _stringify_cell(dt.time(4, 5, 30)) == "04:05:30"
    assert _stringify_cell(27.0) == "27"           # whole float -> int text
    assert _stringify_cell(75.783333) == "75.783333"  # precision kept
    assert _stringify_cell(None) == ""
    # Excel time-only cells arrive as a 1899-epoch datetime
    assert _stringify_cell(dt.datetime(1899, 12, 31, 4, 5, 30)) == "04:05:30"
    assert _stringify_cell(dt.datetime(1985, 6, 15, 0, 0, 0)) == "1985,6,15"


def test_excel_reads_typed_cells(tmp_path):
    wb = Workbook(); ws = wb.active
    ws.append(["Name", "Date of Birth", "Time of Birth", "Lat"])
    ws.append(["Devi", dt.date(1978, 7, 9), dt.time(4, 5, 30), 12.9716])
    ws.append([None, None, None, None])            # blank -> skipped
    ws.append(["Ravi", "1965,12,25", "23:10:00", 9.9312])
    path = tmp_path / "s.xlsx"; wb.save(path)

    rows = list(read_excel(path))
    assert [r.data["name"] for r in rows] == ["Devi", "Ravi"]
    assert rows[0].data["date of birth"] == "1978,7,9"
    assert rows[0].data["time of birth"] == "04:05:30"
    assert rows[0].data["lat"] == "12.9716"


def test_space_before_a_quoted_field_is_tolerated(tmp_path):
    """`a, "1998,9,10",b` — a quote after a space is otherwise literal text,
    letting the commas inside split the field and shift every later column."""
    src = tmp_path / "spaced.csv"
    src.write_text(
        "name,date_of_birth,time_of_birth,place,latitude,longitude,timezone,gender\n"
        'Ravi Kumar, "2001,11,3",07:15:00,"Chennai, Tamil Nadu",'
        "27.147869,74.859489,5.5, male\n",
        encoding="utf-8")
    rows = list(read_csv(src))
    assert len(rows) == 1
    data = rows[0].data
    assert data["date_of_birth"] == "2001,11,3"
    assert data["place"] == "Chennai, Tamil Nadu"
    assert data["gender"] == "male"
    assert data["timezone"] == "5.5"
