"""Button platform — manual refresh."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import PortfolioDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: PortfolioDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities([PortfolioRefreshButton(coordinator, entry)])


class PortfolioRefreshButton(CoordinatorEntity, ButtonEntity):
    """Force an immediate Yahoo Finance refresh."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: PortfolioDataCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self.entity_id = "button.portfolio_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Portfolio Tracker",
            manufacturer="Portfolio Tracker",
            model="Yahoo Finance",
            sw_version=VERSION,
        )

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
