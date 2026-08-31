# Changelog

## 1.5.9 — 2026-08-31

### Added
- **Top Movers** — `sensor.portfolio_top_movers` ranks open holdings by day change %.
  - State: symbol with the largest absolute day move
  - Attributes: `movers`, `symbols`, `day_change_pcts`, `top_gainer`, `top_loser`
- Dashboard examples: `dashboards/top_movers.yaml` (ApexCharts) and
  `dashboards/top_movers_button_card.yaml` (exact bar styling)

### Fixed
- **Day change vs Yahoo/broker** — `day_change` / `day_change_pct` no longer use
  `meta.chartPreviousClose` (that field is the close *before the chart range*,
  e.g. ~1 year ago when `range=1y`). Previous session close is taken from the
  daily series (`closes[-2]`), then `regularMarketPreviousClose` /
  `previousClose`, and only then `chartPreviousClose` as a last resort.
  Fixes `sensor.portfolio_day_change`, holdings table day columns, top movers,
  and per-symbol day attributes so they match broker session P/L.

### Notes
- Non-breaking for config/entities: additive Top Movers sensor + corrected
  day-change math only.

## 1.5.8.3 — 2026-08-31

### Changed
- Version bump to **1.5.8.3** for HACS default-store revalidation after
  repository description/topics and green hassfest + HACS Action runs.
- `manifest.json` keys remain hassfest-sorted (`domain`, `name`, then A–Z).

## 1.5.8.2 — 2026-08-31

### Fixed
Carries forward the audit fixes from 1.5.8.1 as a clean, standalone
tagged release (rather than a note appended to a prior version):
- `manifest.json`: `"dependencies": ["http"]` present — required because
  `__init__.py` calls `hass.http.async_register_static_paths(...)`
  unconditionally to serve the bundled Lovelace card.
- `services.yaml`: `step: 0.001` on the `shares` field for both
  `buy_shares` and `sell_shares` (was `0.0001`, which is below Home
  Assistant's actual `NumberSelectorConfig` floor of `vol.Range(min=1e-3)`
  and fails schema validation).
- `.github/workflows/validate.yaml` present (hassfest + HACS validation).

### Verified
Full audit re-run clean: `py_compile` + `pyflakes` across all 14 Python
files, `manifest.json`/`hacs.json`/`strings.json`/translations all valid
JSON, all 19 dashboard YAML files valid, `retire.py` math re-checked
standalone. Add/remove/re-add holding behavior re-confirmed via a
standalone simulation of the actual `add_holding`/`_save_holdings`/
`remove_holding` logic — no duplicate/ghost entries, case-insensitive
de-dupe works, and `sensor.portfolio_total_value` /
`sensor.portfolio_total_invested` recompute correctly from the live
holdings dict in every scenario tested.

## 1.5.8.1 — 2026-08-30

### Fixed
- **Event triggers options flow** — missing imports for `CONF_EVENTS_ENABLED` /
  milestone & volatility settings caused "Unknown error occurred" when opening
  Configure → Event triggers. Imports restored.

## 1.5.8 — 2026-08-30

### Added
- **Event triggers** (Configure → Event triggers)
  - `portfolio_tracker_milestone` — fires when portfolio total value crosses
    multiples of a configurable step (default 10,000)
  - `portfolio_tracker_volatility_alert` — fires when portfolio day % or any
    holding's day % exceeds a threshold (default 5%)
- Debounced so the same alert is not repeated every poll
- Automations: use trigger type **Event** with those event types

## 1.5.7.2 — 2026-08-30

### Fixed
- **Re-add same symbol after delete** — Add no longer fails with "already exists"
  for residual keys; it **replaces** the position (shares + cost basis).
- **Cost basis entry** — Add form accepts **average cost per share** (preferred)
  and computes total invested as `shares × cost_per_share`, or total paid.
- Case-insensitive symbol matching when replacing holdings.
- `sensor.portfolio_total_invested` exposes `by_symbol` attribute for verification.
- Coordinator always reads **live** holdings keys after options changes.

## 1.5.7.1 — 2026-08-30

### Changed
- Version bump to **1.5.7.1** (aligned across `manifest.json`, docs, and package).

## 1.5.7 — 2026-08-30

### Fixed
- Total invested stale after remove + re-add — sensors read live config entry.
- `state_class` for total invested changed from `total` to `measurement`.
- Buy/sell services refresh the coordinator after updating options.
- Holdings normalized on save.

## 1.5.6 — 2026-08-30

### Fixed
- Version alignment to **1.5.6**.
- Stale holding sensors removed from entity registry when a symbol is deleted.

## 1.5.0 — 2026-08-29

### Added
- Retirement forecast plan and ApexCharts-ready sensors.

## 1.4.6
- Schedule presets + optional fixed snapshots

## 1.4.5.1
- Restored working sensors after import error
