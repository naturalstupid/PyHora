import pytest

from pyjhora_batch.pdf_writer import (_col_widths, _to_ascii, render_pdf,
                                      resolve_font)
from pyjhora_batch.report_data import Report, Section
from pyjhora_batch.wrapper import BirthRecord

pypdf = pytest.importorskip("pypdf")


def _record():
    return BirthRecord.from_dict({
        "name": "Test Person", "date_of_birth": "1985,6,15",
        "time_of_birth": "10:30:00", "place_name": "Ujjain",
        "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5, "gender": "male"})


def _report(*sections):
    return Report(record=_record(), sections=list(sections))


def test_column_widths_fill_exactly_the_available_width():
    widths = _col_widths(["A", "B", "C"], [["x", "yy", "zzz"]], avail=400.0)
    assert sum(widths) == pytest.approx(400.0)
    assert all(w > 0 for w in widths)


def test_column_widths_handle_no_columns():
    assert _col_widths([], [], avail=400.0) == []


def test_ascii_fallback_replaces_symbols():
    out = _to_ascii("Sun☉ in ♑Capricorn")
    assert "☉" not in out and "♑" not in out
    assert "(Su)" in out and "Capricorn" in out


def test_pdf_contains_real_text_not_images(tmp_path):
    """The whole point of this renderer: vector text, zero rasterised pages."""
    target = tmp_path / "report.pdf"
    render_pdf(_report(
        Section("Birth Details", pairs=[("Name", "Test Person")]),
        Section("Yogas", headers=["Yoga", "Description"],
                rows=[["Nipuna Yoga", "Sun and Mercury are together."]]),
        Section("Notes", body="Narrative paragraph."),
    ), target)

    reader = pypdf.PdfReader(str(target))
    page = reader.pages[0]
    text = page.extract_text()
    assert list(page.images) == []
    assert "Test Person" in text
    assert "Nipuna Yoga" in text
    assert "Narrative paragraph." in text


def test_pdf_is_small(tmp_path):
    """A screenshot-based page of the same content ran to megabytes."""
    target = tmp_path / "report.pdf"
    render_pdf(_report(Section("Birth Details", pairs=[("Name", "Test Person")])), target)
    assert target.stat().st_size < 400_000


def test_pdf_renders_astro_symbols_when_a_unicode_font_exists(tmp_path):
    if resolve_font() is None:
        pytest.skip("no Unicode font on this machine")
    target = tmp_path / "symbols.pdf"
    render_pdf(_report(Section("Positions", pairs=[("Sun☉", "♑Capricorn 10° 13’ 41\"")])),
               target)
    text = pypdf.PdfReader(str(target)).pages[0].extract_text()
    assert "☉" in text and "♑" in text


def test_warnings_are_surfaced_in_the_pdf(tmp_path):
    target = tmp_path / "warned.pdf"
    report = _report(Section("Birth Details", pairs=[("Name", "Test Person")]))
    report.warnings.append("Doshas: KeyError: 0")
    render_pdf(report, target)
    text = pypdf.PdfReader(str(target)).pages[0].extract_text()
    assert "could not be generated" in text
    assert "KeyError" in text


def test_render_pdf_creates_parent_directories(tmp_path):
    target = tmp_path / "a" / "b" / "report.pdf"
    render_pdf(_report(Section("X", body="y")), target)
    assert target.is_file()


# --- vector chart diagrams ---------------------------------------------

from pyjhora_batch.report_data import ChartDiagram
from pyjhora_batch.pdf_writer import (ChartFlowable, _NORTH_HOUSE_CENTROIDS,
                                      _SOUTH_CELLS)


def _diagram(style="south_indian"):
    occ = [[] for _ in range(12)]
    occ[0] = ["Sun", "Mercury"]
    occ[4] = ["Ascendant"]
    occ[9] = ["Moon", "Saturn", "Raagu"]
    return ChartDiagram("Raasi (D1)", occ, ascendant=4, style=style)


def test_south_cells_cover_every_sign_on_the_ring():
    assert sorted(_SOUTH_CELLS) == list(range(12))
    cells = set(_SOUTH_CELLS.values())
    assert len(cells) == 12
    # the 2x2 centre is deliberately unoccupied
    assert cells.isdisjoint({(1, 1), (1, 2), (2, 1), (2, 2)})
    # Pisces top-left, Aries next to it, running clockwise
    assert _SOUTH_CELLS[11] == (0, 0) and _SOUTH_CELLS[0] == (0, 1)


def test_north_centroids_are_twelve_distinct_points_inside_the_box():
    assert len(_NORTH_HOUSE_CENTROIDS) == 12
    assert len(set(_NORTH_HOUSE_CENTROIDS)) == 12
    assert all(0 < x < 1 and 0 < y < 1 for x, y in _NORTH_HOUSE_CENTROIDS)
    # house 1 sits top-centre, house 7 directly opposite
    assert _NORTH_HOUSE_CENTROIDS[0][0] == pytest.approx(0.5)
    assert _NORTH_HOUSE_CENTROIDS[6][0] == pytest.approx(0.5)
    assert _NORTH_HOUSE_CENTROIDS[0][1] < _NORTH_HOUSE_CENTROIDS[6][1]


def test_chart_flowable_is_square_and_fits_the_frame():
    flow = ChartFlowable(_diagram(), 250.0, "Helvetica")
    assert flow.wrap(180.0, 800.0) == (180.0, 180.0)     # shrinks to fit
    assert flow.wrap(400.0, 800.0) == (180.0, 180.0)     # never grows back


@pytest.mark.parametrize("style", ["south_indian", "north_indian"])
def test_chart_is_drawn_as_vector_text_not_an_image(tmp_path, style):
    target = tmp_path / f"{style}.pdf"
    render_pdf(_report(Section("Raasi (D1)", chart=_diagram(style))), target)
    page = pypdf.PdfReader(str(target)).pages[0]
    text = page.extract_text()
    assert list(page.images) == []
    for planet in ("Sun", "Mercury", "Ascendant", "Moon", "Saturn", "Raagu"):
        assert planet in text
    assert "Le" in text and "Ar" in text                 # sign abbreviations


def test_north_chart_labels_houses_from_the_ascendant(tmp_path):
    target = tmp_path / "north.pdf"
    render_pdf(_report(Section("D1", chart=_diagram("north_indian"))), target)
    text = pypdf.PdfReader(str(target)).pages[0].extract_text()
    assert "Lagna" in text                               # house 1 is marked


def test_chart_section_omits_the_duplicate_table(tmp_path):
    target = tmp_path / "chart.pdf"
    render_pdf(_report(Section("Raasi (D1)", headers=["Rasi", "Occupants"],
                               rows=[["Aries", "Sun Mercury"]],
                               chart=_diagram())), target)
    text = pypdf.PdfReader(str(target)).pages[0].extract_text()
    assert "Occupants" not in text
