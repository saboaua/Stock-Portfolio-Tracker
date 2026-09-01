# Lovelace card templates (Portfolio Tracker)

Copy any YAML into a **Manual** card, or paste a full view file into a dashboard.

## HACS components required for the complete dashboard

Install these from **HACS → Frontend** before using
[`portfolio_dashboard_complete.yaml`](./portfolio_dashboard_complete.yaml):

| HACS package | Category | Required for complete dashboard |
|--------------|----------|----------------------------------|
| **button-card** | Frontend | Yes — market status, overview, tiles, top movers |
| **card-mod** | Frontend | Yes — card CSS / styling |
| **layout-card** | Frontend | Yes — responsive grids |
| **vertical-stack-in-card** | Frontend | Yes — stacked sections |
| **Mushroom** | Frontend | Yes — title card |
| **auto-entities** | Frontend | Yes — auto holding tiles |
| **flex-table-card** | Frontend | Yes — holdings table |
| **mini-graph-card** | Frontend | Yes — 24h value graph |
| **apexcharts-card** | Frontend | Yes — retirement / forecast charts |

**Optional** (only if you keep those cards in the YAML):

| HACS package | Category | Notes |
|--------------|----------|--------|
| **Easy Stock** | Integration | `custom:easy-stock-card` block |
| **Yahoo Finance** | Integration | `sensor.yahoofinance_*` distribution card |

If you skip Easy Stock / Yahoo Finance, **remove those two cards** from the
complete dashboard YAML so Lovelace does not error on missing types.

**Portfolio Tracker** (this integration) must already be installed and configured
with holdings.

### Quick install order

1. HACS → Frontend → download each **Required** package above  
2. Restart Home Assistant if HACS asks (frontend-only often needs only a refresh)  
3. Confirm Portfolio Tracker sensors exist (`sensor.portfolio_total_value`, etc.)  
4. Paste `portfolio_dashboard_complete.yaml` into a dashboard raw editor  

---

## Entity reference

| Entity | Purpose |
|--------|---------|
| `sensor.portfolio_total_value` | Market value (base currency) |
| `sensor.portfolio_total_invested` | Cost basis (`by_symbol` attribute) |
| `sensor.portfolio_total_gain` | Unrealized P/L (`gain_pct`) |
| `sensor.portfolio_day_change` | Day $ change (`gain_pct`) |
| `sensor.portfolio_holdings_count` | Open positions |
| `sensor.portfolio_realized_gain` | Closed trades P/L + trade log |
| `sensor.portfolio_last_update` | Last successful Yahoo refresh |
| `sensor.portfolio_holdings_table` | `rows[]` for flex-table / tiles |
| `sensor.portfolio_top_movers` | Ranked day movers for bar charts |
| `sensor.portfolio_retire_plan` | Retirement scenarios + `*_points` |
| `sensor.{slug}_price` | Per-symbol price |
| `sensor.{slug}_position_value` | Per-symbol position value |
| `sensor.us_market_session` / `eu_market_session` | `open` / `closed` |
| `binary_sensor.us_market_open` / `eu_market_open` | on/off + `next_open` / `next_close` |
| `button.portfolio_refresh` | Force Yahoo refresh |
| `calendar.portfolio_dividends` | Dividend events |

## Templates

| File | What it is | HACS frontend |
|------|------------|---------------|
| **`portfolio_dashboard_complete.yaml`** | **Full sections dashboard** (markets, overview, tiles, table, top movers, retirement) | See table above |
| `native_card.yaml` | Built-in card (`summary` / `charts` / `holdings`) | none |
| `entities_simple.yaml` | Pure HA entities + history graph | none |
| `summary_stats.yaml` | Hero gradient total / gain / day | button-card |
| `glance_compact.yaml` | 4 mushroom KPI tiles | mushroom |
| `market_hours.yaml` | US/EU countdown (grid) | button-card, layout-card, card_mod, vertical-stack-in-card |
| `market_hours_simple.yaml` | US/EU countdown (horizontal) | button-card |
| `holdings_table.yaml` | Full flex table | flex-table-card |
| `holdings_tiles.yaml` | Auto tiles per position | auto-entities, button-card |
| `top_movers.yaml` | ApexCharts top movers | apexcharts-card |
| `top_movers_button_card.yaml` | Broker-style top movers bars | button-card |
| `refresh_status.yaml` | Last update + refresh button | mushroom |
| `realized_gain.yaml` | Realized P/L + recent trades | button-card |
| `dividend_calendar.yaml` | Dividend calendar | none |
| `manage_portfolio_launcher.yaml` | Link to Configure | button-card, mushroom |
| `portfolio_overview_dynamic.yaml` | Full overview (hero + auto tiles) | button-card, auto-entities, mushroom, layout-card, card_mod |
| `full_dashboard.yaml` | Complete multi-section view | several (see file header) |
| `retire_forecast_apexcharts.yaml` | Retirement forecast chart | apexcharts-card |

## Complete dashboard sample

Use [`portfolio_dashboard_complete.yaml`](./portfolio_dashboard_complete.yaml) as a full **sections** view:

1. Install all **Required** HACS Frontend packages listed above  
2. Create a new dashboard (or edit an existing one)  
3. Open **Raw configuration editor**  
4. Paste the contents (starts with `views:`)  
5. Save and hard-refresh the browser  

Optional blocks (`easy-stock-card`, `sensor.yahoofinance_*`) need those integrations; remove those cards if unused.

## Minimal install (no HACS frontend)

1. `native_card.yaml` — or add resource `/portfolio_tracker_static/portfolio-tracker-card.js` as **JavaScript Module** if needed  
2. `entities_simple.yaml`  
3. `dividend_calendar.yaml`

## Recommended HACS frontend packs (summary)

- **Core UX:** `button-card`, `card-mod`, `Mushroom`  
- **Tables / grids:** `flex-table-card`, `auto-entities`, `layout-card`  
- **Stacks:** `vertical-stack-in-card`  
- **Charts:** `apexcharts-card`, `mini-graph-card`  
