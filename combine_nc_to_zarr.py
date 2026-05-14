import glob
import xarray as xr

data_dir = "/Users/costanza/data"
out_path = f"{data_dir}/c130_caesar_combined.zarr"
time_chunk = 20000

files = sorted(
    glob.glob(f"{data_dir}/FF*.PNI.nc")
    + glob.glob(f"{data_dir}/RF*.PNI.nc")
    + glob.glob(f"{data_dir}/TF*.PNI.nc")
)
print(f"Found {len(files)} files")

# Variables present in every file (intersection on name).
common = None
for f in files:
    with xr.open_dataset(f, decode_timedelta=True) as ds:
        names = set(ds.variables.keys())
        common = names if common is None else common & names
common = sorted(common)
print(f"Keeping {len(common)} variables common to all files")

# Use the first file's dim names per variable as canonical, so subsequent files
# with different dim *names* (e.g. F2DC003_P2D vs Vector128) get normalized.
with xr.open_dataset(files[0], decode_timedelta=True) as ds0:
    canonical_dims = {v: ds0[v].dims for v in common}


def normalize(ds):
    """Drop non-common vars and rename any non-canonical dims to match file 1."""
    ds = ds[common]
    rename = {}
    for v in common:
        for cur_dim, canon_dim in zip(ds[v].dims, canonical_dims[v]):
            if cur_dim != canon_dim and cur_dim not in rename:
                rename[cur_dim] = canon_dim
    if rename:
        ds = ds.rename(rename)
    return ds


total_time = 0
for i, f in enumerate(files):
    ds = xr.open_dataset(f, decode_timedelta=True, chunks={"Time": time_chunk})
    ds = normalize(ds)
    n = ds.sizes["Time"]
    print(f"[{i+1}/{len(files)}] {f.split('/')[-1]}  Time={n}")
    if i == 0:
        encoding = {}
        for name, var in ds.variables.items():
            if "Time" in var.dims:
                encoding[name] = {
                    "chunks": tuple(
                        time_chunk if d == "Time" else ds.sizes[d] for d in var.dims
                    )
                }
        ds.to_zarr(
            out_path,
            mode="w",
            consolidated=False,
            encoding=encoding,
            align_chunks=True,
        )
    else:
        ds.to_zarr(
            out_path,
            mode="a",
            append_dim="Time",
            consolidated=False,
            align_chunks=True,
        )
    total_time += n
    ds.close()

print(f"\nWrote {out_path}")
print(f"Combined Time length: {total_time}")

check = xr.open_zarr(out_path, consolidated=False)
print(f"Time range: {check.Time.values[0]} -> {check.Time.values[-1]}")
