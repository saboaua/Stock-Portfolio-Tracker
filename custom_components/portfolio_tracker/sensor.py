"""Sensors for Portfolio Tracker."""
from __future__ import annotations

from datetime import date, datetime
import logging
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOLDINGS, CONF_SHARES, CONF_INVESTED, CONF_ENTRY_DATE
from .coordinator import PortfolioDataCoordinator

_LOGGER = logging.getLogger(__name__)


def _slug(symbol: str) -> str:
    """Yahoo-style ticker to entity-id friendly slug (VUAA.L -> vuaa_l)."""
    return re.sub(r"[^a-z0-9]+", "_", symbol.lower()).strip("_")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: PortfolioDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    await coordinator.async_config_entry_first_refresh()

    holdings = entry.options.get(CONF_HOLDINGS, {})

    entities: list[SensorEntity] = []
    for symbol in holdings:
        entities.append(PortfolioPriceSensor(coordinator, entry, symbol))
        entities.append(PortfolioPositionSensor(coordinator, entry, symbol))

    entities.append(PortfolioTotalValueSensor(coordinator, entry))
    entities.append(PortfolioTotalInvestedSensor(coordinator, entry))
    entities.append(PortfolioTotalGainSensor(coordinator, entry))
    entities.append(PortfolioDayChangeSensor(coordinator, entry))
    entities.append(PortfolioHoldingsTableSensor(coordinator, entry))
    # Market session clocks (open / close times as text sensors)
    entities.append(MarketSessionSensor(entry, "us", "US Market Session"))
    entities.append(MarketSessionSensor(entry, "eu", "EU Market Session"))

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Portfolio Tracker",
        manufacturer="Custom",
        model="Portfolio Tracker",
        sw_version="1.1.0",
    )


class _BaseHoldingSensor(CoordinatorEntity, SensorEntity):
    """Base for sensors tied to one specific holding/symbol."""

    def __init__(self, coordinator, entry, symbol):
        super().__init__(coordinator)
        self._entry = entry
        self._symbol = symbol
        self._attr_device_info = _device_info(entry)
        self._attr_has_entity_name = False

    @property
    def _holding(self) -> dict:
        return self._entry.options.get(CONF_HOLDINGS, {}).get(self._symbol, {})

    @property
    def _price_data(self) -> dict:
        return (self.coordinator.data or {}).get(self._symbol) or {}

    @property
    def available(self) -> bool:
        return super().available and bool(self._holding)


class PortfolioPriceSensor(_BaseHoldingSensor):
    """Live market price for one symbol."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, symbol):
        super().__init__(coordinator, entry, symbol)
        slug = _slug(symbol)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_price"
        self._attr_name = f"{symbol} Price"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        price = self._price_data.get("price")
        return round(price, 4) if price is not None else None

    @property
    def native_unit_of_measurement(self):
        return self._price_data.get("currency") or "USD"

    @property
    def extra_state_attributes(self):
        d = self._price_data
        return {
            "symbol": self._symbol,
            "previous_close": d.get("previous_close"),
            "day_change": d.get("day_change"),
            "day_change_pct": d.get("day_change_pct"),
            "currency": d.get("currency"),
        }


class PortfolioPositionSensor(_BaseHoldingSensor):
    """Market value of one holding (shares * price), with gain/loss attributes."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, symbol):
        super().__init__(coordinator, entry, symbol)
        slug = _slug(symbol)
        self._attr_unique_id = f"{entry.entry_id}_{slug}_position_value"
        self._attr_name = f"{symbol} Position Value"
        self._attr_icon = "mdi:cash-multiple"

    def _shares(self) -> float:
        return float(self._holding.get(CONF_SHARES, 0) or 0)

    def _invested(self) -> float:
        return float(self._holding.get(CONF_INVESTED, 0) or 0)

    @property
    def native_unit_of_measurement(self):
        return self._price_data.get("currency") or "USD"

    @property
    def native_value(self):
        price = self._price_data.get("price")
        if price is None:
            return None
        return round(price * self._shares(), 2)

    @property
    def extra_state_attributes(self):
        price = self._price_data.get("price")
        shares = self._shares()
        invested = self._invested()
        value = (price * shares) if price is not None else None
        gain = (value - invested) if value is not None else None
        gain_pct = ((gain / invested) * 100) if gain is not None and invested else 0
        avg_cost = (invested / shares) if shares else 0

        entry_date = self._holding.get(CONF_ENTRY_DATE)
        days_held = None
        if entry_date:
            try:
                d = datetime.fromisoformat(str(entry_date)).date()
                days_held = (date.today() - d).days
            except ValueError:
                days_held = None

        return {
            "symbol": self._symbol,
            "shares": round(shares, 6),
            "invested": round(invested, 2),
            "gain": round(gain, 2) if gain is not None else None,
            "gain_pct": round(gain_pct, 2),
            "avg_cost_per_share": round(avg_cost, 4),
            "entry_date": entry_date,
            "days_held": days_held,
            "currency": self._price_data.get("currency"),
        }


class _BaseTotalSensor(CoordinatorEntity, SensorEntity):
    """Base for sensors that aggregate across the whole portfolio."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "USD"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = _device_info(entry)
        self._attr_has_entity_name = False

    @property
    def _holdings(self) -> dict:
        return self._entry.options.get(CONF_HOLDINGS, {})

    def _position_value(self, symbol, holding):
        price_data = (self.coordinator.data or {}).get(symbol) or {}
        price = price_data.get("price")
        shares = float(holding.get(CONF_SHARES, 0) or 0)
        if price is None:
            return None
        return price * shares

    def _day_change_dollar(self, symbol, holding):
        price_data = (self.coordinator.data or {}).get(symbol) or {}
        change = price_data.get("day_change")
        shares = float(holding.get(CONF_SHARES, 0) or 0)
        if change is None:
            return 0.0
        return change * shares


class PortfolioTotalValueSensor(_BaseTotalSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_value"
        self._attr_name = "Portfolio Total Value"
        self._attr_icon = "mdi:wallet"

    @property
    def native_value(self):
        total = 0.0
        for symbol, holding in self._holdings.items():
            val = self._position_value(symbol, holding)
            if val is not None:
                total += val
        return round(total, 2)


class PortfolioTotalInvestedSensor(_BaseTotalSensor):
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_invested"
        self._attr_name = "Portfolio Total Invested"
        self._attr_icon = "mdi:piggy-bank"

    @property
    def native_value(self):
        return round(
            sum(float(h.get(CONF_INVESTED, 0) or 0) for h in self._holdings.values()), 2
        )


class PortfolioTotalGainSensor(_BaseTotalSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_gain"
        self._attr_name = "Portfolio Total Gain"
        self._attr_icon = "mdi:trending-up"

    def _totals(self):
        total_value = 0.0
        total_invested = 0.0
        for symbol, holding in self._holdings.items():
            val = self._position_value(symbol, holding)
            if val is not None:
                total_value += val
            total_invested += float(holding.get(CONF_INVESTED, 0) or 0)
        return total_value, total_invested

    @property
    def native_value(self):
        total_value, total_invested = self._totals()
        return round(total_value - total_invested, 2)

    @property
    def extra_state_attributes(self):
        total_value, total_invested = self._totals()
        gain_pct = (
            ((total_value - total_invested) / total_invested * 100)
            if total_invested
            else 0
        )
        return {"gain_pct": round(gain_pct, 2)}


class PortfolioDayChangeSensor(_BaseTotalSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_day_change"
        self._attr_name = "Portfolio Day Change"
        self._attr_icon = "mdi:chart-timeline-variant"

    @property
    def native_value(self):
        total = 0.0
        for symbol, holding in self._holdings.items():
            total += self._day_change_dollar(symbol, holding)
        return round(total, 2)

    @property
    def extra_state_attributes(self):
        total_change = self.native_value or 0.0
        total_value = 0.0
        for symbol, holding in self._holdings.items():
            val = self._position_value(symbol, holding)
            if val is not None:
                total_value += val
        previous_total = total_value - total_change
        gain_pct = (total_change / previous_total * 100) if previous_total else 0
        return {"gain_pct": round(gain_pct, 2)}


class PortfolioHoldingsTableSensor(_BaseTotalSensor):
    """Feeds a custom:flex-table-card holdings table."""

    _attr_device_class = None
    _attr_state_class = None
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_holdings_table"
        self._attr_name = "Portfolio Holdings Table"
        self._attr_icon = "mdi:table"

    @property
    def native_value(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def extra_state_attributes(self):
        rows = []
        for symbol, holding in self._holdings.items():
            price_data = (self.coordinator.data or {}).get(symbol) or {}
            price = price_data.get("price") or 0
            shares = float(holding.get(CONF_SHARES, 0) or 0)
            invested = float(holding.get(CONF_INVESTED, 0) or 0)
            avg_cost = (invested / shares) if shares else 0
            market_value = price * shares
            day_change = price_data.get("day_change") or 0
            day_change_pct = price_data.get("day_change_pct") or 0
            gain = market_value - invested
            gain_pct = (gain / invested * 100) if invested else 0

            rows.append(
                {
                    "symbol": symbol,
                    "status": "Open",
                    "shares": round(shares, 2),
                    "last_price": round(price, 2),
                    "ac_share": round(avg_cost, 2),
                    "total_cost": round(invested, 2),
                    "market_value": round(market_value, 2),
                    "day_gain_pct": round(day_change_pct, 2),
                    "day_gain_dollar": round(day_change * shares, 2),
                    "tot_gain_pct": round(gain_pct, 2),
                    "tot_gain_dollar": round(gain, 2),
                }
            )
        return {"rows": rows}


class MarketSessionSensor(SensorEntity):
    """Human-readable open/close schedule for US or EU markets.

    State is 'open' or 'closed'. Attributes carry next open/close timestamps
    and the exchange-local clock times so dashboards can display them.
    """

    _attr_should_poll = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, entry: ConfigEntry, market: str, name: str) -> None:
        self._entry = entry
        self._market = market  # "us" or "eu"
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{market}_market_session"
        self._attr_device_info = _device_info(entry)
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta

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
    def native_value(self) -> str:
        from . import market_hours

        if self._market == "us":
            return "open" if market_hours.us_market_open() else "closed"
        return "open" if market_hours.eu_market_open() else "closed"

    @property
    def extra_state_attributes(self):
        from . import market_hours
        from datetime import datetime

        if self._market == "us":
            tz = market_hours.US_TZ
            open_t = market_hours.US_OPEN
            close_t = market_hours.US_CLOSE
            next_open = market_hours.us_next_open()
            next_close = market_hours.us_next_close()
            is_open = market_hours.us_market_open()
        else:
            tz = market_hours.EU_TZ
            open_t = market_hours.EU_OPEN
            close_t = market_hours.EU_CLOSE
            next_open = market_hours.eu_next_open()
            next_close = market_hours.eu_next_close()
            is_open = market_hours.eu_market_open()

        now = datetime.now(tz)
        return {
            "is_open": is_open,
            "exchange_timezone": str(tz),
            "opens_at_local": open_t.strftime("%H:%M"),
            "closes_at_local": close_t.strftime("%H:%M"),
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "next_open": next_open.isoformat(),
            "next_close": next_close.isoformat(),
            "next_open_local": next_open.strftime("%Y-%m-%d %H:%M"),
            "next_close_local": next_close.strftime("%Y-%m-%d %H:%M"),
        }
