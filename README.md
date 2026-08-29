# Portfolio Tracker for Home Assistant

A HACS-installable custom integration that tracks a stock portfolio with a proper UI:

- **Add stocks, log buys/sells, edit cost basis, or remove a position** from  
  **Settings → Devices & Services → Portfolio Tracker → Configure**  
  (no YAML for day-to-day changes)
- Live prices from **Yahoo Finance** public chart API (no API key, no `yfinance` package)
- Adaptive polling: every **5 minutes** while US or EU markets are open, every **30 minutes** otherwise
- Ready-made Lovelace cards under `dashboards/`

**Current version:** `1.1.0` (HACS detects updates from `manifest.json` → `version`)

---

## What you get

### Per stock (e.g. `NVDA`, `VUAA.L`)

| Entity | Description |
|--------|-------------|
| `sensor.<symbol>_price` | Live price + previous close / day change attributes |
| `sensor.<symbol>_position_value` | Market value + `shares`, `invested`, `gain`, `gain_pct`, `avg_cost_per_share`, `entry_date`, `days_held` |

Symbols with dots (e.g. `VUAA.L`) become entity IDs with underscores (`sensor.vuaa_l_price`).

### Portfolio-wide

| Entity | Description |
|--------|-------------|
| `sensor.portfolio_total_value` | Sum of all position values |
| `sensor.portfolio_total_invested` | Sum of cost basis |
| `sensor.portfolio_total_gain` | Unrealized P/L (`gain_pct` attribute) |
| `sensor.portfolio_day_change` | Day P/L in currency (`gain_pct` attribute) |
| `sensor.portfolio_holdings_table` | `rows` attribute shaped for `custom:flex-table-card` |

### Market hours

| Entity | Description |
|--------|-------------|
| `binary_sensor.us_market_open` | On while NYSE/NASDAQ regular session is open |
| `binary_sensor.eu_market_open` | On while LSE regular session is open |
| `sensor.us_market_session` | State `open` / `closed` + open/close times & next open/close |
| `sensor.eu_market_session` | Same for Europe |

Attributes on the binary and session sensors include:

- `opens_at_local` / `closes_at_local` (exchange local clock, e.g. `09:30`)
- `next_open` / `next_close` (ISO timestamps)
- `next_open_local` / `next_close_local`
- `exchange_timezone` (`America/New_York` or `Europe/London`)
- `local_time` (current exchange local time)

Times are computed with `zoneinfo` so they stay correct across DST and regardless of Home Assistant’s or the browser’s timezone. **Market holidays are not modelled.**

---

## Install via HACS (custom repository)

1. Push this repository to GitHub (e.g. `github.com/you/ha-portfolio-tracker`).
2. In Home Assistant: **HACS → Integrations → ⋮ → Custom repositories**.
3. Repository URL = your repo, Category = **Integration**.
4. Find **Portfolio Tracker**, click **Download**.
5. **Restart Home Assistant**.
6. **Settings → Devices & Services → Add Integration → Portfolio Tracker**.  
   First setup creates an empty portfolio — click Submit.

### Version updates

Bump `version` in `custom_components/portfolio_tracker/manifest.json` when you release. HACS compares that field and offers the update. After updating, restart Home Assistant so the new code loads.

### Dependencies

None beyond Home Assistant itself. Prices are fetched with Home Assistant’s built-in `aiohttp` client against Yahoo’s public chart endpoint. **You do not need to install `yfinance` or any other pip package.**

---

## Manage holdings (UI)

**Settings → Devices & Services → Portfolio Tracker → Configure**:

| Menu item | What it does |
|-----------|--------------|
| **Add a new stock** | Symbol, shares, invested capital, entry date |
| **Buy more shares** | Adds shares + cost; averages cost basis |
| **Sell shares** | Reduces shares; invested capital reduced proportionally. Selling all shares removes the holding |
| **Edit shares / cost basis** | Direct correction of shares / invested / entry date |
| **Remove a stock** | Deletes the holding and its sensors |

Any change reloads the integration automatically — sensors update within seconds, no restart required.

---

## Services (automations / scripts)

```yaml
service: portfolio_tracker.buy_shares
data:
  symbol: NVDA
  shares: 2
  cost: 350.00      # total $ spent, not per-share
```

```yaml
service: portfolio_tracker.sell_shares
data:
  symbol: NVDA
  shares: 2
```

---

## London-listed / non-US tickers

Use the Yahoo Finance suffix as the symbol, e.g. `VUAA.L`. Entity IDs slugify dots to underscores (`VUAA.L` → `sensor.vuaa_l_position_value`).

---

## Dashboards (`dashboards/` folder)

Paste these into a Lovelace dashboard (raw YAML or as a view).

| File | Purpose | Extra frontend cards |
|------|---------|----------------------|
| `portfolio_overview_dynamic.yaml` | Auto tile grid for every `*_position_value` sensor | `auto-entities`, `button-card`, `card_mod`, etc. |
| `market_hours.yaml` | US/EU open status + open/close times | `layout-card`, `card_mod` |
| `holdings_table.yaml` | Table from `sensor.portfolio_holdings_table` | `flex-table-card` |
| `manage_portfolio_launcher.yaml` | Button that opens the Configure flow | none |

Adding or removing a stock via Configure updates the dynamic overview and holdings table without editing dashboard YAML.

---

## Uninstalling

1. Delete the integration under **Settings → Devices & Services**.
2. Remove it from HACS.
3. Optional: delete any leftover helpers you no longer use.

---

## Development notes

- Domain: `portfolio_tracker`
- Config entry stores holdings only in **options** (`holdings` dict)
- Platforms: `sensor`, `binary_sensor`
- Minimum Home Assistant: **2024.6.0**
