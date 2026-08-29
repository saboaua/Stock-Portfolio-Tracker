"""US / EU market-open binary sensors."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from . import market_hours
from .device import device_info as _device_info


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities(
        [
            MarketOpenSensor(
                entry,
                name="US Market Open",
                key="us_market_open",
                tz=market_hours.US_TZ,
                open_time=market_hours.US_OPEN,
                close_time=market_hours.US_CLOSE,
                icon="mdi:flag-variant",
            ),
            MarketOpenSensor(
                entry,
                name="EU Market Open",
                key="eu_market_open",
                tz=market_hours.EU_TZ,
                open_time=market_hours.EU_OPEN,
                close_time=market_hours.EU_CLOSE,
                icon="mdi:flag-variant-outline",
            ),
        ]
    )


class MarketOpenSensor(BinarySensorEntity):
    """True while the given exchange is in its regular trading session.

    Computed from the exchange's own timezone (DST-aware via zoneinfo), so
    it's correct no matter what timezone Home Assistant or the person
    viewing the dashboard is in. Does not account for market holidays.

    Created once per portfolio entry (so each "Investing {name}" device
    has its own copy) - a small redundancy if you run multiple portfolios,
    traded for simplicity of not needing a cross-entry shared entity.
    """

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_should_poll = False

    def __init__(self, entry, name, key, tz, open_time, close_time, icon):
        self._entry = entry
        self._tz = tz
        self._open_time = open_time
        self._close_time = close_time
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    async def _tick(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        from datetime import datetime

        now = datetime.now(self._tz)
        if now.weekday() >= 5:
            return False
        return self._open_time <= now.time() < self._close_time

    @property
    def extra_state_attributes(self):
        from datetime import datetime

        now = datetime.now(self._tz)
        return {
            "exchange_timezone": str(self._tz),
            "opens_at_local": self._open_time.strftime("%H:%M"),
            "closes_at_local": self._close_time.strftime("%H:%M"),
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
