"""Render a :class:`~pyjhora_batch.report_data.Report` as a plain-text file.

Fixed-width output meant to be read in a terminal, printed, or pasted into an
email. Tables wrap inside their columns rather than overflowing the page width,
so a long yoga description stays inside its column instead of destroying the
alignment of every row after it.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List, Sequence

from .report_data import ChartDiagram, Report, Section, build_report

DEFAULT_WIDTH = 100
_MIN_COL = 8

#: Sign index -> (row, col) in the South Indian 4x4 ring, matching
#: SouthIndianChart._zodiac_symbols in jhora/ui/chart_styles.py.
_SOUTH_CELLS = {
    11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3),
    10: (1, 0),                       3: (1, 3),
    9: (2, 0),                        4: (2, 3),
    8: (3, 0), 7: (3, 1), 6: (3, 2), 5: (3, 3),
}
_SIGN_ABBR = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi",
              "Li", "Sc", "Sg", "Cp", "Aq", "Pi")


def _rule(char: str, width: int) -> str:
    return char * width


def _wrap(text: str, width: int) -> List[str]:
    """Wrap one cell/paragraph, preserving deliberate blank lines."""
    lines: List[str] = []
    for para in str(text).split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=max(width, _MIN_COL)) or [""])
    return lines or [""]


def _render_pairs(pairs: Sequence, width: int) -> List[str]:
    label_w = min(max((len(str(k)) for k, _ in pairs), default=0), width // 2)
    value_w = width - label_w - 3
    out: List[str] = []
    for key, value in pairs:
        wrapped = _wrap(value, value_w)
        out.append(f"{str(key)[:label_w]:<{label_w}} : {wrapped[0]}")
        for cont in wrapped[1:]:
            out.append(f"{'':<{label_w}}   {cont}")
    return out


def _column_widths(headers: Sequence[str], rows: Sequence[Sequence[str]],
                   width: int) -> List[int]:
    """Distribute the available width across columns, favouring wide content."""
    ncols = max([len(headers)] + [len(r) for r in rows]) if rows or headers else 0
    if ncols == 0:
        return []
    # A column's natural width is its widest cell, capped so that one very long
    # cell cannot claim the whole line. The cap must stay well above short
    # labels like "Raasi Adhipathi", which used to wrap with 80 columns spare.
    natural = [len(str(headers[i])) if i < len(headers) else 0 for i in range(ncols)]
    for row in rows:
        for i, cell in enumerate(row):
            natural[i] = max(natural[i], min(len(str(cell)), 48))
    budget = width - 3 * (ncols - 1)
    total = sum(natural) or 1
    if total <= budget:
        return natural
    # scale down proportionally, but never below a readable minimum
    widths = [max(_MIN_COL, int(n * budget / total)) for n in natural]
    while sum(widths) > budget and max(widths) > _MIN_COL:
        widths[widths.index(max(widths))] -= 1
    return widths


def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]],
                  width: int) -> List[str]:
    widths = _column_widths(headers, rows, width)
    if not widths:
        return []
    out: List[str] = []
    if headers:
        out.append("   ".join(f"{str(h)[:w]:<{w}}" for h, w in zip(headers, widths)))
        out.append("   ".join("-" * w for w in widths))
    for row in rows:
        cells = [_wrap(row[i] if i < len(row) else "", widths[i])
                 for i in range(len(widths))]
        height = max(len(c) for c in cells)
        for line_no in range(height):
            parts = []
            for i, w in enumerate(widths):
                text = cells[i][line_no] if line_no < len(cells[i]) else ""
                parts.append(f"{text:<{w}}")
            out.append("   ".join(parts).rstrip())
    return out


def _render_chart(diagram: ChartDiagram, width: int) -> List[str]:
    """Draw the chart as a South Indian ASCII grid.

    The 4x4 ring with an open middle is the one chart layout that survives in
    fixed-width text, so it is used for every style; each cell is annotated with
    its house number so North Indian readers still get the house sequence.
    """
    houses = {sign: h + 1 for h, sign in enumerate(diagram.house_order())}
    # 4 cells + 5 border columns must fit; floor at 8 so a narrow page
    # truncates names rather than overflowing the requested width
    cell_w = max(8, min(22, (width - 5) // 4))
    cell_h = max(2, 1 + max((len(o) for o in diagram.occupants), default=0))

    canvas_w = 4 * (cell_w + 1) + 1
    canvas_h = 4 * (cell_h + 1) + 1
    grid = [[" "] * canvas_w for _ in range(canvas_h)]

    def put(row, col, text):
        for i, ch in enumerate(text):
            if 0 <= row < canvas_h and 0 <= col + i < canvas_w:
                grid[row][col + i] = ch

    for sign, (r, c) in _SOUTH_CELLS.items():
        x0, y0 = c * (cell_w + 1), r * (cell_h + 1)
        # box outline; shared edges simply overwrite with the same characters
        put(y0, x0, "+" + "-" * cell_w + "+")
        put(y0 + cell_h + 1, x0, "+" + "-" * cell_w + "+")
        for dy in range(1, cell_h + 1):
            put(y0 + dy, x0, "|")
            put(y0 + dy, x0 + cell_w + 1, "|")

        header = f"{_SIGN_ABBR[sign]} H{houses[sign]}"
        if sign == diagram.ascendant:
            header += " <"                      # lagna marker
        put(y0 + 1, x0 + 1, f" {header[:cell_w - 1]}")
        for i, name in enumerate(diagram.occupants[sign]):
            put(y0 + 2 + i, x0 + 1, f" {name[:cell_w - 1]}")

    return ["".join(row).rstrip() for row in grid]


def _render_section(section: Section, width: int) -> List[str]:
    out = [section.title, _rule("-", min(len(section.title), width))]
    if section.note:
        out.extend(_wrap(f"Note: {section.note}", width) + [""])
    if section.chart is not None:
        # the diagram carries the same data as the sign/occupant table
        out.extend(_render_chart(section.chart, width))
        out.append("")
        return out
    if section.pairs:
        out.extend(_render_pairs(section.pairs, width))
    if section.rows:
        if section.pairs:
            out.append("")
        out.extend(_render_table(section.headers, section.rows, width))
    if section.body:
        if section.pairs or section.rows:
            out.append("")
        for para in section.body.split("\n"):
            out.extend(_wrap(para, width) if para.strip() else [""])
    out.append("")
    return out


def render_text(report: Report, *, width: int = DEFAULT_WIDTH) -> str:
    """Return the full report as plain text."""
    rec = report.record
    title = rec.name or rec.place_name
    lines = [_rule("=", width), f"HOROSCOPE REPORT — {title}", _rule("=", width), ""]

    for section in report.sections:
        lines.extend(_render_section(section, width))

    if report.warnings:
        lines.extend([_rule("=", width), "Sections that could not be generated",
                      _rule("-", width)])
        lines.extend(f"  - {w}" for w in report.warnings)
        lines.append("")

    lines.append(_rule("=", width))
    lines.append(f"Generated by pyjhora_batch — {len(report.sections)} sections")
    return "\n".join(lines) + "\n"


def write_text(record, out_path, *, width: int = DEFAULT_WIDTH,
               report: Report | None = None, **build_kwargs) -> Path:
    """Build (or reuse) a report for ``record`` and write it as ``out_path``."""
    report = report if report is not None else build_report(record, **build_kwargs)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_text(report, width=width), encoding="utf-8")
    return out_path
