import xarray as xr
import numpy as np

# Create a sample Xarray Dataset
data = xr.Dataset(
    data_vars = {"temperature": (("x", "y"), np.random.randn(100, 100)),
                "wind_speed": (("x", "y"), np.random.randn(100, 100))},
    coords={"x": np.arange(100), "y": np.arange(100)}
)

# Save to Zarr
data.to_zarr("/Users/costanza/data/weather_data.zarr", mode="w")

# Open Zarr
ds = xr.open_zarr("/Users/costanza/data/weather_data.zarr")
print(ds)
print(ds.temperature.values)
print(ds.wind_speed.values)
