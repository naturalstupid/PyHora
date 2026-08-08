from pyjhora_batch.report_data import Report, Section
from pyjhora_batch.text_writer import _render_table, _wrap, render_text, write_text
from pyjhora_batch.wrapper import BirthRecord


def _record():
    return BirthRecord.from_dict({
        "name": "Test Person", "date_of_birth": "1985,6,15",
        "time_of_birth": "10:30:00", "place_name": "Ujjain",
        "latitude": 23.5, "longitude": 75.75,
        "timezone": 5.5, "gender": "male"})


def _report(*sections):
    return Report(record=_record(), sections=list(sections))


def test_wrap_preserves_blank_lines():
    assert _wrap("a\n\nb", 40) == ["a", "", "b"]


def test_table_columns_stay_aligned_when_a_cell_wraps():
    long_text = "word " * 40
    lines = _render_table(["A", "B"], [["short", long_text], ["x", "y"]], width=60)
    body = [ln for ln in lines[2:] if ln.strip()]
    # every rendered line must fit the page width - a wrapped cell must not
    # push the second column off the edge
    assert all(len(ln) <= 60 for ln in body)
    assert len(body) > 2                       # the long cell really did wrap


def test_render_text_includes_all_section_kinds():
    out = render_text(_report(
        Section("Pairs", pairs=[("Key", "Value")]),
        Section("Table", headers=["H1", "H2"], rows=[["a", "b"]]),
        Section("Prose", body="Some narrative text."),
    ), width=80)
    assert "HOROSCOPE REPORT — Test Person" in out
    assert "Key" in out and "Value" in out
    assert "H1" in out and "H2" in out
    assert "Some narrative text." in out


def test_render_text_reports_warnings():
    report = _report(Section("Pairs", pairs=[("K", "V")]))
    report.warnings.append("Doshas: KeyError: 0")
    out = render_text(report)
    assert "could not be generated" in out
    assert "Doshas: KeyError: 0" in out


def test_no_line_exceeds_the_requested_width():
    report = _report(Section("Prose", body="lorem ipsum dolor sit amet " * 20))
    for line in render_text(report, width=72).splitlines():
        assert len(line) <= 72


def test_write_text_creates_parent_directories(tmp_path):
    target = tmp_path / "nested" / "deeper" / "report.txt"
    written = write_text(_record(), target, report=_report(
        Section("Pairs", pairs=[("Key", "Value")])))
    assert written == target
    assert "Key" in target.read_text(encoding="utf-8")


# --- ASCII chart diagrams ----------------------------------------------

from pyjhora_batch.report_data import ChartDiagram
from pyjhora_batch.text_writer import _render_chart


def _diagram(style="south_indian"):
    occ = [[] for _ in range(12)]
    occ[0] = ["Sun", "Mercury"]          # Aries
    occ[4] = ["Ascendant"]               # Leo (the ascendant)
    occ[9] = ["Moon", "Saturn", "Raagu"]  # Capricorn
    return ChartDiagram("Raasi (D1)", occ, ascendant=4, style=style)


def test_ascii_chart_places_signs_in_the_south_indian_ring():
    lines = _render_chart(_diagram(), width=100)
    # top row runs Pisces, Aries, Taurus, Gemini left to right
    header = next(ln for ln in lines if "Pi " in ln)
    assert header.index("Pi ") < header.index("Ar ") < header.index("Ta ") < header.index("Ge ")
    # Capricorn sits on the left edge, two rows down
    assert any("Cp " in ln for ln in lines)


def test_ascii_chart_middle_is_open():
    """The 2x2 centre has no cell of its own — rows 1-2 span it as blank space."""
    lines = _render_chart(_diagram(), width=100)
    # an interior row has exactly four pipes: both outer edges plus the inner
    # edge of the left and right cells, with nothing drawn between them
    interior = [ln for ln in lines if ln.count("|") == 4]
    assert interior
    for line in interior:
        first, second = line.index("|", line.index("|") + 1), line.rindex("|", 0, line.rindex("|"))
        assert line[first + 1:second].strip() == ""
    # by contrast the top and bottom rows are divided into four cells
    assert any(ln.count("|") == 5 for ln in lines)


def test_ascii_chart_marks_the_ascendant_and_numbers_houses():
    lines = _render_chart(_diagram(), width=100)
    text = "\n".join(lines)
    assert "Le H1 <" in text          # ascendant is house 1 and flagged
    assert "Vi H2" in text            # houses continue from the ascendant
    assert "Ar H9" in text


def test_ascii_chart_shows_every_occupant():
    text = "\n".join(_render_chart(_diagram(), width=100))
    for planet in ("Sun", "Mercury", "Ascendant", "Moon", "Saturn", "Raagu"):
        assert planet in text


def test_ascii_chart_respects_the_width():
    for width in (60, 80, 100):
        assert all(len(ln) <= width for ln in _render_chart(_diagram(), width=width))


def test_chart_section_renders_the_diagram_instead_of_the_table():
    section = Section("Raasi (D1)", headers=["Rasi", "Occupants"],
                      rows=[["Aries", "Sun Mercury"]], chart=_diagram())
    out = render_text(_report(section))
    assert "+---" in out                      # the diagram is drawn
    assert "Rasi   Occupants" not in out      # the redundant table is not


def test_ascii_chart_never_overflows_a_narrow_page():
    """A floor of 12 per cell used to force 53 columns regardless of width."""
    for width in (40, 50, 60, 80, 100):
        lines = _render_chart(_diagram(), width=width)
        assert max(len(ln) for ln in lines) <= width, f"overflow at width={width}"
