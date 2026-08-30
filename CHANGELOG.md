# Changelog

## 1.5.3.1 — 2026-08-30

### Fixed
- **Device metadata was drifting across four separate hardcoded copies.**
  `sensor.py`, `binary_sensor.py`, `button.py`, and `calendar.py` each
  built their own `DeviceInfo` block instead of sharing one. They'd gone
  out of sync: `binary_sensor.py` had `manufacturer`/`model` swapped
  relative to the other three, and hardcoded `sw_version="1.2.0"` as a
  literal string that never tracked the real integration version at all.
  This is why the device page's "Firmware" field could show a stale or
  wrong version depending on which entity's metadata Home Assistant
  happened to read. Consolidated into a single `device.py` module
  (`device_info(entry)`) that every platform now imports and uses —
  eliminates this entire class of drift going forward.
- **`VERSION` in `const.py` had also drifted from `manifest.json`**
  (`1.5.1` vs `1.5.3`) after the previous release only bumped one of the
  two places version was hardcoded. `const.py` now reads `VERSION`
  directly from `manifest.json` at import time — there is only one place
  to update per release, and the device page's firmware field can never
  disagree with what HACS reports as installed again.
- **Retirement chart still showed "N/A" in the header** even after the
  1.5.1 sensor fix, because the bundled
  `dashboards/retire_forecast_apexcharts.yaml` still used `extend_to: now`
  for the Actual series. With `graph_span: 11y`, ApexCharts Card queries
  Home Assistant's long-term statistics rather than raw state history for
  that calculation — statistics that don't exist yet for a freshly
  created/renamed entity. Replaced with a `data_generator` that reads the
  entity's live state directly, bypassing statistics entirely. Also added
  a full grid (x + y gridlines) to the chart for readability, and a
  header comment explaining the legacy-entity-prefix scenario for anyone
  upgrading from a pre-2.0-style install.

### Audited (Home Assistant forward-compatibility)
Checked the full codebase for deprecated/at-risk patterns: no
`hass.helpers.*` dotted access, no legacy `async_setup_platform`, no
`_attr_unit_of_measurement`/raw `unit_of_measurement` setters (correctly
uses `native_unit_of_measurement` throughout), no blocking calls
(`time.sleep`, `requests`, `urllib`) anywhere in the async code paths, and
no synchronous file I/O outside the one intentional one-time
`manifest.json` read in `const.py`. All entities across all four
platforms confirmed to share identical device `identifiers`, so they
correctly group into Home Assistant's automatic per-domain sections
(Sensors / Binary sensors / Controls / Calendar) on one device page.

One deliberate thing left unchanged: several entities still force a fixed
`self.entity_id` (e.g. `sensor.portfolio_total_value`) rather than letting
Home Assistant's entity registry generate one from `has_entity_name` +
device name. This is intentionally *not* being changed here — doing so
would rename entities yet again for anyone upgrading, exactly the
disruption already seen with the legacy `portfolio_tracker_`-prefixed
entities from older installs. It's noted here as a known tradeoff rather
than an oversight.

### Verified before packaging
`py_compile` and `pyflakes` clean across all 13 Python files; `retire.py`
math re-verified with a standalone unit test; `const.VERSION` verified at
runtime to equal `manifest.json`'s version with zero possible drift;
`manifest.json`, `hacs.json`, `strings.json`, `translations/en.json`
JSON-validated; all dashboard YAML re-validated after edits.

## 1.5.3 — 2026-08-29

Version bump only — no functional code changes were included in this
release despite the version number implying otherwise. (Documented here
for the historical record; superseded by 1.5.3.1 above.)

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
