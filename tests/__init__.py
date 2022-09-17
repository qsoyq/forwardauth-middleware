import pretty_errors  # nopycln: import
import pytest

from fastapi.testclient import TestClient

from forwardauth_middleware.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
