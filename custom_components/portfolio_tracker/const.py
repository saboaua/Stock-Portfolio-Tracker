"""Constants for Portfolio Tracker."""

DOMAIN = "portfolio_tracker"
VERSION = "1.4.6"

CONF_HOLDINGS = "holdings"
CONF_SYMBOL = "symbol"
CONF_SHARES = "shares"
CONF_INVESTED = "invested"
CONF_ENTRY_DATE = "entry_date"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IDLE_SCAN_INTERVAL = "idle_scan_interval"
CONF_REALIZED_GAIN = "realized_gain"
CONF_TRADE_LOG = "trade_log"
CONF_BASE_CURRENCY = "base_currency"
CONF_SCHEDULE_PRESET = "schedule_preset"
CONF_SNAPSHOT_ENABLED = "snapshot_enabled"

DEFAULT_SCAN_INTERVAL_MINUTES = 5
IDLE_SCAN_INTERVAL_MINUTES = 30
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_SCHEDULE_PRESET = "balanced"
MAX_TRADE_LOG = 50

SERVICE_BUY = "buy_shares"
SERVICE_SELL = "sell_shares"
SERVICE_REFRESH = "refresh"
NOTIFICATION_ID = "portfolio_tracker_error"

# Preset → (open minutes, closed minutes)
SCHEDULE_PRESETS: dict[str, tuple[int, int]] = {
    "active": (5, 30),       # frequent while open
    "balanced": (15, 60),    # default hobbyist
    "conservative": (30, 120),
    "custom": (DEFAULT_SCAN_INTERVAL_MINUTES, IDLE_SCAN_INTERVAL_MINUTES),
}

SCHEDULE_PRESET_LABELS = {
    "active": "Active — every 5 min open / 30 min closed",
    "balanced": "Balanced — every 15 min open / 60 min closed",
    "conservative": "Conservative — every 30 min open / 2 h closed",
    "custom": "Custom — set intervals below",
}

SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "CHF", "CAD", "AUD", "JPY", "HKD", "SGD",
    "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "INR", "CNY",
    "KRW", "BRL", "MXN", "ZAR", "NZD",
]


def resolve_scan_intervals(options: dict) -> tuple[int, int]:
    """Return (open_minutes, closed_minutes) from options + preset."""
    preset = str(options.get(CONF_SCHEDULE_PRESET, DEFAULT_SCHEDULE_PRESET) or DEFAULT_SCHEDULE_PRESET)
    if preset != "custom" and preset in SCHEDULE_PRESETS:
        return SCHEDULE_PRESETS[preset]
    scan = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES))
    idle = int(options.get(CONF_IDLE_SCAN_INTERVAL, IDLE_SCAN_INTERVAL_MINUTES))
    scan = max(1, min(120, scan))
    idle = max(5, min(360, idle))
    return scan, idle
