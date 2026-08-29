"""Shared exchange-hours helpers.

Uses each exchange's real local timezone via zoneinfo, so results are
correct regardless of what timezone Home Assistant (or the viewing
browser) is running in, and correctly handle daylight saving transitions.

Limitation: does not account for market holidays (or early closes).
"""
from __future__ import annotations

from datetime import datetime, time, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9
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


def _next_session_boundary(
    tz: ZoneInfo, open_time: time, close_time: time, *, want_open: bool
) -> datetime:
    """Return the next open (or close) datetime in the exchange timezone."""
    now = datetime.now(tz)
    today_open = datetime.combine(now.date(), open_time, tzinfo=tz)
    today_close = datetime.combine(now.date(), close_time, tzinfo=tz)

    if want_open:
        candidate = today_open
        if now >= today_open or now.weekday() >= 5:
            candidate = today_open + timedelta(days=1)
            while candidate.weekday() >= 5:
                candidate += timedelta(days=1)
        return candidate

    if now.weekday() < 5 and now < today_close:
        return today_close
    candidate = today_close + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def us_next_open() -> datetime:
    return _next_session_boundary(US_TZ, US_OPEN, US_CLOSE, want_open=True)


def us_next_close() -> datetime:
    return _next_session_boundary(US_TZ, US_OPEN, US_CLOSE, want_open=False)


def eu_next_open() -> datetime:
    return _next_session_boundary(EU_TZ, EU_OPEN, EU_CLOSE, want_open=True)


def eu_next_close() -> datetime:
    return _next_session_boundary(EU_TZ, EU_OPEN, EU_CLOSE, want_open=False)
