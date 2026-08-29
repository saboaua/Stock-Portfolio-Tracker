"""Constants for Portfolio Tracker."""

DOMAIN = "portfolio_tracker"
VERSION = "1.2.0"

CONF_HOLDINGS = "holdings"
CONF_SYMBOL = "symbol"
CONF_SHARES = "shares"
CONF_INVESTED = "invested"
CONF_ENTRY_DATE = "entry_date"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IDLE_SCAN_INTERVAL = "idle_scan_interval"

# Poll while any tracked market is open; back off otherwise.
DEFAULT_SCAN_INTERVAL_MINUTES = 5
IDLE_SCAN_INTERVAL_MINUTES = 30

SERVICE_BUY = "buy_shares"
SERVICE_SELL = "sell_shares"
