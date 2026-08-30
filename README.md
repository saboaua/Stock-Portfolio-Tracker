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
  <a href="https://ko-fi.com/patrickgfortin"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FF5E5B?style=flat-square&logo=ko-fi&logoColor=white" alt="Buy Me a Coffee"></a>
  <a href="https://github.com/saboaua/Stock-Portfolio-Tracker/issues"><img src="https://img.shields.io/github/issues/saboaua/Stock-Portfolio-Tracker?style=flat-square" alt="Issues"></a>
</p>

---

## Overview

Most stock integrations require manual YAML editing or API key setups just to monitor prices, P/L, and basic charts.  

**Portfolio Tracker** brings your entire investment portfolio directly into Home Assistant's native UI. It fetches live Yahoo Finance market data without external API tokens, handles multi-currency conversions automatically, tracks stock market trading sessions, and includes an intuitive dashboard card.

---

## Core Features

| Feature | Description |
| :--- | :--- |
| **No-Code Configuration** | Add, buy, sell, edit, or remove holdings directly via Home Assistant UI modal flows. |
| **Yahoo Finance Engine** | Live prices for worldwide stocks, ETFs, and cryptocurrencies without requiring `yfinance` or API keys. |
| **Multi-Currency FX** | Automatic currency conversion into your designated portfolio base currency. |
| **Native Lovelace Card** | Includes `summary`, `charts` (sparklines), and `holdings` views. |
| **Retirement Forecasting** | 4–10 year compound growth projection scenarios with ApexCharts-ready sensors. |
| **Smart Update Schedules** | Active, Balanced, Conservative, or Custom poll intervals with optional fixed snapshot times. |
| **Session Tracking** | Native binary sensors for US & EU market session open/close status. |
| **Dividends & Realized P/L** | Native dividend calendar integration and sell trade logging with FIFO gain calculations. |

---

## Support the Project

If you find Portfolio Tracker helpful and want to support its continued development, feel free to buy me a coffee!

<a href="https://ko-fi.com/patrickgfortin" target="_blank"><img src="https://storage.ko-fi.com/cdn/kofi3.png?v=3" height="36" alt="Buy Me a Coffee at ko-fi.com" /></a>

---

## How It Works: UI Walkthrough

Manage your portfolio using Home Assistant’s built-in UI flow under **Settings → Devices & Services → Portfolio Tracker → Configure**.

### 1. Integration Dashboard & Overview
Once installed, Portfolio Tracker aggregates all sensors, binary sensors, controls, and calendars into a single unified Home Assistant device.

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/integration_setup.png" alt="Integration Setup Card" width="380">
  <br>
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/integration_screen.png" alt="Integration Devices Screen" width="700">
</p>

---

### 2. Management Hub
Clicking **Configure** opens the main action menu where you can manage positions or adjust global configuration settings.

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/manage_portfolio_menu.png" alt="Manage Portfolio Menu" width="450">
</p>

---

### 3. Adding & Managing Holdings

* **Add a New Stock / ETF / Crypto:** Search by Yahoo Finance ticker (e.g., `NVDA`, `VUAA.L`, `BTC-USD`), enter shares/units, total cost basis, and purchase date.
* **Buy / Sell / Edit / Remove:** Adjust position sizes or log sells to calculate realized P/L automatically.

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/add_holding.png" alt="Add Holding Modal" width="420">
</p>

<table align="center">
  <tr>
    <td align="center"><b>Buy More Shares</b></td>
    <td align="center"><b>Sell Shares</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/buy_stock.png" width="340"></td>
    <td><img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/sell_stock.png" width="340"></td>
  </tr>
  <tr>
    <td align="center"><b>Edit Shares / Cost Basis</b></td>
    <td align="center"><b>Remove Stock</b></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/edit_stock.png" width="340"></td>
    <td><img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/remove_stock.png" width="340"></td>
  </tr>
</table>

---

### 4. Global Settings & Schedule
Customize base currency, poll schedules during market hours, custom refresh intervals, and optional fixed daily snapshot times (09:35, 12:00, 16:05 local time).

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/component_settings.png" alt="Component Settings" width="450">
</p>

---

### 5. Retirement Forecast Planning
Configure compound-growth projections (4–10 years) using customizable baseline values, annual contributions, and benchmark scenarios (e.g., Nasdaq 15%) to automatically generate retirement sensors for your dashboards.

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/retirement_setting.png" alt="Retirement Forecast Settings" width="450">
</p>

---

## Entity Reference

| Entity | Description / Attributes |
| :--- | :--- |
| `sensor.<symbol>_price` | Current market price, 52-week highs/lows, volume |
| `sensor.<symbol>_position_value` | Market value, shares held, total unrealized gain, weight % |
| `sensor.portfolio_total_value` | Aggregate portfolio value in base currency |
| `sensor.portfolio_total_invested` | Total cost basis across open positions |
| `sensor.portfolio_total_gain` | Total unrealized gain/loss ($ and %) |
| `sensor.portfolio_day_change` | Combined day change ($ and %) |
| `sensor.portfolio_realized_gain` | Realized profit/loss history |
| `sensor.portfolio_holdings_table` | JSON table array formatted for dashboard views |
| `sensor.portfolio_last_update` | Timestamp of last successful Yahoo sync |
| `button.portfolio_refresh` | Trigger manual price updates |
| `binary_sensor.us_market_open` / `eu_market_open` | Session active indicators |
| `calendar.portfolio_dividends` | Scheduled ex-dividend dates and payouts |

---

## Dashboard Card Setup

1. Go to **Settings → Dashboards → ⋮ (Top Right) → Resources → Add Resource**
2. Configure as follows:
   * **URL:** `/portfolio_tracker_static/portfolio-tracker-card.js`
   * **Resource Type:** `JavaScript Module`

3. Add the card to your dashboard:

```yaml
type: custom:portfolio-tracker-card
title: My Portfolio
view: charts
range: 1W
```

---

## Roadmap

**Income Insights & Event Automations** (planned, not yet in this release):

- 🚀 **Dividend Income Tracking** — `sensor.portfolio_tracker_projected_dividend_income`, calculating total projected annual passive payout.
- 🚀 **Event Triggers** — native HA events `portfolio_tracker_milestone` and `portfolio_tracker_volatility_alert`, for wiring up custom mobile notifications and automations.
- ⚙️ Enhanced Long-Term Statistics (LTS) compliance across all portfolio sensors (`MONETARY` device class + integer precision defaults).
- ⚙️ Replace the `--` placeholders in the holdings table view with a dynamic dividend yield per asset.

These are documented here as planned work — see [CHANGELOG.md](./CHANGELOG.md) for why they weren't folded into this release.
