# Changelog

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

### Audit notes (packaging this release)
Two regressions were found and corrected while auditing this exact
package — both are re-fixes of issues already resolved in 1.5.7, which
had been reverted somewhere in the 1.5.7.1–1.5.8 chain:
- `manifest.json` was missing `"dependencies": ["http"]` again. The code
  still calls `hass.http.async_register_static_paths(...)` unconditionally
  in `__init__.py` to serve the bundled Lovelace card, so this is
  required — confirmed by re-checking the actual usage, not assumed.
- `services.yaml`'s `shares` field `step` was back to `0.0001` on both
  `buy_shares` and `sell_shares`. Re-verified against Home Assistant's
  actual `NumberSelectorConfig` schema (`vol.Range(min=1e-3)`): 0.001 is
  the hard floor, 0.0001 fails regardless of exact error wording.
- `.github/workflows/validate.yaml` was absent from this zip (as it has
  been from every zip export so far) — re-added.

Also concretely verified (not just read) via a standalone simulation
mirroring `add_holding`/`_save_holdings`/`remove_holding` exactly: add →
remove → re-add the same symbol produces no duplicate/ghost entries, case
mismatches (`xlk` vs `XLK`) correctly de-dupe to one entry, and both
`sensor.portfolio_total_value` and `sensor.portfolio_total_invested`
recompute from the live post-change holdings dict with the exact expected
totals in every scenario tested.

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
  Entering only the share price as "invested" was understating cost basis
  (e.g. XLK showing +10,000% gain).
- Case-insensitive symbol matching when replacing holdings.
- `sensor.portfolio_total_invested` exposes `by_symbol` attribute for verification.
- Coordinator always reads **live** holdings keys after options changes.

## 1.5.7.1 — 2026-08-30

### Changed
- Version bump to **1.5.7.1** (aligned across `manifest.json`, docs, and package).
- Includes 1.5.7 fixes: live config-entry holdings for total invested, measurement state class, buy/sell refresh, normalized holdings on save.

## 1.5.7 — 2026-08-30

### Fixed
- **Total invested stale after remove + re-add** — sensors now always read
  holdings from the *live* config entry (not the setup-time snapshot), so
  `sensor.portfolio_total_invested` / gain / counts update when symbols are
  added, removed, or edited.
- **`state_class`** for total invested changed from `total` to `measurement`
  (cost basis goes up and down; `total` was inappropriate and could surface
  confusing values).
- Buy/sell **services** now refresh the coordinator after updating options so
  UI totals rewrite immediately without waiting for the next poll.
- Holdings are **normalized on save** (upper-case symbols, numeric shares /
  invested, drop empty positions).

## 1.5.6 — 2026-08-30

### Fixed
- **Version alignment** — every release reference now points at **1.5.6**
  - `manifest.json` (source of truth; `const.VERSION` reads it)
  - `info.md` version line
  - Changelog entry for this release
- Prior drift: docs said `1.5.4` while `manifest.json` was `1.5.5`

### Included from 1.5.5
- Stale holding sensors removed from the entity registry when a symbol is
  deleted via Configure (options reload + differential cleanup)

## 1.5.4 — 2026-08-30

### HACS store readiness
Working through the HACS default-store submission checklist:
- `hacs.json` present at repo root (was already there — verified valid).
- `manifest.json` confirmed correct: `codeowners: ["@saboaua"]` and
  `iot_class: "cloud_polling"` (both were already set correctly).
- Added `.github/workflows/validate.yaml` running `hassfest` and the
  `hacs/action` validator on every push/PR and daily on a schedule.
  **Note:** I validated this workflow's own YAML syntax and independently
  simulated the manifest/hacs.json schema checks these actions run
  offline (all pass — see "Verified before packaging" below), but I
  cannot execute GitHub Actions myself from here. You'll need to push
  this and confirm the green checkmark on your actual repo.
- **Not done here, needs you:** tagging a GitHub Release, and opening a
  PR to add this repo to `hacs/default`. Both require write access to
  GitHub that isn't available in this environment. See the README's
  "Publishing to HACS" section for exact steps.
- **Flagging a conflict:** the request asked to both bump this release to
  `1.5.4` and tag it `v1.0.0`. Those disagree — HACS/AwesomeVersion
  compares the manifest's `version` against the release tag, and this
  project already has real version history through `1.5.3.1`. Shipped
  `manifest.json` as `1.5.4` to match the actual version bump; recommend
  tagging the release `v1.5.4` to match rather than `v1.0.0`, unless the
  intent is to deliberately reset public versioning for the HACS debut —
  in which case `manifest.json` should say `1.0.0` too, not `1.5.4`.

### Branding & documentation
- Replaced `logo.png` (root and `brand/`) with the new wordmark.
- Cropped the new logo's square icon mark into a proper `icon.png`
  (512×512) instead of stretching the wide banner into a square — a
  distorted stretch would have looked wrong in HA's integration list.
- Added all 10 UI walkthrough screenshots to `brand/`: `integration_setup`,
  `integration_screen`, `manage_portfolio_menu`, `add_holding`,
  `buy_stock`, `sell_stock`, `edit_stock`, `remove_stock`,
  `component_settings`, `retirement_setting`.
- Replaced `README.md` with the provided version. Fixed one bug in it
  while copying: the file was missing its closing ` ``` ` fence at the
  very end, which would leave the last code block unterminated on GitHub.
- Synced `info.md`'s version reference to `1.5.4`.

### Roadmap (documented, not yet implemented)
Added a "Roadmap" section (see README) for the planned "Income Insights &
Event Automations" release: `sensor.portfolio_tracker_projected_dividend_income`,
`portfolio_tracker_milestone` / `portfolio_tracker_volatility_alert` HA
events, LTS/`MONETARY` compliance pass, and dividend yield replacing the
holdings table's `--` placeholders. These are documented as planned, not
built into this release — shipping them without full testing would
conflict with this release's "no broken code" requirement, and each is
substantial enough (especially the new HA events) to warrant its own
audit pass rather than being folded in as a side effect of a
branding/HACS-readiness release.

### Verified before packaging
`py_compile` and `pyflakes` clean across all 13 Python files (unchanged
from 1.5.3.1 — this release touched no application logic, only
`manifest.json`'s version and documentation/branding assets). Manifest
schema re-validated against hassfest's actual required-key list and
`iot_class` enum. All dashboard YAML re-validated. New
`.github/workflows/validate.yaml` YAML-syntax-checked. Confirmed
`brand/` contains exactly the 11 images referenced by the new README
(10 screenshots + logo) with no dangling references left unresolved.

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
