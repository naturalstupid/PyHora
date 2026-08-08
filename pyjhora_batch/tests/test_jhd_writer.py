from pyjhora_batch.jhd_writer import build_jhd, write_jhd, _pack_dms
from pyjhora_batch.wrapper import BirthRecord


def _lines(record_dict):
    return build_jhd(BirthRecord.from_dict(record_dict)).splitlines()


def test_reference_chart(base_record_dict):
    lines = _lines(base_record_dict)
    assert lines == [
        "6", "15", "1985",
        "10.300000000000000",   # time  packed H.MMSS, 15 dp
        "-5.300000",            # tz    packed H.MM, East negative
        "-75.450000",           # lon   packed D.MMSS, East negative
        "23.300000",            # lat   packed D.MMSS, North positive
        "0.000000",
        "-5.500000", "-5.500000",   # tz again, decimal hours
        "0", "105",
        "Ujjain", "India",    # city, country -- the name is in the filename
        "1", "1013.250000", "20.000000", "1",
    ]
    assert len(lines) == 18


def test_full_body_layout_is_byte_exact(base_record_dict):
    """The whole file, CRLF included.

    The field order, packing and sign conventions asserted here were derived
    byte-for-byte from a .jhd written by the Jagannatha Hora Windows app and
    the app's own rendering of it; see the jhd_writer module docstring. The
    fixture is a synthetic chart, so this guards the layout, not one export.
    """
    assert build_jhd(BirthRecord.from_dict(base_record_dict)) == (
        "6\r\n15\r\n1985\r\n"
        "10.300000000000000\r\n"
        "-5.300000\r\n"
        "-75.450000\r\n"
        "23.300000\r\n"
        "0.000000\r\n"
        "-5.500000\r\n-5.500000\r\n"
        "0\r\n105\r\n"
        "Ujjain\r\nIndia\r\n"
        "1\r\n1013.250000\r\n20.000000\r\n1\r\n"
    )


def test_crlf_line_endings(base_record_dict, tmp_path):
    out = write_jhd(BirthRecord.from_dict(base_record_dict), tmp_path / "x.jhd")
    raw = out.read_bytes()
    assert raw.count(b"\r\n") == 18
    assert b"\n" not in raw.replace(b"\r\n", b"")   # no bare LF anywhere


def test_western_hemisphere_signs():
    # NYC: North lat positive, West lon positive, West tz positive
    lines = _lines({
        "date_of_birth": "2000,1,1", "time_of_birth": "06:05:09", "place_name": "NYC",
        "latitude": 40.7128, "longitude": -74.006, "timezone": -5, "gender": 1,
    })
    assert lines[3] == "6.050900000000000"   # time 06:05:09 packed H.MMSS
    assert lines[4] == "5.000000"            # tz positive for west
    assert lines[5] == "74.002200"           # lon positive for west
    assert lines[6] == "40.424600"           # lat positive for north
    assert lines[8] == lines[9] == "5.000000"


def test_southern_latitude_negative():
    lines = _lines({
        "date_of_birth": "1990,1,1", "time_of_birth": "00:00:00", "place_name": "Sydney",
        "latitude": -33.8688, "longitude": 151.2093, "timezone": 10, "gender": 1,
    })
    assert lines[6].startswith("-33.")   # south latitude negative
    assert lines[5].startswith("-151.")  # east longitude negative


def test_place_and_country_lines():
    lines = _lines({
        "name": "Someone",
        "date_of_birth": "1990,1,1", "time_of_birth": "00:00:00", "place_name": "OnlyPlace",
        "latitude": 1.0, "longitude": 2.0, "timezone": 5.5,
    })
    assert lines[12] == "OnlyPlace"   # city
    assert lines[13] == "India"       # country default
    assert "Someone" not in lines     # the person's name is never in the file


def test_pack_dms_basic():
    assert _pack_dms(75.78) == "75.464800"     # 0.78*60=46.8' -> 46'48"
    assert _pack_dms(27.73) == "27.434800"


def test_pack_dms_seconds_carry():
    # a value whose seconds round to 60 must carry into minutes, not print ":60"
    packed = _pack_dms(10.0 + 59.996 / 60.0)   # ~10 deg 59' 59.76" -> carries
    d, frac = packed.split(".")
    mm, ss = frac[:2], frac[2:4]
    assert int(mm) < 60 and int(ss) < 60


def test_timezone_rounds_to_minute():
    assert _pack_dms(5.5, seconds=False) == "5.300000"
