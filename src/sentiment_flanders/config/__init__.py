"""Sentiment Flanders configuration."""
from .config import __version__, load_config
from .logging import configure_root_logger
from .sentry import log_function_with_sentry, log_module_with_sentry

configure_root_logger()
config = load_config()

__all__ = [
    "__version__",
    "config",
    "load_config",
    "log_function_with_sentry",
    "log_module_with_sentry",
]
