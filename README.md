<p align="center">
  <img src="logo.png" alt="Portfolio Tracker" width="420">
</p>

<h1 align="center">Portfolio Tracker</h1>

<p align="center">
  <strong>Stock, ETF &amp; crypto portfolio tracking for Home Assistant</strong><br>
  UI-managed holdings · Yahoo Finance · multi-currency FX · dividends · Lovelace card
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.4.3-blue?style=flat-square">
  <img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square">
  <img alt="HA" src="https://img.shields.io/badge/Home%20Assistant-2024.6+-41BDF5?style=flat-square">
</p>

<p align="center">
  <a href="https://github.com/saboaua/Stock-Portfolio-Tracker">GitHub</a> ·
  <a href="https://github.com/saboaua/Stock-Portfolio-Tracker/issues">Issues</a>
</p>

---

## Highlights

- **Configure menu with icons** — add / buy / sell / edit / remove / settings  
- **Yahoo Finance** prices (no API key, no `yfinance`)  
- **Multi-currency FX** — pick a base currency; totals convert via Yahoo FX pairs  
- **Dividend calendar** — `calendar.portfolio_dividends` from Yahoo dividend events  
- **Native Lovelace card** — `custom:portfolio-tracker-card`  
- **Realized P/L** + trade log on sells  
- **US & EU market** open/session sensors  

---

## Sensors & entities

| Entity | Description |
|--------|-------------|
| `sensor.<symbol>_price` | Live price + 52w, volume, name |
| `sensor.<symbol>_position_value` | Value, gain, **allocation %** |
| `sensor.portfolio_total_value` | Total in **base currency** |
| `sensor.portfolio_total_invested` | Cost basis |
| `sensor.portfolio_total_gain` | Unrealized P/L |
| `sensor.portfolio_day_change` | Day P/L |
| `sensor.portfolio_realized_gain` | Realized P/L + recent trades |
| `sensor.portfolio_holdings_count` | Open positions |
| `sensor.portfolio_holdings_table` | Rows for flex-table-card |
| `binary_sensor.us_market_open` / `eu_market_open` | Session flags |
| `sensor.us_market_session` / `eu_market_session` | `open`/`closed` + times |
| `calendar.portfolio_dividends` | Dividend events |

---

## Native Lovelace card

After install + restart, add a resource:

**Settings → Dashboards → ⋮ → Resources → Add**

| Field | Value |
|-------|--------|
| URL | `/portfolio_tracker_static/portfolio-tracker-card.js` |
| Type | JavaScript Module |

```yaml
type: custom:portfolio-tracker-card
title: My Portfolio
view: charts    # summary | charts | holdings
range: 1W       # 1W | 1M  (charts view sparklines)
```

| `view` | What you see |
|--------|----------------|
| `summary` | Total value, unrealized / day P/L, market pills |
| `charts` | Grid of tickers with price, % change, and sparkline (like a watchlist) |
| `holdings` | Shares, avg cost, invested, market value, gain for every position |

Tabs on the card switch views without editing YAML.

### Adding crypto

Use Yahoo Finance symbols when you **Add a new stock** (same form as equities):

| Asset | Symbol |
|-------|--------|
| Bitcoin | `BTC-USD` |
| Ethereum | `ETH-USD` |
| Solana | `SOL-USD` |

Configure → **Add a new stock** → enter `BTC-USD`, units, and total cost basis.

---

## Frontend cards (designed dashboard YAML)

From **HACS → Frontend**:

| Required | Optional |
|----------|----------|
| button-card | layout-card |
| auto-entities | vertical-stack-in-card |
| flex-table-card | mini-graph-card |
| card-mod | |
| Mushroom | |

Templates live in `dashboards/`.

---

## Install (HACS custom repository)

1. HACS → Integrations → ⋮ → Custom repositories  
2. `https://github.com/saboaua/Stock-Portfolio-Tracker` · **Integration**  
3. Download → **Restart Home Assistant**  
4. Settings → Devices & Services → Add Integration → Portfolio Tracker  

**Docs / help (?):** [github.com/saboaua/Stock-Portfolio-Tracker](https://github.com/saboaua/Stock-Portfolio-Tracker)

Configure → **Settings** to set **base currency** and poll intervals.

### HACS list icon

HA Devices & Services shows `brand/icon.png`. The HACS *Downloaded* list may still show “Icon not available” for custom repos (HACS limitation).

---

## Version updates

Bump is in `manifest.json` → `version` (**1.4.3**). Publish a GitHub Release so HACS offers the update, then restart HA.
