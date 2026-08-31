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
| **Top Movers** | Ranked day % bar chart for open holdings (`sensor.portfolio_top_movers`). |
| **Event Triggers** | Native HA events `portfolio_tracker_milestone` and `portfolio_tracker_volatility_alert` for mobile notifications and automations. |
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


---

## Event Triggers

Portfolio Tracker fires **native Home Assistant events** after each successful price update so you can drive notifications and automations without polling sensors.

<p align="center">
  <img src="https://raw.githubusercontent.com/saboaua/Stock-Portfolio-Tracker/main/brand/event_triggers.png" alt="Event Trigger Settings" width="450">
</p>

Configure under **Configure → Event triggers**:

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| Enable event triggers | On | Master switch |
| Milestone step | `10000` | Fire when total portfolio value crosses multiples of this amount (base currency) |
| Volatility threshold | `5` | Fire when portfolio or any holding day-change % exceeds this absolute value |

### Event types

| Event | When it fires |
| :--- | :--- |
| `portfolio_tracker_milestone` | Total value crosses a milestone step **up** or **down** (debounced per level) |
| `portfolio_tracker_volatility_alert` | Portfolio day % **or** any symbol’s day % exceeds the threshold (debounced until the move cools off) |

### Example automation (milestone)

```yaml
alias: Portfolio milestone notification
trigger:
  - platform: event
    event_type: portfolio_tracker_milestone
action:
  - service: notify.mobile_app_your_phone
    data:
      title: Portfolio milestone
      message: >
        Moved {{ trigger.event.data.direction }} past
        {{ trigger.event.data.threshold }} {{ trigger.event.data.currency }}
        (now {{ trigger.event.data.total_value }}).
```

### Example automation (volatility)

```yaml
alias: Portfolio volatility alert
trigger:
  - platform: event
    event_type: portfolio_tracker_volatility_alert
action:
  - service: notify.mobile_app_your_phone
    data:
      title: Portfolio volatility
      message: >
        {% if trigger.event.data.scope == 'symbol' %}
        {{ trigger.event.data.symbol }} moved {{ trigger.event.data.day_change_pct }}% today.
        {% else %}
        Portfolio day change {{ trigger.event.data.day_change_pct }}%.
        {% endif %}
```

More examples: [`dashboards/event_automations.yaml`](./dashboards/event_automations.yaml).

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
| `sensor.portfolio_top_movers` | Ranked day movers for charts (`movers`, `symbols`, `day_change_pcts`) |
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

## Top Movers

Ranks your open holdings by **day change %** (gainers on the left, losers on the right).

| Item | Detail |
| :--- | :--- |
| **Sensor** | `sensor.portfolio_top_movers` |
| **State** | Symbol with the largest absolute day move |
| **Attributes** | `movers`, `symbols`, `day_change_pcts`, `top_gainer`, `top_loser` |

**Requirement:** [button-card](https://github.com/custom-cards/button-card) (HACS → Frontend).

### Card YAML (broker-style bars)

Add a **Manual** card and paste:

```yaml
type: custom:button-card
entity: sensor.portfolio_top_movers
show_name: false
show_icon: false
show_state: false
show_label: true
tap_action:
  action: more-info
styles:
  card:
    - background: '#1a1d23'
    - border-radius: 16px
    - border: 1px solid rgba(255,255,255,0.06)
    - box-shadow: none
    - padding: 16px 18px 20px 18px
  grid:
    - grid-template-areas: '"l"'
    - grid-template-columns: 1fr
  label:
    - justify-self: stretch
label: |
  [[[
    const s = entity;
    const movers = (s && s.attributes && s.attributes.movers) || [];
    if (!movers.length) {
      return `<div style="color:#94a3b8;font-size:13px;">No holdings yet</div>`;
    }
    const pcts = movers.map(m => Number(m.day_change_pct) || 0);
    const maxAbs = Math.max(0.5, ...pcts.map(p => Math.abs(p)));
    const bars = movers.map(m => {
      const pct = Number(m.day_change_pct) || 0;
      const h = Math.max(4, Math.round((Math.abs(pct) / maxAbs) * 72));
      const up = pct >= 0;
      const color = up ? '#26a69a' : '#ef5350';
      const label = (up && pct > 0 ? '+' : '') + pct.toFixed(1) + '%';
      return `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;flex:1;min-width:0;gap:6px;">
          <div style="font-size:12px;font-weight:700;color:${color};white-space:nowrap;">${label}</div>
          <div style="width:18px;height:80px;display:flex;align-items:flex-end;justify-content:center;">
            <div style="width:14px;height:${h}px;background:${color};border-radius:3px;"></div>
          </div>
          <div style="font-size:12px;font-weight:700;color:#e2e8f0;letter-spacing:0.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;">${m.symbol}</div>
        </div>`;
    }).join('');
    return `
      <div style="width:100%;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
          <div style="font-size:12px;font-weight:700;letter-spacing:0.14em;color:#94a3b8;">YOUR TOP MOVERS</div>
          <div style="opacity:0.45;font-size:16px;color:#94a3b8;">☰</div>
        </div>
        <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:8px;min-height:130px;border-top:1px dashed rgba(148,163,184,0.2);border-bottom:1px dashed rgba(148,163,184,0.2);padding:10px 4px 8px 4px;background:repeating-linear-gradient(to bottom, transparent, transparent 24px, rgba(148,163,184,0.12) 24px, rgba(148,163,184,0.12) 25px);">
          ${bars}
        </div>
      </div>`;
  ]]]
grid_options:
  columns: full
```

Optional ApexCharts variant: [`dashboards/top_movers.yaml`](./dashboards/top_movers.yaml).

---

## Roadmap

**Income Insights** (planned):

- 🚀 **Dividend Income Tracking** — `sensor.portfolio_tracker_projected_dividend_income`, calculating total projected annual passive payout.
- ⚙️ Enhanced Long-Term Statistics (LTS) compliance across all portfolio sensors (`MONETARY` device class + integer precision defaults).
- ⚙️ Replace the `--` placeholders in the holdings table view with a dynamic dividend yield per asset.

**Shipped in 1.5.8:** Event triggers (`portfolio_tracker_milestone`, `portfolio_tracker_volatility_alert`) — see [Event Triggers](#event-triggers).

**Shipped in 1.5.9:** Top Movers (`sensor.portfolio_top_movers`) + day-change baseline fix — see [Top Movers](#top-movers) and [CHANGELOG.md](./CHANGELOG.md).
