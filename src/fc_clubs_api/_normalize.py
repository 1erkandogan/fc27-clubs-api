"""Turn EA's raw JSON into clean, typed records (lists of flat dicts).

This is pure Python, so the ``records`` output format works without pandas. The
``dataframe`` format is built from these records, so both always agree.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, tzinfo
from typing import Any, Dict, Iterable, List, Mapping, Optional

Record = Dict[str, Any]

_NUMBER = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
_INTEGER = re.compile(r"^[+-]?\d+$")


def flatten(record: Mapping[str, Any], prefix: str = "") -> Record:
    """Flatten nested dicts into dotted keys: ``{"a": {"b": 1}}`` -> ``{"a.b": 1}``.

    Lists are kept as values. Mirrors ``pandas.json_normalize`` for one record.
    """
    flat: Record = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(flatten(value, prefix=name + "."))
        else:
            flat[name] = value
    return flat


def _field_names(records: Iterable[Mapping[str, Any]]) -> List[str]:
    """Every key used by any record, in order of first appearance."""
    names: Dict[str, None] = {}
    for record in records:
        for key in record:
            names.setdefault(key, None)
    return list(names)


def _numeric_kind(values: List[Any]) -> Optional[type]:
    """``int`` or ``float`` if every non-null value is numeric, otherwise None."""
    kind: Optional[type] = None
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            kind = kind or int
        elif isinstance(value, float):
            kind = float
        elif isinstance(value, str) and _NUMBER.match(value):
            if not _INTEGER.match(value):
                kind = float
            else:
                kind = kind or int
        else:
            return None
    return kind


def coerce_numbers(records: List[Record]) -> List[Record]:
    """Make records rectangular and convert numeric-text fields to numbers.

    EA sends almost every number as text (``"25"``, ``"7.4"``). A field is
    converted only when *every* non-null value in it is numeric, so a field such
    as a player name is never half-converted. Fields holding any decimal become
    ``float``; the rest become ``int``. Records missing a field get ``None``.
    """
    names = _field_names(records)
    rows: List[Record] = [{name: record.get(name) for name in names} for record in records]
    for name in names:
        kind = _numeric_kind([row[name] for row in rows])
        if kind is None:
            continue
        for row in rows:
            if row[name] is not None:
                row[name] = kind(row[name])
    return rows


def select_columns(
    records: List[Record], columns: Mapping[str, str], all_columns: bool
) -> List[Record]:
    """Keep only the fields in ``columns`` (in that order) and rename them.

    With ``all_columns=True`` the records are returned unchanged.
    """
    if all_columns or not records:
        return records
    present = set(_field_names(records))
    keep = [(source, target) for source, target in columns.items() if source in present]
    return [{target: record.get(source) for source, target in keep} for record in records]


def convert_timestamps(records: List[Record], field: str, tz: tzinfo) -> List[Record]:
    """Replace Unix-seconds ``field`` values with timezone-aware datetimes."""
    for record in records:
        value = record.get(field)
        if value is not None:
            moment = datetime.fromtimestamp(int(value), tz=timezone.utc)
            record[field] = moment.astimezone(tz)
    return records
