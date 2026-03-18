import zarr
import fsspec

source_url = 'https://osdf-director.osg-htc.org/ncar/gdex/d121499/prof449_M2HATS_winds30.zarr'
target_path = '/Users/costanza/data/prof449_M2HATS_winds30.zarr'

# Create a mapper for both source and destination
source_store = fsspec.get_mapper(source_url)
dest_store = fsspec.get_mapper(target_path)

# Copy the entire store
zarr.copy_store(source_store, dest_store)
