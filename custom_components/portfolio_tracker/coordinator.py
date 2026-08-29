"""Coordinator: fetches live prices for every tracked symbol.

Also tracks per-symbol consecutive failures and raises a Home Assistant
Repair issue (Settings > System > Repairs) when a symbol has been failing
for a while, clearing it automatically once fetches succeed again.
"""
from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import market_hours
from .const import (
    DOMAIN,
    CONF_HOLDINGS,
    CONF_UPDATE_INTERVAL,
    CONF_IDLE_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_IDLE_INTERVAL_MINUTES,
    MAX_CONSECUTIVE_FAILURES,
)

_LOGGER = logging.getLogger(__name__)

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Home Assistant Portfolio Tracker)"}


class PortfolioDataCoordinator(DataUpdateCoordinator):
    """Polls Yahoo Finance for every symbol currently in this portfolio."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self.entry = entry
        self._session = async_get_clientsession(hass)
        self._failure_counts: dict[str, int] = {}

    def _symbols(self) -> list[str]:
        return list(self.entry.options.get(CONF_HOLDINGS, {}).keys())

    def _fast_interval(self) -> int:
        return self.entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)

    def _idle_interval(self) -> int:
        return self.entry.options.get(CONF_IDLE_INTERVAL, DEFAULT_IDLE_INTERVAL_MINUTES)

    async def _async_update_data(self):
        # Poll briskly while a market is open, and back off outside trading
        # hours so we're not hammering Yahoo Finance overnight/weekends.
        # Both intervals are configurable via Configure > Update settings.
        if market_hours.any_market_open():
            self.update_interval = timedelta(minutes=self._fast_interval())
        else:
            self.update_interval = timedelta(minutes=self._idle_interval())

        symbols = self._symbols()
        results: dict[str, dict | None] = {}
        for symbol in symbols:
            try:
                results[symbol] = await self._fetch_symbol(symbol)
            except Exception as err:  # noqa: BLE001 - keep other symbols updating
                _LOGGER.warning("Could not update %s: %s", symbol, err)
                results[symbol] = None
                self._note_failure(symbol)
            else:
                self._note_success(symbol)
        return results

    # ------------------------------------------------------------- repairs

    def _issue_id(self, symbol: str) -> str:
        return f"{self.entry.entry_id}_{symbol}_fetch_failing"

    def _note_failure(self, symbol: str) -> None:
        count = self._failure_counts.get(symbol, 0) + 1
        self._failure_counts[symbol] = count
        if count == MAX_CONSECUTIVE_FAILURES:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                self._issue_id(symbol),
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="symbol_fetch_failing",
                translation_placeholders={
                    "symbol": symbol,
                    "portfolio": self.entry.title,
                },
            )

    def _note_success(self, symbol: str) -> None:
        if self._failure_counts.get(symbol, 0) >= MAX_CONSECUTIVE_FAILURES:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(symbol))
        self._failure_counts[symbol] = 0

    # --------------------------------------------------------------- fetch

    async def _fetch_symbol(self, symbol: str) -> dict:
        url = CHART_URL.format(symbol=symbol)
        try:
            async with async_timeout.timeout(15):
                async with self._session.get(
                    url, params={"interval": "1d", "range": "5d"}, headers=HEADERS
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
