"""Sensor platform for Property Bridge – connection health and status."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_CONNECTION_UPDATE
from .connection import BridgeConnection

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="status",
        name="Connection Status",
        icon="mdi:home-assistant",
    ),
    SensorEntityDescription(
        key="entity_count",
        name="Mirrored Entities",
        icon="mdi:counter",
        native_unit_of_measurement="entities",
    ),
    SensorEntityDescription(
        key="maintenance_until",
        name="Maintenance Until",
        icon="mdi:calendar-clock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Property Bridge sensors from a config entry."""
    connection: BridgeConnection = hass.data[DOMAIN][entry.entry_id]

    entities = [
        BridgeConnectionSensor(connection, entry, description)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class BridgeConnectionSensor(SensorEntity):
    """Representation of a Property Bridge connection status sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        connection: BridgeConnection,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._connection = connection
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=connection.property_name,
            manufacturer="Property Bridge",
            model="Remote Home Assistant",
            sw_version=connection.remote_version,
            configuration_url=(
                f"{'https' if connection.secure else 'http'}://"
                f"{connection.host}:{connection.port}"
            ),
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
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
        """Update the sensor state from the connection object."""
        data = self._connection.get_status_data()

        if self.entity_description.key == "status":
            self._attr_native_value = (
                "Connected" if data["connected"] else "Disconnected"
            )
            self._attr_icon = (
                "mdi:check-network" if data["connected"] else "mdi:close-network"
            )
        elif self.entity_description.key == "entity_count":
            self._attr_native_value = data["entity_count"]
        elif self.entity_description.key == "maintenance_until":
            self._attr_native_value = data.get("maintenance_until") or "None"

        self._attr_extra_state_attributes = {
            "property_name": data["property_name"],
            "host": data["host"],
            "port": data["port"],
            "secure": data.get("secure"),
            "ws_url": data.get("ws_url"),
            "last_error": data.get("last_error"),
            "last_seen": data["last_seen"],
            "remote_version": data["remote_version"],
            "area_id": data.get("area_id"),
            "label_id": data.get("label_id"),
            "maintenance_allowed": data.get("maintenance_allowed"),
            "consent_granted": data.get("consent_granted"),
            "maintenance_requested": data.get("maintenance_requested"),
        }
        self.async_write_ha_state()
