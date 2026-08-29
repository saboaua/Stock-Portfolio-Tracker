"""Shared helpers for naming and device grouping across platforms."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_NAME, DEFAULT_PORTFOLIO_NAME


def portfolio_name(entry: ConfigEntry) -> str:
    """The human-readable name of this portfolio, e.g. 'Cesar'."""
    return entry.data.get(CONF_NAME) or entry.title or DEFAULT_PORTFOLIO_NAME


def device_info(entry: ConfigEntry) -> DeviceInfo:
    """All entities for a portfolio are grouped under one 'Investing {name}' device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Investing {portfolio_name(entry)}",
        manufacturer="Custom",
        model="Portfolio Tracker",
    )
