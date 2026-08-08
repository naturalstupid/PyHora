"""Batch engine: turn a stream of raw rows into one PDF (+ .jhd) each, resiliently.

Responsibilities:
* Validate each record and assign deterministic, collision-free output paths in
  the main process (fast, pure) so naming never races across workers.
* Generate outputs per record, isolating failures so one bad row never stops the
  batch.
* Run either single-process (default) or across a configurable pool of worker
  processes — each worker owns its own offscreen QApplication (Qt objects cannot
  cross process boundaries), reused across the records it handles.
* Log successes/failures (console + a log file in the output dir) and emit a
  summary plus a retry CSV of the failed rows.
"""

from __future__ import annotations

import csv
import logging
import multiprocessing as mp
import os
import re
import traceback
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .readers import RawRow, read_csv
from .jhd_writer import write_jhd
from .wrapper import BirthRecord, RecordError, ensure_app, generate_pdf

#: How the PDF is produced. "vector" typesets the extracted data with ReportLab
#: (sharp, searchable, ~150 KB); "screenshot" is PyJHora's original Qt widget
#: capture (raster JPEG, ~10 MB) and is kept for visual chart diagrams.
PDF_MODES = ("vector", "screenshot")

_LOGGER_NAME = "pyjhora_batch"


@dataclass
class RecordResult:
    row_number: int
    line_number: int
    name: str
    status: str                     # "ok" | "invalid" | "error"
    output: Optional[str] = None    # PDF path
    jhd: Optional[str] = None       # JHD path (written even if the PDF fails)
    txt: Optional[str] = None       # plain-text report path
    error: Optional[str] = None
    data: dict = field(default_factory=dict)
    tb: Optional[str] = None        # full traceback for logging (not serialized)


@dataclass
class _Job:
    """A validated record with its resolved output paths, ready to render."""
    row_number: int
    line_number: int
    rec: BirthRecord
    pdf_path: Path
    jhd_path: Path
    txt_path: Path
    data: dict


@dataclass
class BatchSummary:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list = field(default_factory=list)

    @property
    def failures(self):
        return [r for r in self.results if r.status != "ok"]

    def __str__(self):
        return (f"Batch summary: {self.succeeded}/{self.total} succeeded, "
                f"{self.failed} failed")


def _slugify(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "_", (text or "").strip())
    return text.strip("_") or "chart"


def _output_name(rec: BirthRecord, raw: dict) -> str:
    """Deterministic base filename (no extension) for a record."""
    explicit = raw.get("output") or raw.get("filename")
    if explicit:
        return _slugify(Path(str(explicit)).stem)
    dob = rec.date_of_birth.replace(",", "-")
    base = rec.name or rec.place_name
    return f"{_slugify(base)}_{dob}"


def _configure_logger(out_dir: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()          # avoid duplicate handlers across runs
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO if verbose else logging.WARNING)
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = logging.FileHandler(out_dir / "batch.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger


def _prepare(rows: Iterable[RawRow], out_dir: Path) -> Tuple[List[_Job], List[RecordResult]]:
    """Validate rows and assign collision-free output paths.

    Returns (jobs, invalid_results). Validation happens up front in the main
    process so bad rows never reach a worker and filenames are globally unique.
    """
    jobs: List[_Job] = []
    invalids: List[RecordResult] = []
    used_names: set[str] = set()

    for raw in rows:
        try:
            rec = BirthRecord.from_dict(raw.data)
        except RecordError as exc:
            invalids.append(RecordResult(raw.row_number, raw.line_number,
                                         str(raw.data.get("name", "")), "invalid",
                                         error=str(exc), data=raw.data))
            continue
        base = _output_name(rec, raw.data)
        name = base
        n = 2
        while name in used_names:
            name = f"{base}_{n}"
            n += 1
        used_names.add(name)
        jobs.append(_Job(raw.row_number, raw.line_number, rec,
                         out_dir / f"{name}.pdf", out_dir / f"{name}.jhd",
                         out_dir / f"{name}.txt", raw.data))
    return jobs, invalids


def _process_job(job: _Job, *, write_pdf: bool, write_jhd_file: bool,
                 expand_all_tabs, write_txt: bool = True,
                 pdf_mode: str = "vector", dhasas=None) -> RecordResult:
    """Render one job's outputs. Never raises — encodes failure in the result.

    Outputs are produced cheapest-first so a later failure never costs an earlier
    artifact: the pure JHD, then the structured report (shared by the text and
    vector-PDF renderers so the engine runs once, not twice), then the PDF.

    In "screenshot" mode the PDF still comes from PyJHora's Qt widget capture via
    the process-local QApplication, which is why generate_pdf/ensure_app are only
    touched on that path.
    """
    jhd_written = None
    try:
        if write_jhd_file:
            write_jhd(job.rec, job.jhd_path)
            jhd_written = str(job.jhd_path)
    except Exception as exc:  # noqa: BLE001
        return RecordResult(job.row_number, job.line_number, job.rec.name, "error",
                            error=f"JHD write failed: {exc}", data=job.data,
                            tb=traceback.format_exc())

    txt_written = None
    try:
        needs_report = write_txt or (write_pdf and pdf_mode == "vector")
        report = None
        if needs_report:
            from .report_data import DEFAULT_DHASAS, build_report
            report = build_report(job.rec, dhasas=dhasas or DEFAULT_DHASAS)

        if write_txt:
            from .text_writer import write_text
            write_text(job.rec, job.txt_path, report=report)
            txt_written = str(job.txt_path)

        if write_pdf:
            if pdf_mode == "vector":
                from .pdf_writer import render_pdf
                render_pdf(report, job.pdf_path)
            else:
                generate_pdf(job.rec, job.pdf_path, expand_all_tabs=expand_all_tabs)

        return RecordResult(job.row_number, job.line_number, job.rec.name, "ok",
                            output=str(job.pdf_path) if write_pdf else None,
                            jhd=jhd_written, txt=txt_written, data=job.data)
    except Exception as exc:  # noqa: BLE001 - per-record isolation is the point
        return RecordResult(job.row_number, job.line_number, job.rec.name, "error",
                            jhd=jhd_written, txt=txt_written, error=str(exc),
                            data=job.data, tb=traceback.format_exc())


def _log_result(logger, result: RecordResult) -> None:
    if result.status == "ok":
        target = result.output or result.txt or result.jhd
        logger.info("Row %s -> %s", result.row_number,
                    Path(target).name if target else "(no output)")
    elif result.status == "invalid":
        logger.error("Row %s (line %s) invalid: %s", result.row_number,
                     result.line_number, result.error)
    else:
        logger.error("Row %s (line %s) failed: %s\n%s", result.row_number,
                     result.line_number, result.error, result.tb or "")


# --- worker plumbing (top-level so it is picklable under the 'spawn' start method) ---

def _pool_init(needs_qt: bool = True) -> None:
    """Runs once per worker process: create its own offscreen QApplication.

    Only the screenshot PDF path needs Qt; the vector/text path is pure Python,
    so workers skip the QApplication entirely when it is not required.
    """
    if needs_qt:
        ensure_app(headless=True)


def _worker_task(job: _Job, **kwargs) -> RecordResult:
    return _process_job(job, **kwargs)


def run_batch(rows: Iterable[RawRow], out_dir, *, app=None, verbose: bool = True,
              expand_all_tabs=None, write_failures: bool = True,
              write_pdf: bool = True, write_jhd_file: bool = True,
              write_txt: bool = True, pdf_mode: str = "vector", dhasas=None,
              workers: int = 1, max_tasks_per_child: int = 25) -> BatchSummary:
    """Generate outputs for each row in ``rows``, isolating per-record failures.

    Each record yields up to three files: a ``.pdf``, a ``.jhd`` and a ``.txt``.
    ``pdf_mode`` picks the PDF pipeline — "vector" (default) typesets the
    extracted data, "screenshot" uses PyJHora's Qt capture.

    ``workers`` selects the number of worker processes: 1 (default) runs
    in-process; >1 spreads records across a process pool. Returns a
    :class:`BatchSummary`; never raises for a bad record.
    """
    if pdf_mode not in PDF_MODES:
        raise ValueError(f"pdf_mode must be one of {PDF_MODES}, got {pdf_mode!r}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = _configure_logger(out_dir, verbose)

    jobs, invalids = _prepare(rows, out_dir)

    summary = BatchSummary()
    summary.results.extend(invalids)
    for inv in invalids:
        _log_result(logger, inv)

    job_kwargs = dict(write_pdf=write_pdf, write_jhd_file=write_jhd_file,
                      write_txt=write_txt, pdf_mode=pdf_mode, dhasas=dhasas,
                      expand_all_tabs=expand_all_tabs)
    needs_qt = write_pdf and pdf_mode == "screenshot"

    if workers and workers > 1 and len(jobs) > 1:
        results = _run_parallel(jobs, logger, workers=workers,
                                max_tasks_per_child=max_tasks_per_child,
                                needs_qt=needs_qt, **job_kwargs)
    else:
        if workers and workers > 1:
            logger.info("Only %d job(s); running single-process.", len(jobs))
        if needs_qt:
            app = app or ensure_app()
        results = []
        for job in jobs:
            result = _process_job(job, **job_kwargs)
            _log_result(logger, result)
            results.append(result)

    summary.results.extend(results)
    summary.results.sort(key=lambda r: r.row_number)
    summary.total = len(summary.results)
    summary.succeeded = sum(1 for r in summary.results if r.status == "ok")
    summary.failed = summary.total - summary.succeeded

    logger.warning(str(summary))
    if write_failures and summary.failures:
        _write_failures_csv(summary, out_dir / "failures.csv", logger)
    return summary


def _run_parallel(jobs: List[_Job], logger, *, workers: int, max_tasks_per_child: int,
                  needs_qt: bool = True, **job_kwargs) -> List[RecordResult]:
    n_workers = min(workers, len(jobs))
    logger.warning("Running %d job(s) across %d worker process(es).", len(jobs), n_workers)
    # 'spawn' avoids forking a process that has touched Qt/Cocoa (unsafe on macOS).
    ctx = mp.get_context("spawn")
    task = partial(_worker_task, **job_kwargs)
    results: List[RecordResult] = []
    with ctx.Pool(processes=n_workers, initializer=_pool_init,
                  initargs=(needs_qt,),
                  maxtasksperchild=max_tasks_per_child) as pool:
        for result in pool.imap_unordered(task, jobs):
            _log_result(logger, result)
            results.append(result)
    return results


def _write_failures_csv(summary: BatchSummary, path: Path, logger) -> None:
    # Union of all original columns across failed rows, plus diagnostics.
    cols: list[str] = []
    for r in summary.failures:
        for k in r.data:
            if k not in cols:
                cols.append(k)
    fieldnames = ["_row", "_line", "_status", "_error"] + cols
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in summary.failures:
            writer.writerow({"_row": r.row_number, "_line": r.line_number,
                             "_status": r.status, "_error": r.error, **r.data})
    logger.warning("Wrote %d failed row(s) for retry -> %s", len(summary.failures), path)


def run_csv(csv_path, out_dir, **kwargs) -> BatchSummary:
    """Convenience: read a CSV and run the batch over it."""
    return run_batch(read_csv(csv_path), out_dir, **kwargs)


def run_excel(xlsx_path, out_dir, *, sheet=None, **kwargs) -> BatchSummary:
    """Convenience: read an .xlsx worksheet and run the batch over it."""
    from .readers.excel_reader import read_excel  # lazy: openpyxl optional
    return run_batch(read_excel(xlsx_path, sheet=sheet), out_dir, **kwargs)


def default_worker_count() -> int:
    """A sensible default worker count (leaves one core free)."""
    return max(1, (os.cpu_count() or 2) - 1)
