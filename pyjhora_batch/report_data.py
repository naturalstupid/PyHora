"""Build a complete, structured horoscope report straight from PyJHora's engine.

This is the data layer behind both the plain-text report and the vector PDF. It
deliberately bypasses the Qt GUI: ``jhora.horoscope.info.Horoscope`` and the
chart/prediction modules are the same code the GUI calls, so the content is
identical while costing ~1s instead of ~60s and needing no QApplication.

Two things learned the hard way and encoded here:

* ``jhora.horoscope.main`` is stale — its ``get_calendar_information`` calls
  ``drik.vaara(jd)`` against a two-argument signature and raises. The live class
  is ``jhora.horoscope.info.Horoscope`` (what ``horo_chart_tabs`` imports).
* The engine modules share mutable global state (``utils.resource_strings`` and
  friends). Calling predictions -> dosha -> yoga -> raja_yoga in one process can
  make ``raja_yoga`` raise IndexError, while any shorter prefix of that sequence
  is fine. Every section therefore re-applies the language and is isolated, so a
  poisoned section degrades to a warning instead of losing the whole report.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

from .wrapper import BirthRecord, RecordError

# Chart-scoped keys come in two shapes: "Raasi (D1)-Sun☉" and "D-1-Arudha Lagna".
_CHART_KEY_RE = re.compile(r"^(?P<chart>.+\(D\d+\))-(?P<item>.+)$", re.DOTALL)
_ALT_KEY_RE = re.compile(r"^D-(?P<num>\d+)-(?P<item>.+)$", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_BREAK_RE = re.compile(r"<\s*(br|/p|/div|/tr)\s*/?\s*>", re.IGNORECASE)
# U+FE0E/U+FE0F select text vs emoji presentation. The engine appends VS15 to
# some zodiac glyphs ("♑︎Capricorn"); most PDF/terminal fonts have no glyph for
# it and draw a tofu box, so it is stripped everywhere.
_VARIATION_RE = re.compile("[︎️]")

#: Dhasa systems included by default. The engine exposes 26 graha dhasas plus
#: rasi/annual ones; emitting all of them yields hundreds of pages, so the
#: standard Vimsottari is the default and the rest are opt-in via ``dhasas=``.
DEFAULT_DHASAS: Tuple[str, ...] = ("vimsottari",)

#: Passed as a dhasa name, expands to every system the engine exposes.
ALL_DHASAS = "all"


def available_dhasas() -> List[str]:
    """Every dhasa system PyJHora exposes: graha, then rasi, then annual.

    Four of these (aayu, patyayini, varsha_vimsottari, varsha_narayana) take
    arguments a natal report has no value for and will be reported as warnings
    rather than sections.
    """
    from jhora import const
    return (list(const._graha_dhasa_dict) + list(const._rasi_dhasa_dict)
            + list(const._annual_dhasa_dict))


def resolve_dhasas(names: Optional[Sequence[str]]) -> Tuple[str, ...]:
    """Expand the ``all`` sentinel and de-duplicate, preserving order."""
    if not names:
        return DEFAULT_DHASAS
    resolved: List[str] = []
    for name in names:
        for item in (available_dhasas() if str(name).strip().lower() == ALL_DHASAS
                     else [name]):
            if item not in resolved:
                resolved.append(item)
    return tuple(resolved)


#: Chart styles that can be drawn as a diagram; anything else falls back to
#: the South Indian grid (with the substitution noted on the section).
DRAWABLE_STYLES = ("south_indian", "north_indian")


@dataclass
class ChartDiagram:
    """A divisional chart in the form a renderer can draw.

    ``occupants`` is indexed by *sign* (0=Aries .. 11=Pisces) — the South Indian
    style paints signs into fixed cells, while the North Indian style paints
    fixed houses, so it rotates this by ``ascendant``.
    """

    label: str
    occupants: List[List[str]]
    ascendant: int = 0
    style: str = "south_indian"

    def house_order(self) -> List[int]:
        """Sign index for each house 1..12, i.e. counting from the ascendant."""
        return [(self.ascendant + h) % 12 for h in range(12)]


@dataclass
class Section:
    """One titled block of the report.

    A section carries whichever shapes it needs: ``pairs`` for label/value
    lists, ``headers``+``rows`` for tables, ``body`` for prose, and ``chart``
    for a drawable divisional chart.
    """

    title: str
    pairs: List[Tuple[str, str]] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    body: str = ""
    note: str = ""
    chart: Optional[ChartDiagram] = None

    @property
    def is_empty(self) -> bool:
        return not (self.pairs or self.rows or self.body.strip() or self.chart)


@dataclass
class Report:
    record: BirthRecord
    sections: List[Section] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def section(self, title: str) -> Optional[Section]:
        for s in self.sections:
            if s.title == title:
                return s
        return None


def clean_text(value) -> str:
    """Normalize an engine string for display in any renderer.

    Strips presentation variation selectors and turns the literal two-character
    sequence ``\\n`` (which some prediction strings embed) into a real newline.
    """
    text = _VARIATION_RE.sub("", str(value))
    return text.replace("\\n", "\n")


def _normalize(report: Report) -> Report:
    """Apply :func:`clean_text` across every string the report will render."""
    for section in report.sections:
        section.title = clean_text(section.title)
        section.pairs = [(clean_text(k), clean_text(v)) for k, v in section.pairs]
        section.headers = [clean_text(h) for h in section.headers]
        section.rows = [[clean_text(c) for c in row] for row in section.rows]
        section.body = clean_text(section.body)
        section.note = clean_text(section.note)
        if section.chart is not None:
            section.chart.label = clean_text(section.chart.label)
            section.chart.occupants = [[clean_text(p) for p in cell]
                                       for cell in section.chart.occupants]
    return report


def _strip_html(value: str) -> str:
    """Turn the engine's HTML prediction/dosha blobs into readable plain text."""
    text = _BREAK_RE.sub("\n", str(value))
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    # collapse the ragged blank lines the tag removal leaves behind
    lines = [ln.strip() for ln in text.splitlines()]
    out: List[str] = []
    for ln in lines:
        if ln or (out and out[-1]):
            out.append(ln)
    return "\n".join(out).strip()


def _split_chart_key(key: str) -> Tuple[Optional[str], str]:
    """Split an info key into (chart label, item). Chart is None if unscoped."""
    key = str(key)
    m = _CHART_KEY_RE.match(key)
    if m:
        return m.group("chart").strip(), m.group("item").strip()
    m = _ALT_KEY_RE.match(key)
    if m:
        return f"D-{m.group('num')}", m.group("item").strip()
    return None, key.strip()


class _Builder:
    """Assembles the report, isolating each section from the others."""

    def __init__(self, record: BirthRecord, dhasas: Sequence[str]):
        self.rec = record
        self.dhasas = tuple(dhasas)
        self.report = Report(record=record)
        self._horo = None
        self._info = None
        self._charts = None
        self._asc_houses = None

    # --- infrastructure -------------------------------------------------

    def _reset_language(self) -> None:
        """Re-apply the language before each section (see module docstring)."""
        from jhora import utils
        utils.set_language(self._lang_code())

    def _lang_code(self) -> str:
        from jhora import const
        name = (self.rec.language or "English").strip()
        for code, label in getattr(const, "available_languages", {}).items():
            # available_languages maps display name -> code in some versions and
            # the reverse in others; accept either direction.
            if label == name:
                return code
            if code == name:
                return label
        return "en"

    def _safe(self, title: str, fn: Callable[[], Optional[Section]]) -> None:
        try:
            self._reset_language()
            section = fn()
        except Exception as exc:  # noqa: BLE001 - one bad section must not sink the report
            self.report.warnings.append(f"{title}: {type(exc).__name__}: {exc}")
            return
        if section is not None and not section.is_empty:
            self.report.sections.append(section)
        elif section is not None:
            self.report.warnings.append(f"{title}: no data produced")

    # --- engine handles -------------------------------------------------

    def _place(self):
        from jhora.panchanga import drik
        return drik.Place(self.rec.place_name, self.rec.latitude,
                          self.rec.longitude, self.rec.timezone)

    def _date(self):
        from jhora.panchanga import drik
        y, m, d = (int(x) for x in self.rec.date_of_birth.split(","))
        return drik.Date(y, m, d)

    def _tob_tuple(self) -> Tuple[int, int, int]:
        hh, mm, ss = (int(x) for x in self.rec.time_of_birth.split(":"))
        return hh, mm, ss

    def _jd(self) -> float:
        from jhora import utils
        return utils.julian_day_number(self._date(), self._tob_tuple())

    def horoscope(self):
        if self._horo is None:
            from jhora.horoscope import info
            self._horo = info.Horoscope(
                place_with_country_code=self.rec.place_name,
                latitude=self.rec.latitude, longitude=self.rec.longitude,
                timezone_offset=self.rec.timezone, date_in=self._date(),
                birth_time=self.rec.time_of_birth, language=self._lang_code(),
            )
        return self._horo

    def horoscope_information(self):
        if self._info is None:
            (self._info, self._charts,
             self._asc_houses) = self.horoscope().get_horoscope_information()
        return self._info, self._charts

    # --- sections -------------------------------------------------------

    def birth_details(self) -> Section:
        from jhora import utils
        y, m, d = (int(x) for x in self.rec.date_of_birth.split(","))
        hh, mi, ss = self._tob_tuple()
        tz = self.rec.timezone
        sign = "+" if tz >= 0 else "-"
        tz_h, tz_m = divmod(round(abs(tz) * 60), 60)
        pairs = [
            ("Name", self.rec.name or "(not given)"),
            ("Date of Birth", f"{d:02d}-{m:02d}-{y:04d}"),
            ("Time of Birth", f"{hh:02d}:{mi:02d}:{ss:02d}"),
            ("Place", self.rec.place_name),
            ("Latitude", utils.to_dms(self.rec.latitude, is_lat_long="lat", as_string=True)),
            ("Longitude", utils.to_dms(self.rec.longitude, is_lat_long="long", as_string=True)),
            ("Timezone", f"UTC{sign}{tz_h:02d}:{tz_m:02d}"),
        ]
        gender_names = {0: "Female", 1: "Male", 2: "Transgender", 3: "Not specified"}
        pairs.append(("Gender", gender_names.get(self.rec.gender, "Not specified")))
        return Section("Birth Details", pairs=pairs)

    def panchanga(self) -> Section:
        cal = self.horoscope().calendar_info or {}
        return Section("Panchanga at Birth",
                       pairs=[(str(k), str(v)) for k, v in cal.items()])

    def positions(self) -> List[Section]:
        """One section per divisional chart, from the 989 formatted info keys.

        The engine uses three key shapes, which have to be told apart or the
        most important table in the report ends up under a meaningless heading:

        * ``Hora (D2)-Sun``       -> planetary positions for a divisional chart
        * ``Raasi-Sun``           -> the same, for D-1, with no "(D1)" marker
        * ``D-1-Arudha Lagna``    -> arudha padas, NOT positions
        """
        info_dict, _ = self.horoscope_information()
        rasi_word = self._rasi_word(info_dict)
        rasi_prefix = f"{rasi_word}-"

        positions: dict = {}
        arudhas: dict = {}
        other: List[Tuple[str, str]] = []

        for key, value in info_dict.items():
            text = str(key)
            chart, item = _split_chart_key(text)
            if chart is None:
                if text.startswith(rasi_prefix):
                    # D-1 positions; drop the redundant prefix from each label
                    positions.setdefault(f"{rasi_word} (D1)", []).append(
                        (text[len(rasi_prefix):].strip(), str(value)))
                else:
                    other.append((item, str(value)))
            elif _ALT_KEY_RE.match(text):
                arudhas.setdefault(chart, []).append((item, str(value)))
            else:
                positions.setdefault(chart, []).append((item, str(value)))

        sections = [Section(f"Positions — {chart}", pairs=pairs)
                    for chart, pairs in positions.items() if pairs]
        sections += [Section(f"Arudha Padas — {chart}", pairs=pairs)
                     for chart, pairs in arudhas.items() if pairs]
        if other:
            sections.append(Section("Other Values", pairs=other))
        return sections

    @staticmethod
    def _rasi_word(info_dict) -> str:
        """The engine's localized word for the D-1 chart (e.g. 'Raasi')."""
        return next((str(k).split("-")[0] for k in info_dict
                     if "Ascendant" in str(k) and not _CHART_KEY_RE.match(str(k))),
                    "Raasi")

    def _resolved_style(self) -> Tuple[str, str]:
        """The drawable chart style for this record, plus a note if substituted."""
        style = (self.rec.chart_type or "south_indian").strip().lower()
        if style in DRAWABLE_STYLES:
            return style, ""
        return "south_indian", (f"{style!r} diagrams are not drawn; the chart "
                                f"below uses the South Indian layout.")

    def _chart_labels(self, count: int) -> List[str]:
        """Names for each divisional chart, in ``horoscope_charts`` order."""
        info_dict, _ = self.horoscope_information()
        labels: List[str] = []
        seen = set()
        for key in info_dict:
            m = _CHART_KEY_RE.match(str(key))
            if m and m.group("chart") not in seen:
                seen.add(m.group("chart"))
                labels.append(m.group("chart"))
        # The D-1 chart's keys are prefixed with the bare rasi word ("Raasi-Sun")
        # and carry no "(D1)", so the loop above never sees it. It is chart 0.
        labels.insert(0, f"{self._rasi_word(info_dict)} (D1)")
        while len(labels) < count:
            labels.append(f"Chart D-{len(labels) + 1}")
        return labels[:count]

    def divisional_charts(self) -> List[Section]:
        """Each chart as a drawable diagram plus a sign -> occupants table."""
        from jhora import utils
        _, charts = self.horoscope_information()
        if not charts:
            return []
        ascendants = self._asc_houses or []
        signs = list(utils.RAASI_LIST)
        labels = self._chart_labels(len(charts))

        style, note = self._resolved_style()
        sections = []
        for idx, chart in enumerate(charts):
            if not isinstance(chart, (list, tuple)) or len(chart) != len(signs):
                continue
            occupants = [str(cell).split() and
                         [p for p in str(cell).splitlines() if p.strip()] or []
                         for cell in chart]
            asc = ascendants[idx] if idx < len(ascendants) else 0
            diagram = ChartDiagram(label=labels[idx], occupants=occupants,
                                   ascendant=int(asc) if isinstance(asc, int) else 0,
                                   style=style)
            rows = [[signs[i], " ".join(occ) or "—"] for i, occ in enumerate(occupants)]
            sections.append(Section(labels[idx], headers=["Rasi", "Occupants"],
                                    rows=rows, chart=diagram, note=note))
        return sections

    def _dhasa_years(self, name: str) -> int:
        """The varsha year number, following the engine's own aggregator.

        ``_get_annual_dhasa_bhukthi`` passes ``self.years`` to varsha-narayana
        but ``self.years - 1`` to varsha-vimsottari (mudda). Matching that is
        what puts mudda's year on the birth-year solar return instead of the
        following one.
        """
        years = getattr(self.horoscope(), "years", 1)
        return years - 1 if name == "varsha_vimsottari" else years

    def _dhasa_call_args(self, method, name: str) -> list:
        """Positional arguments for ``method``, derived from its signature.

        The dhasa methods do NOT share a calling convention: most take
        ``(dob, tob, place)``, the varsha ones additionally need ``years``,
        ``_get_varsha_vimsottari_dhasa`` takes ``(jd, place, years)``, and
        ``_get_patyayini_dhasa`` takes none at all (it derives everything from
        the Horoscope). Passing one fixed triple to all of them raises
        TypeError on four systems, so the signature decides.
        """
        import inspect
        suppliers = {
            "dob": self._date,
            "tob": self._tob_tuple,
            "place": self._place,
            "jd": self._jd,
            "years": lambda: self._dhasa_years(name),
        }
        args = []
        for param in inspect.signature(method).parameters.values():
            if param.kind not in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                continue
            if param.default is not param.empty:      # optional - leave it alone
                continue
            if param.name not in suppliers:
                raise TypeError(f"unsupported dhasa parameter {param.name!r}")
            args.append(suppliers[param.name]())
        return args

    def _dhasa_kwargs(self, name: str) -> dict:
        """Per-system keyword arguments needed to work around engine defects."""
        if name != "aayu":
            return {}
        # aayu's "pick the type automatically" sentinel is AAYU_TYPE.NONE, i.e.
        # Python None -- but initialize_runtime() reloads it from
        # factory_settings.json where it round-trips to the STRING "NONE".
        # get_dhasa_antardhasa then takes it for a real choice and uses it as a
        # planet key (KeyError: 'NONE'). Supply the value the auto branch would
        # have computed: the stronger of lagna, Sun and Moon.
        from jhora import const
        from jhora.horoscope.chart import charts
        from jhora.horoscope.dhasa.graha import aayu
        positions = charts.rasi_chart(self._jd(), self._place())[:const._pp_count_upto_ketu]
        return {"aayur_type": aayu._get_aayur_type(positions)}

    def dhasa(self, name: str) -> Section:
        horo = self.horoscope()
        horo.get_dhasa_bhukthi_as_raw_data = False
        method = getattr(horo, f"_get_{name}_dhasa_bhukthi", None) or \
            getattr(horo, f"_get_{name}_dhasa", None)
        if method is None:
            raise AttributeError(f"no engine method for dhasa {name!r}")
        # tob is supplied as the (h, m, s) tuple; the engine feeds it to
        # julian_day_number, which cannot parse "HH:MM:SS"
        data = method(*self._dhasa_call_args(method, name), **self._dhasa_kwargs(name))
        rows = []
        for entry in data or []:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                rows.append([str(entry[0]), str(entry[1])])
            else:
                rows.append([str(entry), ""])
        title = name.replace("_", " ").title()
        return Section(f"Dhasa-Bhukthi — {title}",
                       headers=["Dhasa-Bhukthi", "Starts"], rows=rows)

    def ashtakavarga(self) -> Section:
        from jhora import utils
        from jhora.horoscope.chart import ashtakavarga, charts
        planet_positions = charts.rasi_chart(self._jd(), self._place())
        # get_ashtaka_varga wants the 1-D house->planet-index list, not positions
        chart_1d = utils.get_house_planet_list_from_planet_positions(planet_positions)
        bav, sav, _ = ashtakavarga.get_ashtaka_varga(chart_1d)
        signs = list(utils.RAASI_LIST)
        # BAV has 8 rows: the seven grahas THEN the lagna (0=Sun .. 6=Saturn,
        # 7=Lagnam). Taking PLANET_NAMES[:8] would label that last row "Raagu",
        # which is wrong — Rahu/Ketu have no bhinnashtakavarga.
        names = list(utils.PLANET_NAMES)[:max(len(bav) - 1, 0)] + ["Lagna"]
        # clean first, then slice: several sign names carry a variation selector
        # that would otherwise eat one of the three characters ("♉T" vs "♈Ar")
        headers = ["Planet"] + [clean_text(s)[:3] for s in signs]
        rows = []
        for i, row in enumerate(bav):
            label = names[i] if i < len(names) else f"P{i}"
            rows.append([label] + [str(v) for v in row])
        if sav:
            rows.append(["Sarva"] + [str(v) for v in sav])
        return Section("Ashtakavarga", headers=headers, rows=rows)

    # -- strengths and special points ------------------------------------
    # These are computed by the GUI but absent from get_horoscope_information().
    # Row/column labels come from utils.resource_strings so they localize with
    # the rest of the report; the orientation matches the GUI's own tables.

    @staticmethod
    def _res(key: str, fallback: str) -> str:
        from jhora import utils
        return (getattr(utils, "resource_strings", {}) or {}).get(key, fallback)

    @staticmethod
    def _flat(value) -> str:
        """Bala cells embed newlines ('Vyanjanaamsa\\n(D1/D2/D3)\\n14.5')."""
        return " ".join(str(value).split())

    def _planets(self) -> List[str]:
        from jhora import utils
        return list(utils.PLANET_NAMES)[:7]

    def sphuta(self) -> Section:
        horo = self.horoscope()
        data = horo._get_sphuta(self._date(), self._tob_tuple(), self._place())
        return Section(self._res("sphuta_str", "Sphuta"),
                       pairs=[(str(k), str(v)) for k, v in (data or {}).items()])

    def shad_bala(self) -> Section:
        horo = self.horoscope()
        data = horo._get_shad_bala(self._date(), self._tob_tuple(), self._place())
        row_keys = [("sthaana_bala_str", "Positional Strength"),
                    ("kaala_bala_str", "Temporal Strength"),
                    ("dig_bala_str", "Directional Strength"),
                    ("chesta_bala_str", "Motion Strength"),
                    ("naisargika_bala_str", "Natural Strength"),
                    ("drik_bala_str", "Aspect Strength"),
                    ("shad_bala_str", "Shadh Bala"),
                    ("shad_bala_rupas_str", "Shadh Bala (Rupas)"),
                    ("shad_bala_strength_str", "Shad Bala (Strength)")]
        rows = [[self._res(*row_keys[i])] + [str(v) for v in row]
                for i, row in enumerate(data or []) if i < len(row_keys)]
        return Section(self._res("shad_bala_str", "Shadh Bala"),
                       headers=["Strength"] + self._planets(), rows=rows)

    def bhava_bala(self) -> Section:
        horo = self.horoscope()
        data = horo._get_bhava_bala(self._date(), self._tob_tuple(), self._place())
        house = self._res("house_str", "House")
        rows = [[f"{house}-{i + 1}"] + [str(v) for v in row]
                for i, row in enumerate(data or [])]
        return Section(self._res("bhava_bala_str", "Bhava Bala"),
                       headers=[house,
                                self._res("bhava_bala_str", "Bhava Bala"),
                                self._res("bhava_bala_rupas_str", "Bhava Bala (Rupas)"),
                                self._res("bhava_bala_strength_str", "Bhava Bala (Strength)")],
                       rows=rows)

    def _planet_keyed_bala(self, title: str, data, column_titles) -> Section:
        """Shape a list-of-{planet: value} dicts into one planet-per-row table."""
        parts = list(data or [])
        rows = []
        for planet in self._planets():
            row = [planet] + [self._flat(part.get(planet, "")) for part in parts]
            rows.append(row)
        return Section(title, headers=["Planet"] + list(column_titles[:len(parts)]),
                       rows=rows)

    def vimsopaka_bala(self) -> Section:
        horo = self.horoscope()
        data = horo._get_vimsopaka_bala(self._date(), self._tob_tuple(), self._place())
        return self._planet_keyed_bala(
            self._res("vimsopaka_bala_str", "Varga Amsa Vimsopaka Bala"), data,
            [self._res("shadvarga_bala_str", "Shad varga"),
             self._res("sapthavarga_bala_str", "Saptha varga"),
             self._res("dhasavarga_bala_str", "Dhasa varga"),
             self._res("shodhasavarga_bala_str", "Shodhasa varga")])

    def vaiseshikamsa_bala(self) -> Section:
        horo = self.horoscope()
        data = horo._get_vaiseshikamsa_bala(self._date(), self._tob_tuple(), self._place())
        return self._planet_keyed_bala(
            self._res("vaiseshikamsa_bala_str", "Varga Amsa Vaiseshikamsa Bala"), data,
            [self._res("shadvarga_bala_str", "Shad varga"),
             self._res("sapthavarga_bala_str", "Saptha varga"),
             self._res("dhasavarga_bala_str", "Dhasa varga"),
             self._res("shodhasavarga_bala_str", "Shodhasa varga")])

    def other_bala(self) -> Section:
        horo = self.horoscope()
        data = horo._get_other_bala(self._date(), self._tob_tuple(), self._place())
        return self._planet_keyed_bala(
            self._res("harsha_pancha_dwadhasa_vargeeya_bala_str",
                      "Harsha Pancha Dwadhasa Vargeeya Bala"), data,
            [self._res("harsha_bala_str", "Harsha bala"),
             self._res("pancha_vargeeya_bala_str", "Pancha Vargeeya bala"),
             self._res("dwadhasa_vargeeya_bala_str", "Dwadhasa Vargeeya bala")])

    def bhava_chart(self) -> List[Section]:
        """House cusps and the drawn bhava chart.

        Two sections, not one: the renderers show a section's diagram *or* its
        table (they are normally the same data), but here the cusp table adds
        the begin/middle/end degrees the diagram cannot express.
        """
        horo = self.horoscope()
        chart_1d, bhava_info, asc_house = horo.get_bhava_chart_information(
            horo.julian_day, self._place())
        title = self._res("bhava_str", "Bhava Chart")
        sections: List[Section] = []

        if isinstance(chart_1d, (list, tuple)) and len(chart_1d) == 12:
            style, note = self._resolved_style()
            sections.append(Section(title, note=note, chart=ChartDiagram(
                label=title,
                occupants=[[p for p in str(cell).splitlines() if p.strip()]
                           for cell in chart_1d],
                ascendant=int(asc_house) if isinstance(asc_house, int) else 0,
                style=style)))

        rows = [[str(c) for c in row] for row in (bhava_info or [])]
        if rows:
            width = max(len(r) for r in rows)
            headers = [self._res("house_str", "House"), "Begins", "Middle",
                       "Ends", "Planets"][:width]
            sections.append(Section(f"{title} — Cusps", headers=headers, rows=rows))
        return sections

    # -- marriage compatibility -------------------------------------------

    def _star_from_birth(self, date_str: str, time_str: str, lat: float,
                         lon: float, tz: float) -> Tuple[int, int]:
        """Moon's nakshatra (1-27) and pada (1-4) for a set of birth details."""
        from jhora import utils
        from jhora.panchanga import drik
        from jhora.horoscope.chart import charts
        year, month, day = (int(x) for x in date_str.split(","))
        hh, mm, ss = (int(x) for x in time_str.split(":"))
        jd = utils.julian_day_number(drik.Date(year, month, day), (hh, mm, ss))
        place = drik.Place("spouse", lat, lon, tz)
        moon = [p for p in charts.rasi_chart(jd, place) if p[0] == 1][0]
        longitude = moon[1][0] * 30 + moon[1][1]
        nakshatra, pada, _ = drik.nakshatra_pada(longitude)
        return int(nakshatra), int(pada)

    def _spouse_star(self) -> Tuple[int, int, str]:
        """(nakshatra, pada, how it was obtained) for the spouse."""
        from jhora import utils
        rec = self.rec
        if rec.has_spouse_birth_data():
            nak, pada = self._star_from_birth(
                rec.spouse_date_of_birth, rec.spouse_time_of_birth,
                rec.spouse_latitude, rec.spouse_longitude, rec.spouse_timezone)
            return nak, pada, "computed from the spouse's birth details"

        raw = str(rec.spouse_nakshatra).strip()
        if raw.isdigit():
            nak = int(raw)
        else:
            names = [str(n).strip().lower() for n in utils.NAKSHATRA_LIST]
            key = raw.lower()
            if key not in names:
                raise RecordError(f"unknown spouse_nakshatra {rec.spouse_nakshatra!r}; "
                                  f"use 1-27 or one of: {', '.join(names[:4])}, ...")
            nak = names.index(key) + 1
        if not 1 <= nak <= 27:
            raise RecordError(f"spouse_nakshatra must be 1-27 (got {nak})")
        return nak, int(rec.spouse_pada), "taken from the supplied star and pada"

    def compatibility(self) -> Optional[Section]:
        """Score the native against the spouse.

        Only the pair's nakshatra + pada feed the calculation. Which partner is
        the "boy" matters (several kootas are asymmetric), so the native's
        gender decides and the spouse is taken as the opposite unless stated.
        """
        from jhora import utils
        from jhora.horoscope.match import compatibility as comp
        rec = self.rec
        if not rec.has_spouse():
            return None

        spouse_nak, spouse_pada, provenance = self._spouse_star()
        native_nak, native_pada = self._star_from_birth(
            rec.date_of_birth, rec.time_of_birth, rec.latitude, rec.longitude,
            rec.timezone)

        native_is_male = rec.gender == 1
        if rec.spouse_gender is not None:
            native_is_male = rec.spouse_gender != 1
        if native_is_male:
            boy, girl = (native_nak, native_pada), (spouse_nak, spouse_pada)
        else:
            boy, girl = (spouse_nak, spouse_pada), (native_nak, native_pada)

        method = rec.resolved_compatibility_method()
        koota = comp.Ashtakoota(boy[0], boy[1], girl[0], girl[1],
                                method="South" if method == "south" else "North")
        stars = list(utils.NAKSHATRA_LIST)

        def star_name(n):
            return stars[n - 1] if 1 <= n <= len(stars) else str(n)

        pairs = [
            ("Spouse", rec.spouse_name or "(not named)"),
            ("Native star", f"{star_name(native_nak)} pada {native_pada}"),
            ("Spouse star", f"{star_name(spouse_nak)} pada {spouse_pada}"),
            ("Spouse star source", provenance),
            ("Boy / Girl", f"{star_name(boy[0])} p{boy[1]} / "
                           f"{star_name(girl[0])} p{girl[1]}"),
            ("Method", "South (10 poruthams)" if method == "south"
                       else "North (Ashtakoota, out of 36)"),
        ]

        if method == "south":
            checks = [("Vasiya", "vasiya_porutham_south"),
                      ("Gana", "gana_porutham_south"),
                      ("Dina", "dina_porutham_south"),
                      ("Yoni", "yoni_porutham_south"),
                      ("Raasi Adhipathi", "raasi_adhipathi_porutham_south"),
                      ("Raasi", "raasi_porutham_south"),
                      ("Mahendra", "mahendra_porutham_south"),
                      ("Vedha", "vedha_porutham_south"),
                      ("Rajju", "rajju_porutham_south"),
                      ("Sthree Dheerga", "sthree_dheerga_porutham_south")]
            rows, score = [], 0
            for label, attr in checks:
                passed = bool(getattr(koota, attr)())
                score += passed
                rows.append([label, "Yes" if passed else "No"])
            pairs.append(("Score", f"{score} / {len(checks)}"))
            headers = ["Porutham", "Agrees"]
        else:
            # compatibility_score() -> 8 koota scores, total, then the 4 extras
            result = koota.compatibility_score()
            koota_names = ["Varna", "Vasiya", "Gana", "Nakshathra", "Yoni",
                           "Raasi Adhipathi", "Bahkut", "Naadi"]
            maxima = [comp.varna_max_score, comp.vasiya_max_score,
                      comp.gana_max_score, comp.nakshathra_max_score,
                      comp.yoni_max_score, comp.raasi_adhipathi_max_score,
                      comp.raasi_max_score, comp.naadi_max_score]
            rows = [[name, str(result[i]), str(maxima[i])]
                    for i, name in enumerate(koota_names)]
            for label, value in zip(["Mahendra", "Vedha", "Rajju", "Sthree Dheerga"],
                                    result[9:13]):
                rows.append([label, "Yes" if value else "No", "-"])
            pairs.append(("Score", f"{result[8]} / 36"))
            headers = ["Koota", "Score", "Max"]

        return Section("Marriage Compatibility", pairs=pairs, headers=headers,
                       rows=rows)

    def yogas(self) -> Section:
        from jhora.horoscope.chart import yoga
        results, _, _ = yoga.get_yoga_details(self._jd(), self._place(),
                                              divisional_chart_factor=1,
                                              language=self._lang_code())
        return _findings("Yogas", _yoga_rows(results))

    def raja_yogas(self) -> Section:
        from jhora.horoscope.chart import raja_yoga
        results, _, _ = raja_yoga.get_raja_yoga_details(self._jd(), self._place(),
                                                        divisional_chart_factor=1,
                                                        language=self._lang_code())
        return _findings("Raja Yogas", _yoga_rows(results))

    def doshas(self) -> Section:
        from jhora.horoscope.chart import dosha
        results = dosha.get_dosha_details(self._jd(), self._place(),
                                          language=self._lang_code())
        parts = [f"{key}\n{'-' * len(str(key))}\n{_strip_html(value)}"
                 for key, value in (results or {}).items()]
        return Section("Doshas", body="\n\n".join(parts))

    def predictions(self) -> Section:
        from jhora.horoscope.prediction import general
        results = general.get_prediction_details(self._jd(), self._place(),
                                                 language=self._lang_code())
        parts = [f"{key}\n{'-' * len(str(key))}\n{_strip_html(value)}"
                 for key, value in (results or {}).items()]
        return Section("General Predictions", body="\n\n".join(parts))


def _findings(title: str, rows: List[List[str]]) -> Section:
    """A findings table, or an explicit 'none' note — never a silently empty section."""
    if not rows:
        return Section(title, body="None found for this chart.")
    return Section(title, headers=["Yoga", "Description"], rows=rows,
                   note="Only yogas present in this chart are listed.")


def _yoga_rows(results) -> List[List[str]]:
    """Normalize a yoga/raja-yoga result dict into [name, description].

    The upstream result also carries a canned 'prediction' sentence, which we
    deliberately drop: it is fixed boilerplate keyed on the yoga name, identical
    for every chart the yoga fires in, and reads as an individual prognosis when
    it is nothing of the sort. Reporting the rule and its condition is honest;
    reporting its stock verdict is not.
    """
    rows: List[List[str]] = []
    for key, value in (results or {}).items():
        if isinstance(value, (list, tuple)):
            parts = [str(p) for p in value]
            # shape is [chart, name, description, prediction]
            name = parts[1] if len(parts) > 1 else str(key)
            desc = _strip_html(parts[2]) if len(parts) > 2 else ""
        else:
            name, desc = str(key), _strip_html(value)
        rows.append([name, desc])
    return rows


def build_report(record, *, dhasas: Sequence[str] = DEFAULT_DHASAS,
                 include_charts: bool = True) -> Report:
    """Build the full structured report for ``record``.

    ``record`` may be a :class:`BirthRecord` or a raw dict. Individual sections
    that fail are recorded in ``report.warnings`` rather than raising, so a
    partial report is still produced.
    """
    rec = record if isinstance(record, BirthRecord) else BirthRecord.from_dict(record)
    dhasas = resolve_dhasas(dhasas)

    from jhora import config, const
    from jhora.panchanga import drik
    config.initialize_runtime(force_reload=True, silent=True)
    # ChartTabbed.__init__ does this before computing anything. Skip it and
    # swisseph keeps its own default sidereal mode, so every longitude — and
    # therefore tithi, nakshatra, yoga and all divisional charts — silently
    # disagrees with the GUI. Must happen before any engine call.
    drik.set_ayanamsa_mode(const._DEFAULT_AYANAMSA_MODE)
    drik.refresh_planet_flags(rec.longitude, rec.latitude, rec.elevation)

    b = _Builder(rec, dhasas)
    b._safe("Birth Details", b.birth_details)
    b._safe("Panchanga at Birth", b.panchanga)

    # raja_yoga runs before the other readings: the engine's shared globals make
    # it fail if predictions/dosha/yoga have already run in this process.
    b._safe("Raja Yogas", b.raja_yogas)
    b._safe("Yogas", b.yogas)
    b._safe("Doshas", b.doshas)
    b._safe("General Predictions", b.predictions)
    b._safe("Ashtakavarga", b.ashtakavarga)

    # strengths and special points — computed by the GUI but not returned by
    # get_horoscope_information(), so each needs its own engine call
    b._safe("Marriage Compatibility", b.compatibility)
    b._safe("Sphuta", b.sphuta)
    b._safe("Shad Bala", b.shad_bala)
    b._safe("Bhava Bala", b.bhava_bala)
    b._safe("Other Bala", b.other_bala)
    b._safe("Vimsopaka Bala", b.vimsopaka_bala)
    b._safe("Vaiseshikamsa Bala", b.vaiseshikamsa_bala)

    def _bhava():
        for s in b.bhava_chart():
            b.report.sections.append(s)
        return None
    b._safe("Bhava Chart", _bhava)

    for name in b.dhasas:
        b._safe(f"Dhasa-Bhukthi — {name}", lambda n=name: b.dhasa(n))

    if include_charts:
        def _positions():
            for s in b.positions():
                b.report.sections.append(s)
            return None
        b._safe("Positions", _positions)

        def _grids():
            for s in b.divisional_charts():
                b.report.sections.append(s)
            return None
        b._safe("Chart Grids", _grids)

    return _normalize(b.report)
