"""Coordinator: fetches live prices, FX rates, and dividend events."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import market_hours
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    IDLE_SCAN_INTERVAL_MINUTES,
    DEFAULT_BASE_CURRENCY,
)
from .fx import build_rate_table

_LOGGER = logging.getLogger(__name__)

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-PortfolioTracker/1.4)"
}


class PortfolioDataCoordinator(DataUpdateCoordinator):
    """Polls Yahoo Finance for prices, FX, and dividends."""

    def __init__(
        self,
        hass: HomeAssistant,
        symbols_getter,
        base_currency_getter=None,
        scan_minutes: int = DEFAULT_SCAN_INTERVAL_MINUTES,
        idle_minutes: int = IDLE_SCAN_INTERVAL_MINUTES,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_minutes),
        )
        self._symbols_getter = symbols_getter
        self._base_currency_getter = base_currency_getter or (lambda: DEFAULT_BASE_CURRENCY)
        self._scan_minutes = scan_minutes
        self._idle_minutes = idle_minutes
        self._session = async_get_clientsession(hass)

    def set_intervals(self, scan_minutes: int, idle_minutes: int) -> None:
        self._scan_minutes = scan_minutes
        self._idle_minutes = idle_minutes

    async def _async_update_data(self):
        if market_hours.any_market_open():
            self.update_interval = timedelta(minutes=self._scan_minutes)
        else:
            self.update_interval = timedelta(minutes=self._idle_minutes)

        symbols = self._symbols_getter()
        base = (self._base_currency_getter() or DEFAULT_BASE_CURRENCY).upper()

        prices: dict[str, dict | None] = {}
        currencies: set[str] = set()
        dividends: list[dict] = []

        for symbol in symbols:
            try:
                data = await self._fetch_symbol(symbol)
                prices[symbol] = data
                if data and data.get("currency"):
                    currencies.add(data["currency"])
                if data and data.get("dividends"):
                    dividends.extend(data["dividends"])
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Could not update %s: %s", symbol, err)
                prices[symbol] = None

        rates = await build_rate_table(self._session, currencies | {base}, base)

        return {
            "prices": prices,
            "fx_rates": rates,
            "base_currency": base,
            "dividends": sorted(dividends, key=lambda d: d.get("date") or ""),
        }

    async def _fetch_symbol(self, symbol: str) -> dict:
        url = CHART_URL.format(symbol=symbol)
        try:
            async with self._session.get(
                url,
                params={
                    "interval": "1d",
                    "range": "1y",
                    "events": "div",
                },
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

        # Sparkline: last closes from the daily series (up to 30 points)
        sparkline: list[float] = []
        try:
            quotes = (result.get("indicators") or {}).get("quote") or []
            closes = (quotes[0].get("close") if quotes else None) or []
            sparkline = [float(c) for c in closes if c is not None][-30:]
        except (TypeError, ValueError, IndexError, AttributeError):
            sparkline = []

        day_change = None
        day_change_pct = None
        if price is not None and previous_close:
            day_change = price - previous_close
            day_change_pct = (day_change / previous_close) * 100

        # Dividend events from chart
        divs: list[dict] = []
        events = (result.get("events") or {}).get("dividends") or {}
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)
        horizon = now + timedelta(days=365)
        for _key, ev in events.items():
            try:
                ts = int(ev.get("date", 0))
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                amount = float(ev.get("amount", 0))
            except (TypeError, ValueError, OSError):
                continue
            # Yahoo chart mainly returns past dividends; keep recent + any future
            if dt < cutoff:
                continue
            divs.append(
                {
                    "symbol": symbol,
                    "amount": amount,
                    "date": dt.date().isoformat(),
                    "datetime": dt.isoformat(),
                    "currency": currency,
                }
            )

        return {
            "price": price,
            "previous_close": previous_close,
            "day_change": day_change,
            "day_change_pct": day_change_pct,
            "currency": currency,
            "short_name": meta.get("shortName") or meta.get("symbol") or symbol,
            "long_name": meta.get("longName") or meta.get("shortName"),
            "exchange": meta.get("exchangeName") or meta.get("fullExchangeName"),
            "market_state": meta.get("marketState"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "regular_market_volume": meta.get("regularMarketVolume"),
            "instrument_type": meta.get("instrumentType"),
            "sparkline": sparkline,
            "dividends": divs,
        }

    # ---- helpers for sensors ----

    def price_data(self, symbol: str) -> dict:
        """Return price payload for symbol; always a dict (never None)."""
        data = self.data or {}
        prices = data.get("prices")
        if isinstance(prices, dict):
            payload = prices.get(symbol)
            if isinstance(payload, dict):
                return payload
        # Back-compat if old flat shape {symbol: {...}}
        payload = data.get(symbol)
        if isinstance(payload, dict):
            return payload
        return {}

    def fx_rate(self, currency: str | None) -> float:
        data = self.data or {}
        rates = data.get("fx_rates") or {}
        base = data.get("base_currency") or DEFAULT_BASE_CURRENCY
        ccy = (currency or base).upper()
        return float(rates.get(ccy, 1.0))

    def base_currency(self) -> str:
        return (self.data or {}).get("base_currency") or DEFAULT_BASE_CURRENCY

    def dividends(self) -> list[dict]:
        return list((self.data or {}).get("dividends") or [])
