"""Constants for Portfolio Tracker."""

DOMAIN = "portfolio_tracker"

CONF_HOLDINGS = "holdings"
CONF_SYMBOL = "symbol"
CONF_SHARES = "shares"
CONF_INVESTED = "invested"
CONF_ENTRY_DATE = "entry_date"

# Poll every 5 min while any tracked market is open; back off otherwise.
DEFAULT_SCAN_INTERVAL_MINUTES = 5
IDLE_SCAN_INTERVAL_MINUTES = 30

SERVICE_BUY = "buy_shares"
SERVICE_SELL = "sell_shares"
