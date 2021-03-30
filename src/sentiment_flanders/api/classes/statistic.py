"""Statistical specific data classes."""
from typing import List

from pydantic import BaseModel


class Statistic(BaseModel):
    """Statistics of twitter data."""

    positive: int
    neutral: int
    negative: int


class DateStatistic(BaseModel):
    """Statistic of single day."""

    date: str
    statistic: Statistic


class DateStatisticSeries(BaseModel):
    """Series of DayStatistic data objects."""

    series: List[DateStatistic]
