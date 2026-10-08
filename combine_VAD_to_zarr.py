import glob
import numpy as np
import xarray as xr

data_dir = "/Users/costanza/data"
out_path = f"{data_dir}/m2hats_windcube_vad30min_combined.zarr"
time_chunk = 48 * 7  # one week of 30-min profiles per chunk

files = sorted(glob.glob(f"{data_dir}/30min*.nc"))
print(f"Found {len(files)} files")

# Variables present in every file (intersection on name).
common = None
for f in files:
    with xr.open_dataset(f, decode_timedelta=True) as ds:
        names = set(ds.variables.keys())
        common = names if common is None else common & names
# base_time is a per-file scalar (that day's midnight) and can't be combined;
# time is already absolute, so drop it.
common.discard("base_time")
common = sorted(common)
print(f"Keeping {len(common)} variables common to all files")

# Height gates jitter by a few cm between files; treat the first file's
# heights as canonical so every day lines up on the same height axis.
with xr.open_dataset(files[0], decode_timedelta=True) as ds0:
    height = ds0["height"].load()

datasets = []
for f in files:
    with xr.open_dataset(f, decode_timedelta=True) as ds:
        ds = ds[common].load()
    max_diff = float(np.abs(ds["height"].values - height.values).max())
    if max_diff > 1.0:
        raise ValueError(f"{f}: height differs from canonical by {max_diff:.3f} m")
    datasets.append(ds.assign_coords(height=height))

combined = xr.concat(datasets, dim="time", data_vars="minimal", coords="minimal",
                     compat="override", join="exact")
combined = combined.sortby("time")
combined.attrs.pop("history", None)
combined.attrs.pop("command_line", None)

encoding = {
    name: {"chunks": (time_chunk,) + combined[name].shape[1:]}
    for name in combined.variables
    if combined[name].dims and combined[name].dims[0] == "time"
}
combined.to_zarr(out_path, mode="w", consolidated=False, encoding=encoding)

print(f"\nWrote {out_path}")
print(f"Combined time length: {combined.sizes['time']}")

check = xr.open_zarr(out_path, consolidated=False)
print(check)
print(f"Time range: {check.time.values[0]} -> {check.time.values[-1]}")
