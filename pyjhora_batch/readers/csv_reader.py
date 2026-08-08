"""CSV reader for the batch layer.

Yields one ``RawRow`` per data row: the raw column dict plus its 1-based source
line number (for error messages and retry files). It intentionally does no
astrology-specific validation — that belongs to ``BirthRecord.from_dict`` so a
single validation path is shared by every reader.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class RawRow:
    """One raw input row before validation."""

    row_number: int          # 1-based, counting data rows (header excluded)
    line_number: int         # 1-based physical line in the file (header included)
    data: dict


def read_csv(path, *, encoding: str = "utf-8-sig") -> Iterator[RawRow]:
    """Yield ``RawRow`` for each non-empty data row in ``path``.

    Uses ``utf-8-sig`` so a leading BOM is stripped from the first header. Fully
    blank rows are skipped. Header names are lower-cased and stripped so the
    downstream alias map matches regardless of source casing/whitespace.

    ``skipinitialspace`` matters more than it looks: a quoted field must
    normally start immediately after the comma, so ``a, "1998,9,10",b`` would
    otherwise parse the quote as literal text and let the commas inside split
    the field into extra columns — corrupting every column after it. A space
    after the comma is a very easy thing to type, so it is tolerated here.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")

    with path.open("r", newline="", encoding=encoding) as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        if reader.fieldnames is None:
            return  # empty file
        reader.fieldnames = [(name or "").strip().lower() for name in reader.fieldnames]
        row_number = 0
        for row in reader:
            # csv.DictReader sets line_num to the physical line just read.
            line_number = reader.line_num
            cleaned = {
                k: (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()
                if k is not None
            }
            if not any(v not in (None, "") for v in cleaned.values()):
                continue  # skip fully-blank row
            row_number += 1
            yield RawRow(row_number=row_number, line_number=line_number, data=cleaned)
