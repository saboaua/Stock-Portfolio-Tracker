# Changelog

## 1.4.5 — 2026-08-29

### Fixed
- **$0.00 / empty portfolio data** — more reliable Yahoo chart fetch (browser User-Agent, 5d/1mo fallback, no whole-update failure on single-symbol errors)
- Holding sensors stay available when holdings exist (show last data instead of blanking the dashboard)
- FX rate never applied as 0
- HACS detail page content — README synced with modern `info.md` (HACS uses README when `render_readme: true`)

### Notes
- Multi-portfolio support planned for a following release

## 1.4.4 — 2026-08-29

### Added
- **Manual refresh** — `button.portfolio_refresh` + `portfolio_tracker.refresh` service
- **Last update** — `sensor.portfolio_last_update` (timestamp of last successful poll)
- **Error notifications** — persistent notification after repeated Yahoo failures; cleared on recovery
- Modern HACS `info.md` with logo and feature matrix

## 1.4.3 — 2026-08-29

### Added
- Wide **logo** on HACS info / README
- Sparkline history on price data and holdings table rows
- Native card **charts** view — ticker grid with price, % change, sparkline
- Native card **holdings** view — shares, avg cost, invested, market value, gain
- Card tabs: Summary / Charts / Holdings; range 1W / 1M
- Crypto guidance in Configure (Yahoo symbols e.g. BTC-USD)

### Fixed (from 1.4.1 / 1.4.2)
- Config flow load failure from invalid `SelectOptionDict(icon=...)`
- Holdings table sensor unavailable (no longer inherits monetary base class)

## 1.4.2
- Holdings table availability fix

## 1.4.1
- Config flow 400 Bad Request fix

## 1.4.0
- Base currency FX, dividend calendar, menu selector, native card foundation

## 1.3.0
- Realized P/L, trade log, brand icons

## 1.2.0
- Diagnostics, holdings count, allocation %, update intervals
