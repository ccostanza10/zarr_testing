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
| `make_zarr.py` | Reads radiosonde CSV files and writes each as a separate Zarr group |
| `open_zarr_make_wp.py` | Opens a remote Zarr wind profiler dataset and plots a 24-hour wind barb profile |
| `zarr_skewt.py` | Opens a local Zarr radiosonde group and produces a skew-T log-P diagram with MetPy |

## Patterns

- Remote Zarr access uses `fsspec.get_mapper(url)` passed to `xr.open_zarr()`.
- Multi-sounding Zarr stores use Zarr groups (one group per sounding), opened with `consolidated=False`.
- GDEX/OSDF remote data is Zarr v3 format (`zarr.json`, not `.zmetadata`); requires zarr >= 3.0.
- When writing Zarr v3 locally, use `consolidated=False` to avoid non-standard consolidated metadata warnings.
- Hardcoded paths are common; update them when adapting scripts.
