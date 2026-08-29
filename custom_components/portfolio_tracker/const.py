"""Constants for Portfolio Tracker."""

DOMAIN = "portfolio_tracker"
VERSION = "1.4.5"

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

DEFAULT_SCAN_INTERVAL_MINUTES = 5
IDLE_SCAN_INTERVAL_MINUTES = 30
DEFAULT_BASE_CURRENCY = "USD"
MAX_TRADE_LOG = 50

SERVICE_BUY = "buy_shares"
SERVICE_SELL = "sell_shares"
SERVICE_REFRESH = "refresh"

NOTIFICATION_ID = "portfolio_tracker_error"
