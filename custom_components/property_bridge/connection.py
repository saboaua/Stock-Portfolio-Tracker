"""Connection management for a remote Home Assistant instance.

Implements real WebSocket entity mirroring:
  - Authenticate with long-lived access token
  - Fetch all states (get_states)
  - Subscribe to state_changed events
  - Mirror entities locally with optional prefix
  - Clean up on disconnect / reconnect with backoff
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CALL_SERVICE, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_AREA_ID,
    ATTR_CONNECTED,
    ATTR_ENTITY_COUNT,
    ATTR_LABEL_ID,
    ATTR_LAST_SEEN,
    ATTR_MAINTENANCE_ALLOWED,
    ATTR_MAINTENANCE_UNTIL,
    ATTR_REMOTE_VERSION,
    CONF_ACCESS_TOKEN,
    CONF_AREA_ID,
    CONF_CREATE_AREA,
    CONF_CREATE_LABEL,
    CONF_ENTITY_PREFIX,
    CONF_EXCLUDE_DOMAINS,
    CONF_FRIENDLY_NAME_PREFIX,
    CONF_HOST,
    CONF_INCLUDE_DOMAINS,
    CONF_LABEL_ID,
    CONF_MAINTENANCE_ALLOWED_UNTIL,
    CONF_PORT,
    CONF_PROPERTY_NAME,
    CONF_SECURE,
    CONF_VERIFY_SSL,
    DEFAULT_CREATE_AREA,
    DEFAULT_CREATE_LABEL,
    DEFAULT_EXCLUDE_DOMAINS,
    DEFAULT_PORT,
    DOMAIN,
    PROXY_SERVICE_DOMAINS,
    RECONNECT_MAX_DELAY,
    RECONNECT_MIN_DELAY,
    SIGNAL_CONNECTION_UPDATE,
)
from .helpers import async_ensure_area, async_ensure_label

_LOGGER = logging.getLogger(__name__)


class BridgeConnection:
    """Manages a WebSocket connection to a single remote Home Assistant instance.

    Also owns property-level metadata: area, label, maintenance window state.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the connection object."""
        self.hass = hass
        self.entry = entry
        self._connected = False
        self._last_seen: datetime | None = None
        self._entity_count = 0
        self._remote_version: str | None = None
        self._ws_task: asyncio.Task | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._msg_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self._mirrored_entities: set[str] = set()  # local entity_ids we created
        self._local_to_remote: dict[str, str] = {}  # local eid → remote eid
        self._automation_configs: dict[str, dict[str, Any]] = {}  # remote auto id → config
        self._stop = False
        self._last_error: str | None = None
        self._proxying: set[str] = set()  # guard against service-call recursion
        self._service_unsub = None

        self.property_name: str = entry.data.get(
            CONF_PROPERTY_NAME, entry.title or "Unknown Property"
        )
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.secure: bool = entry.data.get(CONF_SECURE, True)
        self.verify_ssl: bool = entry.data.get(CONF_VERIFY_SSL, True)
        self.access_token: str = entry.data[CONF_ACCESS_TOKEN]
        self.entity_prefix: str = entry.data.get(CONF_ENTITY_PREFIX, "") or ""
        self.friendly_name_prefix: str = (
            entry.data.get(CONF_FRIENDLY_NAME_PREFIX, "") or ""
        )

        # Fix cloud hosts that were saved with port 8123 (Nabu Casa / DuckDNS need 443)
        self.host, self.secure, self.port = self._normalize_endpoint(
            self.host, self.secure, self.port
        )

        # Domain filters (options override data)
        options = {**entry.data, **entry.options}
        include = options.get(CONF_INCLUDE_DOMAINS)
        exclude = options.get(CONF_EXCLUDE_DOMAINS)
        self._include_domains: set[str] | None = (
            set(include) if include else None
        )
        self._exclude_domains: set[str] = (
            set(exclude) if exclude else set(DEFAULT_EXCLUDE_DOMAINS)
        )

        # Area / label
        self.area_id: str | None = entry.options.get(CONF_AREA_ID) or entry.data.get(
            CONF_AREA_ID
        )
        self.label_id: str | None = entry.options.get(CONF_LABEL_ID) or entry.data.get(
            CONF_LABEL_ID
        )

        # Maintenance / consent state
        self.maintenance_requested: bool = False
        self.consent_granted: bool = False
        self.maintenance_allowed_until: datetime | None = None
        until_raw = entry.options.get(CONF_MAINTENANCE_ALLOWED_UNTIL)
        if until_raw:
            try:
                self.maintenance_allowed_until = dt_util.parse_datetime(until_raw)
                if self.maintenance_allowed_until and (
                    self.maintenance_allowed_until > dt_util.utcnow()
                ):
                    self.consent_granted = True
                    self.maintenance_requested = True
            except (TypeError, ValueError):
                self.maintenance_allowed_until = None

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """Return True if currently connected to the remote instance."""
        return self._connected

    @property
    def last_seen(self) -> datetime | None:
        """Return the last successful communication timestamp."""
        return self._last_seen

    @property
    def entity_count(self) -> int:
        """Return the number of mirrored entities."""
        return self._entity_count

    @property
    def remote_version(self) -> str | None:
        """Return the Home Assistant version reported by the remote instance."""
        return self._remote_version

    @property
    def maintenance_allowed(self) -> bool:
        """Return True if a valid maintenance window is currently open."""
        if not self.maintenance_allowed_until:
            return False
        return self.maintenance_allowed_until > dt_util.utcnow()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_connect(self) -> None:
        """Establish the connection and ensure area/label exist."""
        _LOGGER.debug(
            "Connecting to remote HA at %s:%s (property: %s)",
            self.host,
            self.port,
            self.property_name,
        )

        # --- Automatic area / label assignment ---
        options = {**self.entry.data, **self.entry.options}
        create_area = options.get(CONF_CREATE_AREA, DEFAULT_CREATE_AREA)
        create_label = options.get(CONF_CREATE_LABEL, DEFAULT_CREATE_LABEL)

        if create_area:
            self.area_id = await async_ensure_area(
                self.hass, self.property_name, self.area_id
            )
        if create_label:
            self.label_id = await async_ensure_label(
                self.hass, self.property_name, self.label_id
            )

        # Defer options write so it does not reload platforms mid-setup
        if self.area_id or self.label_id:
            new_options = dict(self.entry.options)
            changed = False
            if self.area_id and new_options.get(CONF_AREA_ID) != self.area_id:
                new_options[CONF_AREA_ID] = self.area_id
                changed = True
            if self.label_id and new_options.get(CONF_LABEL_ID) != self.label_id:
                new_options[CONF_LABEL_ID] = self.label_id
                changed = True
            if changed:

                async def _persist_options() -> None:
                    await asyncio.sleep(2)
                    try:
                        self.hass.config_entries.async_update_entry(
                            self.entry, options=new_options
                        )
                    except Exception:  # pylint: disable=broad-except
                        _LOGGER.debug(
                            "Could not persist area/label options for '%s'",
                            self.property_name,
                        )

                self.hass.async_create_task(_persist_options())

        self._stop = False
        self._ws_task = self.hass.async_create_background_task(
            self._connection_loop(),
            name=f"property_bridge_{self.property_name}",
        )

        # Forward local service calls on mirrored entities to the remote instance
        if self._service_unsub is None:
            self._service_unsub = self.hass.bus.async_listen(
                EVENT_CALL_SERVICE, self._on_local_service_call
            )
            self.entry.async_on_unload(self._service_unsub)

        # Stop cleanly when HA shuts down
        self.entry.async_on_unload(
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, self._on_hass_stop
            )
        )

        _LOGGER.info(
            "Property Bridge starting connection to '%s' (%s:%s) area=%s label=%s",
            self.property_name,
            self.host,
            self.port,
            self.area_id,
            self.label_id,
        )

    async def async_disconnect(self) -> None:
        """Cleanly disconnect and remove all mirrored entities."""
        _LOGGER.debug("Disconnecting from '%s'", self.property_name)
        self._stop = True

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        await self._clear_mirrored_entities()
        self._connected = False
        self._entity_count = 0
        self._notify_update()

        _LOGGER.info("Property Bridge disconnected from '%s'", self.property_name)

    async def _on_hass_stop(self, _event) -> None:
        await self.async_disconnect()

    # ------------------------------------------------------------------
    # WebSocket core
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_endpoint(
        host: str, secure: bool, port: int
    ) -> tuple[str, bool, int]:
        """Normalize host/port for cloud remote-access providers."""
        host = (host or "").strip()
        # Strip scheme if present
        if host.startswith(("http://", "https://")):
            from urllib.parse import urlparse

            parsed = urlparse(host)
            host = parsed.hostname or host
            if parsed.scheme == "https":
                secure = True
            elif parsed.scheme == "http":
                secure = False
            if parsed.port:
                port = parsed.port
        host = host.split("/")[0].split("?")[0].rstrip("/")

        # Nabu Casa always terminates TLS on 443. DuckDNS is only adjusted
        # when the user left the default local port (8123) with Secure ON.
        host_l = host.lower()
        if host_l.endswith(".ui.nabu.casa") or host_l.endswith(".nabu.casa"):
            secure = True
            port = 443
        elif host_l.endswith(".duckdns.org") and secure and port in (
            8123,
            DEFAULT_PORT,
            None,
        ):
            port = 443
        return host, secure, int(port or (443 if secure else DEFAULT_PORT))

    def _ws_url(self) -> str:
        """Build WebSocket URL (omit standard ports for better proxy compatibility)."""
        scheme = "wss" if self.secure else "ws"
        if self.secure and self.port == 443:
            return f"{scheme}://{self.host}/api/websocket"
        if not self.secure and self.port == 80:
            return f"{scheme}://{self.host}/api/websocket"
        return f"{scheme}://{self.host}:{self.port}/api/websocket"

    async def _connection_loop(self) -> None:
        """Background task: connect, mirror, reconnect on failure."""
        delay = RECONNECT_MIN_DELAY
        try:
            while not self._stop:
                try:
                    await self._run_session()
                    delay = RECONNECT_MIN_DELAY  # reset on clean exit
                except asyncio.CancelledError:
                    raise
                except Exception as err:  # pylint: disable=broad-except
                    self._last_error = f"{type(err).__name__}: {err}"
                    _LOGGER.warning(
                        "WebSocket session for '%s' ended: %s – reconnecting in %ss",
                        self.property_name,
                        self._last_error,
                        delay,
                        exc_info=True,
                    )
                    self._connected = False
                    self._notify_update()
                    await self._clear_mirrored_entities()

                if self._stop:
                    break

                await asyncio.sleep(delay)
                delay = min(delay * 2, RECONNECT_MAX_DELAY)
        except asyncio.CancelledError:
            _LOGGER.debug("Connection loop for '%s' cancelled", self.property_name)
            raise
        finally:
            await self._clear_mirrored_entities()
            self._connected = False
            self._notify_update()

    async def _run_session(self) -> None:
        """Single WebSocket session: auth → get_states → subscribe → pump."""
        # NOTE: Do NOT call async_update_entry here — it triggers a reload loop.
        # Host/port normalization is applied in-memory only.

        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        url = self._ws_url()

        # Pre-flight REST check so failures are easy to diagnose
        rest_url = url.replace("wss://", "https://").replace("ws://", "http://")
        rest_url = rest_url.replace("/api/websocket", "/api/")
        try:
            async with session.get(
                rest_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (401, 403):
                    raise RuntimeError(
                        f"Token rejected by remote HA (HTTP {resp.status}). "
                        "Create a new long-lived access token on the remote instance."
                    )
                if resp.status >= 400:
                    raise RuntimeError(
                        f"Remote HA REST check failed: HTTP {resp.status} at {rest_url}"
                    )
                _LOGGER.info(
                    "REST preflight OK for '%s' (%s → HTTP %s)",
                    self.property_name,
                    rest_url,
                    resp.status,
                )
        except RuntimeError:
            raise
        except Exception as err:
            raise RuntimeError(
                f"REST preflight failed for {rest_url}: {type(err).__name__}: {err}"
            ) from err

        _LOGGER.info(
            "Opening WebSocket to %s for property '%s'",
            url,
            self.property_name,
        )

        # Match the proven pattern used by remote_homeassistant:
        # let the shared HA session handle SSL; only disable when asked.
        ws_kwargs: dict[str, Any] = {
            "heartbeat": 30,
            "timeout": 30.0,
        }
        if self.secure and not self.verify_ssl:
            ws_kwargs["ssl"] = False

        async with session.ws_connect(url, **ws_kwargs) as ws:
            self._ws = ws
            self._msg_id = 1
            self._pending.clear()

            # --- Auth handshake ---
            msg = await ws.receive_json()
            if msg.get("type") != "auth_required":
                raise RuntimeError(f"Expected auth_required, got: {msg}")

            await ws.send_json(
                {"type": "auth", "access_token": self.access_token}
            )
            msg = await ws.receive_json()
            if msg.get("type") != "auth_ok":
                raise RuntimeError(
                    f"Auth failed: {msg.get('message', msg)}"
                )

            self._remote_version = msg.get("ha_version", "unknown")
            self._last_seen = dt_util.utcnow()
            _LOGGER.info(
                "Authenticated to '%s' (HA %s) – fetching states…",
                self.property_name,
                self._remote_version,
            )

            # --- Initial state dump ---
            states = await self._send_command(ws, "get_states")
            mirrored = 0
            if isinstance(states, list):
                for state in states:
                    before = len(self._mirrored_entities)
                    self._apply_remote_state(state)
                    if len(self._mirrored_entities) > before:
                        mirrored += 1
                self._entity_count = len(self._mirrored_entities)
                _LOGGER.info(
                    "Mirrored %s / %s entities from '%s'",
                    self._entity_count,
                    len(states),
                    self.property_name,
                )
            else:
                _LOGGER.warning(
                    "get_states returned unexpected payload for '%s': %s",
                    self.property_name,
                    type(states),
                )

            # Only mark connected after a successful state sync
            self._connected = True
            self._last_error = None
            self._notify_update()

            # --- Subscribe to live updates ---
            await self._send_command(
                ws, "subscribe_events", event_type="state_changed"
            )
            _LOGGER.info(
                "Subscribed to state_changed for '%s'", self.property_name
            )

            # --- Message pump ---
            async for raw in ws:
                if self._stop:
                    break
                if raw.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                ):
                    break
                if raw.type != aiohttp.WSMsgType.TEXT:
                    continue

                try:
                    data = raw.json()
                except Exception:  # pylint: disable=broad-except
                    continue

                self._last_seen = dt_util.utcnow()
                await self._handle_message(data)

                # Expire maintenance window opportunistically
                if (
                    self.maintenance_allowed_until
                    and self.maintenance_allowed_until <= dt_util.utcnow()
                ):
                    self.maintenance_allowed_until = None
                    self.maintenance_requested = False
                    self.consent_granted = False
                    self._notify_update()

    async def _send_command(
        self, ws: aiohttp.ClientWebSocketResponse, cmd_type: str, **kwargs: Any
    ) -> Any:
        """Send a WS command and pump messages until the matching result arrives.

        The result is delivered on the same socket, so we must receive while waiting.
        """
        msg_id = self._msg_id
        self._msg_id += 1
        payload = {"id": msg_id, "type": cmd_type, **kwargs}
        fut: asyncio.Future = self.hass.loop.create_future()
        self._pending[msg_id] = fut
        await ws.send_json(payload)

        try:
            loop = asyncio.get_running_loop()
            deadline = loop.time() + 60.0
            while not fut.done():
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Timed out waiting for result of '{cmd_type}' (id={msg_id})"
                    )
                try:
                    raw = await asyncio.wait_for(ws.receive(), timeout=remaining)
                except asyncio.TimeoutError as err:
                    raise TimeoutError(
                        f"Timed out waiting for result of '{cmd_type}' (id={msg_id})"
                    ) from err

                if raw.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                    aiohttp.WSMsgType.CLOSE,
                ):
                    raise RuntimeError(
                        f"WebSocket closed while waiting for '{cmd_type}': {raw}"
                    )
                if raw.type != aiohttp.WSMsgType.TEXT:
                    continue
                try:
                    data = raw.json()
                except Exception:  # pylint: disable=broad-except
                    continue
                await self._handle_message(data)

            return fut.result()
        finally:
            self._pending.pop(msg_id, None)

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Dispatch incoming WebSocket messages."""
        msg_type = data.get("type")

        if msg_type == "result":
            msg_id = data.get("id")
            fut = self._pending.get(msg_id)
            if fut and not fut.done():
                if data.get("success"):
                    fut.set_result(data.get("result"))
                else:
                    fut.set_exception(
                        RuntimeError(str(data.get("error", "unknown error")))
                    )
            return

        if msg_type == "event":
            event = data.get("event") or {}
            if event.get("event_type") == "state_changed":
                event_data = event.get("data") or {}
                new_state = event_data.get("new_state")
                entity_id = event_data.get("entity_id")
                if new_state is None and entity_id:
                    # Entity removed on remote
                    self._remove_local_entity(entity_id)
                elif new_state:
                    self._apply_remote_state(new_state)
            return

    # ------------------------------------------------------------------
    # Entity mirroring helpers
    # ------------------------------------------------------------------

    def _should_mirror(self, entity_id: str) -> bool:
        """Return True if this remote entity should be mirrored."""
        if not entity_id or "." not in entity_id:
            return False
        domain = entity_id.split(".", 1)[0]
        if domain in self._exclude_domains:
            return False
        if self._include_domains is not None and domain not in self._include_domains:
            return False
        # Never mirror our own integration entities if they somehow appear
        if domain == DOMAIN:
            return False
        return True

    def _local_entity_id(self, remote_entity_id: str) -> str:
        """Build the local entity_id (with optional prefix)."""
        domain, object_id = remote_entity_id.split(".", 1)
        if self.entity_prefix:
            object_id = f"{self.entity_prefix}{object_id}"
        return f"{domain}.{object_id}"

    def _apply_remote_state(self, state: dict[str, Any]) -> None:
        """Publish a remote state onto the local state machine."""
        remote_eid = state.get("entity_id")
        if not remote_eid or not self._should_mirror(remote_eid):
            return

        local_eid = self._local_entity_id(remote_eid)
        attrs = dict(state.get("attributes") or {})

        # Prefix friendly name
        if self.friendly_name_prefix:
            original = attrs.get("friendly_name") or remote_eid
            attrs["friendly_name"] = f"{self.friendly_name_prefix}{original}"

        # Tag with remote origin for service forwarding / debugging
        attrs["property_bridge_remote"] = self.property_name
        attrs["property_bridge_remote_entity_id"] = remote_eid
        attrs["property_bridge_entry_id"] = self.entry.entry_id

        try:
            self.hass.states.async_set(
                local_eid,
                state.get("state"),
                attrs,
            )
            self._mirrored_entities.add(local_eid)
            self._local_to_remote[local_eid] = remote_eid
            self._entity_count = len(self._mirrored_entities)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Failed to set state for %s: %s", local_eid, err)

    def _remove_local_entity(self, remote_entity_id: str) -> None:
        """Remove a locally mirrored entity that disappeared on the remote."""
        local_eid = self._local_entity_id(remote_entity_id)
        if local_eid in self._mirrored_entities:
            self.hass.states.async_remove(local_eid)
            self._mirrored_entities.discard(local_eid)
            self._local_to_remote.pop(local_eid, None)
            self._entity_count = len(self._mirrored_entities)
            self._notify_update()

    async def _clear_mirrored_entities(self) -> None:
        """Remove all entities we mirrored for this property."""
        for eid in list(self._mirrored_entities):
            try:
                self.hass.states.async_remove(eid)
            except Exception:  # pylint: disable=broad-except
                pass
        self._mirrored_entities.clear()
        self._local_to_remote.clear()
        self._entity_count = 0

    # ------------------------------------------------------------------
    # Service proxy + automation config
    # ------------------------------------------------------------------

    @callback
    def _on_local_service_call(self, event: Event) -> None:
        """Forward service calls that target our mirrored entities."""
        if not self._connected or self._stop:
            return

        domain = event.data.get("domain")
        service = event.data.get("service")
        if not domain or not service or domain not in PROXY_SERVICE_DOMAINS:
            return

        service_data = dict(event.data.get("service_data") or {})
        entity_ids = service_data.get("entity_id")
        if entity_ids is None:
            return
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        remote_ids: list[str] = []
        for eid in entity_ids:
            if eid in self._proxying:
                continue
            remote = self._local_to_remote.get(eid)
            if remote:
                remote_ids.append(remote)

        if not remote_ids:
            return

        # Fire-and-forget async forward
        self.hass.async_create_task(
            self._forward_service(domain, service, service_data, remote_ids)
        )

    async def _forward_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any],
        remote_ids: list[str],
    ) -> None:
        """Call a service on the remote instance for the given remote entity_ids."""
        data = {k: v for k, v in service_data.items() if k != "entity_id"}
        data["entity_id"] = remote_ids if len(remote_ids) > 1 else remote_ids[0]
        key = f"{domain}.{service}:{','.join(remote_ids)}"
        self._proxying.add(key)
        for rid in remote_ids:
            self._proxying.add(rid)
        try:
            await self.async_call_remote_service(domain, service, data)
            _LOGGER.debug(
                "Forwarded %s.%s → %s on '%s'",
                domain,
                service,
                remote_ids,
                self.property_name,
            )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning(
                "Failed to forward %s.%s to '%s': %s",
                domain,
                service,
                self.property_name,
                err,
            )
        finally:
            self._proxying.discard(key)
            for rid in remote_ids:
                self._proxying.discard(rid)

    async def async_call_remote_service(
        self, domain: str, service: str, data: dict[str, Any] | None = None
    ) -> Any:
        """Call a service on the remote Home Assistant via REST.

        Uses REST (not WebSocket) so it does not race with the live message pump.
        """
        if not self._connected:
            raise RuntimeError(f"Not connected to '{self.property_name}'")
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        url = f"{self._rest_base()}/api/services/{domain}/{service}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with session.post(
            url,
            headers=headers,
            json=data or {},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(
                    f"Remote service {domain}.{service} failed ({resp.status}): {text}"
                )
            try:
                return await resp.json()
            except Exception:  # pylint: disable=broad-except
                return None

    def _rest_base(self) -> str:
        scheme = "https" if self.secure else "http"
        if self.secure and self.port == 443:
            return f"{scheme}://{self.host}"
        if not self.secure and self.port == 80:
            return f"{scheme}://{self.host}"
        return f"{scheme}://{self.host}:{self.port}"

    async def async_list_automations(self) -> list[dict[str, Any]]:
        """Return mirrored automation entities for this property."""
        result: list[dict[str, Any]] = []
        for local_eid, remote_eid in self._local_to_remote.items():
            if not remote_eid.startswith("automation."):
                continue
            state = self.hass.states.get(local_eid)
            attrs = dict(state.attributes) if state else {}
            result.append(
                {
                    "local_entity_id": local_eid,
                    "remote_entity_id": remote_eid,
                    "state": state.state if state else None,
                    "friendly_name": attrs.get("friendly_name"),
                    "automation_id": attrs.get("id"),
                    "last_triggered": attrs.get("last_triggered"),
                    "entry_id": self.entry.entry_id,
                    "property_name": self.property_name,
                }
            )
        return result

    async def async_get_automation_config(
        self, automation_id: str
    ) -> dict[str, Any]:
        """Fetch full automation config from the remote instance.

        ``automation_id`` is the automation's unique id (attribute ``id``),
        or the object_id portion of the entity_id.
        """
        automation_id = automation_id.removeprefix("automation.")
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        url = f"{self._rest_base()}/api/config/automation/config/{automation_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            if resp.status == 404:
                raise RuntimeError(
                    f"Automation '{automation_id}' not found on remote "
                    f"(use the automation unique id, not only the entity_id)"
                )
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(
                    f"Failed to get automation config ({resp.status}): {text}"
                )
            config = await resp.json()
        self._automation_configs[automation_id] = config
        return config

    async def async_update_automation_config(
        self, automation_id: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Create or update an automation config on the remote instance."""
        automation_id = automation_id.removeprefix("automation.")
        session = async_get_clientsession(self.hass, verify_ssl=self.verify_ssl)
        url = f"{self._rest_base()}/api/config/automation/config/{automation_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with session.post(
            url,
            headers=headers,
            json=config,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(
                    f"Failed to update automation config ({resp.status}): {text}"
                )
            try:
                result = await resp.json()
            except Exception:  # pylint: disable=broad-except
                result = {"result": "ok"}
        self._automation_configs[automation_id] = config
        _LOGGER.info(
            "Updated automation '%s' on property '%s'",
            automation_id,
            self.property_name,
        )
        return result if isinstance(result, dict) else {"result": "ok"}

    # ------------------------------------------------------------------
    # Status / sensors
    # ------------------------------------------------------------------

    @callback
    def _notify_update(self) -> None:
        """Notify listeners (sensors) that connection state changed."""
        async_dispatcher_send(
            self.hass,
            f"{SIGNAL_CONNECTION_UPDATE}_{self.entry.entry_id}",
        )

    def get_status_data(self) -> dict[str, Any]:
        """Return a dict of status attributes for sensors."""
        return {
            ATTR_CONNECTED: self._connected,
            ATTR_LAST_SEEN: self._last_seen.isoformat() if self._last_seen else None,
            ATTR_ENTITY_COUNT: self._entity_count,
            ATTR_REMOTE_VERSION: self._remote_version,
            ATTR_AREA_ID: self.area_id,
            ATTR_LABEL_ID: self.label_id,
            ATTR_MAINTENANCE_ALLOWED: self.maintenance_allowed,
            ATTR_MAINTENANCE_UNTIL: (
                self.maintenance_allowed_until.isoformat()
                if self.maintenance_allowed_until
                else None
            ),
            "property_name": self.property_name,
            "host": self.host,
            "port": self.port,
            "secure": self.secure,
            "ws_url": self._ws_url(),
            "last_error": self._last_error,
            "consent_granted": self.consent_granted,
            "maintenance_requested": self.maintenance_requested,
        }
