from pathlib import Path
import xarray as xr
import zarr
import pandas as pd
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
from metpy.cbook import get_test_data
from metpy.plots import add_metpy_logo, SkewT
from metpy.units import units
import os

zarr_path = "/Users/costanza/data/zarr/SWEX_sondes_HQ_SBFD"

# open specific zarr file
ds = xr.open_zarr(f"{zarr_path}/SWEX_SBFS38_DFM09_bufr309052_20220418_110040", consolidated=False)
print(ds)

# Pull the needed vars for skewT
p = ds.PRES.values * units.hPa
T = ds.TEMP.values * units.degC
Td = ds.DEWP.values * units.degC
wind_speed = ds.WS.values[::100] * units.knots
wind_dir = ds.WD.values[::100] * units.degrees
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

plt.title('SWEX_SBFS38_DFM09_bufr309052_20220418_110040')
plt.savefig('/Users/costanza/data/SWEX_SBFS38_DFM09_bufr309052_20220418_110040_SKEWT.png', dpi=300, bbox_inches='tight')
os.system(f"open /Users/costanza/data/SWEX_SBFS38_DFM09_bufr309052_20220418_110040_SKEWT.png")
