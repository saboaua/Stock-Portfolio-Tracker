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
| **Retirement forecast** | 4–10y scenarios + ApexCharts-ready sensors (`sensor.portfolio_retire_plan/progress/target` — fixed in 1.5.1, chart header fixed in 1.5.3.1) |
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

**Version:** 1.5.3.1 — see [CHANGELOG.md](./CHANGELOG.md) for what's new.

---

### Device grouping & firmware version

All entities from every platform (sensors, binary sensors, the refresh
button, the dividend calendar) share one device — "Portfolio Tracker" —
via a single `device.py` helper, so Home Assistant's device page groups
them into its automatic Sensors / Binary sensors / Controls / Calendar
sections. The device page's **Firmware** field reflects the exact version
you have installed: `const.py` reads it live from `manifest.json` rather
than a second hardcoded value, so it can't drift out of sync with what
HACS reports as installed.

### Releasing updates so HACS detects them

HACS always displays whatever version is in your installed
`manifest.json` — that's automatic, no action needed. What HACS needs to
show an **"Update available"** badge is a matching GitHub Release:

1. Bump `"version"` in `custom_components/portfolio_tracker/manifest.json`
   (this is now the *only* place to change — `const.py` reads it
   automatically, and the device page's firmware field follows).
2. Commit and push.
3. Create a Git tag matching the version (e.g. `v1.5.3.1`) and a GitHub
   Release from that tag.
4. HACS polls releases periodically; users see the update on their next
   check.

Stick to standard `MAJOR.MINOR.PATCH` for future releases where possible —
this release used a four-segment `1.5.3.1` hotfix version to correct a
release that shipped with no functional changes despite its version bump;
`AwesomeVersion` (what HACS uses for comparisons) handles it fine, but
three-segment versions are the safer default going forward.
