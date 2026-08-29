<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/logo.png" alt="Portfolio Tracker" width="420">
</p>

<p align="center">
  <strong>One integration for hobby investors</strong><br>
  Stocks · ETFs · Crypto — live prices, FX, charts, and holdings in Home Assistant
</p>

<p align="center">
  <a href="https://github.com/saboaua/Stock-Portfolio-Tracker/releases"><img src="https://img.shields.io/github/v/release/saboaua/Stock-Portfolio-Tracker?style=flat-square&label=release" alt="Release"></a>
  <img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square" alt="HACS">
  <img src="https://img.shields.io/badge/HA-2024.6+-41BDF5?style=flat-square" alt="Home Assistant">
  <a href="https://github.com/saboaua/Stock-Portfolio-Tracker/issues"><img src="https://img.shields.io/github/issues/saboaua/Stock-Portfolio-Tracker?style=flat-square" alt="Issues"></a>
</p>

---

### Why this integration

Most people install several stock components just to see price, P/L, and a chart.  
**Portfolio Tracker** keeps it in one place: manage positions in the UI, pull Yahoo Finance data (no API key), convert currencies, watch market hours, and use a built-in Lovelace card.

---

### Features

| | |
|:--|:--|
| **Configure UI** | Add · buy · sell · edit · remove holdings — no YAML for day-to-day trades |
| **Yahoo Finance** | Live prices without tokens or `yfinance` |
| **Multi-currency FX** | Pick a base currency; foreign tickers convert automatically |
| **Native card** | `summary` · `charts` (sparklines) · `holdings` |
| **Update schedule** | Active / Balanced / Conservative / Custom + optional fixed snapshots |
| **Refresh button** | Force an update anytime (`button.portfolio_refresh`) |
| **Last update** | Know when data last succeeded (`sensor.portfolio_last_update`) |
| **Error alerts** | Persistent notification if Yahoo refreshes keep failing |
| **Dividends** | `calendar.portfolio_dividends` |
| **Realized P/L** | Tracked on sells with a short trade log |
| **Market sessions** | US & EU open/closed sensors + schedules |
| **Crypto** | Same form as stocks — e.g. `BTC-USD`, `ETH-USD` |

---

### Entities (overview)

| Entity | Role |
|--------|------|
| `sensor.<symbol>_price` | Live price + 52w / volume / name |
| `sensor.<symbol>_position_value` | Value, shares, gain, allocation % |
| `sensor.portfolio_total_value` | Portfolio in base currency |
| `sensor.portfolio_total_invested` | Cost basis |
| `sensor.portfolio_total_gain` | Unrealized P/L |
| `sensor.portfolio_day_change` | Day P/L |
| `sensor.portfolio_realized_gain` | Realized + recent trades |
| `sensor.portfolio_holdings_count` | Open positions |
| `sensor.portfolio_holdings_table` | Rows for tables / card |
| `sensor.portfolio_last_update` | Last successful refresh |
| `button.portfolio_refresh` | Manual Yahoo refresh |
| `binary_sensor.us_market_open` / `eu_market_open` | Session flags |
| `sensor.us_market_session` / `eu_market_session` | open/closed + times |
| `calendar.portfolio_dividends` | Dividend events |

---

### Lovelace card

**Settings → Dashboards → ⋮ → Resources → Add**

| Field | Value |
|-------|--------|
| URL | `/portfolio_tracker_static/portfolio-tracker-card.js` |
| Type | JavaScript Module |

```yaml
type: custom:portfolio-tracker-card
title: My Portfolio
view: charts
range: 1W
```

| `view` | Description |
|--------|-------------|
| `summary` | Totals, unrealized / day P/L, market pills |
| `charts` | Ticker grid with price, % change, sparklines |
| `holdings` | Shares, avg cost, invested, market value, gain |

---

### Quick start

1. HACS → custom repository → install → **restart HA**  
2. **Settings → Devices & Services → Add Integration → Portfolio Tracker**  
3. **Configure** → add symbols (e.g. `NVDA`, `VUAA.L`, `BTC-USD`)  
4. Optional: add the card resource above  

**Docs:** [github.com/saboaua/Stock-Portfolio-Tracker](https://github.com/saboaua/Stock-Portfolio-Tracker)

**Version:** 1.4.6
