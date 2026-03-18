from pathlib import Path
import zarr
import pandas as pd

zarr_path = "/Users/costanza/data/zarr/SWEX_sondes_HQ_SBFD"
root = zarr.open_group(zarr_path, mode = "a")

radiosonde_path = Path("/Users/costanza/data/SWEX_sondes_HQ_SBFD")
radiosonde_files = sorted([p for p in radiosonde_path.iterdir() if p.suffix == ".csv"])

for sonde in radiosonde_files:
    # various short cuts for reading in the csv file
    df = pd.read_csv(sonde, sep=r'[,\s]+', engine='python', skiprows=[0, 1, 3, 4])
    df.columns = df.columns.str.strip().str.replace('.', '', regex=False)
    # create the xarray object from the csv
    df = df.set_index(['TIME'])
    ds = df.to_xarray()
    # remove the last two columns that are formatted weird
    vars_to_drop = list(ds.data_vars)[-2:]
    ds = ds.drop_vars(vars_to_drop)
    ds.to_zarr(zarr_path, group=sonde.stem, consolidated=False, mode='w')
