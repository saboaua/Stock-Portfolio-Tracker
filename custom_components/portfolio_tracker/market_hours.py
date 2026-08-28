"""Shared exchange-hours helpers.

Uses each exchange's real local timezone via zoneinfo, so results are
correct regardless of what timezone Home Assistant (or the viewing
browser) is running in, and correctly handle daylight saving transitions.

Limitation: does not account for market holidays.
"""
from __future__ import annotations

from datetime import datetime, time

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

US_TZ = ZoneInfo("America/New_York")
US_OPEN = time(9, 30)
US_CLOSE = time(16, 0)

EU_TZ = ZoneInfo("Europe/London")
EU_OPEN = time(8, 0)
EU_CLOSE = time(16, 30)


def _is_open(tz: ZoneInfo, open_time: time, close_time: time) -> bool:
    now = datetime.now(tz)
    if now.weekday() >= 5:  # Saturday / Sunday
        return False
    return open_time <= now.time() < close_time


def us_market_open() -> bool:
    return _is_open(US_TZ, US_OPEN, US_CLOSE)


def eu_market_open() -> bool:
    return _is_open(EU_TZ, EU_OPEN, EU_CLOSE)


def any_market_open() -> bool:
    return us_market_open() or eu_market_open()
