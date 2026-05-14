import xarray as xr
import matplotlib.pyplot as plt
import os

url = "https://data.eol.ucar.edu/opendap/data/caesar/aircraft/c130_n130ar/LRT/v1.4/FF03.20240226.112700_151900.PNI.nc"

ds = xr.open_dataset(url)

altitude = ds["GGALT"]
time = ds["Time"]

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(time, altitude, color="tab:blue", linewidth=1)

ax.set_xlabel("Time (UTC)")
ax.set_ylabel(f"Altitude ({altitude.attrs.get('units', 'm')})")
ax.set_title("C-130 N130AR Altitude vs Time — Flight FF03 2024-02-26")
ax.grid(True, alpha=0.3)

plt.xticks(rotation=45)
plt.tight_layout()

out_path = "/Users/costanza/data/FF03_20240226_altitude.jpg"
plt.savefig(out_path, dpi=150)
os.system(f"open {out_path}")
