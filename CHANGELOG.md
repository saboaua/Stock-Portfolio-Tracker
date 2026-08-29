# Changelog

## 1.4.0 — 2026-08-29

### Added
- Configure menu options with **Material icons** (list selector)
- **Base currency** + multi-currency FX (Yahoo pairs, totals in base ccy)
- **Dividend calendar** entity `calendar.portfolio_dividends`
- Native **Lovelace card** `portfolio-tracker-card.js`
- Documentation / issue links → https://github.com/saboaua/Stock-Portfolio-Tracker

### Changed
- Coordinator data shape includes `prices`, `fx_rates`, `dividends`
- Portfolio aggregate sensors report values in the configured base currency

## 1.3.0
- Realized P/L, trade log, 512px icons, polished README

## 1.2.0
- Diagnostics, holdings count, allocation %, update intervals

## 1.4.1 — 2026-08-29

### Fixed
- **Config flow could not be loaded (400)** — removed invalid `SelectOptionDict(..., icon=...)` which raised at import on many HA versions
- Configure menu still shows icons via emoji labels in a list selector
- Hardened Lovelace static-path registration for older HA builds
- Position allocation total uses FX-aware values

## 1.4.2 — 2026-08-29

### Fixed
- **`sensor.portfolio_holdings_table` unavailable** — table sensor no longer inherits the monetary base class (currency unit + MEASUREMENT on a timestamp state). Stays available even if the last Yahoo poll failed; builds rows safely from holdings + last prices.
