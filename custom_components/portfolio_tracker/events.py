"""Fire native Home Assistant events for milestones and volatility.

Events (usable in automations → Event trigger):
  - portfolio_tracker_milestone
  - portfolio_tracker_volatility_alert

Debounced via hass.data so the same milestone / symbol alert is not
re-fired every poll until the condition clears or a new level is hit.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_HOLDINGS,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_EVENTS_ENABLED,
    CONF_MILESTONE_STEP,
    CONF_VOLATILITY_PCT,
    DEFAULT_EVENTS_ENABLED,
    DEFAULT_MILESTONE_STEP,
    DEFAULT_VOLATILITY_PCT,
    EVENT_MILESTONE,
    EVENT_VOLATILITY,
)

_LOGGER = logging.getLogger(__name__)


def _state_bucket(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    hass.data.setdefault(DOMAIN, {})
    data = hass.data[DOMAIN].setdefault(entry_id, {})
    return data.setdefault(
        "event_state",
        {
            "last_milestone_level": None,  # int level index (value // step)
            "vol_portfolio_active": False,
            "vol_symbols_active": set(),
        },
    )


def _portfolio_totals(coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> tuple[float, float, float]:
    """Return (total_value, total_invested, day_change) in base currency."""
    live = coordinator.hass.config_entries.async_get_entry(entry.entry_id) or entry
    holdings = (live.options.get(CONF_HOLDINGS, {}) or {})
    total_value = 0.0
    total_invested = 0.0
    day_change = 0.0
    price_fn = getattr(coordinator, "price_data", None)
    fx_fn = getattr(coordinator, "fx_rate", lambda c: 1.0)

    for symbol, holding in holdings.items():
        try:
            invested = float(holding.get(CONF_INVESTED, 0) or 0)
        except (TypeError, ValueError):
            invested = 0.0
        total_invested += invested
        if not price_fn:
            continue
        pd = price_fn(symbol) or {}
        price = pd.get("price")
        shares = float(holding.get(CONF_SHARES, 0) or 0)
        if price is None:
            continue
        rate = float(fx_fn(pd.get("currency")) or 1.0)
        total_value += float(price) * shares * rate
        ch = pd.get("day_change")
        if ch is not None:
            day_change += float(ch) * shares * rate

    return total_value, total_invested, day_change


@callback
def async_check_events(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: DataUpdateCoordinator,
) -> None:
    """Run after a successful coordinator refresh."""
    live = hass.config_entries.async_get_entry(entry.entry_id) or entry
    opts = live.options or {}
    if not opts.get(CONF_EVENTS_ENABLED, DEFAULT_EVENTS_ENABLED):
        return

    try:
        step = float(opts.get(CONF_MILESTONE_STEP, DEFAULT_MILESTONE_STEP) or DEFAULT_MILESTONE_STEP)
    except (TypeError, ValueError):
        step = DEFAULT_MILESTONE_STEP
    if step <= 0:
        step = DEFAULT_MILESTONE_STEP

    try:
        vol_pct = float(opts.get(CONF_VOLATILITY_PCT, DEFAULT_VOLATILITY_PCT) or DEFAULT_VOLATILITY_PCT)
    except (TypeError, ValueError):
        vol_pct = DEFAULT_VOLATILITY_PCT
    if vol_pct <= 0:
        vol_pct = DEFAULT_VOLATILITY_PCT

    total_value, total_invested, day_change = _portfolio_totals(coordinator, entry)
    state = _state_bucket(hass, entry.entry_id)
    base = getattr(coordinator, "base_currency", lambda: "USD")()

    # ----- Milestone: cross N * step boundaries (up or down) -----
    level = int(total_value // step) if total_value > 0 else 0
    last = state.get("last_milestone_level")
    if last is None:
        state["last_milestone_level"] = level
    elif level != last:
        direction = "up" if level > last else "down"
        threshold = level * step if direction == "up" else (last) * step
        hass.bus.async_fire(
            EVENT_MILESTONE,
            {
                "entry_id": entry.entry_id,
                "direction": direction,
                "level": level,
                "previous_level": last,
                "threshold": round(threshold, 2),
                "step": step,
                "total_value": round(total_value, 2),
                "total_invested": round(total_invested, 2),
                "currency": base,
            },
        )
        _LOGGER.info(
            "Fired %s direction=%s level=%s value=%s",
            EVENT_MILESTONE,
            direction,
            level,
            total_value,
        )
        state["last_milestone_level"] = level

    # ----- Volatility: portfolio day % move -----
    day_pct = None
    if total_value - day_change != 0:
        try:
            # approximate previous close portfolio value
            prev = total_value - day_change
            if prev:
                day_pct = (day_change / prev) * 100.0
        except (TypeError, ZeroDivisionError):
            day_pct = None

    vol_active = state.get("vol_portfolio_active", False)
    if day_pct is not None and abs(day_pct) >= vol_pct:
        if not vol_active:
            hass.bus.async_fire(
                EVENT_VOLATILITY,
                {
                    "entry_id": entry.entry_id,
                    "scope": "portfolio",
                    "symbol": None,
                    "day_change": round(day_change, 2),
                    "day_change_pct": round(day_pct, 2),
                    "threshold_pct": vol_pct,
                    "total_value": round(total_value, 2),
                    "currency": base,
                },
            )
            _LOGGER.info(
                "Fired %s portfolio day_pct=%.2f", EVENT_VOLATILITY, day_pct
            )
            state["vol_portfolio_active"] = True
    else:
        state["vol_portfolio_active"] = False

    # ----- Volatility: per-symbol day % -----
    price_fn = getattr(coordinator, "price_data", None)
    if not price_fn:
        return
    holdings = (live.options.get(CONF_HOLDINGS, {}) or {})
    active_syms: set[str] = set(state.get("vol_symbols_active") or set())
    still_hot: set[str] = set()

    for symbol in holdings:
        pd = price_fn(symbol) or {}
        pct = pd.get("day_change_pct")
        if pct is None:
            continue
        try:
            pct_f = float(pct)
        except (TypeError, ValueError):
            continue
        if abs(pct_f) < vol_pct:
            continue
        still_hot.add(symbol)
        if symbol in active_syms:
            continue  # already alerted this move
        hass.bus.async_fire(
            EVENT_VOLATILITY,
            {
                "entry_id": entry.entry_id,
                "scope": "symbol",
                "symbol": symbol,
                "day_change": pd.get("day_change"),
                "day_change_pct": round(pct_f, 2),
                "threshold_pct": vol_pct,
                "price": pd.get("price"),
                "currency": pd.get("currency") or base,
                "name": pd.get("short_name") or symbol,
            },
        )
        _LOGGER.info(
            "Fired %s symbol=%s day_pct=%.2f", EVENT_VOLATILITY, symbol, pct_f
        )

    state["vol_symbols_active"] = still_hot


def async_setup_event_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: DataUpdateCoordinator,
) -> None:
    """Attach a coordinator listener that evaluates events after each update."""

    @callback
    def _on_update() -> None:
        if coordinator.last_update_success:
            async_check_events(hass, entry, coordinator)

    entry.async_on_unload(coordinator.async_add_listener(_on_update))
