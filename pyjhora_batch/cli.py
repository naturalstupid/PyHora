"""Command-line interface for the batch layer.

    python -m pyjhora_batch input.csv -o reports/ --workers auto

Auto-detects CSV vs Excel by file extension and dispatches to the engine.
Running as a module puts the repo root on sys.path, which the 'spawn' worker
processes need to re-import the package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import PDF_MODES, default_worker_count, run_csv, run_excel

_EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm"}
_CSV_SUFFIXES = {".csv", ".tsv", ".txt"}


def _parse_workers(value: str) -> int:
    if value == "auto":
        return default_worker_count()
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--workers must be an integer or 'auto' (got {value!r})")
    if n < 1:
        raise argparse.ArgumentTypeError("--workers must be >= 1")
    return n


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pyjhora_batch",
        description="Batch-generate horoscope PDFs (and importable .jhd files) "
                    "from a CSV or Excel file of birth details.",
    )
    p.add_argument("input", type=Path,
                   help="Input file (.csv/.tsv or .xlsx). Columns: name, "
                        "date_of_birth (YYYY,M,D), time_of_birth (HH:MM:SS), place, "
                        "latitude, longitude, timezone, gender (aliases accepted).")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("reports"),
                   help="Output directory (default: reports).")
    p.add_argument("-w", "--workers", type=_parse_workers, default=1, metavar="N",
                   help="Worker processes: an integer, or 'auto' (cpus-1). Default: 1.")
    p.add_argument("--sheet", default=None,
                   help="Excel worksheet name or 0-based index (default: active sheet).")
    p.add_argument("--no-pdf", action="store_true", help="Skip PDF generation.")
    p.add_argument("--no-jhd", action="store_true", help="Skip .jhd generation.")
    p.add_argument("--no-txt", action="store_true",
                   help="Skip the plain-text report.")
    p.add_argument("--pdf-mode", choices=PDF_MODES, default="vector",
                   help="vector: typeset the data as real text — sharp, searchable, "
                        "~150 KB (default). screenshot: PyJHora's Qt widget capture — "
                        "includes the drawn chart diagrams but is ~130 DPI JPEG, ~10 MB.")
    p.add_argument("--dhasa", action="append", metavar="NAME", dest="dhasas",
                   help="Dhasa system to include (repeatable). Default: vimsottari. "
                        "Use '--dhasa all' for all 60 systems PyJHora exposes "
                        "(adds ~8500 rows). "
                        "e.g. --dhasa vimsottari --dhasa ashtottari")
    p.add_argument("--expand-all-tabs", action="store_true",
                   help="Expand all chart tabs in the PDF (screenshot mode only).")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="Only print warnings/errors and the final summary.")
    p.add_argument("--allow-failures", action="store_true",
                   help="Exit 0 even if some records fail (default: exit 1 on any failure).")
    return p


def _resolve_sheet(sheet):
    if sheet is None:
        return None
    try:
        return int(sheet)
    except (TypeError, ValueError):
        return sheet


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 2
    if args.no_pdf and args.no_jhd and args.no_txt:
        print("error: --no-pdf, --no-jhd and --no-txt together produce no output.",
              file=sys.stderr)
        return 2

    suffix = args.input.suffix.lower()
    common = dict(
        verbose=not args.quiet,
        workers=args.workers,
        write_pdf=not args.no_pdf,
        write_jhd_file=not args.no_jhd,
        write_txt=not args.no_txt,
        pdf_mode=args.pdf_mode,
        dhasas=tuple(args.dhasas) if args.dhasas else None,
        expand_all_tabs=True if args.expand_all_tabs else None,
    )

    if suffix in _EXCEL_SUFFIXES:
        summary = run_excel(args.input, args.out_dir, sheet=_resolve_sheet(args.sheet), **common)
    elif suffix in _CSV_SUFFIXES:
        summary = run_csv(args.input, args.out_dir, **common)
    else:
        print(f"error: unsupported input type {suffix!r}; use a .csv or .xlsx file.",
              file=sys.stderr)
        return 2

    print(f"\n{summary}")
    print(f"Output: {args.out_dir}")
    if summary.failures:
        print(f"Failures: {len(summary.failures)} (see {args.out_dir / 'failures.csv'} "
              f"and {args.out_dir / 'batch.log'})")
        for r in summary.failures:
            print(f"  row {r.row_number} [{r.status}] {r.name or ''}: {r.error}")

    if summary.failed and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
