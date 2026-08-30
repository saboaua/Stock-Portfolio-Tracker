"""Constants for Portfolio Tracker."""
import json
from pathlib import Path

DOMAIN = "portfolio_tracker"


def _load_version() -> str:
    """Read the version from manifest.json - the single source of truth.

    Previously VERSION was a second hardcoded string here that had to be
    kept in sync with manifest.json by hand; it drifted (manifest said
    1.5.3, this said 1.5.1) and caused the device page's "Firmware" field
    to show a stale version. Reading it directly from manifest.json makes
    that impossible - there is now only one place to bump per release.
    """
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        return json.loads(manifest_path.read_text())["version"]
    except Exception:  # noqa: BLE001 - never let a bad manifest crash setup
        return "0.0.0"


VERSION = _load_version()

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

# Retirement / forecast plan
CONF_RETIRE_ENABLED = "retire_enabled"
CONF_RETIRE_HORIZON = "retire_horizon"
CONF_RETIRE_BASELINE = "retire_baseline"
CONF_RETIRE_START_YEAR = "retire_start_year"
CONF_RETIRE_CONTRIBUTION = "retire_annual_contribution"
CONF_RETIRE_SCENARIO = "retire_scenario"
CONF_RETIRE_YEARLY_ACTUALS = "retire_yearly_actuals"

DEFAULT_RETIRE_HORIZON = 10
DEFAULT_RETIRE_SCENARIO = "moderate"

# Native Home Assistant events (for automations / mobile notifications)
EVENT_MILESTONE = "portfolio_tracker_milestone"
EVENT_VOLATILITY = "portfolio_tracker_volatility_alert"

CONF_EVENTS_ENABLED = "events_enabled"
CONF_MILESTONE_STEP = "milestone_step"  # fire each time total value crosses N * step
CONF_VOLATILITY_PCT = "volatility_pct"  # |day change %| threshold for portfolio or symbol
CONF_VOLATILITY_SYMBOL = "volatility_watch_symbols"  # optional; empty = portfolio only

DEFAULT_EVENTS_ENABLED = True
DEFAULT_MILESTONE_STEP = 10000.0  # currency units
DEFAULT_VOLATILITY_PCT = 5.0
