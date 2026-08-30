"""Button platform — manual refresh."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import device_info as _device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    async_add_entities([PortfolioRefreshButton(hass, entry)])


class PortfolioRefreshButton(ButtonEntity):
    """Force an immediate Yahoo Finance refresh."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self.entity_id = "button.portfolio_refresh"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        coordinator = data.get("coordinator")
        if coordinator is not None:
            await coordinator.async_request_refresh()
