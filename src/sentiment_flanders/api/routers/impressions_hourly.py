"""API router hourly sentiment impressions."""
import re
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from sentiment_flanders.api.classes import DateStatistic, DateStatisticSeries
from sentiment_flanders.api.utils import query_hour, query_hourly

router = APIRouter()


@router.get("/recent/", response_model=DateStatisticSeries)
async def get_impressions_hourly(date: str, ) -> Any:  # noqa: B008
    """Get the hourly sentiment impressions of the requested day, which is at least the day before yesterday.."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM-DD",
        )
    impressions = query_hourly(
            date_from=f"{date}:00",
            date_to=f"{date}:24"
    )
    return {"series": impressions}


@router.get("/period/", response_model=DateStatisticSeries)
async def get_impressions_period(
        start: str, end: Optional[str] = Query(None, title="ending date"),  # noqa: B008
) -> Any:
    """
    Get the daily sentiment impressions in between a period of time, start and end are inclusive.

    :param start: Starting date (inclusive) in YYYY-MM-DD:HH format
    :param end: Ending date (inclusive) in YYYY-MM-DD:HH format
    """
    impressions = query_hourly(date_from=start, date_to=end)
    return {"series": impressions}


@router.get("/date/{date}", response_model=DateStatistic)
async def get_impressions_date(date: str, ) -> Any:
    """Get the sentiment impressions of the given date."""
    return query_hour(date)
