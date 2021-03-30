"""API router for monthly sentiment impressions."""
import re
from datetime import datetime
from typing import Any, Optional

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Query

from sentiment_flanders.api.classes import DateStatistic, DateStatisticSeries
from sentiment_flanders.api.utils import query_month, query_monthly

router = APIRouter()

# Number of days offset (the delay there exists before fetching the data)
OFFSET = 2


@router.get("/last_year/", response_model=DateStatisticSeries)
async def get_last_years_impressions(date: str, ) -> Any:  # noqa: B008
    """Get the monthly sentiment impressions for the past 12 months. Date attribute is added to circumvent cache."""
    if not re.match(r"^\d{4}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM",
        )
    return await get_impressions_monthly(n=12)


@router.get("/recent/", response_model=DateStatisticSeries)
async def get_impressions_monthly(n: int = Query(12, ge=1), ) -> Any:  # noqa: B008
    """Get the monthly sentiment impressions for the past n months."""
    start = datetime.now() - relativedelta(months=n, days=OFFSET)
    impressions = query_monthly(date_from=start.strftime("%Y-%m"))
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
    impressions = query_monthly(date_from=start, date_to=end)
    return {"series": impressions}


@router.get("/date/{date}", response_model=DateStatistic)
async def get_impressions_date(date: str, ) -> Any:
    """Get the sentiment impressions of the given date."""
    return query_month(date)
