from api.services.pandascore_client import (
    PandaScoreClient,
    pandascore_cache,
)


def test_pandascore_cache(monkeypatch):
    pandascore_cache.clear()

    calls = 0

    def fake_get(path, params=None):
        nonlocal calls
        calls += 1

        return ResponseStub()

    class ResponseStub:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"id": 123, "name": "Example Player"}]

    with PandaScoreClient() as client:
        monkeypatch.setattr(client.client, "get", fake_get)

        first = client.get("/lol/players", {"page": 1})
        second = client.get("/lol/players", {"page": 1})

    assert first == second
    assert calls == 1

    pandascore_cache.clear()