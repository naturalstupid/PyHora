"""Render a :class:`~pyjhora_batch.report_data.Report` as a true vector PDF.

The GUI's ``save_as_pdf`` pastes ~975x770 JPEG screenshots of Qt widgets onto
A4 — roughly 130 DPI of lossy pixels, ~10 MB, and nothing in it is real text.
This module lays the same content out with ReportLab instead, so glyphs stay
vector outlines: sharp at any zoom, selectable, searchable, and a fraction of
the size.

Fonts
-----
The engine's strings are full of astrological symbols (Sun☉, ♑Capricorn, ℒ).
The built-in Type1 faces cannot render those, so a Unicode TrueType font is
located at import time (see :func:`resolve_font`). If none is found the text is
transliterated to ASCII rather than emitting black boxes, and the report says so.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

from .report_data import ChartDiagram, Report, build_report

# --- chart geometry ---------------------------------------------------
# South Indian: signs sit in fixed cells of a 4x4 ring, Pisces top-left and
# running clockwise. Taken from SouthIndianChart._zodiac_symbols in
# jhora/ui/chart_styles.py so the layout matches what the GUI draws.
_SOUTH_CELLS = {
    11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3),
    10: (1, 0),                       3: (1, 3),
    9: (2, 0),                        4: (2, 3),
    8: (3, 0), 7: (3, 1), 6: (3, 2), 5: (3, 3),
}

# North Indian: houses are fixed and signs rotate. The outer square, its two
# diagonals and the diamond on the four edge midpoints cut the box into twelve
# regions — four kites touching the edge midpoints and eight corner triangles.
# These are the exact centroids of those regions in a unit square measured DOWN
# from the top-left, in house order (H1 = top kite, then counter-clockwise).
# The ordering matches NorthIndianChart._north_label_positions in
# jhora/ui/chart_styles.py; only the anchoring differs — PyJHora left-aligns
# text at a tuned offset, here it is centred in the region.
_K = 0.25            # kite centroid, measured in from its edge
_TA, _TB = 0.25, 1.0 / 12.0     # corner-triangle centroid (long side, short side)
_NORTH_HOUSE_CENTROIDS = [
    (0.5, _K),        (_TA, _TB),       (_TB, _TA),       (_K, 0.5),
    (_TB, 1 - _TA),   (_TA, 1 - _TB),   (0.5, 1 - _K),    (1 - _TA, 1 - _TB),
    (1 - _TB, 1 - _TA), (1 - _K, 0.5),  (1 - _TB, _TA),   (1 - _TA, _TB),
]

#: Short sign labels; the engine's own names carry glyphs we may not be able to
#: draw in ASCII fallback mode, so the diagram uses these instead.
_SIGN_ABBR = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi",
              "Li", "Sc", "Sg", "Cp", "Aq", "Pi")

#: Probe characters that a usable report font must be able to draw.
_GLYPH_PROBE = "♑☉☾♂☿♃♀♄☊☋ℒ°"

#: Searched in order; the first file that exists and covers _GLYPH_PROBE wins.
FONT_CANDIDATES: Tuple[str, ...] = (
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "C:/Windows/Fonts/arialuni.ttf",
    "C:/Windows/Fonts/seguisym.ttf",
)

_ASCII_FALLBACK = {
    "☉": "(Su)", "☾": "(Mo)", "♂": "(Ma)", "☿": "(Me)", "♃": "(Ju)", "♀": "(Ve)",
    "♄": "(Sa)", "☊": "(Ra)", "☋": "(Ke)", "ℒ": "(Asc)", "°": " deg ", "’": "'",
    "♈": "", "♉": "", "♊": "", "♋": "", "♌": "", "♍": "",
    "♎": "", "♏": "", "♐": "", "♑": "", "♒": "", "♓": "", "︎": "",
}

_registered_font: Optional[str] = None


def resolve_font(candidates: Sequence[str] = FONT_CANDIDATES) -> Optional[str]:
    """Return the path of the first candidate that covers the astro symbols."""
    override = os.environ.get("PYJHORA_REPORT_FONT")
    ordered = ([override] if override else []) + list(candidates)
    for path in ordered:
        if not path or not os.path.exists(path):
            continue
        try:
            face = TTFont("_probe", path).face
            if all(ord(ch) in face.charToGlyph for ch in _GLYPH_PROBE):
                return path
        except Exception:  # noqa: BLE001 - an unreadable font is simply not a candidate
            continue
    return None


def _ensure_font() -> Optional[str]:
    """Register the Unicode font once; return its reportlab name or None."""
    global _registered_font
    if _registered_font is not None:
        return _registered_font or None
    path = resolve_font()
    if path is None:
        _registered_font = ""
        return None
    name = "JHoraUnicode"
    pdfmetrics.registerFont(TTFont(name, path))
    # No matching bold face ships with these files; map bold onto the same
    # outlines so <b> never falls back to a font that lacks the symbols.
    pdfmetrics.registerFont(TTFont(name + "-Bold", path))
    pdfmetrics.registerFontFamily(name, normal=name, bold=name + "-Bold",
                                  italic=name, boldItalic=name + "-Bold")
    _registered_font = name
    return name


def _to_ascii(text: str) -> str:
    for symbol, replacement in _ASCII_FALLBACK.items():
        text = text.replace(symbol, replacement)
    return text.encode("ascii", "ignore").decode("ascii")


def _escape(text: str, ascii_only: bool) -> str:
    text = str(text)
    if ascii_only:
        text = _to_ascii(text)
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class _Styles:
    def __init__(self, font: Optional[str]):
        self.ascii_only = font is None
        body_font = font or "Helvetica"
        bold_font = (font + "-Bold") if font else "Helvetica-Bold"
        self.title = ParagraphStyle("title", fontName=bold_font, fontSize=18,
                                    leading=22, spaceAfter=2, textColor=colors.HexColor("#1a1a1a"))
        self.subtitle = ParagraphStyle("subtitle", fontName=body_font, fontSize=9.5,
                                       leading=13, textColor=colors.HexColor("#555555"),
                                       spaceAfter=10)
        self.heading = ParagraphStyle("heading", fontName=bold_font, fontSize=11.5,
                                      leading=14, spaceBefore=12, spaceAfter=5,
                                      textColor=colors.HexColor("#20364f"))
        self.body = ParagraphStyle("body", fontName=body_font, fontSize=8.6,
                                   leading=11.4, alignment=TA_LEFT, spaceAfter=4)
        self.cell = ParagraphStyle("cell", fontName=body_font, fontSize=7.8, leading=10)
        self.cell_bold = ParagraphStyle("cellb", parent=self.cell, fontName=bold_font)
        self.note = ParagraphStyle("note", parent=self.body, fontSize=8,
                                   textColor=colors.HexColor("#8a3b3b"))
        self.chart_font = body_font


class ChartFlowable(Flowable):
    """Draws one divisional chart as vector lines and text.

    Square by construction. ``occupants`` is sign-indexed; the North Indian
    style rotates it so house 1 is the ascendant, which is why both styles can
    share the same :class:`~pyjhora_batch.report_data.ChartDiagram`.
    """

    def __init__(self, diagram: ChartDiagram, size: float, font: str,
                 ascii_only: bool = False):
        super().__init__()
        self.diagram = diagram
        self.size = size
        self.font = font
        self.ascii_only = ascii_only

    def wrap(self, availWidth, availHeight):
        self.size = min(self.size, availWidth)
        return self.size, self.size

    # -- helpers --------------------------------------------------------

    def _label(self, text: str) -> str:
        return _to_ascii(text) if self.ascii_only else text

    def _planet_font_size(self) -> float:
        busiest = max((len(o) for o in self.diagram.occupants), default=0)
        cell = self.size / 4.0
        # keep the fullest cell's stack inside its box
        return max(4.2, min(7.5, cell / max(busiest, 1) / 1.45))

    def _draw_stack(self, x, y, width, names, size):
        """Draw planet names top-down from (x, y-as-top), clipped to width."""
        c = self.canv
        c.setFont(self.font, size)
        c.setFillColor(colors.HexColor("#14304d"))
        line = size * 1.22
        for i, name in enumerate(names):
            text = self._label(name)
            while text and c.stringWidth(text, self.font, size) > width:
                text = text[:-1]
            c.drawString(x, y - (i + 1) * line, text)

    # -- styles ---------------------------------------------------------

    def _draw_south(self):
        c = self.canv
        s = self.size
        cell = s / 4.0
        size = self._planet_font_size()

        c.setStrokeColor(_GRID_STRONG)
        c.setLineWidth(0.7)
        for sign, (row, col) in _SOUTH_CELLS.items():
            # ReportLab's origin is bottom-left; the table above is top-down
            x = col * cell
            y = s - (row + 1) * cell
            c.rect(x, y, cell, cell, stroke=1, fill=0)

            if sign == self.diagram.ascendant:
                # the traditional lagna mark: a stroke across the cell corner.
                # Bottom-left, because the top-left holds the sign abbreviation
                # and the planet stack grows down from there.
                c.setStrokeColor(_ASC_MARK)
                c.setLineWidth(1.0)
                c.line(x, y + cell * 0.26, x + cell * 0.26, y)
                c.setStrokeColor(_GRID_STRONG)
                c.setLineWidth(0.7)

            c.setFont(self.font, 5.4)
            c.setFillColor(_SIGN_COLOR)
            c.drawString(x + 2, y + cell - 6.5, _SIGN_ABBR[sign])
            self._draw_stack(x + 2, y + cell - 6.0, cell - 4,
                             self.diagram.occupants[sign], size)

    def _draw_north(self):
        c = self.canv
        s = self.size
        size = self._planet_font_size()

        c.setStrokeColor(_GRID_STRONG)
        c.setLineWidth(0.7)
        c.rect(0, 0, s, s, stroke=1, fill=0)
        c.line(0, 0, s, s)                       # diagonals
        c.line(0, s, s, 0)
        h = s / 2.0                              # inner diamond on the midpoints
        c.line(h, 0, s, h)
        c.line(s, h, h, s)
        c.line(h, s, 0, h)
        c.line(0, h, h, 0)

        line = size * 1.22
        for house, sign in enumerate(self.diagram.house_order()):
            fx, fy = _NORTH_HOUSE_CENTROIDS[house]
            cx = fx * s
            cy = s - fy * s                      # flip to ReportLab's y-up
            names = self.diagram.occupants[sign]
            # centre the sign label + planet stack vertically on the centroid
            top = cy + (len(names) + 1) * line / 2.0

            c.setFont(self.font, 5.4)
            c.setFillColor(_SIGN_COLOR)
            c.drawCentredString(cx, top - line * 0.8, _SIGN_ABBR[sign])
            if house == 0:
                c.setFillColor(_ASC_MARK)
                c.drawCentredString(cx, top + line * 0.35, "Lagna")

            c.setFont(self.font, size)
            c.setFillColor(colors.HexColor("#14304d"))
            for i, name in enumerate(names):
                text = self._label(name)
                while text and c.stringWidth(text, self.font, size) > s * 0.30:
                    text = text[:-1]
                c.drawCentredString(cx, top - (i + 2) * line, text)

    def draw(self):
        if self.diagram.style == "north_indian":
            self._draw_north()
        else:
            self._draw_south()


_GRID = colors.HexColor("#c9d2dc")
_GRID_STRONG = colors.HexColor("#7f8c9b")
_SIGN_COLOR = colors.HexColor("#9aa5b1")
_ASC_MARK = colors.HexColor("#c0392b")
_HEAD_BG = colors.HexColor("#e8edf3")
_ALT_BG = colors.HexColor("#f6f8fa")


def _table_style(has_header: bool) -> TableStyle:
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.25, _GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]
    if has_header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), _HEAD_BG),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_BG])]
    else:
        cmds += [("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, _ALT_BG])]
    return TableStyle(cmds)


def _col_widths(headers: Sequence[str], rows: Sequence[Sequence[str]],
                avail: float) -> List[float]:
    ncols = max([len(headers)] + [len(r) for r in rows]) if (headers or rows) else 0
    if ncols == 0:
        return []
    weights = [max(len(str(headers[i])) if i < len(headers) else 0, 1)
               for i in range(ncols)]
    for row in rows[:200]:                       # sampling is enough to size columns
        for i, cell in enumerate(row):
            weights[i] = max(weights[i], min(len(str(cell)), 90))
    total = sum(weights) or 1
    widths = [avail * w / total for w in weights]
    floor = min(28.0, avail / max(ncols, 1))
    widths = [max(w, floor) for w in widths]
    scale = avail / sum(widths)
    return [w * scale for w in widths]


def _build_flowables(report: Report, styles: _Styles, avail: float) -> list:
    esc = lambda t: _escape(t, styles.ascii_only)  # noqa: E731
    rec = report.record
    story: list = [
        Paragraph(esc(rec.name or rec.place_name), styles.title),
        Paragraph(esc(f"{rec.date_of_birth.replace(',', '-')} at {rec.time_of_birth} — "
                      f"{rec.place_name}"), styles.subtitle),
    ]

    for section in report.sections:
        block: list = [Paragraph(esc(section.title), styles.heading)]

        if section.pairs:
            rows = [[Paragraph(esc(k), styles.cell_bold), Paragraph(esc(v), styles.cell)]
                    for k, v in section.pairs]
            table = Table(rows, colWidths=[avail * 0.32, avail * 0.68], repeatRows=0)
            table.setStyle(_table_style(has_header=False))
            block.append(table)

        if section.note:
            block.append(Paragraph(esc(section.note), styles.note))

        if section.chart is not None:
            # the diagram carries the same information as the sign/occupant
            # table, so only one of the two is emitted
            block.append(ChartFlowable(section.chart, min(avail, 250.0),
                                       styles.chart_font, styles.ascii_only))
            story.append(KeepTogether(block))
            continue

        if section.rows:
            headers = list(section.headers)
            data = []
            if headers:
                data.append([Paragraph(esc(h), styles.cell_bold) for h in headers])
            for row in section.rows:
                data.append([Paragraph(esc(c), styles.cell) for c in row])
            widths = _col_widths(headers, section.rows, avail)
            table = Table(data, colWidths=widths, repeatRows=1 if headers else 0)
            table.setStyle(_table_style(has_header=bool(headers)))
            block.append(table)

        if section.body:
            for para in section.body.split("\n"):
                if para.strip():
                    block.append(Paragraph(esc(para), styles.body))
                else:
                    block.append(Spacer(1, 3))

        # Keep short blocks whole; let long tables flow across pages naturally.
        story.extend([KeepTogether(block)] if len(block) <= 2 and section.pairs
                     else block)

    if report.warnings:
        story.append(Paragraph("Sections that could not be generated", styles.heading))
        for warning in report.warnings:
            story.append(Paragraph(esc(f"• {warning}"), styles.note))
    if styles.ascii_only:
        story.append(Paragraph(
            "No Unicode font was available, so astrological symbols were replaced "
            "with ASCII abbreviations. Set PYJHORA_REPORT_FONT to a .ttf to restore them.",
            styles.note))
    return story


def render_pdf(report: Report, out_path, *, pagesize=A4, margin: float = 15 * mm) -> Path:
    """Write ``report`` to ``out_path`` as a vector PDF."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    font = _ensure_font()
    styles = _Styles(font)
    page_w, page_h = pagesize
    avail = page_w - 2 * margin

    rec = report.record
    title = rec.name or rec.place_name
    footer_font = font or "Helvetica"
    footer_text = _escape(title, styles.ascii_only)

    def _decorate(canvas, doc):
        canvas.saveState()
        canvas.setFont(footer_font, 7.5)
        canvas.setFillColor(colors.HexColor("#8a94a0"))
        canvas.drawString(margin, margin * 0.6, footer_text)
        canvas.drawRightString(page_w - margin, margin * 0.6, f"Page {doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(str(out_path), pagesize=pagesize,
                          leftMargin=margin, rightMargin=margin,
                          topMargin=margin, bottomMargin=margin,
                          title=f"Horoscope — {title}", author="pyjhora_batch")
    frame = Frame(margin, margin, avail, page_h - 2 * margin, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_decorate)])
    doc.build(_build_flowables(report, styles, avail))
    return out_path


def write_pdf_report(record, out_path, *, report: Report | None = None,
                     **build_kwargs) -> Path:
    """Build (or reuse) a report for ``record`` and write it as a vector PDF."""
    report = report if report is not None else build_report(record, **build_kwargs)
    return render_pdf(report, out_path)
