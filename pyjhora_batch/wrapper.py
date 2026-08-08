"""Reusable wrapper around PyJHora's ChartTabbed for headless/batch PDF generation.

This is Phase 2 of the batch framework: a single clean entry point,
``generate_pdf(record, out_path)``, that the batch engine calls once per input
row. It deliberately treats the GUI as a presentation layer and drives it
programmatically rather than duplicating any horoscope calculations.

Why the setters (and not the constructor kwargs)
-------------------------------------------------
``ChartTabbed.__init__`` documents ``date_of_birth`` / ``time_of_birth`` /
``place_of_birth`` kwargs, but as of V4.8.7 it never applies them: it only uses
them to decide whether to fall back to *now* and an *IP-based location*. Passing
birth details to the constructor therefore silently produces a chart for today
at the host's IP location.

So we construct with networking disabled (``use_internet_for_location_check=
False``) and inject every field through the public setters — ``date_of_birth()``,
``time_of_birth()``, ``place()``, ``gender()``, ``name()`` — which do wire the
values into the widgets that ``compute_horoscope()`` reads. This keeps each
record's own coordinates honored and makes the run fully offline/deterministic.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ChartTabbed needs a QApplication. In headless/batch use we default to Qt's
# offscreen platform; a caller that already created a GUI QApplication is
# respected (see ensure_app).
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication  # noqa: E402

from jhora import config  # noqa: E402
from jhora.ui.horo_chart_tabs import ChartTabbed  # noqa: E402

_DATE_RE = re.compile(r"^\s*\d{1,5},\d{1,2},\d{1,2}\s*$")
_TIME_RE = re.compile(r"^\s*\d{1,2}:\d{1,2}:\d{1,2}\s*$")

# ChartTabbed's gender combo is initially ['Female','Male','Transgender',
# 'No preference'] -> gender() takes that index. We pass the int straight
# through and map a few common strings onto the same ordering.
_GENDER_ALIASES = {
    "female": 0, "f": 0, "woman": 0,
    "male": 1, "m": 1, "man": 1,
    "transgender": 2, "trans": 2, "t": 2,
    "no preference": 3, "none": 3, "na": 3, "n/a": 3, "": 3,
}

# Accepted input column names -> canonical BirthRecord field.
_FIELD_ALIASES = {
    "name": "name", "person": "name", "full_name": "name",
    "date_of_birth": "date_of_birth", "dob": "date_of_birth", "date": "date_of_birth",
    "time_of_birth": "time_of_birth", "tob": "time_of_birth", "time": "time_of_birth",
    "place_name": "place_name", "place": "place_name", "place_of_birth": "place_name",
    "location": "place_name", "city": "place_name",
    "latitude": "latitude", "lat": "latitude",
    "longitude": "longitude", "long": "longitude", "lon": "longitude", "lng": "longitude",
    "timezone": "timezone", "tz": "timezone", "timezone_offset": "timezone",
    "time_zone": "timezone", "utc_offset": "timezone",
    "gender": "gender", "sex": "gender",
    "elevation": "elevation", "altitude": "elevation",
    "chart_type": "chart_type", "chart": "chart_type",
    "language": "language", "lang": "language",
    # --- spouse / marriage compatibility ---
    "spouse_name": "spouse_name", "partner_name": "spouse_name",
    "spouse_date_of_birth": "spouse_date_of_birth", "spouse_dob": "spouse_date_of_birth",
    "partner_dob": "spouse_date_of_birth", "spouse_date": "spouse_date_of_birth",
    "spouse_time_of_birth": "spouse_time_of_birth", "spouse_tob": "spouse_time_of_birth",
    "partner_tob": "spouse_time_of_birth", "spouse_time": "spouse_time_of_birth",
    "spouse_place": "spouse_place_name", "spouse_place_name": "spouse_place_name",
    "spouse_location": "spouse_place_name", "spouse_city": "spouse_place_name",
    "spouse_latitude": "spouse_latitude", "spouse_lat": "spouse_latitude",
    "spouse_longitude": "spouse_longitude", "spouse_long": "spouse_longitude",
    "spouse_lon": "spouse_longitude", "spouse_lng": "spouse_longitude",
    "spouse_timezone": "spouse_timezone", "spouse_tz": "spouse_timezone",
    "spouse_gender": "spouse_gender", "spouse_sex": "spouse_gender",
    "spouse_nakshatra": "spouse_nakshatra", "spouse_star": "spouse_nakshatra",
    "spouse_nakshathra": "spouse_nakshatra",
    "spouse_pada": "spouse_pada", "spouse_paadham": "spouse_pada",
    "spouse_quarter": "spouse_pada",
    "compatibility_method": "compatibility_method", "match_method": "compatibility_method",
}


class RecordError(ValueError):
    """Raised when an input record is missing or has invalid mandatory fields."""


@dataclass
class BirthRecord:
    """A validated set of birth details for one horoscope."""

    date_of_birth: str            # "YYYY,M,D"  e.g. "1985,6,15"
    time_of_birth: str            # "HH:MM:SS"  e.g. "15:43:00"
    place_name: str
    latitude: float
    longitude: float
    timezone: float               # hours offset from UTC, e.g. 5.5
    name: str = ""
    gender: int = 3               # 0=Female,1=Male,2=Transgender,3=No preference
    elevation: float = 0.0
    chart_type: str = "south_indian"
    language: str = "English"

    # --- spouse, for marriage compatibility (all optional) ---
    # Compatibility needs only the pair's nakshatra + pada. Supply the spouse's
    # birth details and they are derived exactly; or give the star directly when
    # the birth time is unknown (pada is ~6 hours of Moon travel, so a guessed
    # time makes the pada — and the score — unreliable).
    spouse_name: str = ""
    spouse_date_of_birth: str = ""     # "YYYY,M,D"
    spouse_time_of_birth: str = ""     # "HH:MM:SS"
    spouse_place_name: str = ""
    spouse_latitude: Optional[float] = None
    spouse_longitude: Optional[float] = None
    spouse_timezone: Optional[float] = None
    spouse_gender: Optional[int] = None
    spouse_nakshatra: Optional[str] = None   # 1..27, or a name ("Swaathi")
    spouse_pada: Optional[int] = None        # 1..4
    compatibility_method: str = ""            # "north" | "south"; else from chart_type

    def __post_init__(self):
        self.date_of_birth = str(self.date_of_birth).strip()
        self.time_of_birth = str(self.time_of_birth).strip()
        self.place_name = str(self.place_name).strip()
        if not _DATE_RE.match(self.date_of_birth):
            raise RecordError(f"date_of_birth must be 'YYYY,M,D' (got {self.date_of_birth!r})")
        if not _TIME_RE.match(self.time_of_birth):
            raise RecordError(f"time_of_birth must be 'HH:MM:SS' (got {self.time_of_birth!r})")
        if not self.place_name:
            raise RecordError("place_name is required")
        try:
            self.latitude = float(self.latitude)
            self.longitude = float(self.longitude)
            self.timezone = float(self.timezone)
            self.elevation = float(self.elevation)
        except (TypeError, ValueError) as exc:
            raise RecordError(f"latitude/longitude/timezone/elevation must be numeric ({exc})") from exc
        if not (-90.0 <= self.latitude <= 90.0):
            raise RecordError(f"latitude out of range: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise RecordError(f"longitude out of range: {self.longitude}")
        if not (-14.0 <= self.timezone <= 14.0):
            raise RecordError(f"timezone out of range: {self.timezone}")
        self.gender = _normalize_gender(self.gender)
        self._validate_spouse()

    def _validate_spouse(self) -> None:
        """Validate whatever spouse fields were supplied; all are optional."""
        self.spouse_name = str(self.spouse_name or "").strip()
        self.spouse_place_name = str(self.spouse_place_name or "").strip()
        self.spouse_date_of_birth = str(self.spouse_date_of_birth or "").strip()
        self.spouse_time_of_birth = str(self.spouse_time_of_birth or "").strip()

        if self.spouse_date_of_birth and not _DATE_RE.match(self.spouse_date_of_birth):
            raise RecordError("spouse_date_of_birth must be 'YYYY,M,D' "
                              f"(got {self.spouse_date_of_birth!r})")
        if self.spouse_time_of_birth and not _TIME_RE.match(self.spouse_time_of_birth):
            raise RecordError("spouse_time_of_birth must be 'HH:MM:SS' "
                              f"(got {self.spouse_time_of_birth!r})")

        for field_name in ("spouse_latitude", "spouse_longitude", "spouse_timezone"):
            value = getattr(self, field_name)
            if value in (None, ""):
                setattr(self, field_name, None)
                continue
            try:
                setattr(self, field_name, float(value))
            except (TypeError, ValueError) as exc:
                raise RecordError(f"{field_name} must be numeric ({exc})") from exc
        if self.spouse_latitude is not None and not (-90.0 <= self.spouse_latitude <= 90.0):
            raise RecordError(f"spouse_latitude out of range: {self.spouse_latitude}")
        if self.spouse_longitude is not None and not (-180.0 <= self.spouse_longitude <= 180.0):
            raise RecordError(f"spouse_longitude out of range: {self.spouse_longitude}")
        if self.spouse_timezone is not None and not (-14.0 <= self.spouse_timezone <= 14.0):
            raise RecordError(f"spouse_timezone out of range: {self.spouse_timezone}")

        if self.spouse_gender not in (None, ""):
            self.spouse_gender = _normalize_gender(self.spouse_gender)
        else:
            self.spouse_gender = None

        if self.spouse_pada not in (None, ""):
            try:
                self.spouse_pada = int(self.spouse_pada)
            except (TypeError, ValueError) as exc:
                raise RecordError(f"spouse_pada must be 1-4 ({exc})") from exc
            if not 1 <= self.spouse_pada <= 4:
                raise RecordError(f"spouse_pada must be 1-4 (got {self.spouse_pada})")
        else:
            self.spouse_pada = None

        if self.spouse_nakshatra in (None, ""):
            self.spouse_nakshatra = None
        else:
            self.spouse_nakshatra = str(self.spouse_nakshatra).strip()

        method = str(self.compatibility_method or "").strip().lower()
        if method and method not in ("north", "south"):
            raise RecordError("compatibility_method must be 'north' or 'south' "
                              f"(got {self.compatibility_method!r})")
        self.compatibility_method = method

    def has_spouse_birth_data(self) -> bool:
        """True when the spouse's star can be computed exactly from birth data."""
        return bool(self.spouse_date_of_birth and self.spouse_time_of_birth
                    and self.spouse_latitude is not None
                    and self.spouse_longitude is not None
                    and self.spouse_timezone is not None)

    def has_spouse_star(self) -> bool:
        """True when the spouse's nakshatra and pada were given directly."""
        return self.spouse_nakshatra is not None and self.spouse_pada is not None

    def has_spouse(self) -> bool:
        return self.has_spouse_birth_data() or self.has_spouse_star()

    def resolved_compatibility_method(self) -> str:
        """Explicit column wins; otherwise follow the chart style, as the GUI does."""
        if self.compatibility_method:
            return self.compatibility_method
        return "south" if "south" in (self.chart_type or "").lower() else "north"

    @classmethod
    def from_dict(cls, data: dict) -> "BirthRecord":
        """Build a record from a raw dict (e.g. a CSV row), tolerating aliases."""
        if not isinstance(data, dict):
            raise RecordError(f"record must be a dict, got {type(data).__name__}")
        canonical: dict = {}
        for key, value in data.items():
            if key is None:
                continue
            # normalize header: lowercase, and collapse spaces/hyphens to '_'
            # so "Date of Birth" / "date-of-birth" both match "date_of_birth".
            norm = re.sub(r"[\s\-]+", "_", str(key).strip().lower())
            field_name = _FIELD_ALIASES.get(norm)
            if field_name is None or value in (None, ""):
                continue
            canonical[field_name] = value
        missing = [f for f in ("date_of_birth", "time_of_birth", "place_name",
                               "latitude", "longitude", "timezone") if f not in canonical]
        if missing:
            raise RecordError(f"missing required field(s): {', '.join(missing)}")
        return cls(**canonical)


def _normalize_gender(value) -> int:
    if isinstance(value, bool):  # avoid True/False sneaking through as ints
        raise RecordError(f"gender must not be a boolean: {value!r}")
    if isinstance(value, (int, float)) and int(value) in (0, 1, 2, 3):
        return int(value)
    key = str(value).strip().lower()
    if key in _GENDER_ALIASES:
        return _GENDER_ALIASES[key]
    raise RecordError(f"gender must be 0-3 or a known label (got {value!r})")


def ensure_app(headless: bool = True) -> QApplication:
    """Return the singleton QApplication, creating a headless one if needed.

    A batch should create the app once and reuse it across all records. If a
    QApplication already exists (e.g. the caller is running the GUI) it is
    returned unchanged.
    """
    app = QApplication.instance()
    if app is None:
        if headless and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication(sys.argv[:1])
    return app


_runtime_ready = False


def _ensure_runtime() -> None:
    global _runtime_ready
    if not _runtime_ready:
        config.initialize_runtime(force_reload=True, silent=True)
        _runtime_ready = True


def generate_pdf(record, out_path, *, app: QApplication | None = None,
                 expand_all_tabs=None) -> Path:
    """Generate one horoscope PDF for ``record`` at ``out_path``.

    ``record`` may be a :class:`BirthRecord` or a raw dict (see
    ``BirthRecord.from_dict``). Returns the written path. Raises
    :class:`RecordError` for bad input and propagates any error from the
    PyJHora engine; the batch engine is responsible for per-record isolation.
    """
    rec = record if isinstance(record, BirthRecord) else BirthRecord.from_dict(record)
    app = app or ensure_app()
    _ensure_runtime()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    chart = ChartTabbed(
        chart_type=rec.chart_type,
        language=rec.language,
        use_internet_for_location_check=False,
    )
    try:
        if rec.name:
            chart.name(rec.name)
        chart.date_of_birth(rec.date_of_birth)
        chart.time_of_birth(rec.time_of_birth)
        chart.place(rec.place_name, rec.latitude, rec.longitude, rec.timezone, rec.elevation)
        chart.gender(rec.gender)
        chart.compute_horoscope()
        app.processEvents()  # let Qt finish laying out widgets before rendering
        chart.save_as_pdf(str(out_path), expand_all_tabs=expand_all_tabs)
        app.processEvents()
    finally:
        chart.close()
        chart.deleteLater()
        app.processEvents()
    return out_path
