"""pyjhora_batch — a thin batch layer on top of PyJHora.

Reuses PyJHora's astrology engine; never reimplements calculations. Each record
can produce three artifacts:

* ``report_data.build_report`` extracts the whole horoscope as structured data
  (no Qt), which ``text_writer`` and ``pdf_writer`` render as a ``.txt`` and a
  vector ``.pdf``.
* ``jhd_writer.write_jhd`` writes the Jagannatha Hora ``.jhd`` seed file.
* ``wrapper.generate_pdf`` is the legacy screenshot PDF (drives the Qt GUI).

``engine.run_csv`` / ``engine.run_batch`` drive all of it over many records.
"""

from .wrapper import BirthRecord, RecordError, ensure_app, generate_pdf
from .jhd_writer import build_jhd, write_jhd
from .report_data import Report, Section, build_report
from .text_writer import render_text, write_text
from .engine import (PDF_MODES, BatchSummary, RecordResult, run_batch, run_csv,
                     run_excel, default_worker_count)

__all__ = [
    "BirthRecord", "RecordError", "ensure_app", "generate_pdf",
    "build_jhd", "write_jhd",
    "Report", "Section", "build_report",
    "render_text", "write_text",
    "PDF_MODES", "BatchSummary", "RecordResult", "run_batch", "run_csv",
    "run_excel", "default_worker_count",
]


def __getattr__(name):
    # pdf_writer imports reportlab; keep that optional for .txt/.jhd-only users.
    if name in ("render_pdf", "write_pdf_report"):
        from . import pdf_writer
        return getattr(pdf_writer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
