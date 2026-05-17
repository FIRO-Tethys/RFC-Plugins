# RFC-Plugins

[Intake](https://intake.readthedocs.io/) drivers for [TethysDash](https://github.com/Aquaveo/tethysapp-tethys_dash), organized into six modules that can be installed independently:

- **River Observations and Forecasts** — NWPS gauge streamflow, HEFS / MMEFS plots, flood outlooks (active: `rfc_river_streamflow`)
- **Weather Observations and Forecasts** — QPE/QPF, NDFD, MRMS, freezing & thawing degree day maps and time series (active: `rfc_precip_viewer`, `rfc_ndfd_viewer`, `rfc_mrms_viewer`, `rfc_fdd_map`, `rfc_fdd_timeseries`, `rfc_tdd_map`, `rfc_tdd_timeseries`)
- **Water Supply** — NRCS SWE, snow depth, Bradley Lake (no active drivers yet)
- **Climate and History** — CPC outlooks, drought (active: `rfc_cpc_outlooks`)
- **Seasonal Interest** — breakup temperature outlooks, ice thickness, water temperature (active: `aprfc_breakup_temperature_outlooks`)
- **Additional Info** — Hawaii RFC forecasts and other catch-all drivers (no active drivers yet)

## Install

Pick the modules you need. Each extra installs only that module's dependencies — though today every active driver runs on the shared core (`intake`, `httpx`, `requests`), so the extras are mostly forward-compatibility seams for future module-specific deps.

```bash
# Everything
pip install 'git+ssh://git@github.com/FIRO-Tethys/RFC-Plugins.git#egg=rfc-plugins[all]'

# Just weather
pip install 'git+ssh://git@github.com/FIRO-Tethys/RFC-Plugins.git#egg=rfc-plugins[weather]'

# Subset (combine extras as needed)
pip install 'git+ssh://git@github.com/FIRO-Tethys/RFC-Plugins.git#egg=rfc-plugins[river,weather,climate]'
```

Available extras: `river`, `weather`, `water_supply`, `climate`, `seasonal`, `additional_info`, `all`.

> TODO: once published to PyPI, this simplifies to `pip install 'rfc-plugins[<extra>]'`.

## How it works

Drivers are exposed to TethysDash via Intake's `intake.drivers` entry-point group. After `pip install`, Intake discovers every driver name regardless of which extras you installed — but each driver calls its module's `validate_dependencies()` on instantiation. If you installed `rfc-plugins[river]` and then try to instantiate a weather driver whose extras you skipped, you'll get a clean error pointing at the right install command, not a raw `ModuleNotFoundError`.

## Development

```bash
git clone git@github.com:FIRO-Tethys/RFC-Plugins.git
cd RFC-Plugins
python -m venv .venv && source .venv/bin/activate
pip install -e '.[all]'
```

## Adding a new driver

1. Drop the driver class into the appropriate `rfc_plugins/<module>/<file>.py`. Use one of the existing drivers (`rfc_plugins/weather/ndfd.py` is a good template) as a reference.
2. Add `from rfc_plugins.<module> import validate_dependencies` + `validate_dependencies()` as the first two lines of `__init__`.
3. Register the driver in `[project.entry-points."intake.drivers"]` in `pyproject.toml`.
4. Reinstall (`pip install -e .`) so the new entry point is registered.

If the driver needs a new third-party package, add it to the matching extra in `[project.optional-dependencies]` and to the module's `validate_dependencies()` `require([...], extra=...)` call.
