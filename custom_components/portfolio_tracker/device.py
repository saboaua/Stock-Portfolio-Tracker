"""Single source of truth for device grouping and metadata.

Every entity across every platform (sensor, binary_sensor, button,
calendar) must call device_info(entry) from here rather than building its
own DeviceInfo. Previously each platform module built its own copy with
slightly different (and drifting) manufacturer/model/sw_version values -
binary_sensor.py even had manufacturer and model swapped and a hardcoded
sw_version="1.2.0" that never tracked the real integration version. That
inconsistency is exactly what caused the device page's "Firmware" field to
show a stale/wrong version. Consolidating to one function makes that class
of bug structurally impossible going forward.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, VERSION


def device_info(entry: ConfigEntry) -> DeviceInfo:
    """All entities for a portfolio are grouped under this one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Portfolio Tracker",
        manufacturer="Portfolio Tracker",
        model="Yahoo Finance",
        sw_version=VERSION,
        configuration_url="homeassistant://config/integrations/integration/portfolio_tracker",
    )
