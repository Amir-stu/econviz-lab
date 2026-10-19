import pytest

from world_bank import WorldBankError, fetch_indicator, normalize_response


def payload():
    return [{"page": 1, "pages": 1, "total": 2}, [
        {"date": "2022", "value": 2.0, "countryiso3code": "FRA", "country": {"value": "France"}, "indicator": {"value": "GDP growth"}, "unit": ""},
        {"date": "2021", "value": None, "countryiso3code": "FRA", "country": {"value": "France"}, "indicator": {"value": "GDP growth"}, "unit": ""},
    ]]


def test_normalizer_sorts_and_preserves_missing_observations():
    frame = normalize_response(payload(), "NY.GDP.MKTP.KD.ZG", "2026-01-01T00:00:00+00:00")
    assert frame["year"].tolist() == [2021, 2022]
    assert frame["value"].isna().iloc[0]
    assert frame["retrieved_at_utc"].nunique() == 1


def test_rejects_invalid_country_before_network_call():
    with pytest.raises(WorldBankError, match="three-letter ISO"):
        fetch_indicator("France", "NY.GDP.MKTP.KD.ZG", 2000, 2024)


def test_rejects_unsupported_indicator_before_network_call():
    with pytest.raises(WorldBankError, match="Unsupported indicator"):
        fetch_indicator("FRA", "NOT.A.REAL.CODE", 2000, 2024)


def test_rejects_malformed_response():
    with pytest.raises(WorldBankError, match="Unexpected"):
        normalize_response({"error": "bad"}, "NY.GDP.MKTP.KD.ZG")
