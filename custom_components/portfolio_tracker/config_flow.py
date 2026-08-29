"""Config flow for Portfolio Tracker.

Each config entry is one portfolio. Adding a second portfolio is just
Add Integration again with a different name. Ongoing management (adding a
stock, buying/selling, editing cost basis, removing a stock, and update
schedule) happens through each entry's own "Configure" (options) flow.
"""
from __future__ import annotations

from datetime import date
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_HOLDINGS,
    CONF_SYMBOL,
    CONF_SHARES,
    CONF_INVESTED,
    CONF_ENTRY_DATE,
    CONF_UPDATE_INTERVAL,
    CONF_IDLE_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_IDLE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class PortfolioTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one portfolio. Run this again to add another portfolio."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            existing_names = {
                e.data.get(CONF_NAME, "").lower() for e in self._async_current_entries()
            }
            if not name:
                errors["base"] = "name_required"
            elif name.lower() in existing_names:
                errors["base"] = "name_exists"
            else:
                return self.async_create_entry(
                    title=f"Investing {name}",
                    data={CONF_NAME: name},
                    options={CONF_HOLDINGS: {}},
                )

        schema = vol.Schema({vol.Required(CONF_NAME, default="Main"): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PortfolioTrackerOptionsFlow(config_entry)


class PortfolioTrackerOptionsFlow(config_entries.OptionsFlow):
    """Add stocks, log buys/sells, edit or remove holdings, tune polling."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._pending_symbol: str | None = None

    @property
    def _holdings(self) -> dict:
        return dict(self.config_entry.options.get(CONF_HOLDINGS, {}))

    async def _save(self, holdings: dict):
        new_options = dict(self.config_entry.options)
        new_options[CONF_HOLDINGS] = holdings
        return self.async_create_entry(title="", data=new_options)

    # ---------------------------------------------------------------- menu

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add_holding",
                "buy_shares_symbol",
                "sell_shares_symbol",
                "edit_holding_symbol",
                "remove_holding",
                "update_settings",
            ],
        )

    # ---------------------------------------------------------------- add

    async def async_step_add_holding(self, user_input=None):
        errors = {}
        if user_input is not None:
            symbol = user_input[CONF_SYMBOL].strip().upper()
            holdings = self._holdings
            if symbol in holdings:
                errors["base"] = "already_exists"
            else:
                holdings[symbol] = {
                    CONF_SHARES: user_input[CONF_SHARES],
                    CONF_INVESTED: user_input[CONF_INVESTED],
                    CONF_ENTRY_DATE: user_input.get(CONF_ENTRY_DATE) or str(date.today()),
                }
                return await self._save(holdings)

        schema = vol.Schema(
            {
                vol.Required(CONF_SYMBOL): str,
                vol.Required(CONF_SHARES): vol.Coerce(float),
                vol.Required(CONF_INVESTED): vol.Coerce(float),
                vol.Optional(CONF_ENTRY_DATE, default=str(date.today())): str,
            }
        )
        return self.async_show_form(step_id="add_holding", data_schema=schema, errors=errors)

    # ---------------------------------------------------------------- buy

    async def async_step_buy_shares_symbol(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            self._pending_symbol = user_input[CONF_SYMBOL]
            return await self.async_step_buy_shares_amount()
        schema = vol.Schema({vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))})
        return self.async_show_form(step_id="buy_shares_symbol", data_schema=schema)

    async def async_step_buy_shares_amount(self, user_input=None):
        symbol = self._pending_symbol
        if user_input is not None:
            holdings = self._holdings
            h = holdings[symbol]
            h[CONF_SHARES] = round(float(h[CONF_SHARES]) + float(user_input["shares"]), 6)
            h[CONF_INVESTED] = round(float(h[CONF_INVESTED]) + float(user_input["cost"]), 2)
            holdings[symbol] = h
            return await self._save(holdings)
        schema = vol.Schema(
            {
                vol.Required("shares"): vol.Coerce(float),
                vol.Required("cost"): vol.Coerce(float),
            }
        )
        return self.async_show_form(
            step_id="buy_shares_amount",
            data_schema=schema,
            description_placeholders={"symbol": symbol},
        )

    # ---------------------------------------------------------------- sell

    async def async_step_sell_shares_symbol(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            self._pending_symbol = user_input[CONF_SYMBOL]
            return await self.async_step_sell_shares_amount()
        schema = vol.Schema({vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))})
        return self.async_show_form(step_id="sell_shares_symbol", data_schema=schema)

    async def async_step_sell_shares_amount(self, user_input=None):
        symbol = self._pending_symbol
        holdings = self._holdings
        h = holdings[symbol]
        errors = {}

        if user_input is not None:
            cur_shares = float(h[CONF_SHARES])
            sell_shares = float(user_input["shares"])
            if sell_shares <= 0 or sell_shares > cur_shares:
                errors["base"] = "invalid_shares"
            else:
                avg_cost = float(h[CONF_INVESTED]) / cur_shares if cur_shares else 0
                h[CONF_SHARES] = round(cur_shares - sell_shares, 6)
                h[CONF_INVESTED] = round(float(h[CONF_INVESTED]) - (avg_cost * sell_shares), 2)
                if h[CONF_SHARES] <= 0:
                    holdings.pop(symbol, None)
                else:
                    holdings[symbol] = h
                return await self._save(holdings)

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
                "symbol": symbol,
                "current_shares": str(h.get(CONF_SHARES)),
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
        schema = vol.Schema({vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))})
        return self.async_show_form(step_id="edit_holding_symbol", data_schema=schema)

    async def async_step_edit_holding_values(self, user_input=None):
        symbol = self._pending_symbol
        holdings = self._holdings
        h = holdings[symbol]

        if user_input is not None:
            h[CONF_SHARES] = float(user_input["shares"])
            h[CONF_INVESTED] = float(user_input["invested"])
            if user_input.get(CONF_ENTRY_DATE):
                h[CONF_ENTRY_DATE] = user_input[CONF_ENTRY_DATE]
            holdings[symbol] = h
            return await self._save(holdings)

        schema = vol.Schema(
            {
                vol.Required("shares", default=h.get(CONF_SHARES, 0)): vol.Coerce(float),
                vol.Required("invested", default=h.get(CONF_INVESTED, 0)): vol.Coerce(float),
                vol.Optional(
                    CONF_ENTRY_DATE, default=h.get(CONF_ENTRY_DATE, str(date.today()))
                ): str,
            }
        )
        return self.async_show_form(
            step_id="edit_holding_values",
            data_schema=schema,
            description_placeholders={"symbol": symbol},
        )

    # -------------------------------------------------------------- remove

    async def async_step_remove_holding(self, user_input=None):
        holdings = self._holdings
        if not holdings:
            return self.async_abort(reason="no_holdings")
        if user_input is not None:
            holdings.pop(user_input[CONF_SYMBOL], None)
            return await self._save(holdings)
        schema = vol.Schema({vol.Required(CONF_SYMBOL): vol.In(sorted(holdings.keys()))})
        return self.async_show_form(step_id="remove_holding", data_schema=schema)

    # ------------------------------------------------------ update settings

    async def async_step_update_settings(self, user_input=None):
        current_fast = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )
        current_idle = self.config_entry.options.get(
            CONF_IDLE_INTERVAL, DEFAULT_IDLE_INTERVAL_MINUTES
        )

        if user_input is not None:
            new_options = dict(self.config_entry.options)
            new_options[CONF_UPDATE_INTERVAL] = int(user_input[CONF_UPDATE_INTERVAL])
            new_options[CONF_IDLE_INTERVAL] = int(user_input[CONF_IDLE_INTERVAL])
            return self.async_create_entry(title="", data=new_options)

        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL, default=current_fast): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=120)
                ),
                vol.Required(CONF_IDLE_INTERVAL, default=current_idle): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=360)
                ),
            }
        )
        return self.async_show_form(step_id="update_settings", data_schema=schema)
