import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

zarr_path = "/Users/costanza/data/c130_caesar_combined.zarr"
flight_date = "2024-03-16"

ds = xr.open_zarr(zarr_path, consolidated=False)

# Time isn't monotonic in the combined store (files were appended in alphabetical
# order, not chronological), so select via a boolean mask rather than .sel slicing.
time = ds["Time"].values
day_start = np.datetime64(flight_date)
day_end = day_start + np.timedelta64(1, "D")
mask = (time >= day_start) & (time < day_end)

time_sel = time[mask]
print(time_sel)
altitude_sel = ds["GGALT"].values[mask]
units = ds["GGALT"].attrs.get("units", "m")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(time_sel, altitude_sel, color="tab:blue", linewidth=1)

ax.set_xlabel("Time (UTC)")
ax.set_ylabel(f"Altitude ({units})")
ax.set_title(f"C-130 N130AR Altitude vs Time — {flight_date} ({len(time_sel)} samples)")
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

plt.xticks(rotation=45)
plt.tight_layout()

out_path = f"/Users/costanza/data/caesar_{flight_date}_altitude_zarr.jpg"
plt.savefig(out_path, dpi=150)
os.system(f"open {out_path}")
