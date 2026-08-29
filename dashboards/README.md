# Lovelace card templates (Portfolio Tracker v1.4.5.1)

Copy any YAML into a **Manual** card, or use `full_dashboard.yaml` as a view.

## Entity reference

| Entity | Purpose |
|--------|---------|
| `sensor.portfolio_total_value` | Market value (base currency) |
| `sensor.portfolio_total_invested` | Cost basis |
| `sensor.portfolio_total_gain` | Unrealized P/L (`gain_pct`) |
| `sensor.portfolio_day_change` | Day $ change (`gain_pct`) |
| `sensor.portfolio_holdings_count` | Open positions |
| `sensor.portfolio_realized_gain` | Closed trades P/L + trade log |
| `sensor.portfolio_last_update` | Last successful Yahoo refresh |
| `sensor.portfolio_holdings_table` | `rows[]` for flex-table / tiles |
| `sensor.{slug}_price` | Per-symbol price |
| `sensor.{slug}_position_value` | Per-symbol position value |
| `sensor.us_market_session` / `eu_market_session` | `open` / `closed` |
| `binary_sensor.us_market_open` / `eu_market_open` | on/off + `next_open` / `next_close` |
| `button.portfolio_refresh` | Force Yahoo refresh |
| `calendar.portfolio_dividends` | Dividend events |

## Templates

| File | What it is | HACS frontend |
|------|------------|---------------|
| `native_card.yaml` | Built-in card (`summary` / `charts` / `holdings`) | none |
| `entities_simple.yaml` | Pure HA entities + history graph | none |
| `summary_stats.yaml` | Hero gradient total / gain / day | button-card |
| `glance_compact.yaml` | 4 mushroom KPI tiles | mushroom |
| `market_hours.yaml` | US/EU countdown (grid) | button-card, layout-card, card_mod, vertical-stack-in-card |
| `market_hours_simple.yaml` | US/EU countdown (horizontal) | button-card |
| `holdings_table.yaml` | Full flex table | flex-table-card |
| `holdings_tiles.yaml` | Auto tiles per position | auto-entities, button-card |
| `refresh_status.yaml` | Last update + refresh button | mushroom |
| `realized_gain.yaml` | Realized P/L + recent trades | button-card |
| `dividend_calendar.yaml` | Dividend calendar | none |
| `manage_portfolio_launcher.yaml` | Link to Configure | button-card, mushroom |
| `portfolio_overview_dynamic.yaml` | Full overview (hero + auto tiles) | button-card, auto-entities, mushroom, layout-card, card_mod |
| `full_dashboard.yaml` | Complete multi-section view | several (see file header) |

## Minimal install (no HACS frontend)

1. `native_card.yaml` — or add resource `/portfolio_tracker_static/portfolio-tracker-card.js` as **JavaScript Module** if needed  
2. `entities_simple.yaml`  
3. `dividend_calendar.yaml`

## Recommended HACS frontend packs

- **Core UX:** `button-card`, `card_mod`, `mushroom`  
- **Tables / grids:** `flex-table-card`, `auto-entities`, `layout-card`  
- **Stacks:** `vertical-stack-in-card`
