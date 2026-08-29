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

from .const import (
    DOMAIN,
    VERSION,
    CONF_HOLDINGS,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    CONF_REALIZED_GAIN,
    CONF_TRADE_LOG,
    CONF_RETIRE_ENABLED,
    CONF_RETIRE_HORIZON,
    CONF_RETIRE_BASELINE,
    CONF_RETIRE_START_YEAR,
    CONF_RETIRE_CONTRIBUTION,
    CONF_RETIRE_SCENARIO,
    DEFAULT_RETIRE_HORIZON,
    DEFAULT_RETIRE_SCENARIO,
)
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
    entities.append(PortfolioHoldingsCountSensor(coordinator, entry))
    entities.append(PortfolioLastUpdateSensor(coordinator, entry))
    entities.append(PortfolioRealizedGainSensor(coordinator, entry))
    entities.append(PortfolioHoldingsTableSensor(coordinator, entry))
    entities.append(MarketSessionSensor(entry, "us", "US Market Session"))
    entities.append(MarketSessionSensor(entry, "eu", "EU Market Session"))
    entities.append(PortfolioRetirePlanSensor(coordinator, entry))
    entities.append(PortfolioRetireProgressSensor(coordinator, entry))
    entities.append(PortfolioRetireTargetSensor(coordinator, entry))

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Portfolio Tracker",
        manufacturer="Portfolio Tracker",
        model="Yahoo Finance",
        sw_version=VERSION,
        configuration_url="homeassistant://config/integrations/integration/portfolio_tracker",
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
        return self.coordinator.price_data(self._symbol)

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
        self.entity_id = f"sensor.{slug}_price"

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
            "short_name": d.get("short_name"),
            "long_name": d.get("long_name"),
            "exchange": d.get("exchange"),
            "previous_close": d.get("previous_close"),
            "day_change": d.get("day_change"),
            "day_change_pct": d.get("day_change_pct"),
            "currency": d.get("currency"),
            "market_state": d.get("market_state"),
            "fifty_two_week_high": d.get("fifty_two_week_high"),
            "fifty_two_week_low": d.get("fifty_two_week_low"),
            "regular_market_volume": d.get("regular_market_volume"),
            "instrument_type": d.get("instrument_type"),
            "sparkline": d.get("sparkline") or [],
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
        self.entity_id = f"sensor.{slug}_position_value"

    def _shares(self) -> float:
        return float(self._holding.get(CONF_SHARES, 0) or 0)

    def _invested(self) -> float:
        return float(self._holding.get(CONF_INVESTED, 0) or 0)

    def _portfolio_total(self) -> float:
        total = 0.0
        holdings = self._entry.options.get(CONF_HOLDINGS, {})
        for sym, holding in holdings.items():
            pd = self.coordinator.price_data(sym)
            price = pd.get("price")
            shares = float(holding.get(CONF_SHARES, 0) or 0)
            if price is not None:
                total += price * shares * self.coordinator.fx_rate(pd.get("currency"))
        return total

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
        portfolio_total = self._portfolio_total()
        allocation_pct = (
            (value / portfolio_total * 100) if value is not None and portfolio_total else 0
        )

        entry_date = self._holding.get(CONF_ENTRY_DATE)
        days_held = None
        if entry_date:
            try:
                d = datetime.fromisoformat(str(entry_date)).date()
                days_held = (date.today() - d).days
            except ValueError:
                days_held = None

        d = self._price_data
        return {
            "symbol": self._symbol,
            "short_name": d.get("short_name"),
            "long_name": d.get("long_name"),
            "shares": round(shares, 6),
            "invested": round(invested, 2),
            "gain": round(gain, 2) if gain is not None else None,
            "gain_pct": round(gain_pct, 2),
            "allocation_pct": round(allocation_pct, 2),
            "avg_cost_per_share": round(avg_cost, 4),
            "entry_date": entry_date,
            "days_held": days_held,
            "currency": d.get("currency"),
            "day_change": d.get("day_change"),
            "day_change_pct": d.get("day_change_pct"),
            "fifty_two_week_high": d.get("fifty_two_week_high"),
            "fifty_two_week_low": d.get("fifty_two_week_low"),
        }


class _BaseTotalSensor(CoordinatorEntity, SensorEntity):
    """Base for sensors that aggregate across the whole portfolio."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = _device_info(entry)
        self._attr_has_entity_name = False

    @property
    def _holdings(self) -> dict:
        return self._entry.options.get(CONF_HOLDINGS, {})

    def _position_value(self, symbol, holding, *, in_base: bool = True):
        price_data = self.coordinator.price_data(symbol)
        price = price_data.get("price")
        shares = float(holding.get(CONF_SHARES, 0) or 0)
        if price is None:
            return None
        value = price * shares
        if in_base:
            value *= self.coordinator.fx_rate(price_data.get("currency"))
        return value

    def _day_change_dollar(self, symbol, holding, *, in_base: bool = True):
        price_data = self.coordinator.price_data(symbol)
        change = price_data.get("day_change")
        shares = float(holding.get(CONF_SHARES, 0) or 0)
        if change is None:
            return 0.0
        value = change * shares
        if in_base:
            value *= self.coordinator.fx_rate(price_data.get("currency"))
        return value

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.base_currency()


class PortfolioTotalValueSensor(_BaseTotalSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_value"
        self._attr_name = "Portfolio Total Value"
        self._attr_icon = "mdi:wallet"
        self.entity_id = "sensor.portfolio_total_value"

    @property
    def native_value(self):
        total = 0.0
        for symbol, holding in self._holdings.items():
            val = self._position_value(symbol, holding)
            if val is not None:
                total += val
        return round(total, 2)

    @property
    def extra_state_attributes(self):
        return {
            "holdings_count": len(self._holdings),
            "symbols": sorted(self._holdings.keys()),
            "base_currency": self.coordinator.base_currency(),
            "fx_rates": (self.coordinator.data or {}).get("fx_rates"),
        }


class PortfolioTotalInvestedSensor(_BaseTotalSensor):
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_invested"
        self._attr_name = "Portfolio Total Invested"
        self._attr_icon = "mdi:piggy-bank"
        self.entity_id = "sensor.portfolio_total_invested"

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
        self.entity_id = "sensor.portfolio_total_gain"

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
        self.entity_id = "sensor.portfolio_day_change"

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


class PortfolioHoldingsCountSensor(_BaseTotalSensor):
    """Number of open positions in the portfolio."""

    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_holdings_count"
        self._attr_name = "Portfolio Holdings Count"
        self._attr_icon = "mdi:counter"
        self.entity_id = "sensor.portfolio_holdings_count"

    @property
    def native_value(self):
        return len(self._holdings)

    @property
    def extra_state_attributes(self):
        return {"symbols": sorted(self._holdings.keys())}


class PortfolioRealizedGainSensor(_BaseTotalSensor):
    """Lifetimeulated realized P/L from completed sells."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_realized_gain"
        self._attr_name = "Portfolio Realized Gain"
        self._attr_icon = "mdi:cash-check"
        self.entity_id = "sensor.portfolio_realized_gain"

    @property
    def native_value(self):
        return round(float(self._entry.options.get(CONF_REALIZED_GAIN, 0) or 0), 2)

    @property
    def extra_state_attributes(self):
        log = list(self._entry.options.get(CONF_TRADE_LOG, []))
        sells = [t for t in log if t.get("type") == "sell"]
        return {
            "trade_count": len(log),
            "sell_count": len(sells),
            "recent_trades": log[:10],
        }



class PortfolioLastUpdateSensor(CoordinatorEntity, SensorEntity):
    """Timestamp of the last successful Yahoo Finance refresh."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Last Update"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_update"
        self._attr_device_info = _device_info(entry)
        self.entity_id = "sensor.portfolio_last_update"

    @property
    def available(self) -> bool:
        return self.coordinator is not None

    @property
    def native_value(self):
        ts = getattr(self.coordinator, "last_success_time", None)
        if ts is not None:
            return ts
        return getattr(self.coordinator, "last_update_success_time", None)

    @property
    def extra_state_attributes(self):
        return {
            "last_error": getattr(self.coordinator, "last_error", None),
            "last_update_success": getattr(self.coordinator, "last_update_success", None),
        }

class PortfolioHoldingsTableSensor(CoordinatorEntity, SensorEntity):
    """Feeds a custom:flex-table-card holdings table.

    Intentionally does NOT inherit _BaseTotalSensor: that base is MONETARY /
    MEASUREMENT with a currency unit, which is invalid for a timestamp state
    and caused this entity to go unavailable.
    """

    _attr_has_entity_name = False
    _attr_device_class = None
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:table"
    _attr_name = "Portfolio Holdings Table"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_holdings_table"
        self._attr_device_info = _device_info(entry)
        # Prefer clean entity_id; registry may keep portfolio_tracker_ prefix on upgrades
        self.entity_id = "sensor.portfolio_holdings_table"

    @property
    def available(self) -> bool:
        # Stay available as long as the coordinator object exists and we have
        # holdings config — even if the last Yahoo poll failed (show last rows / zeros).
        return self.coordinator is not None

    @property
    def _holdings(self) -> dict:
        return self._entry.options.get(CONF_HOLDINGS, {}) or {}

    @property
    def native_value(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def native_unit_of_measurement(self):
        return None

    @property
    def extra_state_attributes(self):
        rows = []
        portfolio_total = 0.0
        tmp = []
        for symbol, holding in self._holdings.items():
            try:
                price_data = self.coordinator.price_data(symbol) or {}
            except Exception:  # noqa: BLE001
                price_data = {}
            try:
                price = float(price_data.get("price") or 0)
            except (TypeError, ValueError):
                price = 0.0
            try:
                shares = float(holding.get(CONF_SHARES, 0) or 0)
            except (TypeError, ValueError):
                shares = 0.0
            try:
                invested = float(holding.get(CONF_INVESTED, 0) or 0)
            except (TypeError, ValueError):
                invested = 0.0
            market_value = price * shares
            portfolio_total += market_value
            tmp.append((symbol, holding, price_data, price, shares, invested, market_value))

        for symbol, holding, price_data, price, shares, invested, market_value in tmp:
            avg_cost = (invested / shares) if shares else 0.0
            try:
                day_change = float(price_data.get("day_change") or 0)
            except (TypeError, ValueError):
                day_change = 0.0
            try:
                day_change_pct = float(price_data.get("day_change_pct") or 0)
            except (TypeError, ValueError):
                day_change_pct = 0.0
            gain = market_value - invested
            gain_pct = (gain / invested * 100) if invested else 0.0
            alloc = (market_value / portfolio_total * 100) if portfolio_total else 0.0

            rows.append(
                {
                    "symbol": symbol,
                    "name": price_data.get("short_name") or symbol,
                    "long_name": price_data.get("long_name")
                    or price_data.get("short_name")
                    or symbol,
                    "status": "Open",
                    "shares": round(shares, 2),
                    "last_price": round(price, 2),
                    "previous_close": price_data.get("previous_close"),
                    "currency": price_data.get("currency") or "USD",
                    "ac_share": round(avg_cost, 2),
                    "total_cost": round(invested, 2),
                    "market_value": round(market_value, 2),
                    "allocation_pct": round(alloc, 2),
                    "day_gain_pct": round(day_change_pct, 2),
                    "day_gain_dollar": round(day_change * shares, 2),
                    "tot_gain_pct": round(gain_pct, 2),
                    "tot_gain_dollar": round(gain, 2),
                    "sparkline": price_data.get("sparkline") or [],
                }
            )
        return {"rows": rows, "holdings_count": len(rows)}



class MarketSessionSensor(SensorEntity):
    """Human-readable open/close schedule for US or EU markets."""

    _attr_should_poll = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, entry: ConfigEntry, market: str, name: str) -> None:
        self._entry = entry
        self._market = market
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{market}_market_session"
        self._attr_device_info = _device_info(entry)
        self.entity_id = f"sensor.{market}_market_session"
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


class _RetireMixin:
    """Shared retirement plan payload from options + live total value."""

    def _retire_payload(self) -> dict:
        from datetime import date as date_cls
        from .retire import build_plan_payload

        opts = self._entry.options
        if not opts.get(CONF_RETIRE_ENABLED, True):
            return {}

        # Live portfolio value for actual + optional baseline fallback
        actual = None
        try:
            # Reuse total-value math via a lightweight sum
            holdings = opts.get(CONF_HOLDINGS, {}) or {}
            total = 0.0
            any_price = False
            for sym, h in holdings.items():
                pd = self.coordinator.price_data(sym)
                price = pd.get("price")
                if price is None:
                    continue
                shares = float(h.get(CONF_SHARES, 0) or 0)
                ccy = pd.get("currency")
                total += float(price) * shares * float(self.coordinator.fx_rate(ccy))
                any_price = True
            if any_price:
                actual = round(total, 2)
        except Exception:  # noqa: BLE001
            actual = None

        baseline = float(opts.get(CONF_RETIRE_BASELINE) or 0)
        if baseline <= 0 and actual is not None:
            baseline = actual
        if baseline <= 0:
            baseline = 0.0

        start_year = int(opts.get(CONF_RETIRE_START_YEAR) or date_cls.today().year)
        horizon = int(opts.get(CONF_RETIRE_HORIZON) or DEFAULT_RETIRE_HORIZON)
        contrib = float(opts.get(CONF_RETIRE_CONTRIBUTION) or 0)
        selected = str(opts.get(CONF_RETIRE_SCENARIO) or DEFAULT_RETIRE_SCENARIO)

        return build_plan_payload(
            baseline=baseline,
            start_year=start_year,
            horizon_years=horizon,
            annual_contribution=contrib,
            actual=actual,
            selected=selected,
        )


class PortfolioRetirePlanSensor(_RetireMixin, CoordinatorEntity, SensorEntity):
    """Primary retirement plan sensor — attributes power ApexCharts series."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Retire Plan"
    _attr_icon = "mdi:chart-timeline-variant"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_retire_plan"
        self._attr_device_info = _device_info(entry)
        self.entity_id = "sensor.portfolio_retire_plan"

    @property
    def available(self) -> bool:
        return bool(self._entry.options.get(CONF_RETIRE_ENABLED, True))

    @property
    def native_value(self):
        payload = self._retire_payload()
        if not payload:
            return None
        # State = expected value on selected path for current plan year
        return payload.get("expected_now")

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.base_currency()

    @property
    def extra_state_attributes(self):
        payload = self._retire_payload()
        if not payload:
            return {}
        # Flatten scenario targets for easy templates / Apex
        attrs = {
            "baseline": payload.get("baseline"),
            "start_year": payload.get("start_year"),
            "end_year": payload.get("end_year"),
            "horizon_years": payload.get("horizon_years"),
            "annual_contribution": payload.get("annual_contribution"),
            "selected_scenario": payload.get("selected_scenario"),
            "plan_year": payload.get("plan_year"),
            "expected_now": payload.get("expected_now"),
            "actual": payload.get("actual"),
            "progress_pct": payload.get("progress_pct"),
            "delta": payload.get("delta"),
            "on_track": payload.get("on_track"),
            "disclaimer": payload.get("disclaimer"),
        }
        scenarios = payload.get("scenarios") or {}
        for key, sc in scenarios.items():
            attrs[f"{key}_rate_pct"] = sc.get("rate_pct")
            attrs[f"{key}_target"] = sc.get("target")
            attrs[f"{key}_points"] = sc.get("points")
            attrs[f"{key}_label"] = sc.get("label")
        return attrs


class PortfolioRetireProgressSensor(_RetireMixin, CoordinatorEntity, SensorEntity):
    """Actual vs expected for the selected scenario (%)."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Retire Progress"
    _attr_icon = "mdi:target"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_retire_progress"
        self._attr_device_info = _device_info(entry)
        self.entity_id = "sensor.portfolio_retire_progress"

    @property
    def available(self) -> bool:
        return bool(self._entry.options.get(CONF_RETIRE_ENABLED, True))

    @property
    def native_value(self):
        return (self._retire_payload() or {}).get("progress_pct")

    @property
    def extra_state_attributes(self):
        p = self._retire_payload() or {}
        return {
            "delta": p.get("delta"),
            "on_track": p.get("on_track"),
            "expected_now": p.get("expected_now"),
            "actual": p.get("actual"),
            "selected_scenario": p.get("selected_scenario"),
            "plan_year": p.get("plan_year"),
        }


class PortfolioRetireTargetSensor(_RetireMixin, CoordinatorEntity, SensorEntity):
    """Horizon target value for the selected scenario."""

    _attr_has_entity_name = False
    _attr_name = "Portfolio Retire Target"
    _attr_icon = "mdi:flag-checkered"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_retire_target"
        self._attr_device_info = _device_info(entry)
        self.entity_id = "sensor.portfolio_retire_target"

    @property
    def available(self) -> bool:
        return bool(self._entry.options.get(CONF_RETIRE_ENABLED, True))

    @property
    def native_value(self):
        p = self._retire_payload() or {}
        key = p.get("selected_scenario") or "moderate"
        sc = (p.get("scenarios") or {}).get(key) or {}
        return sc.get("target")

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.base_currency()

    @property
    def extra_state_attributes(self):
        p = self._retire_payload() or {}
        return {
            "selected_scenario": p.get("selected_scenario"),
            "horizon_years": p.get("horizon_years"),
            "end_year": p.get("end_year"),
            "baseline": p.get("baseline"),
        }

