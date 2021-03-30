"""Logging configuration."""

import logging

import coloredlogs


def configure_root_logger() -> None:
    """Configure the root logger."""
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    # Configure third-party loggers to propagate to the root logger for WARNING and higher.
    third_party_logger_names = ["boto3", "botocore", "s3transfer"]
    for logger_name in third_party_logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    # Add coloredlogs' coloured StreamHandler to the root logger.
    coloredlogs.install()
