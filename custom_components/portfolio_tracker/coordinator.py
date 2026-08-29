"""Coordinator: fetches live prices, FX rates, and dividend events."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import market_hours
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    IDLE_SCAN_INTERVAL_MINUTES,
    DEFAULT_BASE_CURRENCY,
    NOTIFICATION_ID,
)
from .fx import build_rate_table

_LOGGER = logging.getLogger(__name__)

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Browser-like UA — Yahoo often returns 429/401 for minimal bot UAs
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
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
        self._base_currency_getter = base_currency_getter or (
            lambda: DEFAULT_BASE_CURRENCY
        )
        self._scan_minutes = scan_minutes
        self._idle_minutes = idle_minutes
        self._session = async_get_clientsession(hass)
        self._fail_count = 0
        self.last_success_time: datetime | None = None
        self.last_error: str | None = None

    def set_intervals(self, scan_minutes: int, idle_minutes: int) -> None:
        self._scan_minutes = scan_minutes
        self._idle_minutes = idle_minutes

    async def _async_update_data(self) -> dict[str, Any]:
        if market_hours.any_market_open():
            self.update_interval = timedelta(minutes=self._scan_minutes)
        else:
            self.update_interval = timedelta(minutes=self._idle_minutes)

        symbols = list(self._symbols_getter() or [])
        base = (self._base_currency_getter() or DEFAULT_BASE_CURRENCY).upper()

        prices: dict[str, dict] = {}
        currencies: set[str] = set()
        dividends: list[dict] = []
        failed: list[str] = []

        for symbol in symbols:
            try:
                data = await self._fetch_symbol(symbol)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Could not update %s: %s", symbol, err)
                self.last_error = f"{symbol}: {err}"
                failed.append(symbol)
                continue

            if not data or data.get("price") is None:
                failed.append(symbol)
                continue

            prices[symbol] = data
            if data.get("currency"):
                currencies.add(str(data["currency"]).upper())
            if data.get("dividends"):
                dividends.extend(data["dividends"])

        try:
            rates = await build_rate_table(self._session, currencies | {base}, base)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("FX table failed: %s — using 1.0 rates", err)
            rates = {base: 1.0}
            for c in currencies:
                rates[c] = 1.0

        got_any = bool(prices)
        if symbols and not got_any:
            self._fail_count += 1
            await self._notify_failure(failed)
        else:
            self._fail_count = 0
            if got_any or not symbols:
                self.last_success_time = datetime.now(timezone.utc)
                self.last_error = None
                await self._dismiss_failure()

        return {
            "prices": prices,
            "fx_rates": rates,
            "base_currency": base,
            "dividends": sorted(dividends, key=lambda d: d.get("date") or ""),
            "failed_symbols": failed,
            "last_success": (
                self.last_success_time.isoformat() if self.last_success_time else None
            ),
        }

    async def _notify_failure(self, failed: list[str]) -> None:
        if self._fail_count < 2:
            return
        try:
            from homeassistant.components import persistent_notification

            persistent_notification.async_create(
                self.hass,
                (
                    "Portfolio Tracker could not refresh prices"
                    + (f" for: {', '.join(failed)}" if failed else "")
                    + f". Last error: {self.last_error or 'unknown'}. "
                    "Check network or press Portfolio Refresh."
                ),
                title="Portfolio Tracker — update failed",
                notification_id=NOTIFICATION_ID,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not create notification: %s", err)

    async def _dismiss_failure(self) -> None:
        try:
            from homeassistant.components import persistent_notification

            persistent_notification.async_dismiss(self.hass, NOTIFICATION_ID)
        except Exception:  # noqa: BLE001
            pass

    async def _fetch_symbol(self, symbol: str) -> dict:
        """Fetch quote + optional sparkline. Tries 5d first, then 1y for history."""
        payload = await self._chart_json(symbol, range_="5d")
        if payload is None:
            payload = await self._chart_json(symbol, range_="1mo")
        if payload is None:
            raise RuntimeError(f"No chart data for {symbol}")

        try:
            result = payload["chart"]["result"][0]
            meta = result["meta"]
            price = meta.get("regularMarketPrice")
            previous_close = meta.get("chartPreviousClose", meta.get("previousClose"))
            currency = meta.get("currency") or "USD"
        except (KeyError, IndexError, TypeError) as err:
            raise RuntimeError(f"Unexpected response for {symbol}") from err

        if price is None and previous_close is not None:
            price = previous_close

        day_change = None
        day_change_pct = None
        if price is not None and previous_close:
            try:
                day_change = float(price) - float(previous_close)
                day_change_pct = (day_change / float(previous_close)) * 100
            except (TypeError, ValueError, ZeroDivisionError):
                pass

        sparkline: list[float] = []
        try:
            quotes = (result.get("indicators") or {}).get("quote") or []
            closes = (quotes[0].get("close") if quotes else None) or []
            sparkline = [float(c) for c in closes if c is not None][-30:]
        except (TypeError, ValueError, IndexError, AttributeError):
            sparkline = []

        # Longer history for sparklines when short range was used
        if len(sparkline) < 5:
            long_payload = await self._chart_json(symbol, range_="3mo")
            if long_payload:
                try:
                    res2 = long_payload["chart"]["result"][0]
                    quotes = (res2.get("indicators") or {}).get("quote") or []
                    closes = (quotes[0].get("close") if quotes else None) or []
                    sparkline = [float(c) for c in closes if c is not None][-30:]
                except (TypeError, ValueError, IndexError, AttributeError, KeyError):
                    pass

        divs: list[dict] = []
        events = (result.get("events") or {}).get("dividends") or {}
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=30)
        for _key, ev in events.items():
            try:
                ts = int(ev.get("date", 0))
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                amount = float(ev.get("amount", 0))
            except (TypeError, ValueError, OSError):
                continue
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
            "price": float(price) if price is not None else None,
            "previous_close": float(previous_close) if previous_close is not None else None,
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

    async def _chart_json(self, symbol: str, range_: str = "5d") -> dict | None:
        url = CHART_URL.format(symbol=symbol)
        try:
            async with self._session.get(
                url,
                params={"interval": "1d", "range": range_, "events": "div"},
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.debug("Yahoo HTTP %s for %s range=%s", resp.status, symbol, range_)
                    return None
                payload = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Yahoo request failed %s: %s", symbol, err)
            return None

        try:
            if not payload.get("chart", {}).get("result"):
                return None
        except AttributeError:
            return None
        return payload

    def price_data(self, symbol: str) -> dict:
        """Return price payload for symbol; always a dict (never None)."""
        data = self.data or {}
        prices = data.get("prices")
        if isinstance(prices, dict):
            payload = prices.get(symbol)
            if isinstance(payload, dict):
                return payload
            # Case-insensitive fallback
            upper = {str(k).upper(): v for k, v in prices.items()}
            payload = upper.get(str(symbol).upper())
            if isinstance(payload, dict):
                return payload
        payload = data.get(symbol)
        if isinstance(payload, dict):
            return payload
        return {}

    def fx_rate(self, currency: str | None) -> float:
        data = self.data or {}
        rates = data.get("fx_rates") or {}
        base = (data.get("base_currency") or DEFAULT_BASE_CURRENCY).upper()
        ccy = (currency or base).upper()
        try:
            rate = float(rates.get(ccy, 1.0) or 1.0)
        except (TypeError, ValueError):
            rate = 1.0
        return rate if rate > 0 else 1.0

    def base_currency(self) -> str:
        return (self.data or {}).get("base_currency") or DEFAULT_BASE_CURRENCY

    def dividends(self) -> list[dict]:
        return list((self.data or {}).get("dividends") or [])
