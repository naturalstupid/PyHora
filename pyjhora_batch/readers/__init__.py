"""Input readers for the batch layer. Each reader yields raw row dicts;
validation/normalization happens later in wrapper.BirthRecord.from_dict.
"""

from .csv_reader import RawRow, read_csv

__all__ = ["RawRow", "read_csv"]
