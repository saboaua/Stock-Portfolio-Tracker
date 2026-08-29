"""Coordinator: fetches live prices for every tracked symbol via Yahoo Finance."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import market_hours
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL_MINUTES, IDLE_SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

# Public chart endpoint — no API key required.
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-PortfolioTracker/1.1)"
}


class PortfolioDataCoordinator(DataUpdateCoordinator):
    """Polls Yahoo Finance for every symbol currently in the portfolio."""

    def __init__(self, hass: HomeAssistant, symbols_getter) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self._symbols_getter = symbols_getter
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self):
        # Adaptive polling: 5 min while a market is open, 30 min otherwise.
        if market_hours.any_market_open():
            self.update_interval = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
        else:
            self.update_interval = timedelta(minutes=IDLE_SCAN_INTERVAL_MINUTES)

        symbols = self._symbols_getter()
        if not symbols:
            return {}

        results: dict[str, dict | None] = {}
        for symbol in symbols:
            try:
                results[symbol] = await self._fetch_symbol(symbol)
            except Exception as err:  # noqa: BLE001 — keep other symbols updating
                _LOGGER.warning("Could not update %s: %s", symbol, err)
                results[symbol] = None
        return results

    async def _fetch_symbol(self, symbol: str) -> dict:
        url = CHART_URL.format(symbol=symbol)
        try:
            async with self._session.get(
                url,
                params={"interval": "1d", "range": "5d"},
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status} for {symbol}")
                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(str(err)) from err

        try:
            result = payload["chart"]["result"][0]
            meta = result["meta"]
            price = meta.get("regularMarketPrice")
            previous_close = meta.get("chartPreviousClose", meta.get("previousClose"))
            currency = meta.get("currency")
        except (KeyError, IndexError, TypeError) as err:
            raise UpdateFailed(f"Unexpected response shape for {symbol}") from err

        day_change = None
        day_change_pct = None
        if price is not None and previous_close:
            day_change = price - previous_close
            day_change_pct = (day_change / previous_close) * 100

        return {
            "price": price,
            "previous_close": previous_close,
            "day_change": day_change,
            "day_change_pct": day_change_pct,
            "currency": currency,
        }
