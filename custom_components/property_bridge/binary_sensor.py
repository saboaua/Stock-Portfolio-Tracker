"""Binary sensor platform for Property Bridge – maintenance & consent."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_CONNECTION_UPDATE
from .connection import BridgeConnection

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="maintenance_allowed",
        name="Maintenance Allowed",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:wrench-clock",
    ),
    BinarySensorEntityDescription(
        key="consent_granted",
        name="Maintenance Consent",
        icon="mdi:account-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Property Bridge binary sensors."""
    connection: BridgeConnection = hass.data[DOMAIN][entry.entry_id]

    entities = [
        BridgeBinarySensor(connection, entry, description)
        for description in BINARY_SENSOR_TYPES
    ]
    async_add_entities(entities)


class BridgeBinarySensor(BinarySensorEntity):
    """Binary sensor for maintenance window / consent state."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        connection: BridgeConnection,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        self.entity_description = description
        self._connection = connection
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=connection.property_name,
            manufacturer="Property Bridge",
            model="Remote Home Assistant",
        )

    async def async_added_to_hass(self) -> None:
        """Register update callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_CONNECTION_UPDATE}_{self._entry.entry_id}",
                self._handle_update,
            )
        )
        self._handle_update()

    @callback
    def _handle_update(self) -> None:
        """Update state from connection."""
        data = self._connection.get_status_data()

        if self.entity_description.key == "maintenance_allowed":
            self._attr_is_on = bool(data.get("maintenance_allowed"))
        elif self.entity_description.key == "consent_granted":
            self._attr_is_on = bool(data.get("consent_granted"))

        self._attr_extra_state_attributes = {
            "maintenance_until": data.get("maintenance_until"),
            "maintenance_requested": data.get("maintenance_requested"),
            "property_name": data.get("property_name"),
        }
        self.async_write_ha_state()
