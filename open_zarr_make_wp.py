import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import fsspec

url = "https://osdf-director.osg-htc.org/ncar/gdex/d121499/prof449_M2HATS_winds30.zarr"
mapper = fsspec.get_mapper(url)
ds = xr.open_zarr(mapper, consolidated=True)

index = np.where((ds.time >= np.datetime64('2023-07-22')) & (ds.time <= np.datetime64('2023-07-23')))[0]
X, Y = np.meshgrid(ds.time[index[0]:index[-1]], ds.height_agl)

fig, ax = plt.subplots(figsize=(15, 7))

ax.barbs(X, Y, ds.u_wind[index[0]:index[-1]], ds.v_wind[index[0]:index[-1]], 
         length=5, linewidth=0.5, color='black')

plt.xticks(rotation=45)
ax.set_xlabel("Time (UTC)")
ax.set_ylabel("Height (m)")
ax.set_title("24-Hour Vertical Wind Profile")

plt.savefig("/Users/costanza/data/M2HATS_20240722_WindProfiler.jpg")
#os.system(f"open /Users/costanza/data/M2HATS_20240722_WindProfiler.jpg")
