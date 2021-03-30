"""Functionality used to query the Twitter API."""
import os
from datetime import datetime, timedelta
from math import modf
from typing import Any, List

import pytz
import tweepy

# Hyper-parameters
DAY_DELAY = 2


def connect() -> tweepy.API:
    """Create a connection with the Twitter API."""
    auth = tweepy.OAuthHandler(os.environ["TWITTER_CONSUMER_KEY"], os.environ["TWITTER_CONSUMER_SECRET"])
    auth.set_access_token(os.environ["TWITTER_ACCESS_TOKEN_KEY"], os.environ["TWITTER_ACCESS_TOKEN_SECRET"])
    return tweepy.API(auth)


def get_utc_offset():
    """Get the current UTC offset for Belgium timezone."""
    return pytz.timezone('CET')._utcoffset


def get_ending_timestamps() -> List[datetime]:
    """
    Get a list of ending timestamps - up to minute accuracy - to fetch Twitter data. Every fetch happens over one day.

    Source on twitter distribution: https://buffer.com/resources/best-time-to-tweet-research/
    """
    # Fetch the day of two days ago
    date = datetime.today() - timedelta(days=DAY_DELAY)

    # Splitted points day-points, according to source
    hour_points = [
        6.80,
        8.86,
        9.61,
        10.69,
        11.50,
        12.46,
        13.59,
        14.67,
        15.74,
        16.65,
        17.59,
        18.52,
        19.61,
        20.87,
        22.50,
        23.99,  # Hardcoded 23h59min
    ]

    # Fetch tweets for each time-point, adjust time for UTC
    timestamps = []
    for h_p in hour_points:
        residual, hour = modf(h_p)
        hour = round(hour)
        minute = min(round(residual * 60), 59)
        timestamps.append(date.replace(hour=hour, minute=minute, second=0, microsecond=0) - get_utc_offset())
    return timestamps


def fetch(
        enddate: datetime,
        country: str = "be",
        lang: str = "nl",
        exclude_retweet: bool = True,
        exclude_replies: bool = True,
        is_verified: bool = False,
        is_not_verified: bool = False,
        exclude_media: bool = True,
        exclude_links: bool = False,
        exclude_mentions: bool = False,
) -> List[Any]:
    """
    Perform a single fetch using the TwitterAPI.

    :param enddate: Ending timestamp for which tweets are fetched
    :param country: Country of the Twitter user's profile
    :param lang: Language of the tweets
    :param exclude_retweet: Exclude all retweets
    :param exclude_replies: Exclude all replies
    :param is_verified: Only use verified users
    :param is_not_verified: Only use non-verified users
    :param exclude_media: Exclude embedded videos and images
    :param exclude_links: Exclude tweets that contain URLs
    :param exclude_mentions: Exclude tweets that mention other users
    :return: List of 500 fetched tweets
    """
    # Connect with the API
    api = connect()

    # Create the query
    query = ''

    # Specify the country
    if country: query += f"profile_country:{country}"

    # Add language filter if specified
    if lang: query += f" lang:{lang}"

    # Remaining filters
    assert not (is_verified and is_not_verified)
    if exclude_retweet: query += " -is:retweet"
    if exclude_replies: query += " -is:reply"
    if is_verified: query += " is:verified"
    if is_not_verified: query += " -is:verified"
    if exclude_media: query += " -has:images -has:videos"
    if exclude_links: query += " -has:media -has:links"
    if exclude_mentions: query += " -has:mentions"

    # Perform the query
    response = tweepy.Cursor(
            api.search_30_day,
            label="production",  # Alternative naming for environment_name
            # environment_name="production",   # TODO: Name change at tweepy?
            query=query,
            maxResults=500,  # Maximum number for premium
            # fromDate=enddate.strftime("%Y%m%d0001"),  # Do not go to previous day
            toDate=enddate.strftime("%Y%m%d%H%M"),
    )
    return list(response.items(500))
