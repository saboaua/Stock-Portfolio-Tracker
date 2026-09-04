"""Helper utilities for Property Bridge (areas, labels, presets)."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import label_registry as lr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def slugify(value: str) -> str:
    """Simple slugify for area/label ids."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "_", value)
    return value[:64] or "property"


async def async_ensure_area(
    hass: HomeAssistant, property_name: str, existing_area_id: str | None = None
) -> str | None:
    """Create or return an Area for this property.

    Returns the area_id or None on failure.
    """
    area_reg = ar.async_get(hass)

    if existing_area_id:
        area = area_reg.async_get_area(existing_area_id)
        if area:
            return area.id

    # Try to find by name first
    for area in area_reg.areas.values():
        if area.name.lower() == property_name.lower():
            _LOGGER.debug("Reusing existing area '%s' (%s)", area.name, area.id)
            return area.id

    try:
        area = area_reg.async_create(property_name)
        _LOGGER.info("Created area '%s' (%s) for property", area.name, area.id)
        return area.id
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Failed to create area for '%s': %s", property_name, err)
        return None


async def async_ensure_label(
    hass: HomeAssistant, property_name: str, existing_label_id: str | None = None
) -> str | None:
    """Create or return a Label for this property.

    Returns the label_id or None on failure.
    """
    label_reg = lr.async_get(hass)

    if existing_label_id:
        label = label_reg.async_get_label(existing_label_id)
        if label:
            return label.label_id

    # Labels use label_id as key; name is display
    desired_id = f"pb_{slugify(property_name)}"

    existing = label_reg.async_get_label(desired_id)
    if existing:
        _LOGGER.debug("Reusing existing label '%s'", desired_id)
        return existing.label_id

    # Search by name
    for label in label_reg.labels.values():
        if label.name.lower() == property_name.lower():
            return label.label_id

    try:
        label = label_reg.async_create(
            name=property_name,
            # color optional; leave default
        )
        _LOGGER.info("Created label '%s' (%s) for property", label.name, label.label_id)
        return label.label_id
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Failed to create label for '%s': %s", property_name, err)
        return None


async def async_assign_entity_area_label(
    hass: HomeAssistant,
    entity_id: str,
    area_id: str | None,
    label_id: str | None,
) -> None:
    """Assign area and/or label to an entity (used when mirroring)."""
    from homeassistant.helpers import entity_registry as er

    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    if not entry:
        return

    updates: dict[str, Any] = {}
    if area_id and entry.area_id != area_id:
        updates["area_id"] = area_id

    if label_id:
        current_labels = set(entry.labels or [])
        if label_id not in current_labels:
            updates["labels"] = current_labels | {label_id}

    if updates:
        ent_reg.async_update_entity(entity_id, **updates)
        _LOGGER.debug(
            "Assigned area/label to %s: %s", entity_id, updates
        )
