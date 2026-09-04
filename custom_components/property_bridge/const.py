"""Constants for the Property Bridge integration."""

from typing import Final

DOMAIN: Final = "property_bridge"

# Configuration keys – connection
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_SECURE: Final = "secure"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_PROPERTY_NAME: Final = "property_name"
CONF_ENTITY_PREFIX: Final = "entity_prefix"
CONF_FRIENDLY_NAME_PREFIX: Final = "friendly_name_prefix"
CONF_INCLUDE_DOMAINS: Final = "include_domains"
CONF_EXCLUDE_DOMAINS: Final = "exclude_domains"

# Configuration keys – area / labels
CONF_CREATE_AREA: Final = "create_area"
CONF_CREATE_LABEL: Final = "create_label"
CONF_AREA_ID: Final = "area_id"
CONF_LABEL_ID: Final = "label_id"

# Configuration keys – rental presets
CONF_CHECKIN_SCRIPT: Final = "checkin_script"
CONF_CHECKOUT_SCRIPT: Final = "checkout_script"
CONF_CHECKIN_SCENE: Final = "checkin_scene"
CONF_CHECKOUT_SCENE: Final = "checkout_scene"
CONF_OCCUPANCY_HELPER: Final = "occupancy_helper"

# Configuration keys – maintenance / consent
CONF_MAINTENANCE_ENABLED: Final = "maintenance_enabled"
CONF_MAINTENANCE_REQUIRE_CONSENT: Final = "maintenance_require_consent"
CONF_MAINTENANCE_WINDOW_HOURS: Final = "maintenance_window_hours"
CONF_MAINTENANCE_ALLOWED_UNTIL: Final = "maintenance_allowed_until"

# Defaults
DEFAULT_PORT: Final = 8123
DEFAULT_SECURE: Final = True
DEFAULT_VERIFY_SSL: Final = True
DEFAULT_ENTITY_PREFIX: Final = ""
DEFAULT_CREATE_AREA: Final = True
DEFAULT_CREATE_LABEL: Final = True
DEFAULT_MAINTENANCE_ENABLED: Final = False
DEFAULT_MAINTENANCE_REQUIRE_CONSENT: Final = True
DEFAULT_MAINTENANCE_WINDOW_HOURS: Final = 12

# Domains we never mirror (noise / local-only)
DEFAULT_EXCLUDE_DOMAINS: Final = frozenset(
    {
        "persistent_notification",
        "zone",
        "person",
        "device_tracker",
        "sun",
        "conversation",
        "assist_pipeline",
        "stt",
        "tts",
        "wake_word",
        "notify",
        "update",
    }
)

# Reconnect backoff
RECONNECT_MIN_DELAY: Final = 5
RECONNECT_MAX_DELAY: Final = 60

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor"]

# Connection status attributes
ATTR_CONNECTED: Final = "connected"
ATTR_LAST_SEEN: Final = "last_seen"
ATTR_ENTITY_COUNT: Final = "entity_count"
ATTR_REMOTE_VERSION: Final = "remote_version"
ATTR_AREA_ID: Final = "area_id"
ATTR_LABEL_ID: Final = "label_id"
ATTR_MAINTENANCE_ALLOWED: Final = "maintenance_allowed"
ATTR_MAINTENANCE_UNTIL: Final = "maintenance_until"

# Dispatcher signal
SIGNAL_CONNECTION_UPDATE: Final = f"{DOMAIN}_connection_update"

# Services
SERVICE_APPLY_CHECKIN: Final = "apply_checkin_preset"
SERVICE_APPLY_CHECKOUT: Final = "apply_checkout_preset"
SERVICE_REQUEST_MAINTENANCE: Final = "request_maintenance_window"
SERVICE_END_MAINTENANCE: Final = "end_maintenance_window"
SERVICE_GRANT_CONSENT: Final = "grant_maintenance_consent"
SERVICE_CALL_REMOTE: Final = "call_remote_service"
SERVICE_TRIGGER_AUTOMATION: Final = "trigger_automation"
SERVICE_GET_AUTOMATION_CONFIG: Final = "get_automation_config"
SERVICE_UPDATE_AUTOMATION_CONFIG: Final = "update_automation_config"
SERVICE_LIST_AUTOMATIONS: Final = "list_automations"

# Domains whose local service calls are forwarded to the remote instance
PROXY_SERVICE_DOMAINS: Final = frozenset(
    {
        "automation",
        "script",
        "scene",
        "switch",
        "light",
        "cover",
        "fan",
        "lock",
        "climate",
        "media_player",
        "button",
        "input_boolean",
        "input_button",
        "input_number",
        "input_select",
        "input_text",
        "number",
        "select",
        "vacuum",
        "water_heater",
        "humidifier",
        "siren",
        "alarm_control_panel",
    }
)
