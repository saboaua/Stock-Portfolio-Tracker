"""Config flow for Property Bridge."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CHECKIN_SCENE,
    CONF_CHECKIN_SCRIPT,
    CONF_CHECKOUT_SCENE,
    CONF_CHECKOUT_SCRIPT,
    CONF_CREATE_AREA,
    CONF_CREATE_LABEL,
    CONF_ENTITY_PREFIX,
    CONF_FRIENDLY_NAME_PREFIX,
    CONF_MAINTENANCE_ENABLED,
    CONF_MAINTENANCE_REQUIRE_CONSENT,
    CONF_MAINTENANCE_WINDOW_HOURS,
    CONF_PROPERTY_NAME,
    CONF_SECURE,
    CONF_VERIFY_SSL,
    DEFAULT_CREATE_AREA,
    DEFAULT_CREATE_LABEL,
    DEFAULT_MAINTENANCE_ENABLED,
    DEFAULT_MAINTENANCE_REQUIRE_CONSENT,
    DEFAULT_MAINTENANCE_WINDOW_HOURS,
    DEFAULT_PORT,
    DEFAULT_SECURE,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Common cloud / remote access domains that always use HTTPS on 443
_CLOUD_HOST_SUFFIXES = (
    ".ui.nabu.casa",
    ".nabu.casa",
    ".duckdns.org",
    ".homeassistant.io",
)


def _normalize_host_input(raw_host: str, secure: bool, port: int | None) -> tuple[str, bool, int]:
    """Normalize host / URL input into (hostname, secure, port).

    Accepts plain hostnames, IPs, Tailscale names, or full URLs such as:
      https://abcd1234.ui.nabu.casa
      http://192.168.1.50:8123
    """
    host = (raw_host or "").strip()

    # User pasted a full URL
    if host.startswith(("http://", "https://")):
        parsed = urlparse(host)
        host = parsed.hostname or host
        if parsed.scheme == "https":
            secure = True
        elif parsed.scheme == "http":
            secure = False
        if parsed.port:
            port = parsed.port

    # Strip any leftover path / trailing slash
    host = host.split("/")[0].split("?")[0].rstrip("/")

    # Auto-detect common cloud hosts → force HTTPS + 443
    host_lower = host.lower()
    if any(host_lower.endswith(suffix) for suffix in _CLOUD_HOST_SUFFIXES):
        secure = True
        if port is None or port in (8123, DEFAULT_PORT):
            port = 443

    # Sensible port defaults
    if port is None:
        port = 443 if secure else DEFAULT_PORT

    return host, secure, port


async def validate_connection(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect to the remote Home Assistant."""
    session = async_get_clientsession(hass)

    raw_host = data[CONF_HOST]
    secure = data.get(CONF_SECURE, DEFAULT_SECURE)
    port = data.get(CONF_PORT)
    verify_ssl = data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
    token = data[CONF_ACCESS_TOKEN]

    host, secure, port = _normalize_host_input(raw_host, secure, port)

    # Persist the cleaned values back so the entry stores them correctly
    data[CONF_HOST] = host
    data[CONF_SECURE] = secure
    data[CONF_PORT] = port

    scheme = "https" if secure else "http"
    url = f"{scheme}://{host}:{port}/api/"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    _LOGGER.debug(
        "Validating connection to %s (secure=%s, verify_ssl=%s)",
        url,
        secure,
        verify_ssl,
    )

    try:
        async with session.get(
            url,
            headers=headers,
            ssl=verify_ssl,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            # 200 = success, 401/403 = host reachable but token wrong/expired
            if resp.status in (200, 401, 403):
                if resp.status in (401, 403):
                    _LOGGER.warning(
                        "Remote HA at %s reachable but returned %s – check the long-lived access token",
                        url,
                        resp.status,
                    )
                return {"title": data[CONF_PROPERTY_NAME]}
            resp.raise_for_status()
    except aiohttp.ClientConnectorCertificateError as err:
        _LOGGER.debug("SSL certificate error connecting to %s: %s", url, err)
        raise InvalidSSL from err
    except aiohttp.ClientConnectorError as err:
        _LOGGER.debug("Connection error to %s: %s", url, err)
        raise CannotConnect from err
    except TimeoutError as err:
        _LOGGER.debug("Timeout connecting to %s: %s", url, err)
        raise CannotConnect from err
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.debug("Unexpected error validating %s: %s", url, err)
        raise CannotConnect from err

    return {"title": data[CONF_PROPERTY_NAME]}


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidSSL(Exception):
    """Error to indicate an SSL / certificate problem."""


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Property Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Clean / normalize before uniqueness check
            host, secure, port = _normalize_host_input(
                user_input[CONF_HOST],
                user_input.get(CONF_SECURE, DEFAULT_SECURE),
                user_input.get(CONF_PORT),
            )
            user_input[CONF_HOST] = host
            user_input[CONF_SECURE] = secure
            user_input[CONF_PORT] = port

            unique_id = f"{user_input[CONF_PROPERTY_NAME]}_{host}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_connection(self.hass, user_input)
            except InvalidSSL:
                errors["base"] = "invalid_ssl"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        # Do not pass config_entry into __init__ — on modern HA
        # OptionsFlow.config_entry is a read-only property set by core.
        return OptionsFlowHandler()


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PROPERTY_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Optional(CONF_SECURE, default=DEFAULT_SECURE): bool,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
        vol.Optional(CONF_ENTITY_PREFIX, default=""): str,
        vol.Optional(CONF_FRIENDLY_NAME_PREFIX, default=""): str,
        vol.Optional(CONF_CREATE_AREA, default=DEFAULT_CREATE_AREA): bool,
        vol.Optional(CONF_CREATE_LABEL, default=DEFAULT_CREATE_LABEL): bool,
    }
)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Property Bridge.

    Uses the modern HA pattern: do not assign self.config_entry
    (it is a read-only property provided by the OptionsFlow base class).
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.config_entry.data, **self.config_entry.options}

        options_schema = vol.Schema(
            {
                # Connection / naming
                vol.Optional(
                    CONF_ENTITY_PREFIX,
                    default=data.get(CONF_ENTITY_PREFIX, ""),
                ): str,
                vol.Optional(
                    CONF_FRIENDLY_NAME_PREFIX,
                    default=data.get(CONF_FRIENDLY_NAME_PREFIX, ""),
                ): str,
                vol.Optional(
                    CONF_SECURE,
                    default=data.get(CONF_SECURE, DEFAULT_SECURE),
                ): bool,
                vol.Optional(
                    CONF_VERIFY_SSL,
                    default=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                ): bool,
                # Area / label
                vol.Optional(
                    CONF_CREATE_AREA,
                    default=data.get(CONF_CREATE_AREA, DEFAULT_CREATE_AREA),
                ): bool,
                vol.Optional(
                    CONF_CREATE_LABEL,
                    default=data.get(CONF_CREATE_LABEL, DEFAULT_CREATE_LABEL),
                ): bool,
                # Rental presets
                vol.Optional(
                    CONF_CHECKIN_SCRIPT,
                    default=data.get(CONF_CHECKIN_SCRIPT, ""),
                ): str,
                vol.Optional(
                    CONF_CHECKOUT_SCRIPT,
                    default=data.get(CONF_CHECKOUT_SCRIPT, ""),
                ): str,
                vol.Optional(
                    CONF_CHECKIN_SCENE,
                    default=data.get(CONF_CHECKIN_SCENE, ""),
                ): str,
                vol.Optional(
                    CONF_CHECKOUT_SCENE,
                    default=data.get(CONF_CHECKOUT_SCENE, ""),
                ): str,
                # Maintenance / consent
                vol.Optional(
                    CONF_MAINTENANCE_ENABLED,
                    default=data.get(
                        CONF_MAINTENANCE_ENABLED, DEFAULT_MAINTENANCE_ENABLED
                    ),
                ): bool,
                vol.Optional(
                    CONF_MAINTENANCE_REQUIRE_CONSENT,
                    default=data.get(
                        CONF_MAINTENANCE_REQUIRE_CONSENT,
                        DEFAULT_MAINTENANCE_REQUIRE_CONSENT,
                    ),
                ): bool,
                vol.Optional(
                    CONF_MAINTENANCE_WINDOW_HOURS,
                    default=data.get(
                        CONF_MAINTENANCE_WINDOW_HOURS,
                        DEFAULT_MAINTENANCE_WINDOW_HOURS,
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
