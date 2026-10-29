import argparse
import glob
import sys
import numpy as np
import xarray as xr
import zarr

# Checks a store written by combine_VAD_to_zarr.py against its source files,
# comparing raw on-disk values (so -9999 markers are checked exactly).
data_dir = "/Users/costanza/data"

# Must match the input patterns and output stores in combine_VAD_to_zarr.py.
DATASETS = {
    "30min": ("30min*.nc", "m2hats_windcube_vad30min_combined.zarr"),
    "scan": ("VAD_*.nc", "m2hats_windcube_vad_combined.zarr"),
}

parser = argparse.ArgumentParser(description="Verify a combined VAD Zarr store against its source NetCDF files")
parser.add_argument("-d", "--dataset", choices=DATASETS, default="scan",
                    help="Which store to verify (default: scan)")
args = parser.parse_args()

pattern, store_name = DATASETS[args.dataset]
store = f"{data_dir}/{store_name}"
files = sorted(glob.glob(f"{data_dir}/{pattern}"))

g = zarr.open_group(store, mode="r")
z = {name: arr[...] for name, arr in g.arrays()}  # raw on-disk values
print(f"{len(files)} source files; store arrays: {sorted(z)}")

dropped = {"base_time", "time_offset"}
problems = []
counts = {}
start = 0
for f in files:
    r = xr.open_dataset(f, decode_cf=False)
    n = r.sizes["time"]
    sl = slice(start, start + n)
    tag = f.split("/")[-1]

    # Variables: everything except base_time/time_offset should be in the store.
    missing_vars = set(r.variables) - dropped - set(z)
    if missing_vars:
        problems.append(f"{tag}: variables not in store {sorted(missing_vars)}")

    # time: source is seconds since that day's midnight -> epoch, floored.
    midnight = np.datetime64(r["time"].attrs["units"].split("since ")[1].replace(" UTC", ""), "s")
    epoch = r["time"].values + midnight.astype("int64")
    if not np.array_equal(np.floor(epoch).astype("int64"), z["time"][sl]):
        problems.append(f"{tag}: time mismatch")
    # base_time + time_offset must give the same instants (so dropping them loses nothing).
    if not np.allclose(int(r["base_time"]) + r["time_offset"].values, epoch, atol=1e-3):
        problems.append(f"{tag}: base_time+time_offset disagrees with time")
    if not np.array_equal(np.floor(r["time_bounds"].values).astype("int64"), z["time_bounds"][sl]):
        problems.append(f"{tag}: time_bounds mismatch")

    hd = np.abs(r["height"].values - z["height"]).max()
    if hd > 1.0:
        problems.append(f"{tag}: height differs by {hd:.3f} m")

    for v in r.data_vars:
        if v in dropped or v == "time_bounds":
            continue
        src = r[v].values
        dst = z[v] if r[v].ndim == 0 else z[v][sl]
        if src.dtype != dst.dtype:
            problems.append(f"{tag}: {v} dtype {src.dtype} -> {dst.dtype}")
        if not np.array_equal(src, dst, equal_nan=src.dtype.kind == "f"):
            nbad = int((src != dst).sum())
            problems.append(f"{tag}: {v} values differ ({nbad} elements)")
        if r[v].ndim:
            counts.setdefault(v, [0, 0])
            counts[v][0] += int((src == -9999).sum())
    r.close()
    start += n

if start != z["time"].size:
    problems.append(f"time length: sources {start} vs store {z['time'].size}")
for v in counts:
    counts[v][1] = int((z[v] == -9999).sum())
    if counts[v][0] != counts[v][1]:
        problems.append(f"{v}: -9999 count {counts[v][0]} in sources vs {counts[v][1]} in store")

print(f"Total profiles: sources {start}, store {z['time'].size}")
print("-9999 counts (sources / store):")
for v, (a, b) in sorted(counts.items()):
    print(f"  {v:16s} {a:>9d} / {b:>9d}")
print("\nPROBLEMS:" if problems else "\nAll data match.")
for p in problems:
    print("  " + p)
sys.exit(1 if problems else 0)
