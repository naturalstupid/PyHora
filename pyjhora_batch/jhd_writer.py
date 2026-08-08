"""Write a Jagannatha Hora ``.jhd`` data file from a BirthRecord.

PyJHora itself has no JHD import/export — it only shares JHora's *calculations*.
So this is a fresh serializer, calibrated byte-for-byte against a .jhd exported
by the Jagannatha Hora Windows app on 2026-07-29, read back alongside the app's
own on-screen rendering of that same file. Shown here on the reference chart
(15 Jun 1985, 10:30:00, 23.5N 75.75E, +5:30)::

    file                      app displays
    ----------------------    ---------------------------------
    6 / 15 / 1985             June 15, 1985
    10.300000000000000        10:30:00
    -5.300000                 5:30:00 (East of GMT)
    -75.450000                75 E 45' 00"
    23.300000                 23 N 30' 00"
    Ujjain / India            Ujjain, India

Encoding rules, all confirmed by that pair:

* Every angular/temporal field is PACKED sexagesimal ``D.MMSS`` — the digits
  after the point are literally the minutes and seconds, not a fraction.
  10:30:00 -> ``15.43``; 75 deg 48' -> ``75.48``. The decimal-degrees reading is
  ruled out because it would render as 15:43 -> ``15.716667`` and
  75 deg 48' -> ``75.800000``, neither of which is in the file.
* The ONE exception is lines 9/10, which repeat the timezone as plain DECIMAL
  hours (``-5.500000`` alongside the packed ``-5.300000`` on line 5).
* Line 4 (time) is printed with 15 decimals, lines 5-7 with 6.
* Sign conventions differ from the usual: timezone East-of-Greenwich is
  NEGATIVE (India +5:30 -> ``-5.300000``); longitude East is NEGATIVE;
  latitude North is POSITIVE.
* Lines 13/14 are CITY and COUNTRY, not name and place. The person's name lives
  in the FILENAME only — JHora never stores it inside the file.
* Line endings are CRLF.

The 18-line layout (one value per line):
    1  month            10  timezone decimal (repeat)
    2  day              11  0
    3  year             12  105  (country index; 105 = India)
    4  time H.MMSS      13  city
    5  timezone H.MM    14  country
    6  longitude D.MMSS 15  1        (chart style flag)
    7  latitude  D.MMSS 16  1013.250000 (pressure, hPa)
    8  0.000000 (alt)   17  20.000000   (temperature, C)
    9  timezone decimal 18  1

An earlier transcription of a 1948 export (pasted as text, never as a file)
appeared to show decimal degrees and briefly drove this module to write
decimal. That transcription was wrong — it contained ``-79.099540``, which is
not a legal packed value (95 seconds) nor consistent with this verified export.
Trust the file on disk, not the paste.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_COUNTRY = "India"
COUNTRY_INDEX = "105"      # JHora's atlas index for India (line 12)


def _pack_dms(value: float, *, seconds: bool = True) -> str:
    """Decimal degrees/hours -> JHora packed ``D.MMSS00`` magnitude string.

    Sign is handled by the caller; this returns the absolute-value body.
    With ``seconds=False`` only arc-minutes are encoded (used for timezone,
    matching the reference writer which rounds tz to the minute).
    """
    v = abs(float(value))
    d = int(v)
    minutes_full = (v - d) * 60.0
    m = int(minutes_full)
    if seconds:
        s = round((minutes_full - m) * 60.0)
    else:
        m = round(minutes_full)
        s = 0
    # normalize any rounding carry so MM<60 and SS<60
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{d}.{m:02d}{s:02d}00"


def _timezone_field(tz_hours: float) -> str:
    """Line 5: timezone packed ``H.MM``, East (positive offset) negative."""
    body = _pack_dms(tz_hours, seconds=False)
    return f"-{body}" if tz_hours >= 0 else body


def _timezone_decimal_field(tz_hours: float) -> str:
    """Lines 9/10: the same timezone as decimal hours, East still negative."""
    return f"{-float(tz_hours):f}"


def _longitude_field(longitude: float) -> str:
    """Line 6: longitude packed ``D.MMSS``; East (positive) is negative here."""
    body = _pack_dms(longitude)
    return f"-{body}" if longitude >= 0 else body


def _latitude_field(latitude: float) -> str:
    """Line 7: latitude packed ``D.MMSS``; North (positive) stays positive."""
    body = _pack_dms(latitude)
    return body if latitude >= 0 else f"-{body}"


def _time_field(time_of_birth: str) -> str:
    """Line 4: clock time packed ``H.MMSS``, printed with 15 decimals.

    Built as a string rather than via ``float(...):.15f``: the round trip is
    lossy for values like 15:45, which comes back as ``15.449999999999999`` —
    digits an importer reading MM/SS positionally would see as 44 min 99 sec.
    """
    hh, mm, ss = (int(x) for x in time_of_birth.split(":"))
    return f"{hh}.{mm:02d}{ss:02d}00".ljust(len(str(hh)) + 1 + 15, "0")


def _place_fields(record) -> tuple[str, str]:
    """Lines 13/14: city and country.

    JHora keeps the person's name in the filename, never in the file. Records
    carry a single free-text place ("Ujjain, Madhya Pradesh") and no
    country, so the whole string goes on the city line and the country falls
    back to India — the app displays them joined, "<city>, <country>".
    """
    country = getattr(record, "country", "") or DEFAULT_COUNTRY
    return record.place_name, country


def build_jhd(record) -> str:
    """Return the JHD file contents (str) for a BirthRecord, CRLF-terminated."""
    year, month, day = (int(x) for x in record.date_of_birth.split(","))
    city, country = _place_fields(record)

    lines = [
        str(month),
        str(day),
        str(year),
        _time_field(record.time_of_birth),
        _timezone_field(record.timezone),
        _longitude_field(record.longitude),
        _latitude_field(record.latitude),
        "0.000000",              # altitude / observer height
        # tz repeated twice more, but decimal instead of packed
        _timezone_decimal_field(record.timezone),
        _timezone_decimal_field(record.timezone),
        "0",
        COUNTRY_INDEX,
        city,
        country,
        "1",                     # chart style flag
        "1013.250000",           # atmospheric pressure (hPa)
        "20.000000",             # temperature (C)
        "1",
    ]
    return "\r\n".join(lines) + "\r\n"


def write_jhd(record, out_path) -> Path:
    """Write ``record`` as a .jhd file at ``out_path`` and return the path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" so the CRLF pairs built above survive verbatim on every OS
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(build_jhd(record))
    return out_path
