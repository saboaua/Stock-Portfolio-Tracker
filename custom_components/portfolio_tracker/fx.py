"""FX rate helpers using Yahoo Finance currency pairs."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

PAIR_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{pair}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def yahoo_pair(from_ccy: str, to_ccy: str) -> str:
    """Return Yahoo chart symbol for FX (e.g. EURUSD=X)."""
    from_ccy = (from_ccy or "USD").upper()
    to_ccy = (to_ccy or "USD").upper()
    if from_ccy == to_ccy:
        return ""
    return f"{from_ccy}{to_ccy}=X"


async def fetch_rate(
    session: aiohttp.ClientSession, from_ccy: str, to_ccy: str
) -> float | None:
    """Fetch mid rate from_ccy → to_ccy. 1.0 if same currency."""
    from_ccy = (from_ccy or "USD").upper()
    to_ccy = (to_ccy or "USD").upper()
    if from_ccy == to_ccy:
        return 1.0

    pair = yahoo_pair(from_ccy, to_ccy)
    try:
        async with session.get(
            PAIR_URL.format(pair=pair),
            params={"interval": "1d", "range": "1d"},
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=12),
        ) as resp:
            if resp.status != 200:
                inv = yahoo_pair(to_ccy, from_ccy)
                async with session.get(
                    PAIR_URL.format(pair=inv),
                    params={"interval": "1d", "range": "1d"},
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=12),
                ) as resp2:
                    if resp2.status != 200:
                        _LOGGER.warning(
                            "FX HTTP %s for %s / inv %s", resp.status, pair, inv
                        )
                        return None
                    payload = await resp2.json(content_type=None)
                    rate = _parse_price(payload)
                    return (1.0 / rate) if rate else None
            payload = await resp.json(content_type=None)
            return _parse_price(payload)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("FX fetch failed %s→%s: %s", from_ccy, to_ccy, err)
        return None


def _parse_price(payload: dict[str, Any]) -> float | None:
    try:
        meta = payload["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        return float(price) if price is not None else None
    except (KeyError, IndexError, TypeError, ValueError):
        return None


async def build_rate_table(
    session: aiohttp.ClientSession,
    currencies: set[str],
    base: str,
) -> dict[str, float]:
    """Map currency → rate into base (multiply price_in_ccy * rate = price_in_base)."""
    base = (base or "USD").upper()
    rates: dict[str, float] = {base: 1.0}
    for ccy in currencies:
        ccy = (ccy or base).upper()
        if ccy in rates:
            continue
        rate = await fetch_rate(session, ccy, base)
        if rate is not None and rate > 0:
            rates[ccy] = rate
        else:
            _LOGGER.warning("No FX rate for %s→%s; using 1.0", ccy, base)
            rates[ccy] = 1.0
    return rates
