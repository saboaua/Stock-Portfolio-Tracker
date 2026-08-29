# Portfolio Tracker for Home Assistant

Track a stock/ETF portfolio inside Home Assistant — add positions, log
buys and sells, and see live value/gain/loss — without writing or editing
any YAML. Prices come from Yahoo Finance's public chart endpoint, no API
key required.

Built as a proper Home Assistant custom integration (config flow + options
flow + a `DataUpdateCoordinator`), installable via [HACS](https://hacs.xyz)
as a custom repository.

<!-- Badges - update the repo URL once this is pushed to your own GitHub -->
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![python](https://img.shields.io/badge/python-3.11%2B-blue)

## Screenshots

> Replace these with real screenshots of your dashboard once it's running.

| Overview | Allocation | Holdings table |
|---|---|---|
| _add screenshot_ | _add screenshot_ | _add screenshot_ |

## Features

- **Multiple portfolios** — each is its own config entry ("Add Integration"
  again with a different name). Run "Main", "Cesar", and "Retirement" side
  by side with completely separate holdings and update schedules.
- **Per-portfolio entity naming** — entities are named after the
  portfolio, e.g. `sensor.investing_cesar_nvda_position_value`.
- **Device grouping** — every entity for a portfolio (sensors, market
  binary sensors, refresh button) is grouped under one
  `Investing {Portfolio}` device in Settings → Devices & Services.
- **No YAML for day-to-day use** — add a stock, buy more shares, sell
  shares, edit cost basis, or remove a position, all from each portfolio's
  **Configure** screen.
- **Comprehensive sensors**: invested capital, total value, total gain,
  day change, per-holding gain/loss ($ and %), average cost basis, days
  held.
- **Manual refresh button** — a `button.investing_{name}_refresh_prices`
  entity per portfolio to force an immediate price update, plus a
  `portfolio_tracker.refresh` service for automations.
- **Configurable update schedule** — set the polling interval for market
  hours and off-hours separately, per portfolio, from Configure → Update
  schedule (defaults: 5 min / 30 min).
- **Error notifications via HA Repairs** — if a symbol's price fetch fails
  several updates in a row (rate-limited, delisted, network issue), a
  Repair shows up under Settings → System → Repairs naming the symbol and
  portfolio, and clears itself automatically once fetches succeed again.
- **Uses Home Assistant's shared aiohttp session** (`async_get_clientsession`)
  rather than opening its own connections.
- **US/EU market-open indicators**, computed from each exchange's real
  timezone (DST-aware) instead of guessing from the browser's clock.
- **Ready-made Lovelace dashboards**: a dynamic tile grid that grows
  automatically as you add stocks, a holdings table, an allocation donut
  chart, and a market-hours widget.

## ⚠️ v2.0 breaking change: entity IDs now include the portfolio name

Version 2.0 adds multi-portfolio support, which means every entity ID now
includes the portfolio name — e.g. `sensor.nvda_position_value` becomes
`sensor.investing_main_nvda_position_value` (assuming you named your
portfolio "Main"). This is unavoidable: without a portfolio prefix, two
portfolios holding the same symbol would collide on the same entity ID.

**If you're upgrading from v1.x:**
1. Note your portfolio's name when you re-add the integration (use the
   same name you'd expect, e.g. "Main").
2. Update any dashboards, automations, or scripts that reference the old
   unprefixed entity IDs (`sensor.<symbol>_position_value`,
   `sensor.portfolio_total_value`, etc.) to the new
   `sensor.investing_<name>_...` form. A find-and-replace of
   `sensor.portfolio_` → `sensor.investing_main_` and
   `sensor.<symbol>_` → `sensor.investing_main_<symbol>_` across your
   dashboard YAML covers most of it.
3. The bundled dashboards in `dashboards/` use dynamic entity discovery
   (`auto-entities`, JS scanning `states`) for the parts that vary by
   symbol, so those need no changes — only cards that hardcode
   `sensor.portfolio_total_value` directly (the hero card, market hours,
   holdings table) need their entity references updated to your new
   `investing_<name>_...` IDs.

## Installation

### Via HACS (custom repository)

This isn't in the default HACS store, so add it manually:

1. Fork or copy this repo to your own GitHub account.
2. In Home Assistant: **HACS → Integrations → ⋮ (top right) → Custom
   repositories**.
3. Add your repo URL, category **Integration**.
4. Find **Portfolio Tracker** in HACS and click **Download**.
5. Restart Home Assistant.
6. **Settings → Devices & Services → Add Integration → Portfolio Tracker.**
   The first-time setup just creates an empty portfolio — click Submit.

### Manual install

Copy `custom_components/portfolio_tracker/` into your Home Assistant
`config/custom_components/` folder, restart, then add the integration as
in step 6 above.

## Adding and managing stocks

Go to **Settings → Devices & Services**, find the Portfolio Tracker card,
click **Configure**:

| Menu option | What it does |
|---|---|
| Add a new stock | Enter symbol, shares, invested capital, entry date |
| Buy more shares | Pick a symbol, enter shares + total cost — averages your cost basis automatically |
| Sell shares | Pick a symbol, enter shares sold — invested capital is reduced proportionally at current average cost. Selling all shares removes the holding |
| Edit shares / cost basis | Directly correct shares, invested capital, or entry date |
| Remove a stock | Drops it and its sensors entirely |

Any change reloads the integration automatically — sensors update within
seconds, no restart needed.

**Ticker symbols:** use the same format Yahoo Finance uses, including
exchange suffixes for non-US listings (e.g. `VUAA.L` for a London
listing). Dots in the symbol become underscores in entity IDs
(`VUAA.L` → `sensor.vuaa_l_position_value`).

## Entities

Entity IDs are prefixed with `investing_<portfolio name>_`. For a
portfolio named "Main" holding `NVDA`:

| Entity | Description |
|---|---|
| `sensor.investing_main_nvda_price` | Live price. Attributes: `previous_close`, `day_change`, `day_change_pct`, `symbol` |
| `sensor.investing_main_nvda_position_value` | Market value (shares × price). Attributes: `shares`, `invested`, `gain`, `gain_pct`, `avg_cost_per_share`, `entry_date`, `days_held`, `symbol` |

Portfolio-wide (same "Main" example):

| Entity | Description |
|---|---|
| `sensor.investing_main_total_value` | Sum of all position values |
| `sensor.investing_main_total_invested` | Sum of all invested capital |
| `sensor.investing_main_total_gain` | Total value − total invested. Attribute: `gain_pct` |
| `sensor.investing_main_day_change` | Sum of today's $ change across holdings. Attribute: `gain_pct` |
| `sensor.investing_main_holdings_table` | `rows` attribute shaped for `custom:flex-table-card` |
| `binary_sensor.investing_main_us_market_open` | NYSE/NASDAQ regular session, `America/New_York` time |
| `binary_sensor.investing_main_eu_market_open` | LSE/Euronext regular session, `Europe/London` time |
| `button.investing_main_refresh_prices` | Forces an immediate price refresh for this portfolio |

All entities for a portfolio are grouped under one device named
`Investing Main` in Settings → Devices & Services.

## Dashboards

Ready-to-paste Lovelace YAML lives in [`dashboards/`](./dashboards):

- **`portfolio_overview_dynamic.yaml`** — hero card + a stock-tile grid
  that auto-discovers every `*_position_value` sensor via
  `custom:auto-entities`. Add or remove a stock through Configure and the
  grid updates itself, no dashboard editing.
- **`portfolio_allocation.yaml`** — a donut chart of portfolio allocation
  by holding, with a scrollable legend, built as a self-contained
  `button-card` (no charting library needed).
- **`holdings_table.yaml`** — a `flex-table-card` breakdown of every
  holding (shares, cost basis, market value, day/total gain).
- **`market_hours.yaml`** — live US/EU market open/closed status, driven
  by the `binary_sensor` entities above.
- **`manage_portfolio_launcher.yaml`** — a button that jumps straight to
  the integration's Configure screen.

Frontend cards used across these dashboards, all installable via HACS
(Frontend section): `button-card`, `vertical-stack-in-card`,
`layout-card`, `mini-graph-card`, `flex-table-card`, `auto-entities`,
`card_mod`, and `mushroom` (for title cards).

## Automations & scripts

Three services are registered for use outside the Configure UI — a
script, a voice command, or a Lovelace button:

```yaml
service: portfolio_tracker.buy_shares
data:
  symbol: NVDA
  shares: 2
  cost: 350.00      # total $ spent, not per-share price
  # portfolio: Cesar   # only needed if NVDA exists in more than one portfolio
```

```yaml
service: portfolio_tracker.sell_shares
data:
  symbol: NVDA
  shares: 2
  # portfolio: Cesar
```

```yaml
service: portfolio_tracker.refresh
data: {}
  # portfolio: Cesar   # omit to refresh every portfolio
```

`portfolio` matches the name you gave the portfolio when you added the
integration (not the "Investing " prefix). It's only required when a
symbol could belong to more than one configured portfolio.

The coordinator paces its own polling per portfolio (5 min during market
hours / 30 min otherwise by default, both configurable via Configure →
Update schedule), so you don't need a separate automation to force
refreshes — though the `refresh` service or button is there if you want
one on demand.

## Limitations

- Prices come from Yahoo Finance's unofficial chart endpoint — it can
  change or rate-limit without notice. This project has no affiliation
  with Yahoo.
- Market-open sensors don't account for exchange holidays.
- No dividend or realized-gain tracking yet (see the holdings table's
  placeholder columns).
- One portfolio per Home Assistant instance.

## Contributing

Issues and pull requests are welcome. If you add a feature, please also
update this README and, where relevant, the bundled dashboards in
`dashboards/`.

## Disclaimer

This project is for personal portfolio tracking and is not financial
advice. Price data may be delayed or occasionally unavailable; always
verify against your broker before making decisions.

## License

MIT — see [LICENSE](./LICENSE).
