import xarray as xr
import fsspec

source_url = 'https://osdf-director.osg-htc.org/ncar/gdex/d121499/prof449_M2HATS_winds30.zarr'
target_path = '/Users/costanza/data/prof449_M2HATS_winds30.zarr'

# Open remote Zarr v3 store via xarray and save locally
mapper = fsspec.get_mapper(source_url)
#ds = xr.open_zarr(mapper, consolidated=False, zarr_format=3)
ds = xr.open_zarr(mapper)
ds.to_zarr(target_path, mode='w', consolidated=False)
