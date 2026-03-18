from datetime import datetime
import pandas as pd
import xarray as xr
import numpy as np
import os

source_zarr = "/Users/costanza/data/zarr/SWEX_sondes_HQ_SBFD"
output_zarr = "/Users/costanza/data/zarr/SWEX_sondes_HQ_SBFD_2d.zarr"

# Collect all sounding groups (skip non-group entries like zarr.json)
groups = sorted([d for d in os.listdir(source_zarr)
                 if not d.startswith('.') and d != 'zarr.json'])

# First pass: read all soundings to find max length and collect data
datasets = []
launch_times = []
core_vars = ['TEMP', 'DEWP', 'PRES', 'RH', 'WD', 'WS']

for g in groups:
    ds = xr.open_zarr(source_zarr, group=g, consolidated=False, zarr_format=2)
    # Drop any variables not in our core set (e.g. 'L', malformed CSV columns)
    ds = ds[core_vars]
    datasets.append(ds)

    # Parse launch time from filename: ...YYYYMMDD_HHMMSS
    parts = g.rsplit('_', 2)
    dt_str = parts[-2] + parts[-1]
    launch_times.append(datetime.strptime(dt_str, "%Y%m%d%H%M%S"))

max_levels = max(len(ds.TIME) for ds in datasets)
n_soundings = len(datasets)

print(f"Soundings: {n_soundings}, max levels: {max_levels}")

# Build 2D arrays (sounding x level), NaN-padded
data_vars = {}
for var in core_vars:
    arr = np.full((n_soundings, max_levels), np.nan)
    for i, ds in enumerate(datasets):
        raw = ds[var].values
        # Coerce any non-numeric strings (e.g. '---') to NaN
        vals = pd.to_numeric(raw, errors='coerce').astype(np.float64)
        arr[i, :len(vals)] = vals
    data_vars[var] = (["sounding", "level"], arr)

# TIME in seconds since launch for each sounding
time_seconds = np.full((n_soundings, max_levels), np.nan)
for i, ds in enumerate(datasets):
    n = len(ds.TIME)
    time_seconds[i, :n] = ds.TIME.values.astype(np.float64)
data_vars["TIME"] = (["sounding", "level"], time_seconds)

# Create the combined dataset
combined = xr.Dataset(
    data_vars=data_vars,
    coords={
        "launch_time": ("sounding", np.array(launch_times, dtype="datetime64[s]")),
        "level": np.arange(max_levels),
        "sounding_id": ("sounding", groups),
    },
)

combined.attrs["description"] = "SWEX HQ SBFD radiosondes combined into a 2D grid"
combined.attrs["dimensions"] = "sounding x level (time steps since launch)"

# Close source datasets
for ds in datasets:
    ds.close()

combined.to_zarr(output_zarr, mode="w", consolidated=False)
print(f"Written to {output_zarr}")
print(combined)
