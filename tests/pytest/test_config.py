"""Test config subpackage."""

import dynaconf

from sentiment_flanders.config import config


def test_config() -> None:
    """Test that the config can be loaded."""
    assert isinstance(config, dynaconf.LazySettings)
