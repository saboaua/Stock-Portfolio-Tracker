## Portfolio Tracker

Track a stock portfolio in Home Assistant without writing YAML.

- Add, buy, sell, edit, or remove holdings from **Configure** in the UI
- Live prices from Yahoo Finance (no API key, no extra packages)
- Per-stock and whole-portfolio sensors (value, gain/loss, day change)
- US & EU market-open binary sensors with open/close times
- Optional `buy_shares` / `sell_shares` services for automations
- Ready-made Lovelace cards in the `dashboards/` folder

{% if not installed %}
### Installation
1. Click Download.
2. Restart Home Assistant.
3. Settings > Devices & Services > Add Integration > Portfolio Tracker.
{% endif %}
