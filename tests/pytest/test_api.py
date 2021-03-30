"""Test API subpackage."""

import pytest
from starlette.testclient import TestClient

from sentiment_flanders.api import app


@pytest.fixture
def client() -> TestClient:
    """Create a client for testing the API."""
    return TestClient(app)


def test_config(client: TestClient) -> None:
    """Test that the API responds to a GET request."""
    response = client.get("/")
    assert response.status_code == 200
