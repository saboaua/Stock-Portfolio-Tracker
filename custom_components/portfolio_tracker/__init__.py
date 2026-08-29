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
    CONF_NAME,
    CONF_HOLDINGS,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    SERVICE_BUY,
    SERVICE_SELL,
    SERVICE_REFRESH,
)
from .coordinator import PortfolioDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]

BUY_SCHEMA = vol.Schema(
    {
        vol.Required("symbol"): cv.string,
        vol.Required("shares"): vol.Coerce(float),
        vol.Required("cost"): vol.Coerce(float),
        vol.Optional("portfolio"): cv.string,
    }
)

SELL_SCHEMA = vol.Schema(
    {
        vol.Required("symbol"): cv.string,
        vol.Required("shares"): vol.Coerce(float),
        vol.Optional("portfolio"): cv.string,
    }
)

REFRESH_SCHEMA = vol.Schema({vol.Optional("portfolio"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    coordinator = PortfolioDataCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry whenever holdings or settings change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _find_entry_by_portfolio_name(hass: HomeAssistant, portfolio_name: str):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_NAME, "").lower() == portfolio_name.lower():
            return entry
    return None


def _resolve_entry_for_symbol(hass: HomeAssistant, symbol: str, portfolio_name: str | None):
    """Work out which portfolio a buy/sell service call applies to.

    If `portfolio` was given, use that portfolio by name. Otherwise, look
    for exactly one portfolio that already holds the symbol. If none hold
    it and there's only one portfolio configured, use that one (so buying
    a brand-new symbol still works without specifying a portfolio).
    """
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None, "Portfolio Tracker is not set up"

    if portfolio_name:
        entry = _find_entry_by_portfolio_name(hass, portfolio_name)
        if entry is None:
            return None, f"No portfolio named '{portfolio_name}' found"
        return entry, None

    matches = [e for e in entries if symbol in e.options.get(CONF_HOLDINGS, {})]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        names = ", ".join(e.data.get(CONF_NAME, e.entry_id) for e in matches)
        return None, (
            f"{symbol} exists in multiple portfolios ({names}). "
            "Specify 'portfolio' in the service call."
        )
    if len(entries) == 1:
        return entries[0], None

    names = ", ".join(e.data.get(CONF_NAME, e.entry_id) for e in entries)
    return None, (
        f"Multiple portfolios configured ({names}) and {symbol} isn't in any of them. "
        "Specify 'portfolio' in the service call."
    )


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_BUY):
        return

    async def handle_buy(call: ServiceCall) -> None:
        symbol = call.data["symbol"].strip().upper()
        entry, error = _resolve_entry_for_symbol(hass, symbol, call.data.get("portfolio"))
        if entry is None:
            _LOGGER.error("buy_shares failed: %s", error)
            return

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
        symbol = call.data["symbol"].strip().upper()
        entry, error = _resolve_entry_for_symbol(hass, symbol, call.data.get("portfolio"))
        if entry is None:
            _LOGGER.error("sell_shares failed: %s", error)
            return

        holdings = dict(entry.options.get(CONF_HOLDINGS, {}))
        h = holdings.get(symbol)
        if not h:
            _LOGGER.error("No holding found for %s in portfolio '%s'", symbol, entry.title)
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

    async def handle_refresh(call: ServiceCall) -> None:
        portfolio_name = call.data.get("portfolio")
        entries = hass.config_entries.async_entries(DOMAIN)
        if portfolio_name:
            entry = _find_entry_by_portfolio_name(hass, portfolio_name)
            if entry is None:
                _LOGGER.error("refresh failed: no portfolio named '%s'", portfolio_name)
                return
            entries = [entry]
        for entry in entries:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
            if data:
                await data["coordinator"].async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_BUY, handle_buy, schema=BUY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SELL, handle_sell, schema=SELL_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, handle_refresh, schema=REFRESH_SCHEMA
    )
