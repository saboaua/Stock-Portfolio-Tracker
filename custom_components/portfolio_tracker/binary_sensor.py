"""US / EU market-open binary sensors."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval

from . import market_hours
from .const import DOMAIN


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Portfolio Tracker",
        manufacturer="Custom",
        model="Portfolio Tracker",
        sw_version="1.2.0",
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    async_add_entities(
        [
            MarketOpenSensor(
                entry,
                name="US Market Open",
                key="us_market_open",
                market="us",
                icon="mdi:flag-variant",
            ),
            MarketOpenSensor(
                entry,
                name="EU Market Open",
                key="eu_market_open",
                market="eu",
                icon="mdi:flag-variant-outline",
            ),
        ]
    )


class MarketOpenSensor(BinarySensorEntity):
    """True while the given exchange is in its regular trading session.

    Computed from the exchange's own timezone (DST-aware via zoneinfo).
    Does not account for market holidays.
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_should_poll = False

    def __init__(self, entry, name, key, market, icon):
        self._entry = entry
        self._market = market
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)
        # Stable entity_id: binary_sensor.us_market_open / eu_market_open
        self.entity_id = f"binary_sensor.{key}"
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        self._unsub = async_track_time_interval(
            self.hass, self._tick, timedelta(minutes=1)
        )
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()

    async def _tick(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        if self._market == "us":
            return market_hours.us_market_open()
        return market_hours.eu_market_open()

    @property
    def extra_state_attributes(self):
        if self._market == "us":
            tz = market_hours.US_TZ
            open_t = market_hours.US_OPEN
            close_t = market_hours.US_CLOSE
            next_open = market_hours.us_next_open()
            next_close = market_hours.us_next_close()
        else:
            tz = market_hours.EU_TZ
            open_t = market_hours.EU_OPEN
            close_t = market_hours.EU_CLOSE
            next_open = market_hours.eu_next_open()
            next_close = market_hours.eu_next_close()

        now = datetime.now(tz)
        return {
            "exchange_timezone": str(tz),
            "opens_at_local": open_t.strftime("%H:%M"),
            "closes_at_local": close_t.strftime("%H:%M"),
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "next_open": next_open.isoformat(),
            "next_close": next_close.isoformat(),
            "next_open_local": next_open.strftime("%Y-%m-%d %H:%M"),
            "next_close_local": next_close.strftime("%Y-%m-%d %H:%M"),
        }
