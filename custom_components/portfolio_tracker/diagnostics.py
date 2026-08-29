"""Diagnostics support for Portfolio Tracker."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HOLDINGS, VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = data.get("coordinator")
    holdings = entry.options.get(CONF_HOLDINGS, {})

    prices = {}
    if coordinator and coordinator.data:
        for symbol, payload in coordinator.data.items():
            if not payload:
                prices[symbol] = None
                continue
            prices[symbol] = {
                "price": payload.get("price"),
                "currency": payload.get("currency"),
                "day_change_pct": payload.get("day_change_pct"),
                "market_state": payload.get("market_state"),
            }

    return {
        "version": VERSION,
        "entry_id": entry.entry_id,
        "holdings_count": len(holdings),
        "symbols": sorted(holdings.keys()),
        "holdings_summary": {
            s: {
                "shares": h.get("shares"),
                "invested": h.get("invested"),
                "entry_date": h.get("entry_date"),
            }
            for s, h in holdings.items()
        },
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "prices": prices,
    }
