"""Retirement / forecast helpers.

Deterministic compound-growth paths for ApexCharts and sensors.
Not financial advice — assumes constant annual return.
"""
from __future__ import annotations

from datetime import date
from typing import Any

# Default scenario rates (annual). Keys stable for Apex series names.
SCENARIO_RATES: dict[str, float] = {
    "conservative": 0.08,
    "moderate": 0.10,
    "nasdaq": 0.15,
    "aggressive": 0.20,
    "upside": 0.22,
}

SCENARIO_LABELS: dict[str, str] = {
    "conservative": "Conservative 8%",
    "moderate": "Moderate 10%",
    "nasdaq": "Nasdaq 15%",
    "aggressive": "Aggressive 20%",
    "upside": "Upside 22%",
}


def projected_value(
    baseline: float,
    rate: float,
    years: float,
    annual_contribution: float = 0.0,
) -> float:
    """Future value with optional end-of-year contribution annuity."""
    if years < 0:
        years = 0
    if rate == 0:
        return baseline + annual_contribution * years
    growth = (1.0 + rate) ** years
    fv = baseline * growth
    if annual_contribution:
        fv += annual_contribution * (growth - 1.0) / rate
    return fv


def year_series(
    baseline: float,
    rate: float,
    start_year: int,
    end_year: int,
    annual_contribution: float = 0.0,
) -> list[dict[str, Any]]:
    """List of {year, value} from start_year..end_year inclusive."""
    rows: list[dict[str, Any]] = []
    for y in range(start_year, end_year + 1):
        years = y - start_year
        val = projected_value(baseline, rate, years, annual_contribution)
        rows.append({"year": y, "value": round(val, 2)})
    return rows


def apex_points(
    baseline: float,
    rate: float,
    start_year: int,
    end_year: int,
    annual_contribution: float = 0.0,
) -> list[list[int | float]]:
    """ApexCharts-friendly [timestamp_ms, value] pairs (Jan 1 each year)."""
    points: list[list[int | float]] = []
    for row in year_series(baseline, rate, start_year, end_year, annual_contribution):
        # Use UTC noon-ish via date — Apex uses local; Jan 1 is fine for yearly
        ts = int(date(row["year"], 1, 1).toordinal())  # not ms — fix below
        # JavaScript Date: year, monthIndex 0, day 1
        # Approximate ms: use a simple epoch calc
        # 1970-01-01 ordinal = 719163
        days = date(row["year"], 1, 1).toordinal() - date(1970, 1, 1).toordinal()
        ms = days * 86400000
        points.append([ms, row["value"]])
    return points


def build_plan_payload(
    *,
    baseline: float,
    start_year: int,
    horizon_years: int,
    annual_contribution: float = 0.0,
    rates: dict[str, float] | None = None,
    actual: float | None = None,
    selected: str = "moderate",
) -> dict[str, Any]:
    """Full plan dict for sensor attributes / Apex data_generator."""
    rates = dict(rates or SCENARIO_RATES)
    end_year = start_year + max(1, int(horizon_years))
    scenarios: dict[str, Any] = {}
    for key, rate in rates.items():
        series = year_series(baseline, rate, start_year, end_year, annual_contribution)
        scenarios[key] = {
            "rate": rate,
            "rate_pct": round(rate * 100, 2),
            "label": SCENARIO_LABELS.get(key, key),
            "series": series,
            "points": apex_points(baseline, rate, start_year, end_year, annual_contribution),
            "target": series[-1]["value"] if series else baseline,
        }

    # Current plan year (1-based) vs calendar
    today = date.today()
    plan_year = max(0, today.year - start_year)
    plan_year = min(plan_year, horizon_years)

    selected = selected if selected in scenarios else "moderate"
    sel = scenarios[selected]
    # Expected value at current year fraction (use full years elapsed)
    expected_now = projected_value(baseline, sel["rate"], plan_year, annual_contribution)
    actual_val = float(actual) if actual is not None else None
    progress = None
    delta = None
    on_track = None
    if actual_val is not None and expected_now > 0:
        progress = round((actual_val / expected_now) * 100, 2)
        delta = round(actual_val - expected_now, 2)
        on_track = actual_val >= expected_now * 0.95  # within 5% counts as on track

    return {
        "baseline": round(baseline, 2),
        "start_year": start_year,
        "end_year": end_year,
        "horizon_years": horizon_years,
        "annual_contribution": annual_contribution,
        "selected_scenario": selected,
        "plan_year": plan_year,
        "expected_now": round(expected_now, 2),
        "actual": actual_val,
        "progress_pct": progress,
        "delta": delta,
        "on_track": on_track,
        "scenarios": scenarios,
        "disclaimer": "Illustrative compound growth only — not financial advice.",
    }
