import pytest

from pyjhora_batch.report_data import (Report, Section, _split_chart_key,
                                       _strip_html, _yoga_rows, build_report,
                                       clean_text)
from pyjhora_batch.wrapper import BirthRecord


# --- pure helpers (fast, no engine) ------------------------------------

def test_clean_text_strips_variation_selectors():
    # U+FE0E after a zodiac glyph renders as a tofu box in most PDF fonts
    assert clean_text("♑︎Capricorn") == "♑Capricorn"
    assert clean_text("♈️Aries") == "♈Aries"


def test_clean_text_expands_literal_backslash_n():
    # some prediction strings embed the two characters \ and n, not a newline
    assert clean_text("happy.\\n This yoga") == "happy.\n This yoga"


def test_strip_html_produces_readable_text():
    out = _strip_html("<html><b>Title</b><br>First line<br>Second &amp; last</html>")
    assert "<" not in out and "&amp;" not in out
    assert out.splitlines() == ["Title", "First line", "Second & last"]


@pytest.mark.parametrize("key, chart, item", [
    ("Raasi (D1)-Sun☉", "Raasi (D1)", "Sun☉"),
    ("Dwadas-Dwadasamsa (D144)-Moon", "Dwadas-Dwadasamsa (D144)", "Moon"),
    ("D-1-Arudha Lagna (AL)", "D-1", "Arudha Lagna (AL)"),
    ("Ascendant", None, "Ascendant"),
])
def test_split_chart_key(key, chart, item):
    assert _split_chart_key(key) == (chart, item)


def test_section_is_empty():
    assert Section("t").is_empty
    assert not Section("t", pairs=[("a", "b")]).is_empty
    assert not Section("t", rows=[["a"]]).is_empty
    assert not Section("t", body="x").is_empty


def test_yoga_rows_drop_the_canned_prediction():
    """The 4th element is stock boilerplate keyed on the yoga name — never emit it."""
    results = {"vesi_yoga": ["D1", "Vesai Yoga", "A planet other than Moon in the 2nd "
                             "house from Sun", "You will be happy and comfortable."]}
    assert _yoga_rows(results) == [["Vesai Yoga", "A planet other than Moon in the "
                                    "2nd house from Sun"]]


def test_yoga_rows_survive_short_and_scalar_values():
    assert _yoga_rows({"x": ["D1", "X Yoga"]}) == [["X Yoga", ""]]
    assert _yoga_rows({"y": "<b>plain</b>"}) == [["y", "plain"]]
    assert _yoga_rows(None) == []


def test_report_section_lookup():
    r = Report(record=None, sections=[Section("A"), Section("B", body="x")])
    assert r.section("B").body == "x"
    assert r.section("missing") is None


# --- full build (drives the real engine) -------------------------------

@pytest.fixture(scope="module")
def built_report(base_record_dict_module):
    return build_report(BirthRecord.from_dict(base_record_dict_module))


@pytest.fixture(scope="module")
def base_record_dict_module():
    return {"name": "Test Person", "date_of_birth": "1985,6,15",
            "time_of_birth": "10:30:00", "place_name": "Ujjain",
            "latitude": 23.5, "longitude": 75.75,
            "timezone": 5.5, "gender": "male"}


def test_build_report_has_no_warnings(built_report):
    assert built_report.warnings == []


def test_build_report_core_sections(built_report):
    titles = [s.title for s in built_report.sections]
    for expected in ("Birth Details", "Panchanga at Birth", "Yogas",
                     "Doshas", "General Predictions", "Ashtakavarga"):
        assert expected in titles
    assert len(built_report.sections) > 50


def test_panchanga_matches_the_gui(built_report):
    """Guards the ayanamsa setup: skip drik.set_ayanamsa_mode and these shift.

    Values captured from ChartTabbed.compute_horoscope for the same birth data.
    """
    pan = dict(built_report.section("Panchanga at Birth").pairs)
    assert pan["Day"] == "Saturday"
    assert pan["Sun Rise"] == "05:44:08"
    assert pan["Solar Month:"] == "Aani Date 2"
    assert pan["Yoga"].startswith("Sukarma")
    assert pan["Raasi"].startswith("♈Aries 21:16:46")


def test_birth_details_timezone_is_hours_minutes(built_report):
    # 5.5 hours is +05:30, not +05:50
    assert dict(built_report.section("Birth Details").pairs)["Timezone"] == "UTC+05:30"


def test_dhasa_section_is_a_dated_table(built_report):
    section = built_report.section("Dhasa-Bhukthi — Vimsottari")
    assert section is not None
    assert section.headers == ["Dhasa-Bhukthi", "Starts"]
    assert len(section.rows) > 50
    assert section.rows[0][1].startswith("19")      # an ISO-ish start date


def test_ashtakavarga_is_twelve_signs_wide(built_report):
    section = built_report.section("Ashtakavarga")
    assert len(section.headers) == 13               # planet + 12 rasis
    assert section.rows[-1][0] == "Sarva"
    assert all(cell.isdigit() for cell in section.rows[-1][1:])


def test_no_section_renders_a_tofu_box(built_report):
    """clean_text must have run over every string the renderers will see."""
    for section in built_report.sections:
        blob = "".join([section.title, section.body]
                       + [f"{k}{v}" for k, v in section.pairs]
                       + ["".join(r) for r in section.rows])
        assert "︎" not in blob and "️" not in blob
        assert "\\n" not in blob


def test_bad_record_raises_before_any_work():
    with pytest.raises(Exception):
        build_report({"date_of_birth": "nonsense"})


# --- divisional chart diagrams -----------------------------------------

def _divisional(report):
    """Chart sections for the 23 vargas, excluding the bhava chart."""
    import re as _re
    return [s for s in report.sections
            if s.chart and _re.search(r"\(D\d+\)$", s.title)]


def test_charts_are_named_not_numbered(built_report):
    titles = [s.title for s in _divisional(built_report)]
    assert len(titles) == 23
    assert titles[0].endswith("(D1)")            # the rasi chart is chart 0
    assert "Navamsam (D9)" in titles


def test_d1_chart_matches_the_gui(built_report):
    """Occupants captured from ChartTabbed's Janma-Raasi tab for this birth."""
    chart = _divisional(built_report)[0].chart
    assert chart.ascendant == 4                  # Leo
    assert chart.occupants[0] == ["Moon☾", "Venus♀", "Raagu☊"]    # Aries
    assert chart.occupants[2] == ["Sun☉", "Mars♂", "Mercury☿"]    # Gemini
    assert chart.occupants[4] == ["Ascendantℒ"]                   # Leo
    assert chart.occupants[6] == ["Kethu☋"]                       # Libra
    assert chart.occupants[7] == ["Saturn♄℞"]                     # Scorpio, retrograde
    assert chart.occupants[9] == ["Jupiter♃℞"]                    # Capricorn, retrograde
    assert chart.occupants[1] == []                               # Taurus empty


def test_house_order_starts_at_the_ascendant():
    from pyjhora_batch.report_data import ChartDiagram
    d = ChartDiagram("D1", [[] for _ in range(12)], ascendant=4)
    assert d.house_order() == [4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3]
    assert d.house_order()[0] == d.ascendant


def test_chart_style_follows_the_record():
    rec = BirthRecord.from_dict({
        "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
        "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5, "chart_type": "north_indian"})
    charts = [s.chart for s in build_report(rec).sections if s.chart]
    assert len(charts) == 24 and all(c.style == "north_indian" for c in charts)


def test_undrawable_style_falls_back_with_a_visible_note():
    rec = BirthRecord.from_dict({
        "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
        "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5, "chart_type": "east_indian"})
    report = build_report(rec)
    sections = [s for s in report.sections if s.chart]
    assert sections
    assert all(s.chart.style == "south_indian" for s in sections)
    # every drawn chart discloses the substitution, the bhava chart included
    assert all("east_indian" in s.note for s in sections)


# --- dhasa selection ---------------------------------------------------

def test_resolve_dhasas_defaults_to_vimsottari():
    from pyjhora_batch.report_data import DEFAULT_DHASAS, resolve_dhasas
    assert resolve_dhasas(None) == DEFAULT_DHASAS
    assert resolve_dhasas([]) == DEFAULT_DHASAS


def test_resolve_dhasas_keeps_order_and_dedupes():
    from pyjhora_batch.report_data import resolve_dhasas
    assert resolve_dhasas(["yogini", "vimsottari", "yogini"]) == ("yogini", "vimsottari")


def test_resolve_dhasas_expands_all():
    from pyjhora_batch.report_data import available_dhasas, resolve_dhasas
    every = resolve_dhasas(["all"])
    assert set(every) == set(available_dhasas())
    assert len(every) > 50
    # mixing 'all' with explicit names must not duplicate
    assert len(resolve_dhasas(["vimsottari", "all"])) == len(every)


def test_all_dhasas_mostly_build_and_failures_are_reported(base_record_dict_module):
    """'--dhasa all' is best-effort: a system that cannot apply becomes a warning."""
    report = build_report(BirthRecord.from_dict(base_record_dict_module), dhasas=["all"])
    built = [s for s in report.sections if s.title.startswith("Dhasa-Bhukthi")]
    assert len(built) > 50
    # the four annual/varsha systems need arguments a natal chart has no value for
    assert all(w.startswith("Dhasa-Bhukthi") for w in report.warnings)
    assert len(report.warnings) < 8


# --- regressions found in review ---------------------------------------

def test_ashtakavarga_last_row_is_lagna_not_rahu(built_report):
    """BAV rows are the 7 grahas THEN the lagna; Rahu/Ketu have no BAV.

    PLANET_NAMES[7] is Raagu, so slicing to len(bav) mislabels the lagna row.
    """
    labels = [row[0] for row in built_report.section("Ashtakavarga").rows]
    assert labels[-2] == "Lagna"
    assert labels[-1] == "Sarva"
    assert "Raagu☊" not in labels and "Kethu☋" not in labels


def test_ashtakavarga_totals_are_the_classical_values(built_report):
    """Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39."""
    rows = {r[0]: sum(int(c) for c in r[1:])
            for r in built_report.section("Ashtakavarga").rows}
    assert [rows["Sun☉"], rows["Moon☾"], rows["Mars♂"], rows["Mercury☿"],
            rows["Jupiter♃"], rows["Venus♀"], rows["Saturn♄"]] == [48, 49, 39, 54, 56, 52, 39]
    # Sarva is the sum of the seven grahas only - the lagna row is excluded
    assert rows["Sarva"] == 337


def test_d1_positions_are_a_named_section_not_a_leftover_bucket(built_report):
    """The D-1 keys carry no '(D1)', so they used to land under 'Chart Summary'."""
    assert built_report.section("Chart Summary") is None
    d1 = built_report.section("Positions — Raasi (D1)")
    assert d1 is not None and len(d1.pairs) > 20
    # the redundant "Raasi-" prefix is stripped from every label
    assert all(not k.startswith("Raasi-") for k, _ in d1.pairs)
    assert any(k.startswith("Sun") for k, _ in d1.pairs)


def test_arudha_keys_are_not_labelled_as_positions(built_report):
    """'D-1-Arudha Lagna' is an arudha pada, not a planetary position."""
    section = built_report.section("Arudha Padas — D-1")
    assert section is not None
    assert any("Arudha Lagna" in k for k, _ in section.pairs)
    assert built_report.section("Positions — D-1") is None


def test_ashtakavarga_sign_headers_are_uniform(built_report):
    """Variation selectors used to eat a character from some abbreviations."""
    headers = built_report.section("Ashtakavarga").headers[1:]
    assert len(headers) == 12
    assert len({len(h) for h in headers}) == 1, headers


# --- strengths and special points ---------------------------------------

def test_sphuta_section(built_report):
    section = built_report.section("Sphuta")
    assert section is not None and len(section.pairs) == 14
    assert any("Tri Sphuta" in k for k, _ in section.pairs)


def test_shad_bala_rows_and_arithmetic(built_report):
    """Row 6 must equal the sum of the six component balas; row 7 is /60."""
    section = built_report.section("Shadh Bala")
    assert len(section.rows) == 9
    assert section.headers[0] == "Strength" and len(section.headers) == 8   # + 7 grahas
    col = 1                                   # the Sun column
    components = sum(float(section.rows[i][col]) for i in range(6))
    total = float(section.rows[6][col])
    assert components == pytest.approx(total, abs=0.01)
    assert float(section.rows[7][col]) == pytest.approx(total / 60.0, abs=0.01)


def test_bhava_bala_is_twelve_houses(built_report):
    section = built_report.section("Bhava Bala")
    assert len(section.rows) == 12
    assert section.rows[0][0].endswith("-1") and section.rows[-1][0].endswith("-12")


def test_planet_keyed_balas_have_one_row_per_graha(built_report):
    for title in ("Varga Amsa Vimsoka Bala", "Varga Amsa Vaiseshikamsa  Bala",
                  "Harsha Pancha Dwadhasa Vargeeya bala"):
        section = built_report.section(title)
        assert section is not None, title
        assert len(section.rows) == 7, title          # Sun..Saturn, no nodes
        assert all("\n" not in c for row in section.rows for c in row)


def test_bhava_chart_is_split_into_diagram_and_cusps(built_report):
    """One section would render as either the chart or the table, never both."""
    diagram = built_report.section("Bhava Chart")
    cusps = built_report.section("Bhava Chart — Cusps")
    assert diagram is not None and diagram.chart is not None and not diagram.rows
    assert cusps is not None and cusps.chart is None and len(cusps.rows) == 12


def test_bhava_cusps_centre_house_one_on_the_ascendant(built_report):
    """Bhava madhya convention: the lagna degree is the MIDDLE of house 1."""
    cusps = built_report.section("Bhava Chart — Cusps")
    middle_of_house_1 = cusps.rows[0][2]
    asc = dict(built_report.section("Positions — Raasi (D1)").pairs)
    asc_value = [v for k, v in asc.items() if k.startswith("Ascendant")][0]
    lagna_degree = '4° 55’ 55"'                                  # Leo 4°55'55"
    assert lagna_degree in middle_of_house_1 and lagna_degree in asc_value


def test_bhava_chart_differs_from_the_rasi_chart(built_report):
    """Cusp-based houses move planets that sit within 15 deg of a boundary."""
    rasi = _divisional(built_report)[0].chart
    bhava = built_report.section("Bhava Chart").chart
    assert bhava.occupants != rasi.occupants


# --- dhasa calling conventions ------------------------------------------

def test_every_dhasa_system_builds(base_record_dict_module):
    """All 60 systems, no warnings: they do not share a call signature."""
    from pyjhora_batch.report_data import available_dhasas
    report = build_report(BirthRecord.from_dict(base_record_dict_module), dhasas=["all"])
    built = [s for s in report.sections if s.title.startswith("Dhasa-Bhukthi")]
    assert len(built) == len(available_dhasas()) == 60
    assert report.warnings == []


@pytest.mark.parametrize("name", ["Aayu", "Patyayini", "Varsha Vimsottari",
                                  "Varsha Narayana"])
def test_previously_failing_dhasas_now_produce_rows(base_record_dict_module, name):
    """These four raised TypeError/KeyError when called as (dob, tob, place)."""
    report = build_report(BirthRecord.from_dict(base_record_dict_module), dhasas=["all"])
    section = report.section(f"Dhasa-Bhukthi — {name}")
    assert section is not None and len(section.rows) > 10


def test_varsha_vimsottari_covers_the_birth_year(base_record_dict_module):
    """Mudda takes years-1, as the engine's own _get_annual_dhasa_bhukthi does.

    Passing `years` instead pushed the varsha a whole year late.
    """
    report = build_report(BirthRecord.from_dict(base_record_dict_module),
                          dhasas=["varsha_vimsottari"])
    starts = [row[1][:10] for row in
              report.section("Dhasa-Bhukthi — Varsha Vimsottari").rows]
    assert starts[0] < "1985-06-15" <= starts[-1]     # brackets the birth date
    assert starts[-1] < "1986-06-01"                  # and only about one year


def test_dhasa_call_args_follow_the_signature():
    """The mapping is signature-driven, not a fixed (dob, tob, place) triple."""
    from pyjhora_batch.report_data import _Builder
    b = _Builder(BirthRecord.from_dict({
        "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
        "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5}), ("vimsottari",))

    def standard(dob, tob, place, **kw): ...
    def annual(dob, tob, place, years, divisional_chart_factor=1): ...
    def mudda(jd, place, years, divisional_chart_factor=1): ...
    def none_needed(divisional_chart_factor=1, **kw): ...

    assert len(b._dhasa_call_args(standard, "vimsottari")) == 3
    assert len(b._dhasa_call_args(annual, "varsha_narayana")) == 4
    assert len(b._dhasa_call_args(mudda, "varsha_vimsottari")) == 3
    assert b._dhasa_call_args(none_needed, "patyayini") == []


def test_aayu_type_sentinel_is_worked_around():
    """initialize_runtime turns AAYU_TYPE.NONE (None) into the string 'NONE'."""
    from jhora import config, const
    config.initialize_runtime(force_reload=True, silent=True)
    assert const.AAYU_TYPE_DEFAULT == "NONE"     # the corrupted sentinel
    from pyjhora_batch.report_data import _Builder
    b = _Builder(BirthRecord.from_dict({
        "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
        "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5}), ("aayu",))
    assert b._dhasa_kwargs("aayu")["aayur_type"] in (0, 1, 2, "L")
    assert b._dhasa_kwargs("vimsottari") == {}


# --- spouse columns / marriage compatibility ----------------------------

_SPOUSE_BIRTH = {"spouse_name": "Latha Menon", "spouse_dob": "1993,8,22",
                 "spouse_tob": "09:30:00", "spouse_place": "Jaipur",
                 "spouse_lat": 26.9124, "spouse_long": 75.7873, "spouse_tz": 5.5}


def _with(**extra):
    return BirthRecord.from_dict({
        "name": "Test Person", "date_of_birth": "1985,6,15",
        "time_of_birth": "10:30:00", "place_name": "Ujjain",
        "latitude": 23.5, "longitude": 75.75, "timezone": 5.5,
        "gender": "male", **extra})


def test_spouse_columns_accept_aliases():
    rec = _with(**_SPOUSE_BIRTH)
    assert rec.spouse_name == "Latha Menon"
    assert rec.spouse_date_of_birth == "1993,8,22"
    assert rec.spouse_latitude == 26.9124 and rec.spouse_timezone == 5.5
    assert rec.has_spouse_birth_data() and rec.has_spouse()


def test_spouse_star_columns_are_enough_on_their_own():
    rec = _with(spouse_star="Swaathi", spouse_pada=1)
    assert not rec.has_spouse_birth_data()
    assert rec.has_spouse_star() and rec.has_spouse()


def test_no_spouse_columns_is_valid_and_yields_no_section():
    rec = _with()
    assert not rec.has_spouse()
    report = build_report(rec)
    assert report.section("Marriage Compatibility") is None
    assert report.warnings == []


@pytest.mark.parametrize("bad", [
    {"spouse_dob": "22-08-1993"},
    {"spouse_tob": "9.30am"},
    {"spouse_pada": 5},
    {"spouse_lat": "north"},
    {"compatibility_method": "vedic"},
])
def test_bad_spouse_input_is_rejected(bad):
    with pytest.raises(Exception):
        _with(**bad)


def test_compatibility_method_defaults_from_chart_type():
    assert _with().resolved_compatibility_method() == "south"       # south_indian
    assert _with(chart_type="north_indian").resolved_compatibility_method() == "north"
    # an explicit column always wins
    assert _with(compatibility_method="north").resolved_compatibility_method() == "north"


def test_both_input_routes_give_the_same_star():
    """Birth details -> Moon -> nakshatra/pada must match the star given directly."""
    from_birth = build_report(_with(**_SPOUSE_BIRTH)).section("Marriage Compatibility")
    from_star = build_report(_with(spouse_star="Swaathi", spouse_pada=1)
                             ).section("Marriage Compatibility")
    assert dict(from_birth.pairs)["Spouse star"] == dict(from_star.pairs)["Spouse star"]
    assert "computed from" in dict(from_birth.pairs)["Spouse star source"]
    assert "supplied" in dict(from_star.pairs)["Spouse star source"]


def test_north_scoring_is_out_of_36():
    section = build_report(_with(compatibility_method="north",
                                 **_SPOUSE_BIRTH)).section("Marriage Compatibility")
    assert section.headers == ["Koota", "Score", "Max"]
    assert dict(section.pairs)["Score"].endswith("/ 36")
    assert len(section.rows) == 12          # 8 kootas + 4 extra poruthams
    total = sum(float(r[1]) for r in section.rows[:8])
    assert float(dict(section.pairs)["Score"].split("/")[0]) == pytest.approx(total)


def test_south_scoring_is_ten_poruthams():
    section = build_report(_with(compatibility_method="south",
                                 **_SPOUSE_BIRTH)).section("Marriage Compatibility")
    assert section.headers == ["Porutham", "Agrees"]
    assert len(section.rows) == 10
    passed = sum(1 for r in section.rows if r[1] == "Yes")
    assert dict(section.pairs)["Score"] == f"{passed} / 10"


def test_gender_decides_which_partner_is_the_boy():
    """Several kootas are asymmetric, so the roles must not be arbitrary."""
    male = build_report(_with(gender="male", **_SPOUSE_BIRTH)).section("Marriage Compatibility")
    female = build_report(_with(gender="female", **_SPOUSE_BIRTH)).section("Marriage Compatibility")
    assert dict(male.pairs)["Boy / Girl"] != dict(female.pairs)["Boy / Girl"]
    assert dict(male.pairs)["Boy / Girl"].startswith("Bharani")   # native is the boy


def test_spouse_gender_overrides_the_inference():
    rec = _with(gender="male", spouse_gender="male", **_SPOUSE_BIRTH)
    section = build_report(rec).section("Marriage Compatibility")
    # spouse stated as male -> the native is treated as the girl
    assert dict(section.pairs)["Boy / Girl"].startswith("Swaathi")


def test_unknown_star_name_is_reported_clearly():
    report = build_report(_with(spouse_star="Nonesuch", spouse_pada=1))
    assert report.section("Marriage Compatibility") is None
    assert any("Nonesuch" in w for w in report.warnings)
