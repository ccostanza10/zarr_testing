import glob
import numpy as np
import xarray as xr
import zarr

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
# time is already absolute, so drop it. time_offset decodes to the same values
# as time and only references base_time, so it's redundant too.
common.discard("base_time")
common.discard("time_offset")
common = sorted(common)
print(f"Keeping {len(common)} variables common to all files")

# Height gates jitter by a few cm between files; treat the first file's
# heights as canonical so every day lines up on the same height axis.
with xr.open_dataset(files[0], decode_timedelta=True) as ds0:
    height = ds0["height"].load()

# Source data variables flag missing data with missing_value (-9999). xarray
# decodes those to NaN and doesn't carry the attribute through concat, so
# capture it here and write it back as both _FillValue and missing_value.
with xr.open_dataset(files[0], decode_cf=False) as raw0:
    missing = {v: raw0[v].attrs["missing_value"]
               for v in common if "missing_value" in raw0[v].attrs}

datasets = []
for f in files:
    with xr.open_dataset(f, decode_timedelta=True) as ds:
        ds = ds[common].load()
    # time_bounds holds epoch seconds but has no units attribute, so CF decoding
    # applies time's "seconds since <midnight>" units and lands ~53 years late.
    # Rebuild it from the raw epoch values instead.
    with xr.open_dataset(f, decode_times=False) as raw:
        bounds = raw["time_bounds"].values.astype("int64").astype("datetime64[s]")
    ds["time_bounds"] = (ds["time_bounds"].dims, bounds.astype("datetime64[ns]"))
    max_diff = float(np.abs(ds["height"].values - height.values).max())
    if max_diff > 1.0:
        raise ValueError(f"{f}: height differs from canonical by {max_diff:.3f} m")
    datasets.append(ds.assign_coords(height=height))

combined = xr.concat(datasets, dim="time", data_vars="minimal", coords="minimal",
                     compat="override", join="exact")
combined = combined.sortby("time")
combined.attrs.pop("history", None)
combined.attrs.pop("command_line", None)
combined.attrs["Conventions"] = "CF-1.8 ARM-1.1"

encoding = {
    name: {"chunks": (time_chunk,) + combined[name].shape[1:]}
    for name in combined.variables
    if combined[name].dims and combined[name].dims[0] == "time"
}

# CF time metadata: one epoch reference for all time variables.
combined["time"].attrs.update(long_name="Time (start of 30-minute averaging window)",
                               standard_name="time", axis="T")
for name in ("time", "time_bounds"):
    encoding[name].update(units="seconds since 1970-01-01 00:00:00 UTC",
                          calendar="standard", dtype="int64")
for name, mv in missing.items():
    encoding.setdefault(name, {}).update(_FillValue=mv, missing_value=mv)
combined.to_zarr(out_path, mode="w", consolidated=False, encoding=encoding)

# Per CF 7.1, bounds inherit units/calendar from their parent coordinate, so
# drop the copies xarray writes onto time_bounds.
tb_attrs = zarr.open_array(f"{out_path}/time_bounds", mode="r+").attrs
for key in ("units", "calendar"):
    tb_attrs.pop(key, None)

print(f"\nWrote {out_path}")
print(f"Combined time length: {combined.sizes['time']}")

check = xr.open_zarr(out_path, consolidated=False)
print(check)
print(f"Time range: {check.time.values[0]} -> {check.time.values[-1]}")
