"""Cron-job as used by AWS Batch."""
import pickle
from datetime import datetime, timedelta
from math import log10
from time import sleep

import boto3
from twitter_sentiment_classifier import batch_predict

from .dynamodb import get_daily, put_batch, put_item
from .twitter_api import fetch, get_ending_timestamps, get_utc_offset
from .twitter_process import parse

# Hyper-parameters
ADDER_FAVORITES = .1
ADDER_REPLIES = .05
ADDER_RETWEETS = .2
FOLLOWERS_LOG = 0.


def fetch_and_process(
        adder_favorites: float = ADDER_FAVORITES,
        adder_replies: float = ADDER_REPLIES,
        adder_retweets: float = ADDER_RETWEETS,
        followers_log: float = FOLLOWERS_LOG,
):
    """
    Perform a fetch on the tweets created two days ago, process these accordingly and push results to DynamoDB.

    Every tweet is processed, with its sentiment having a value of one. Afterwards, its weight may increase depending
    on the number of likes, replies, ... it has.

    :param adder_favorites: Additional points for every "favorite" the tweet receives
                            points += adder_favorites * n_favorites
    :param adder_replies: Additional points for every "reply" the tweet has
                          points += adder_replies * n_replies
    :param adder_retweets: Additional points for every "retweet" the tweet has
                           points += adder_retweets * n_retweets
    :param followers_log: Additional points for every follower the user has, logarithmic
                          points += user_followers_log * log_10(user_followers)
    """
    # Get all (16) timestamps for which a fetch is performed
    timestamps = get_ending_timestamps()

    # Fetch all entries
    tweets = []
    min_date = None
    for timestamp in sorted(timestamps, reverse=True):
        if min_date: timestamp = min(min_date, timestamp)  # Prevent overlap
        print("Fetching tweets for timestamp:", timestamp)
        tweets += fetch(enddate=timestamp)
        sleep(0.2)
        min_date = min({t.created_at for t in tweets}).replace(tzinfo=None)
    print(f"Finished fetch of {len(tweets)} tweets")

    # Process all tweets to custom format, recover datetime to current timezone (Europe/Brussels)
    processed = []
    for tweet in tweets:
        tweet.created_at += get_utc_offset()
        processed.append(parse(tweet))
    print(f"Finished processing of {len(processed)} tweets")

    # Remove overlap or tweets tweeted in another day
    day_start = timestamps[0].replace(hour=0, minute=0, second=0)
    texts = set()
    processed_temp = []  # temporary container to store unique processed
    for p in processed:
        text = p['text'] + p['created_at']
        if text in texts: continue
        if datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S") < day_start: continue
        processed_temp.append(p)
        texts.add(text)
    processed = processed_temp
    print(f"Total of {len(processed)} left after duplicate removal")

    # Backup the tweets to S3
    s3_resource = boto3.resource('s3')
    s3_resource.Object(
            'default-sentiment-flanders-data',
            f'backup/{(datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")}.pickle',
    ).put(Body=pickle.dumps(processed))
    print(f"Backed up all {len(processed)} tweets")

    # Predict sentiment for every tweet using the SentimentModel (takes ~30min for all 8000 tweets)
    texts = [tweet['text'] for tweet in processed]
    predictions = batch_predict(texts)
    assert len(predictions) == len(processed)
    print(f"Predicted {len(predictions)} predictions")

    # Bucket by hour
    buckets = {}
    for tweet, pred in zip(processed, predictions):
        key = datetime.strptime(tweet['created_at'], "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0, microsecond=0)
        if key not in buckets: buckets[key] = {'positive': 0, 'neutral': 0, 'negative': 0}

        # Collect the points of the current tweet
        points = 1
        if adder_favorites: points += adder_favorites * tweet['favorite_count']
        if adder_replies: points += adder_replies * tweet['reply_count']
        if adder_retweets: points += adder_retweets * tweet['retweet_count']
        if followers_log and tweet['user_followers']: points += followers_log * log10(tweet['user_followers'])
        points = round(points)  # Round to be integer (DynamoDB does not accept floats)

        # Assign points to the correct sentiment
        assert pred in ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
        if pred == 'POSITIVE': buckets[key]['positive'] += points
        if pred == 'NEUTRAL': buckets[key]['neutral'] += points
        if pred == 'NEGATIVE': buckets[key]['negative'] += points
    print(f"Created {len(buckets)} buckets")
    print("Keys:", buckets.keys())

    # Push hourly data to DynamoDB
    statistics_hourly = []
    for key in buckets.keys():
        statistics_hourly.append({
            'date':      key.strftime('%Y-%m-%d:%H'),
            'statistic': buckets[key]
        })
    put_batch(statistics_hourly)
    print(f"Added {len(statistics_hourly)} hourly statistics to DynamoDB")

    # Push complete day to DynamoDB
    statistics_daily = {'positive': 0, 'neutral': 0, 'negative': 0}
    for statistic in buckets.values():
        for k in statistics_daily.keys(): statistics_daily[k] += statistic[k]
    put_item({
        'date':      list(buckets.keys())[0].strftime("%Y-%m-%d"),
        'statistic': statistics_daily
    })
    print(f"Added daily statistic to DynamoDB")

    # If today is second day of month, combine all days of previous month into month-overview
    if datetime.today().day == 2:
        # Get last month's date of its last day
        last_month = (datetime.today() - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Query all statistics that were gathered last month
        daily_statistics = get_daily(from_date=last_month.replace(day=1), to_date=last_month)
        if not daily_statistics: return

        # Combine all statistics
        statistics_monthly = {'positive': 0, 'neutral': 0, 'negative': 0}
        for statistic in daily_statistics:
            for key in statistics_monthly.keys(): statistics_monthly[key] += int(statistic['statistic'][key])
        put_item({
            'date':      last_month.strftime("%Y-%m"),
            'statistic': statistics_monthly
        })


if __name__ == '__main__':
    fetch_and_process()
