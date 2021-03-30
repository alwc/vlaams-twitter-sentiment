"""Functionality to put elements in DynamoDB."""
import re
from datetime import datetime
from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import Key


def get_table():
    """Get the DynamoDB table."""
    ddb = boto3.resource("dynamodb", region_name='eu-west-1')
    return ddb.Table("sentiment-flanders-impressions")


def get_statistic_id(date: str) -> str:
    """Get the statistic ID that corresponds with the given date."""
    if re.match(r"^\d{4}-\d{2}-\d{2}:\d{2}$", date):
        return 'sentiment_impressions_hourly'
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        return 'sentiment_impressions_daily'
    elif re.match(r"^\d{4}-\d{2}$", date):
        return 'sentiment_impressions_monthly'
    else:
        raise FileNotFoundError("Invalid date(must be either YYYY-MM-DD:HH, YYYY-MM-DD, or YYYY-MM")


def put_item(item: Dict[str, Any]) -> None:
    """Put a batch of DateStatistics on DynamoDB."""
    table = get_table()
    table.put_item(
            Item={
                'statistic_id': get_statistic_id(item['date']),
                'date':         item['date'],
                'statistic':    item['statistic'],
            })


def put_batch(items: List[Dict[str, Any]]) -> None:
    """Put a batch of DateStatistics on DynamoDB."""
    table = get_table()
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(
                    Item={
                        'statistic_id': get_statistic_id(item['date']),
                        'date':         item['date'],
                        'statistic':    item['statistic'],
                    })


def get_daily(from_date: datetime, to_date: datetime):
    """Get all the daily statistics between the given dates (inclusive)."""
    table = get_table()

    # Create query
    startdate = from_date.strftime("%Y-%m-%d")
    enddate = to_date.strftime("%Y-%m-%d")
    expression = Key("statistic_id").eq("sentiment_impressions_daily") & Key("date").between(startdate, enddate)

    # Perform query and return result
    return table.query(KeyConditionExpression=expression)["Items"]
