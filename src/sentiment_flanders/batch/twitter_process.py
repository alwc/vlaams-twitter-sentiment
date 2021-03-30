"""Process raw tweet-objects as received by the TwitterAPI."""
import re
from typing import Any, Dict

import emoji


def process(tweet: str) -> str:
    """Process a tweet's text (body) before storing in final DB."""
    tweet = emoji.demojize(
            tweet
    )  # Substitute unicode emoji by :emoji: type (readable emojis)
    tweet = re.sub(r"^RT", "", tweet)  # Remove retweet-tag
    tweet = re.sub(r"http(s|)://[^ ]+", "", tweet)  # Remove urls
    tweet = re.sub(r"[“”]", '"', tweet)  # Substitute faulty quotes
    tweet = re.sub(r"[‘’]", "'", tweet)  # Substitute faulty quotes
    tweet = re.sub(r"•", "-", tweet)  # Substitute faulty symbols
    tweet = re.sub(r"(›|&gt)", ">", tweet)  # Substitute faulty symbols
    tweet = re.sub(r"(‹|&lt)", "<", tweet)  # Substitute faulty symbols
    tweet = re.sub(r"-[\-]+", "-", tweet)  # Substitute repeating symbols
    tweet = tweet.strip()  # Remove leading and trailing spaces
    tweet = " ".join(tweet.split())  # Remove enters, tabs, ...
    return tweet


def parse(tweet) -> Dict[str, Any]:
    """
    Parse the tweet object to cover only the desired information.

    A parsed tweet looks as follows:
     - id: [int] unique identifier of the tweet
     - created_at: [str] timestamp of when tweet was created, second granularity
     - text: [str] processed text body of the tweet
     - text_raw: [str] text body of the tweet
     - truncated: [bool] indication if the original tweet is truncated
     - is_quote: [bool] indication if this tweet is a quote from another tweet
     - quoted_lang: [str] language of the tweet that is quoted
     - quoted_tweet: [str] the processed text of the quoted tweet, if this tweet quoted another tweet
     - quoted_tweet_raw: [str] the text of the quoted tweet, if this tweet quoted another tweet
     - quote_count: [int] number of tweets quoting this tweet
     - is_reply: [bool] indication if this tweet is a reply to another tweet
     - replied_tweet_id: [int] the ID of the tweet to which this tweet replies, if is_reply
     - reply_count: [int] number of tweets replying on this tweet
     - retweet_count: [int] number of tweets retweeting this tweet
     - favorite_count: [int] number of times the tweet is favored
     - hashtags: [List[str]] list of hashtags that occurred in the tweet
     - user_followers: [int] number of followers the user posting this tweet has
     - user_friends: [int] number of friends the user posting this tweet has
     - user_verified: [bool] indicator if the user is a verified user
     - user_tweet_count: [int] number of tweets sent by the user over its lifetime
     - user_created_at: [str] timestamp of when user account was created, second granularity
    """
    # Pull the right text
    text = tweet.text if not tweet.truncated else tweet.extended_tweet["full_text"]

    # Pull the right quote
    if tweet.is_quote_status and hasattr(tweet, "quoted_status"):
        if tweet.quoted_status.truncated:
            quote = tweet.quoted_status.extended_tweet["full_text"]
        else:
            quote = tweet.quoted_status.text
        quoted_lang = tweet.quoted_status.lang
    else:
        quote, quoted_lang = "", ""

    # Pull only the useful information
    return {
        "id":               tweet.id,
        "created_at":       tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "text":             process(text),
        "text_raw":         text,
        "truncated":        tweet.truncated,
        "is_quote":         tweet.is_quote_status and hasattr(tweet, "quoted_status"),
        "quoted_lang":      quoted_lang,
        "quoted_tweet":     process(quote),
        "quoted_tweet_raw": quote,
        "quote_count":      tweet.quote_count,
        "is_reply":         tweet.in_reply_to_status_id is not None,
        "replied_tweet_id": tweet.in_reply_to_status_id,
        "reply_count":      tweet.reply_count,
        "retweet_count":    tweet.retweet_count,
        "favorite_count":   tweet.favorite_count,
        "hashtags":         [h["text"] for h in tweet.entities["hashtags"]],
        "user_followers":   tweet.user.followers_count,
        "user_friends":     tweet.user.friends_count,
        "user_verified":    tweet.user.verified,
        "user_tweet_count": tweet.user.statuses_count,
        "user_created_at":  tweet.user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
