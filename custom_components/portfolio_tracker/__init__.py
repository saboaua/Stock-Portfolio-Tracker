"""The Portfolio Tracker integration."""
from __future__ import annotations

import logging
from datetime import date

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOLDINGS,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    SERVICE_BUY,
    SERVICE_SELL,
)
from .coordinator import PortfolioDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

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
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    def get_symbols():
        return list(entry.options.get(CONF_HOLDINGS, {}).keys())

    coordinator = PortfolioDataCoordinator(hass, get_symbols)
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry whenever holdings change (added/bought/sold/edited)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register buy_shares / sell_shares so automations & scripts can log trades."""
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
        holdings = dict(entry.options.get(CONF_HOLDINGS, {}))
        h = holdings.get(symbol, {CONF_SHARES: 0, CONF_INVESTED: 0, CONF_ENTRY_DATE: None})
        h[CONF_SHARES] = round(float(h.get(CONF_SHARES, 0)) + float(call.data["shares"]), 6)
        h[CONF_INVESTED] = round(float(h.get(CONF_INVESTED, 0)) + float(call.data["cost"]), 2)
        if not h.get(CONF_ENTRY_DATE):
            h[CONF_ENTRY_DATE] = str(date.today())
        holdings[symbol] = h
        new_options = dict(entry.options)
        new_options[CONF_HOLDINGS] = holdings
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
        h[CONF_SHARES] = round(cur_shares - sell_shares, 6)
        h[CONF_INVESTED] = round(float(h.get(CONF_INVESTED, 0)) - (avg_cost * sell_shares), 2)
        if h[CONF_SHARES] <= 0:
            holdings.pop(symbol, None)
        else:
            holdings[symbol] = h
        new_options = dict(entry.options)
        new_options[CONF_HOLDINGS] = holdings
        hass.config_entries.async_update_entry(entry, options=new_options)

    hass.services.async_register(DOMAIN, SERVICE_BUY, handle_buy, schema=BUY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SELL, handle_sell, schema=SELL_SCHEMA)
