# Changelog

## 1.5.1 — 2026-08-29

### Fixed
- **Retirement sensors were completely non-functional.** `sensor.py` never
  imported the eight `CONF_RETIRE_*` / `DEFAULT_RETIRE_*` constants that
  `_RetireMixin._retire_payload()` depends on, so every access of
  `sensor.portfolio_retire_plan`, `…_retire_progress`, and `…_retire_target`
  (state, `available`, and attributes) raised `NameError`. Home Assistant
  swallows that per-entity and shows it as unavailable/unknown, which is why
  the sensors appeared present but never reported a value. Fixed by adding
  the missing import in `sensor.py`; verified with a standalone unit test of
  `retire.py`'s math (unaffected — the bug was purely a wiring issue, not a
  calculation issue).
- Dividend calendar horizon: `coordinator.py` computed a 365-day `horizon`
  cutoff for upcoming dividends but never applied it, so a future dividend
  arbitrarily far out would not have been filtered out. Now enforced.

### Cleaned up
- Removed a handful of dead/unused local variables and imports flagged by
  static analysis (`__init__.py`, `retire.py`, `sensor.py`) — no behavior
  change, just less noise for anyone reading the code.

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
