# Changelog

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
