"""Config flow for Portfolio Tracker.

Initial setup creates an empty portfolio. Day-to-day management is done
through the Configure (options) flow.
"""
from __future__ import annotations

from datetime import date
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_HOLDINGS,
    CONF_SYMBOL,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    CONF_SCAN_INTERVAL,
    CONF_IDLE_SCAN_INTERVAL,
    CONF_REALIZED_GAIN,
    CONF_TRADE_LOG,
    CONF_BASE_CURRENCY,
    CONF_SCHEDULE_PRESET,
    CONF_SNAPSHOT_ENABLED,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    IDLE_SCAN_INTERVAL_MINUTES,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_SCHEDULE_PRESET,
    SCHEDULE_PRESETS,
    SCHEDULE_PRESET_LABELS,
    MAX_TRADE_LOG,
    SUPPORTED_CURRENCIES,
    CONF_RETIRE_ENABLED,
    CONF_RETIRE_HORIZON,
    CONF_RETIRE_BASELINE,
    CONF_RETIRE_START_YEAR,
    CONF_RETIRE_CONTRIBUTION,
    CONF_RETIRE_SCENARIO,
    DEFAULT_RETIRE_HORIZON,
    DEFAULT_RETIRE_SCENARIO,
)

_LOGGER = logging.getLogger(__name__)

# Plain dicts only (value + label). Do NOT pass icon= into SelectOptionDict —
# that raises TypeError on many HA versions and prevents the flow from loading.
MENU_OPTION_LIST = [
    {"value": "add_holding", "label": "➕  Add a new stock"},
    {"value": "buy_shares_symbol", "label": "🛒  Buy more shares"},
    {"value": "sell_shares_symbol", "label": "💰  Sell shares"},
    {"value": "edit_holding_symbol", "label": "✏️  Edit shares / cost basis"},
    {"value": "remove_holding", "label": "🗑️  Remove a stock"},
    {"value": "settings", "label": "⚙️  Settings (currency & intervals)"},
    {"value": "retire_plan", "label": "🎯  Retirement forecast plan"},
]


class PortfolioTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One-time setup. Only a single instance is supported."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Portfolio Tracker",
                data={},
                options={
                    CONF_HOLDINGS: {},
                    CONF_BASE_CURRENCY: DEFAULT_BASE_CURRENCY,
                    CONF_REALIZED_GAIN: 0.0,
                    CONF_TRADE_LOG: [],
                },
            )

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PortfolioTrackerOptionsFlowHandler()


class PortfolioTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Add / buy / sell / edit / remove holdings and settings."""

    def __init__(self) -> None:
        self._pending_symbol: str | None = None

    @property
    def _holdings(self) -> dict:
        return dict(self.config_entry.options.get(CONF_HOLDINGS, {}))

    async def _save_holdings(self, holdings: dict):
        """Persist holdings and normalize invested/shares so totals stay accurate."""
        normalized: dict = {}
        for symbol, raw in (holdings or {}).items():
            if not symbol or not isinstance(raw, dict):
                continue
            sym = str(symbol).strip().upper()
            try:
                shares = float(raw.get(CONF_SHARES, 0) or 0)
            except (TypeError, ValueError):
                shares = 0.0
            try:
                invested = float(raw.get(CONF_INVESTED, 0) or 0)
            except (TypeError, ValueError):
                invested = 0.0
            # Drop empty positions so total invested does not keep ghost cost basis
            if shares <= 0 and invested <= 0:
                continue
            normalized[sym] = {
                CONF_SHARES: round(shares, 6),
                CONF_INVESTED: round(invested, 2),
                CONF_ENTRY_DATE: raw.get(CONF_ENTRY_DATE) or None,
            }
        new_options = dict(self.config_entry.options)
        new_options[CONF_HOLDINGS] = normalized
        return self.async_create_entry(title="", data=new_options)

    # ---------------------------------------------------------------- menu

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input["action"]
            handler = getattr(self, f"async_step_{action}", None)
            if handler is None:
                return self.async_abort(reason="no_holdings")
            return await handler()

        schema = vol.Schema(
            {
                vol.Required("action"): SelectSelector(
                    SelectSelectorConfig(
                        options=MENU_OPTION_LIST,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    # ---------------------------------------------------------------- add

    async def async_step_add_holding(self, user_input=None):
        """Add a new holding, or replace an existing one (re-add after remove).

        Cost basis is stored as **total invested** (what you paid for all shares).
        Prefer entering average cost per share — total is computed as shares × cost.
        """
        errors = {}
        if user_input is not None:
            symbol = str(user_input[CONF_SYMBOL]).strip().upper()
            holdings = self._holdings
            # Case-insensitive de-dupe (XLK vs xlk)
            existing_key = None
            for k in list(holdings.keys()):
                if str(k).upper() == symbol:
                    existing_key = k
                    break

            if not symbol:
                errors["base"] = "invalid_symbol"
            else:
                try:
                    shares = float(user_input[CONF_SHARES])
                except (TypeError, ValueError):
                    shares = 0.0
                if shares <= 0:
                    errors["base"] = "invalid_shares"
                else:
                    cost_per = user_input.get("cost_per_share")
                    total_in = user_input.get(CONF_INVESTED)
                    invested = None
                    try:
                        if cost_per is not None and float(cost_per) > 0:
                            invested = round(shares * float(cost_per), 2)
                        elif total_in is not None and float(total_in) > 0:
                            invested = round(float(total_in), 2)
                    except (TypeError, ValueError):
                        invested = None

                    if invested is None or invested <= 0:
                        errors["base"] = "invalid_invested"
                    else:
                        # Replace prior key (any casing) so re-add after delete
                        # or correcting basis never leaves a ghost entry
                        if existing_key is not None:
                            holdings.pop(existing_key, None)
                        holdings[symbol] = {
                            CONF_SHARES: round(shares, 6),
                            CONF_INVESTED: invested,
                            CONF_ENTRY_DATE: user_input.get(CONF_ENTRY_DATE)
                            or str(date.today()),
                        }
                        return await self._save_holdings(holdings)

        schema = vol.Schema(
            {
                vol.Required(CONF_SYMBOL): str,
                vol.Required(CONF_SHARES): vol.Coerce(float),
                vol.Optional("cost_per_share"): vol.Coerce(float),
                vol.Optional(CONF_INVESTED): vol.Coerce(float),
                vol.Optional(CONF_ENTRY_DATE, default=str(date.today())): str,
            }
        )
        return self.async_show_form(
            step_id="add_holding",
            data_schema=schema,
            errors=errors,
        )


    async def async_step_buy_shares_symbol(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            self._pending_symbol = user_input[CONF_SYMBOL]
            return await self.async_step_buy_shares_amount()
        schema = vol.Schema(
            {vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))}
        )
        return self.async_show_form(step_id="buy_shares_symbol", data_schema=schema)

    async def async_step_buy_shares_amount(self, user_input=None):
        symbol = self._pending_symbol
        if user_input is not None:
            holdings = self._holdings
            h = dict(holdings[symbol])
            h[CONF_SHARES] = round(
                float(h[CONF_SHARES]) + float(user_input["shares"]), 6
            )
            h[CONF_INVESTED] = round(
                float(h[CONF_INVESTED]) + float(user_input["cost"]), 2
            )
            holdings[symbol] = h
            return await self._save_holdings(holdings)

        schema = vol.Schema(
            {
                vol.Required("shares"): vol.Coerce(float),
                vol.Required("cost"): vol.Coerce(float),
            }
        )
        return self.async_show_form(
            step_id="buy_shares_amount",
            data_schema=schema,
            description_placeholders={"symbol": symbol or ""},
        )

    # ---------------------------------------------------------------- sell

    async def async_step_sell_shares_symbol(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            self._pending_symbol = user_input[CONF_SYMBOL]
            return await self.async_step_sell_shares_amount()
        schema = vol.Schema(
            {vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))}
        )
        return self.async_show_form(step_id="sell_shares_symbol", data_schema=schema)

    async def async_step_sell_shares_amount(self, user_input=None):
        symbol = self._pending_symbol
        holdings = self._holdings
        h = holdings.get(symbol, {})
        errors = {}

        if user_input is not None:
            cur_shares = float(h.get(CONF_SHARES, 0))
            sell_shares = float(user_input["shares"])
            if sell_shares <= 0 or sell_shares > cur_shares:
                errors["base"] = "invalid_shares"
            else:
                avg_cost = (
                    float(h.get(CONF_INVESTED, 0)) / cur_shares if cur_shares else 0
                )
                cost_basis_sold = avg_cost * sell_shares
                proceeds = float(user_input.get("proceeds") or 0)
                realized = (proceeds - cost_basis_sold) if proceeds else 0.0
                new_h = dict(h)
                new_h[CONF_SHARES] = round(cur_shares - sell_shares, 6)
                new_h[CONF_INVESTED] = round(
                    float(h.get(CONF_INVESTED, 0)) - cost_basis_sold, 2
                )
                if new_h[CONF_SHARES] <= 0:
                    holdings.pop(symbol, None)
                else:
                    holdings[symbol] = new_h

                new_options = dict(self.config_entry.options)
                new_options[CONF_HOLDINGS] = holdings
                if proceeds:
                    new_options[CONF_REALIZED_GAIN] = round(
                        float(new_options.get(CONF_REALIZED_GAIN, 0)) + realized, 2
                    )
                log = list(new_options.get(CONF_TRADE_LOG, []))
                log.insert(
                    0,
                    {
                        "type": "sell",
                        "symbol": symbol,
                        "shares": sell_shares,
                        "amount": proceeds,
                        "cost_basis": round(cost_basis_sold, 2),
                        "realized": round(realized, 2),
                    },
                )
                new_options[CONF_TRADE_LOG] = log[:MAX_TRADE_LOG]
                return self.async_create_entry(title="", data=new_options)

        schema = vol.Schema(
            {
                vol.Required("shares"): vol.Coerce(float),
                vol.Optional("proceeds", default=0): vol.Coerce(float),
            }
        )
        return self.async_show_form(
            step_id="sell_shares_amount",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "symbol": symbol or "",
                "current_shares": str(h.get(CONF_SHARES, 0)),
            },
        )

    # ---------------------------------------------------------------- edit

    async def async_step_edit_holding_symbol(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            self._pending_symbol = user_input[CONF_SYMBOL]
            return await self.async_step_edit_holding_values()
        schema = vol.Schema(
            {vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))}
        )
        return self.async_show_form(step_id="edit_holding_symbol", data_schema=schema)

    async def async_step_edit_holding_values(self, user_input=None):
        symbol = self._pending_symbol
        holdings = self._holdings
        h = holdings.get(symbol, {})

        if user_input is not None:
            new_h = dict(h)
            new_h[CONF_SHARES] = float(user_input["shares"])
            new_h[CONF_INVESTED] = float(user_input["invested"])
            if user_input.get(CONF_ENTRY_DATE):
                new_h[CONF_ENTRY_DATE] = user_input[CONF_ENTRY_DATE]
            holdings[symbol] = new_h
            return await self._save_holdings(holdings)

        schema = vol.Schema(
            {
                vol.Required(
                    "shares", default=float(h.get(CONF_SHARES, 0) or 0)
                ): vol.Coerce(float),
                vol.Required(
                    "invested", default=float(h.get(CONF_INVESTED, 0) or 0)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_ENTRY_DATE,
                    default=h.get(CONF_ENTRY_DATE, str(date.today())),
                ): str,
            }
        )
        return self.async_show_form(
            step_id="edit_holding_values",
            data_schema=schema,
            description_placeholders={"symbol": symbol or ""},
        )

    # -------------------------------------------------------------- remove

    async def async_step_remove_holding(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            holdings.pop(user_input[CONF_SYMBOL], None)
            return await self._save_holdings(holdings)
        schema = vol.Schema(
            {vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))}
        )
        return self.async_show_form(step_id="remove_holding", data_schema=schema)

    # -------------------------------------------------------------- settings

    async def async_step_settings(self, user_input=None):
        if user_input is not None:
            new_options = dict(self.config_entry.options)
            preset = str(user_input.get(CONF_SCHEDULE_PRESET, DEFAULT_SCHEDULE_PRESET))
            new_options[CONF_SCHEDULE_PRESET] = preset
            new_options[CONF_BASE_CURRENCY] = str(user_input[CONF_BASE_CURRENCY])
            new_options[CONF_SNAPSHOT_ENABLED] = bool(
                user_input.get(CONF_SNAPSHOT_ENABLED, False)
            )
            new_options[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
            new_options[CONF_IDLE_SCAN_INTERVAL] = int(
                user_input[CONF_IDLE_SCAN_INTERVAL]
            )
            if preset in SCHEDULE_PRESETS and preset != "custom":
                open_m, idle_m = SCHEDULE_PRESETS[preset]
                new_options[CONF_SCAN_INTERVAL] = open_m
                new_options[CONF_IDLE_SCAN_INTERVAL] = idle_m
            return self.async_create_entry(title="", data=new_options)

        opts = self.config_entry.options
        preset_options = [
            {"value": key, "label": SCHEDULE_PRESET_LABELS[key]}
            for key in ("active", "balanced", "conservative", "custom")
        ]
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_BASE_CURRENCY,
                    default=opts.get(CONF_BASE_CURRENCY, DEFAULT_BASE_CURRENCY),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SUPPORTED_CURRENCIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_SCHEDULE_PRESET,
                    default=opts.get(CONF_SCHEDULE_PRESET, DEFAULT_SCHEDULE_PRESET),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=preset_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=int(
                        opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
                vol.Required(
                    CONF_IDLE_SCAN_INTERVAL,
                    default=int(
                        opts.get(CONF_IDLE_SCAN_INTERVAL, IDLE_SCAN_INTERVAL_MINUTES)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=360)),
                vol.Optional(
                    CONF_SNAPSHOT_ENABLED,
                    default=bool(opts.get(CONF_SNAPSHOT_ENABLED, False)),
                ): bool,
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)


    # -------------------------------------------------------------- retirement

    async def async_step_retire_plan(self, user_input=None):
        """Configure multi-year forecast scenarios for ApexCharts / sensors."""
        from datetime import date as date_cls

        opts = self.config_entry.options
        if user_input is not None:
            new_options = dict(opts)
            new_options[CONF_RETIRE_ENABLED] = bool(user_input.get(CONF_RETIRE_ENABLED, True))
            new_options[CONF_RETIRE_HORIZON] = int(user_input[CONF_RETIRE_HORIZON])
            baseline = user_input.get(CONF_RETIRE_BASELINE)
            if baseline is None or baseline == "" or float(baseline) <= 0:
                # Leave existing or 0 — sensor will fall back to live total
                new_options[CONF_RETIRE_BASELINE] = float(
                    opts.get(CONF_RETIRE_BASELINE) or 0
                )
            else:
                new_options[CONF_RETIRE_BASELINE] = float(baseline)
            new_options[CONF_RETIRE_START_YEAR] = int(
                user_input.get(CONF_RETIRE_START_YEAR) or date_cls.today().year
            )
            new_options[CONF_RETIRE_CONTRIBUTION] = float(
                user_input.get(CONF_RETIRE_CONTRIBUTION) or 0
            )
            new_options[CONF_RETIRE_SCENARIO] = str(
                user_input.get(CONF_RETIRE_SCENARIO) or DEFAULT_RETIRE_SCENARIO
            )
            return self.async_create_entry(title="", data=new_options)

        scenario_options = [
            {"value": "conservative", "label": "Conservative 8%"},
            {"value": "moderate", "label": "Moderate 10%"},
            {"value": "nasdaq", "label": "Nasdaq-like 15%"},
            {"value": "aggressive", "label": "Aggressive 20%"},
            {"value": "upside", "label": "Upside 22%"},
        ]
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RETIRE_ENABLED,
                    default=bool(opts.get(CONF_RETIRE_ENABLED, True)),
                ): bool,
                vol.Required(
                    CONF_RETIRE_HORIZON,
                    default=int(opts.get(CONF_RETIRE_HORIZON, DEFAULT_RETIRE_HORIZON)),
                ): vol.All(vol.Coerce(int), vol.Range(min=4, max=10)),
                vol.Optional(
                    CONF_RETIRE_BASELINE,
                    default=float(opts.get(CONF_RETIRE_BASELINE) or 0),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_RETIRE_START_YEAR,
                    default=int(
                        opts.get(CONF_RETIRE_START_YEAR) or date_cls.today().year
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=2000, max=2100)),
                vol.Optional(
                    CONF_RETIRE_CONTRIBUTION,
                    default=float(opts.get(CONF_RETIRE_CONTRIBUTION) or 0),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_RETIRE_SCENARIO,
                    default=opts.get(CONF_RETIRE_SCENARIO, DEFAULT_RETIRE_SCENARIO),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=scenario_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="retire_plan", data_schema=schema)


