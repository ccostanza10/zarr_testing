# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a collection of standalone Python scripts for working with Zarr data stores, focused on atmospheric/meteorological data workflows. There is no build system, test suite, or package structure — each script is run independently.

## Running Scripts

```bash
python <script_name>.py
```

All scripts assume data lives under `/Users/costanza/data/` and write outputs there.

## Key Dependencies

- **zarr >= 3.0** — reading/writing Zarr stores (GDEX/OSDF data uses Zarr v3 format)
- **xarray** — opening Zarr as xarray Datasets (`xr.open_zarr`)
- **fsspec** — remote data access (HTTP/OSDF URLs via `fsspec.get_mapper`)
- **pandas** — CSV ingestion for radiosonde data
- **matplotlib** — plotting (wind profiles, skew-T diagrams)
- **metpy** — meteorological calculations and SkewT plots (used in `zarr_skewt.py`)
- **numpy** — array operations

## Script Purposes

| Script | What it does |
|---|---|
| `create_zarr.py` | Creates a synthetic xarray Dataset and saves/reads it as Zarr |
| `gdex_open.py` | Copies a remote Zarr v3 store (OSDF/GDEX) to local disk via xarray |
| `make_zarr.py` | Reads radiosonde CSV files and writes each as a separate Zarr group (v2) |
| `make_zarr_2d.py` | Combines all sounding groups into a single 2D (sounding x level) Zarr store |
| `open_zarr_make_wp.py` | Plots 24-hour wind barb profiles from the remote 449 MHz profiler and/or local WindCube VAD stores: `python open_zarr_make_wp.py YYYYMMDD [-s profiler\|windcube\|both] [-e N]` |
| `zarr_skewt.py` | Plots a skew-T from the 2D store for a given date: `python zarr_skewt.py YYYYMMDD [-n N]` |
| `combine_nc_to_zarr.py` | Combines per-flight C-130 CAESAR NetCDF files (`FF*/RF*/TF*.PNI.nc`) into a single Zarr store along `Time` |
| `combine_VAD_to_zarr.py` | Combines daily M2HATS WindCube 30-min VAD files (`30min_winds_*.nc`) into `m2hats_windcube_vad30min_combined.zarr` along `time` |

## Patterns

- Remote Zarr access uses `fsspec.get_mapper(url)` passed to `xr.open_zarr()`.
- The original per-sounding Zarr groups (`make_zarr.py`) use Zarr v2 format; open with `zarr_format=2, consolidated=False`.
- The combined 2D store (`make_zarr_2d.py`) has dims `(sounding, level)` with `launch_time` and `sounding_id` as coordinates. Shorter soundings are NaN-padded.
- GDEX/OSDF remote data is Zarr v3 format (`zarr.json`, not `.zmetadata`); requires zarr >= 3.0.
- When writing Zarr v3 locally, use `consolidated=False` to avoid non-standard consolidated metadata warnings.
- Hardcoded paths are common; update them when adapting scripts.

### `combine_nc_to_zarr.py` strategy

The C-130 flight NetCDF files have schema drift across flights (variable counts range from ~300 to 716; some variables share a name but use different dim names like `Vector128` vs `F2DC003_P2D`; Time lengths are non-uniform). The script handles this by:

1. **Computing the intersection of variable names** across all files and keeping only those (287 vars for the current data set).
2. **Treating the first file's dim names as canonical** and renaming mismatched dims in later files (e.g. `F2DC003_P2D` → `Vector128`) so xarray's "different dimension names" check passes.
3. **Writing the first file with an explicit `chunks=(time_chunk, ...)` encoding along `Time`** so every Time-dim variable has a uniform on-disk chunk grid regardless of any single file's length.
4. **Appending each subsequent file with `align_chunks=True`** so xarray re-tiles each file's dask chunks onto the zarr grid before writing (avoids the "incompatible dask chunks" / "would overlap multiple Dask chunks" errors that come from trying to concat 16 differently-sized files in one shot).

### `combine_VAD_to_zarr.py` strategy

The 64 daily VAD files (2023-07-23 → 2023-09-24, 48 profiles/day, 100 height gates) use the ARM `base_time`/`time_offset`/`time` layout, where each file's times are relative to that day's midnight. The script:

1. **Drops `base_time` and `time_offset`** — both only make sense per file; `time_offset` decodes to the same values as `time`.
2. **Uses the first file's `height` as canonical** — gates jitter up to ~0.22 m between days; the script errors if any day differs by > 1 m.
3. **Rebuilds `time_bounds` from raw epoch seconds.** In the source files `time_bounds` holds Unix epoch seconds but has no `units` attribute, so CF decoding inherits `time`'s `seconds since <midnight>` units and lands ~53 years late (e.g. 2077). Always open source files with `decode_times=False` to read `time_bounds` correctly.
4. **Writes CF time metadata:** `time` and `time_bounds` are int64 `seconds since 1970-01-01 00:00:00 UTC`, `calendar="standard"`. `time` gets `standard_name="time"`, `axis="T"`, and `long_name="Time (start of 30-minute averaging window)"`. After writing, `units`/`calendar` are removed from `time_bounds` with `zarr` so it inherits them from `time` (CF §7.1).
5. **Global attrs:** drops per-file `history`/`command_line`; sets `Conventions="CF-1.8 ARM-1.1"`.

Known gap: the source data variables carry `missing_value = -9999`; xarray decodes those to NaN and the store uses NaN as its fill value, so the -9999 sentinel is not recorded in the store's metadata (values are otherwise identical).

## Known Issues

- **OSDF server instability** — The remote OSDF/GDEX server (used by `open_zarr_make_wp.py` and `gdex_open.py`) experiences intermittent errors (HTTP 500, dropped connections). If these scripts fail, check whether it's a server-side issue before modifying code. The `open_zarr_make_wp.py` script intentionally uses `consolidated=True` despite the store being Zarr v3; do not change this to work around server errors.
