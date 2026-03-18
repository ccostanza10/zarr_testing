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
| `open_zarr_make_wp.py` | Opens a remote Zarr wind profiler dataset and plots a 24-hour wind barb profile |
| `zarr_skewt.py` | Plots a skew-T from the 2D store for a given date: `python zarr_skewt.py YYYYMMDD [-n N]` |

## Patterns

- Remote Zarr access uses `fsspec.get_mapper(url)` passed to `xr.open_zarr()`.
- The original per-sounding Zarr groups (`make_zarr.py`) use Zarr v2 format; open with `zarr_format=2, consolidated=False`.
- The combined 2D store (`make_zarr_2d.py`) has dims `(sounding, level)` with `launch_time` and `sounding_id` as coordinates. Shorter soundings are NaN-padded.
- GDEX/OSDF remote data is Zarr v3 format (`zarr.json`, not `.zmetadata`); requires zarr >= 3.0.
- When writing Zarr v3 locally, use `consolidated=False` to avoid non-standard consolidated metadata warnings.
- Hardcoded paths are common; update them when adapting scripts.
