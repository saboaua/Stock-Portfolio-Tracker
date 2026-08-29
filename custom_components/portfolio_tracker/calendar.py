"""Dividend calendar for Portfolio Tracker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
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
    async_add_entities([PortfolioDividendCalendar(coordinator, entry)])


class PortfolioDividendCalendar(CoordinatorEntity, CalendarEntity):
    """Shows recent and upcoming dividend events from Yahoo chart data."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Dividends"
    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator: PortfolioDataCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_dividends_calendar"
        self.entity_id = "calendar.portfolio_dividends"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Portfolio Tracker",
            manufacturer="Portfolio Tracker",
            model="Yahoo Finance",
            sw_version=VERSION,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next dividend event."""
        events = self._events_from_coordinator()
        now = datetime.now(timezone.utc)
        future = [e for e in events if e.end >= now]
        return future[0] if future else (events[-1] if events else None)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        events = self._events_from_coordinator()
        return [e for e in events if e.start < end_date and e.end > start_date]

    def _events_from_coordinator(self) -> list[CalendarEvent]:
        result: list[CalendarEvent] = []
        for d in self.coordinator.dividends():
            try:
                day = datetime.fromisoformat(d["date"]).date()
            except (KeyError, ValueError, TypeError):
                continue
            start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            end = start + timedelta(days=1)
            symbol = d.get("symbol", "?")
            amount = d.get("amount", 0)
            ccy = d.get("currency") or ""
            result.append(
                CalendarEvent(
                    start=start,
                    end=end,
                    summary=f"{symbol} dividend {amount} {ccy}".strip(),
                    description=f"Dividend for {symbol}: {amount} {ccy}".strip(),
                    uid=f"{symbol}-{d.get('date')}-{amount}",
                )
            )
        result.sort(key=lambda e: e.start)
        return result
