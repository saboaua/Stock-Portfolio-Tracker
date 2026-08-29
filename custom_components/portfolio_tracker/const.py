"""Constants for Portfolio Tracker."""

DOMAIN = "portfolio_tracker"

CONF_NAME = "name"
CONF_HOLDINGS = "holdings"
CONF_SYMBOL = "symbol"
CONF_SHARES = "shares"
CONF_INVESTED = "invested"
CONF_ENTRY_DATE = "entry_date"
CONF_UPDATE_INTERVAL = "update_interval_minutes"
CONF_IDLE_INTERVAL = "idle_interval_minutes"

DEFAULT_PORTFOLIO_NAME = "Portfolio"
DEFAULT_SCAN_INTERVAL_MINUTES = 5
DEFAULT_IDLE_INTERVAL_MINUTES = 30
MAX_CONSECUTIVE_FAILURES = 3

SERVICE_BUY = "buy_shares"
SERVICE_SELL = "sell_shares"
SERVICE_REFRESH = "refresh"
