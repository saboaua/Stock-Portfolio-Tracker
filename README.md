# 📈 Portfolio Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Track your stock and ETF portfolio directly inside Home Assistant. Add positions, log buys and sells, and view live market values or gains and losses—**without touching a single line of YAML**. 

Powered by Yahoo Finance's public chart endpoint, requiring **no API keys or signups**. Built as a native Home Assistant custom integration featuring full config flow, options flow, and an efficient `DataUpdateCoordinator`.

---

## ✨ Features

- **Zero-YAML Day-to-Day Management:** Add stocks, buy additional shares, log sales, adjust cost basis, or drop positions directly from `Settings` → `Devices & Services` → `Portfolio Tracker` → `Configure`.
- **Smart Live Updates:** Refreshes every 5 minutes during active market hours and scales back to every 30 minutes off-hours.
- **Detailed Per-Holding Sensors:** Real-time price, total market value, gain/loss ($ and %), average cost basis, and total days held.
- **Portfolio-Wide Metrics:** Aggregated total value, total invested capital, total lifetime gain, and daily performance change.
- **Timezone-Aware Market Indicators:** Real-time US and EU market-open binary sensors calculated from exchange timezones with full DST awareness.
- **Ready-Made Lovelace Dashboards:** Auto-expanding tile grids, allocation donut charts, holdings tables, and market status widgets.
- **Actionable Services:** Trigger `buy_shares` and `sell_shares` actions directly via automations, scripts, or voice commands.

---

## ⚙️ Installation

### Option 1: Via HACS (Recommended)

1. **Fork or copy** this repository to your GitHub account.
2. In Home Assistant, open **HACS** → **Integrations**.
3. Click the **three dots `⋮`** in the top right corner → **Custom repositories**.
4. Paste your repository URL, set the category to **Integration**, and click **Add**.
5. Search for **Portfolio Tracker** in HACS and click **Download**.
6. **Restart** Home Assistant.
7. Navigate to **Settings** → **Devices & Services** → **Add Integration** → **Portfolio Tracker**.
   *(Initial setup creates an empty portfolio—simply click Submit).*

### Option 2: Manual Installation

1. Copy the `custom_components/portfolio_tracker/` directory into your Home Assistant `config/custom_components/` folder.
2. **Restart** Home Assistant.
3. Go to **Settings** → **Devices & Services** → **Add Integration** → search for **Portfolio Tracker**.

---

## 💼 Managing Holdings

Navigate to **Settings** → **Devices & Services**, locate **Portfolio Tracker**, and select **Configure**.

| Menu Option | Action & Description |
| :--- | :--- |
| **Add a new stock** | Specify ticker symbol, share count, invested capital, and entry date. |
| **Buy more shares** | Select an existing symbol and enter shares + total cost. Automatically updates your dollar-weighted cost basis. |
| **Sell shares** | Select a symbol and enter shares sold. Reduces invested capital proportionally based on current average cost. *(Selling 100% of holdings automatically removes the position).* |
| **Edit shares / cost basis** | Manually correct total shares, invested capital, or entry date. |
| **Remove a stock** | Completely removes the holding and purges associated sensors. |

> [!NOTE]  
> All configuration updates instantly reload the integration. Sensors update within seconds without needing a Home Assistant restart.

### 📌 Ticker Formatting
Use standard Yahoo Finance ticker formats, including exchange suffixes for non-US assets (e.g., `VUAA.L` for London listings). Dots in ticker symbols automatically convert to underscores in entity IDs:
- `VUAA.L` ➡️ `sensor.vuaa_l_position_value`

---

## 📊 Sensor Entities

### Holding-Specific Entities
*Generated per ticker symbol added (Example: `NVDA`)*

| Entity ID | Description | Key Attributes |
| :--- | :--- | :--- |
| `sensor.nvda_price` | Real-time unit price | `previous_close`, `day_change`, `day_change_pct`, `symbol` |
| `sensor.nvda_position_value` | Current market value ($) | `shares`, `invested`, `gain`, `gain_pct`, `avg_cost_per_share`, `entry_date`, `days_held`, `symbol` |

### Portfolio-Wide Entities

| Entity ID | Description |
| :--- | :--- |
| `sensor.portfolio_total_value` | Aggregate market value across all holdings |
| `sensor.portfolio_total_invested` | Sum of total capital invested |
| `sensor.portfolio_total_gain` | Net portfolio gain/loss (`total_value` − `total_invested`). Includes `gain_pct` attribute |
| `sensor.portfolio_day_change` | Combined single-day dollar change. Includes `gain_pct` attribute |
| `sensor.portfolio_holdings_table` | Structured row matrix designed for `custom:flex-table-card` |
| `binary_sensor.us_market_open` | NYSE / NASDAQ active trading window status |
| `binary_sensor.eu_market_open` | LSE / Euronext active trading window status |

---

## 🖼️ Dashboards

Pre-configured Lovelace YAML files are available inside the `dashboards/` directory:

- 🧱 **`portfolio_overview_dynamic.yaml`** – Hero summary card + auto-expanding stock grid using `custom:auto-entities`. Automatically adds new stock tiles as you configure them.
- 🍩 **`portfolio_allocation.yaml`** – Standalone visual donut chart illustrating portfolio weight by holding (powered by `button-card`).
- 📋 **`holdings_table.yaml`** – Comprehensive tabular breakdown of shares, basis, value, and gain using `flex-table-card`.
- ⏰ **`market_hours.yaml`** – Live status display for US and European market sessions.
- 🚀 **`manage_portfolio_launcher.yaml`** – Quick-action button linking directly to the integration settings card.

### Required Frontend Components
Install these via **HACS** → **Frontend**:
`button-card` • `vertical-stack-in-card` • `layout-card` • `mini-graph-card` • `flex-table-card` • `auto-entities` • `card_mod` • `mushroom`

---

## 🤖 Automations & Services

Log transactions directly via automations, scripts, or voice commands using these registered services:

### Buy Shares
```yaml
service: portfolio_tracker.buy_shares
data:
  symbol: NVDA
  shares: 2
  cost: 350.00  # Total capital spent (not unit price)
