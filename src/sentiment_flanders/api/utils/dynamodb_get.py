"""Query DynamoDB."""
import re
from typing import Any, Dict, List, Union

import boto3
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException


def query(expression) -> List[Dict[str, Any]]:
    """Query DynamoDB with the given expression."""
    ddb = boto3.resource("dynamodb")
    table = ddb.Table("sentiment-flanders-impressions")
    response = table.query(KeyConditionExpression=expression)
    return response["Items"]


def query_hourly(date_from: str, date_to: Union[str, None] = None) -> List[Dict[str, Any]]:
    """
    Query hourly sentiments ranging from a certain date until a certain date (inclusive).

    :param date_from: Starting date in YYYY-MM-DD:HH (inclusive)
    :param date_to: Ending date YYYY-MM-DD:HH (inclusive), optional
    """
    if date_to and date_from > date_to:
        raise HTTPException(
                status_code=400,
                detail="Bad request, starting date cannot be greater than ending date",
        )
    if (not re.match(r"^\d{4}-\d{2}-\d{2}:\d{2}$", date_from)) or (
            date_to and not re.match(r"^\d{4}-\d{2}-\d{2}:\d{2}$", date_to)
    ):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in YYYY-MM-DD:HH format",
        )

    # Shared expression
    expression = Key("statistic_id").eq("sentiment_impressions_hourly")

    # Define expression to use
    if date_to:
        expression = expression & Key("date").between(date_from, date_to)
    else:
        expression = expression & Key("date").gte(date_from)

    # Perform query and return result
    return query(expression=expression)


def query_daily(date_from: str, date_to: Union[str, None] = None) -> List[Dict[str, Any]]:
    """
    Query daily sentiments ranging from a certain date until a certain date (inclusive).

    :param date_from: Starting date in YYYY-MM-DD (inclusive)
    :param date_to: Ending date YYYY-MM-DD (inclusive), optional
    """
    if date_to and date_from > date_to:
        raise HTTPException(
                status_code=400,
                detail="Bad request, starting date cannot be greater than ending date",
        )
    if (not re.match(r"^\d{4}-\d{2}-\d{2}$", date_from)) or (
            date_to and not re.match(r"^\d{4}-\d{2}-\d{2}$", date_to)
    ):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in YYYY-MM-DD format",
        )

    # Shared expression
    expression = Key("statistic_id").eq("sentiment_impressions_daily")

    # Define expression to use
    if date_to:
        expression = expression & Key("date").between(date_from, date_to)
    else:
        expression = expression & Key("date").gte(date_from)

    # Perform query and return result
    return query(expression=expression)


def query_monthly(date_from: str, date_to: Union[str, None] = None) -> List[Dict[str, Any]]:
    """
    Query daily sentiments ranging from a certain date until a certain date (inclusive).

    :param date_from: Starting date YYYY-MM (inclusive)
    :param date_to: Ending date YYYY-MM (inclusive), optional
    """
    if date_to and date_from > date_to:
        raise HTTPException(
                status_code=400,
                detail="Bad request, starting date cannot be greater than ending date",
        )
    if (not re.match(r"^\d{4}-\d{2}$", date_from)) or (
            date_to and not re.match(r"^\d{4}-\d{2}$", date_to)
    ):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in YYYY-MM format",
        )

    # Shared expression
    expression = Key("statistic_id").eq("sentiment_impressions_monthly")

    # Define expression to use
    if date_to:
        expression = expression & Key("date").between(date_from, date_to)
    else:
        expression = expression & Key("date").gte(date_from)

    # Perform query and return result
    return query(expression=expression)


def query_hour(date: str) -> Dict[str, Any]:
    """Query the impressions of a single day."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}:\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM-DD:HH",
        )

    # Define expression to use
    expression = Key("statistic_id").eq("sentiment_impressions_hourly") & Key("date").eq(date)

    # Perform query and return result
    response = query(expression=expression)
    if len(response) == 0:
        raise HTTPException(
                status_code=404,
                detail="Not found, no information for the requested date",
        )
    return response[0]


def query_day(date: str) -> Dict[str, Any]:
    """Query the impressions of a single day."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM-DD",
        )

    # Define expression to use
    expression = Key("statistic_id").eq("sentiment_impressions_daily") & Key("date").eq(date)

    # Perform query and return result
    response = query(expression=expression)
    if len(response) == 0:
        raise HTTPException(
                status_code=404,
                detail="Not found, no information for the requested date",
        )
    return response[0]


def query_month(date: str) -> Dict[str, Any]:
    """Query the impressions of a single month."""
    if not re.match(r"^\d{4}-\d{2}$", date):
        raise HTTPException(
                status_code=400,
                detail="Bad request, date must be in format YYYY-MM",
        )

    # Define expression to use
    expression = Key("statistic_id").eq("sentiment_impressions_monthly") & Key("date").eq(date)

    # Perform query and return result
    response = query(expression=expression)
    if len(response) == 0:
        raise HTTPException(
                status_code=404,
                detail="Not found, no information for the requested date",
        )
    return response[0]
