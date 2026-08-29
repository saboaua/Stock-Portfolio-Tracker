# Changelog

## 1.5.0 — 2026-08-29

### Added
- **Retirement forecast plan** (Configure → Retirement forecast plan)
  - Horizon 4–10 years, baseline, start year, annual contribution
  - Scenarios: Conservative 8%, Moderate 10%, Nasdaq 15%, Aggressive 20%, Upside 22%
- Sensors: `sensor.portfolio_retire_plan`, `…_retire_progress`, `…_retire_target`
- Plan attributes include `*_points` arrays for **ApexCharts** `data_generator`
- Example dashboard: `dashboards/retire_forecast_apexcharts.yaml`

### Notes
- Forecasts are illustrative constant-growth paths — not financial advice
- Charting uses the community **ApexCharts Card** (install via HACS)

## 1.4.6
- Schedule presets + optional fixed snapshots

## 1.4.5.1
- Restored working sensors after import error
