"""Manual refresh button - one per portfolio."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PortfolioDataCoordinator
from .device import device_info as _device_info


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: PortfolioDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([RefreshPricesButton(coordinator, entry)])


class RefreshPricesButton(ButtonEntity):
    """Forces an immediate price refresh for this portfolio."""

    _attr_has_entity_name = True
    _attr_name = "Refresh Prices"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: PortfolioDataCoordinator, entry: ConfigEntry):
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_refresh_prices"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self._coordinator.async_request_refresh()
