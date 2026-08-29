"""The Portfolio Tracker integration."""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from .const import (
    DOMAIN,
    VERSION,
    CONF_HOLDINGS,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    CONF_SCAN_INTERVAL,
    CONF_IDLE_SCAN_INTERVAL,
    CONF_REALIZED_GAIN,
    CONF_TRADE_LOG,
    CONF_BASE_CURRENCY,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    IDLE_SCAN_INTERVAL_MINUTES,
    DEFAULT_BASE_CURRENCY,
    MAX_TRADE_LOG,
    SERVICE_BUY,
    SERVICE_SELL,
    SERVICE_REFRESH,
)
from .coordinator import PortfolioDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.BUTTON]

BUY_SCHEMA = vol.Schema(
    {
        vol.Required("symbol"): cv.string,
        vol.Required("shares"): vol.Coerce(float),
        vol.Required("cost"): vol.Coerce(float),
    }
)

SELL_SCHEMA = vol.Schema(
    {
        vol.Required("symbol"): cv.string,
        vol.Required("shares"): vol.Coerce(float),
        vol.Optional("proceeds"): vol.Coerce(float),
    }
)


def _append_trade(options: dict, trade: dict) -> None:
    log = list(options.get(CONF_TRADE_LOG, []))
    log.insert(0, trade)
    options[CONF_TRADE_LOG] = log[:MAX_TRADE_LOG]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Portfolio Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    def get_symbols():
        return list(entry.options.get(CONF_HOLDINGS, {}).keys())

    def get_base_currency():
        return entry.options.get(CONF_BASE_CURRENCY, DEFAULT_BASE_CURRENCY)

    scan = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES))
    idle = int(entry.options.get(CONF_IDLE_SCAN_INTERVAL, IDLE_SCAN_INTERVAL_MINUTES))

    coordinator = PortfolioDataCoordinator(
        hass, get_symbols, get_base_currency, scan, idle
    )
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "entry": entry}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    await _async_register_lovelace_card(hass)

    _LOGGER.info("Portfolio Tracker %s started", VERSION)
    return True


async def _async_register_lovelace_card(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card from /portfolio_tracker_static/."""
    if hass.data.get(DOMAIN, {}).get("_card_registered"):
        return
    www = Path(__file__).parent / "www"
    if not www.is_dir():
        return
    try:
        # HA 2024.6+: StaticPathConfig + async_register_static_paths
        try:
            from homeassistant.components.http import StaticPathConfig

            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        "/portfolio_tracker_static",
                        str(www),
                        cache_headers=False,
                    )
                ]
            )
        except (ImportError, AttributeError, TypeError):
            # Older HA fallback
            hass.http.register_static_path(
                "/portfolio_tracker_static", str(www), cache_headers=False
            )
        hass.data[DOMAIN]["_card_registered"] = True
        _LOGGER.debug("Registered Lovelace card static path")
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Lovelace card static path not registered: %s", err)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not any(k for k in hass.data.get(DOMAIN, {}) if k != "_card_registered"):
            for service in (SERVICE_BUY, SERVICE_SELL, SERVICE_REFRESH):
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_BUY):
        return

    def _get_entry():
        entries = hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None

    async def handle_buy(call: ServiceCall) -> None:
        entry = _get_entry()
        if entry is None:
            _LOGGER.error("Portfolio Tracker is not set up")
            return
        symbol = call.data["symbol"].strip().upper()
        shares = float(call.data["shares"])
        cost = float(call.data["cost"])
        holdings = dict(entry.options.get(CONF_HOLDINGS, {}))
        h = holdings.get(
            symbol, {CONF_SHARES: 0, CONF_INVESTED: 0, CONF_ENTRY_DATE: None}
        )
        h[CONF_SHARES] = round(float(h.get(CONF_SHARES, 0)) + shares, 6)
        h[CONF_INVESTED] = round(float(h.get(CONF_INVESTED, 0)) + cost, 2)
        if not h.get(CONF_ENTRY_DATE):
            h[CONF_ENTRY_DATE] = str(date.today())
        holdings[symbol] = h
        new_options = dict(entry.options)
        new_options[CONF_HOLDINGS] = holdings
        _append_trade(
            new_options,
            {
                "type": "buy",
                "symbol": symbol,
                "shares": shares,
                "amount": cost,
                "date": datetime.now().isoformat(timespec="seconds"),
            },
        )
        hass.config_entries.async_update_entry(entry, options=new_options)

    async def handle_sell(call: ServiceCall) -> None:
        entry = _get_entry()
        if entry is None:
            _LOGGER.error("Portfolio Tracker is not set up")
            return
        symbol = call.data["symbol"].strip().upper()
        holdings = dict(entry.options.get(CONF_HOLDINGS, {}))
        h = holdings.get(symbol)
        if not h:
            _LOGGER.error("No holding found for %s", symbol)
            return
        cur_shares = float(h.get(CONF_SHARES, 0))
        sell_shares = float(call.data["shares"])
        if sell_shares <= 0 or sell_shares > cur_shares:
            _LOGGER.error("Invalid share amount to sell for %s", symbol)
            return
        avg_cost = float(h.get(CONF_INVESTED, 0)) / cur_shares if cur_shares else 0
        cost_basis_sold = avg_cost * sell_shares
        proceeds = call.data.get("proceeds")
        if proceeds is None:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
            coord = data.get("coordinator")
            price = None
            if coord:
                price = coord.price_data(symbol).get("price")
            proceeds = float(price * sell_shares) if price is not None else cost_basis_sold
        realized = float(proceeds) - cost_basis_sold

        h[CONF_SHARES] = round(cur_shares - sell_shares, 6)
        h[CONF_INVESTED] = round(float(h.get(CONF_INVESTED, 0)) - cost_basis_sold, 2)
        if h[CONF_SHARES] <= 0:
            holdings.pop(symbol, None)
        else:
            holdings[symbol] = h

        new_options = dict(entry.options)
        new_options[CONF_HOLDINGS] = holdings
        new_options[CONF_REALIZED_GAIN] = round(
            float(new_options.get(CONF_REALIZED_GAIN, 0)) + realized, 2
        )
        _append_trade(
            new_options,
            {
                "type": "sell",
                "symbol": symbol,
                "shares": sell_shares,
                "amount": float(proceeds),
                "cost_basis": round(cost_basis_sold, 2),
                "realized": round(realized, 2),
                "date": datetime.now().isoformat(timespec="seconds"),
            },
        )
        hass.config_entries.async_update_entry(entry, options=new_options)

    async def handle_refresh(call: ServiceCall) -> None:
        entry = _get_entry()
        if entry is None:
            _LOGGER.error("Portfolio Tracker is not set up")
            return
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        coordinator = data.get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_BUY, handle_buy, schema=BUY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SELL, handle_sell, schema=SELL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh)
