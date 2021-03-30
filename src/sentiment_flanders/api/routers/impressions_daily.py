"""API router daily sentiment impressions."""
import re
from datetime import datetime
from typing import Any, Optional

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Query

from sentiment_flanders.api.classes import DateStatistic, DateStatisticSeries
from sentiment_flanders.api.utils import query_daily, query_day

router = APIRouter()

# Number of days offset (the delay there exists before fetching the data)
OFFSET = 2


@router.get("/last_week/", response_model=DateStatisticSeries)
async def get_last_weeks_impressions(date: str, ) -> Any:  # noqa: B008
    """Get the daily sentiment impressions for the past 7 days. Date attribute is added to circumvent cache."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM-DD",
        )
    return await get_impressions_daily(n=7)


@router.get("/last_month/", response_model=DateStatisticSeries)
async def get_last_months_impressions(date: str, ) -> Any:  # noqa: B008
    """Get the daily sentiment impressions for the past 31 days. Date attribute is added to circumvent cache."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM-DD",
        )
    return await get_impressions_daily(n=31)


@router.get("/recent/", response_model=DateStatisticSeries)
async def get_impressions_daily(n: int = Query(7, ge=1), ) -> Any:  # noqa: B008
    """Get the daily sentiment impressions for the past n days."""
    start = datetime.now() - relativedelta(days=n + max(OFFSET - 1, 0))
    impressions = query_daily(date_from=start.strftime("%Y-%m-%d"))
    return {"series": impressions}


@router.get("/period/", response_model=DateStatisticSeries)
async def get_impressions_period(
        start: str, end: Optional[str] = Query(None, title="ending date"),  # noqa: B008
) -> Any:
    """
    Get the daily sentiment impressions in between a period of time, start and end are inclusive.

    :param start: Starting date (inclusive) in YYYY-MM-DD format
    :param end: Ending date (inclusive) in YYYY-MM-DD format
    """
    impressions = query_daily(date_from=start, date_to=end)
    return {"series": impressions}


@router.get("/date/{date}", response_model=DateStatistic)
async def get_impressions_date(date: str, ) -> Any:
    """Get the sentiment impressions of the given date."""
    return query_day(date)
