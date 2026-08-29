# Changelog

## 1.2.0 — 2026-08-29

### Added
- HACS / HA brand icons (`icon.png`, `brand/icon.png`, `brand/logo.png`)
- Diagnostics support (Settings → Devices → Download diagnostics)
- `sensor.portfolio_holdings_count`
- Position `allocation_pct` attribute
- Yahoo enrichment: company name, exchange, 52-week high/low, volume, market state
- Configure → **Update intervals** (open-market vs closed-market poll cadence)
- Holdings table rows include `name` and `allocation_pct`

### Fixed
- Stable entity IDs (`sensor.nvda_price`, `sensor.portfolio_total_value`, …)
- Market session open detection for dashboard templates (`open` / `closed`)

### HACS updates
HACS detects a new version when `manifest.json` → `version` increases on the
default branch or a GitHub Release is published. After updating, **restart
Home Assistant**.

## 1.1.1
- Force stable entity_id values

## 1.1.0
- Initial public packaging for HACS custom repository
