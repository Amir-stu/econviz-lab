"""World Bank World Development Indicators client and normalizer."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests


BASE_URL = "https://api.worldbank.org/v2"
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SL.UEM.TOTL.ZS": "Unemployment, total (% of total labor force) (modeled ILO estimate)",
}


class WorldBankError(RuntimeError):
    """Raised when the World Bank response cannot be retrieved or parsed."""


def normalize_response(payload: list, indicator_code: str, retrieved_at: str | None = None) -> pd.DataFrame:
    """Normalize the World Bank JSON envelope, retaining missing values as NaN."""
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise WorldBankError("Unexpected World Bank API response envelope.")
    stamp = retrieved_at or datetime.now(timezone.utc).isoformat()
    rows = []
    for record in payload[1]:
        if not isinstance(record, dict) or not record.get("date"):
            continue
        try:
            year = int(record["date"])
        except (TypeError, ValueError):
            continue
        value = record.get("value")
        rows.append(
            {
                "year": year,
                "value": float(value) if value is not None else float("nan"),
                "country_code": record.get("countryiso3code", ""),
                "country": (record.get("country") or {}).get("value", ""),
                "indicator_code": indicator_code,
                "indicator": (record.get("indicator") or {}).get("value", INDICATORS.get(indicator_code, indicator_code)),
                "unit": record.get("unit", ""),
                "source_url": f"{BASE_URL}/country/{record.get('countryiso3code', '').lower()}/indicator/{indicator_code}",
                "retrieved_at_utc": stamp,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=["year", "value", "country_code", "country", "indicator_code", "indicator", "unit", "source_url", "retrieved_at_utc"])
    return result.sort_values("year").drop_duplicates(["country_code", "indicator_code", "year"], keep="last").reset_index(drop=True)


def fetch_indicator(country_code: str, indicator_code: str, start_year: int, end_year: int, timeout: int = 20) -> pd.DataFrame:
    """Fetch one WDI series with explicit bounds, timeout, and response validation."""
    country = country_code.strip().upper()
    if len(country) != 3 or not country.isalpha():
        raise WorldBankError("Country must be a three-letter ISO code, such as FRA or USA.")
    if indicator_code not in INDICATORS:
        raise WorldBankError(f"Unsupported indicator code: {indicator_code}")
    if start_year < 1960 or end_year > datetime.now(timezone.utc).year or start_year > end_year:
        raise WorldBankError("Choose a valid year range from 1960 through the current year.")
    url = f"{BASE_URL}/country/{country}/indicator/{indicator_code}"
    try:
        response = requests.get(
            url,
            params={"format": "json", "date": f"{start_year}:{end_year}", "per_page": 1000},
            headers={"User-Agent": "EconViz-Lab/0.1 (open-source educational project)"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise WorldBankError(f"World Bank request failed: {exc}") from exc
    data = normalize_response(payload, indicator_code)
    if data.empty:
        raise WorldBankError("The API returned no observations. Check the country, indicator, and date range.")
    return data


def fetch_panel(country_code: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Fetch each supported series and combine without filling missing observations."""
    frames = [fetch_indicator(country_code, code, start_year, end_year) for code in INDICATORS]
    return pd.concat(frames, ignore_index=True).sort_values(["indicator_code", "year"]).reset_index(drop=True)
