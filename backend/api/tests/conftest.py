
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.db import get_conn

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("api.main.open_pool", lambda: None)
    monkeypatch.setattr("api.main.close_pool", lambda: None)

    def fake_get_conn():
        yield object()

    app.dependency_overrides[get_conn] = fake_get_conn

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_conn, None)