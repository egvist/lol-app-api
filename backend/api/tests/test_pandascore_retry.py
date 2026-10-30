from api.services.pandascore_client import parse_retry_after


def test_retry_after_seconds():
    assert parse_retry_after("30") == 30.0


def test_retry_after_missing():
    assert parse_retry_after(None) == 60.0


def test_retry_after_invalid():
    assert parse_retry_after("invalid") == 60.0