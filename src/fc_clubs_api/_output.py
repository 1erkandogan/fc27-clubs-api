"""Output formats and the conversion to pandas."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, Union

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


class OutputFormat(str, Enum):
    """What a :class:`~fc_clubs_api.FC27API` method returns.

    Members compare equal to their string values, so ``output="records"`` and
    ``output=OutputFormat.RECORDS`` are interchangeable.
    """

    RAW = "raw"
    """EA's JSON exactly as received (``dict`` / ``list``). No renaming, no type
    conversion. Only JSON ``null`` is replaced by ``[]``."""

    RECORDS = "records"
    """A ``list`` of flat ``dict`` rows: nested fields flattened, numeric text
    converted to ``int``/``float``, timestamps as timezone-aware ``datetime``,
    curated camelCase columns. Needs no third-party packages."""

    DATAFRAME = "dataframe"
    """A ``pandas.DataFrame`` with exactly the columns of ``RECORDS``.
    Requires ``pip install "fc-clubs-api[pandas]"``."""

    def __str__(self) -> str:
        return self.value


OutputLike = Union[OutputFormat, str]


def resolve_output(output: Optional[OutputLike], default: OutputFormat) -> OutputFormat:
    """Validate ``output`` (falling back to ``default`` when None)."""
    if output is None:
        return default
    try:
        return OutputFormat(output)
    except ValueError:
        choices = ", ".join(repr(member.value) for member in OutputFormat)
        raise ValueError(f"output must be one of {choices}, not {output!r}") from None


def import_pandas() -> Any:
    """Import pandas, or explain how to get it."""
    try:
        import pandas
    except ImportError:
        raise ImportError(
            "output='dataframe' needs pandas. Install it with "
            "pip install \"fc-clubs-api[pandas]\", or pass output='records' or output='raw'."
        ) from None
    return pandas


def to_dataframe(records: List[dict]) -> pd.DataFrame:
    """Build a DataFrame from normalized records (empty list -> empty DataFrame)."""
    pd = import_pandas()
    return pd.DataFrame.from_records(records) if records else pd.DataFrame()
