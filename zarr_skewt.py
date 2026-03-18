import argparse
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
from metpy.plots import SkewT
from metpy.units import units
import os

zarr_path = "/Users/costanza/data/zarr/SWEX_sondes_HQ_SBFD_2d.zarr"

parser = argparse.ArgumentParser(description="Plot a skew-T from the 2D SWEX sounding store")
parser.add_argument("date", help="Date in YYYYMMDD format")
parser.add_argument("-n", type=int, default=1,
                    help="Which sounding for that day (1=first, 2=second, etc.). Default: 1")
args = parser.parse_args()

date_str = args.date
if len(date_str) != 8 or not date_str.isdigit():
    parser.error("Date must be in YYYYMMDD format")

target_date = np.datetime64(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}")

# Open the 2D zarr store and find soundings for the given day
ds = xr.open_zarr(zarr_path, consolidated=False)
dates = ds.launch_time.values.astype("datetime64[D]")
unique_dates = np.unique(dates)

if target_date < unique_dates[0] or target_date > unique_dates[-1]:
    print(f"Date {date_str} is out of range.")
    print(f"Available range: {unique_dates[0]} to {unique_dates[-1]}")
    exit(1)

day_indices = np.where(dates == target_date)[0]
if len(day_indices) == 0:
    print(f"No soundings found for {date_str}.")
    print(f"Available range: {unique_dates[0]} to {unique_dates[-1]}")
    exit(1)

if args.n < 1 or args.n > len(day_indices):
    print(f"Sounding {args.n} not available for {date_str}.")
    print(f"  {len(day_indices)} sounding(s) available:")
    for i, idx in enumerate(day_indices, 1):
        print(f"    {i}: {ds.sounding_id.values[idx]}  ({ds.launch_time.values[idx]})")
    exit(1)

sounding_idx = int(day_indices[args.n - 1])
sonde = ds.isel(sounding=sounding_idx).dropna(dim="level")
sounding_name = ds.sounding_id.values[sounding_idx]
launch = str(ds.launch_time.values[sounding_idx])

print(f"Plotting sounding {args.n} of {len(day_indices)} for {date_str}")
print(f"  {sounding_name}")
print(f"  Launch time: {launch}")

# Pull the needed vars for skewT
p = sonde.PRES.values * units.hPa
T = sonde.TEMP.values * units.degC
Td = sonde.DEWP.values * units.degC
wind_speed = sonde.WS.values[::100] * units.knots
wind_dir = sonde.WD.values[::100] * units.degrees
u, v = mpcalc.wind_components(wind_speed, wind_dir)

skew = SkewT()

# Plot the data using normal plotting functions, in this case using
# log scaling in Y, as dictated by the typical meteorological plot
skew.plot(p, T, 'r')
skew.plot(p, Td, 'g')
skew.plot_barbs(p[::100], u, v)

# Set some better labels than the default
skew.ax.set_xlabel('Temperature (\N{DEGREE CELSIUS})')
skew.ax.set_ylabel('Pressure (mb)')

# Add the relevant special lines
skew.plot_dry_adiabats()
skew.plot_moist_adiabats()
skew.plot_mixing_lines()
skew.ax.set_ylim(1000, 100)

plt.title(f"{sounding_name}\n{launch}")
outfile = f"/Users/costanza/data/{sounding_name}_SKEWT.png"
plt.savefig(outfile, dpi=300, bbox_inches='tight')
os.system(f"open {outfile}")
