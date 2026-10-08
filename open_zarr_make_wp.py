import argparse
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import fsspec

# Each source maps to its store plus the names it uses for height and u/v.
SOURCES = {
    "profiler": {
        "url": "https://osdf-director.osg-htc.org/ncar/gdex/d121499/prof449_M2HATS_winds30.zarr",
        "height": "height_agl",
        "u": "u_wind",
        "v": "v_wind",
        "label": "449 MHz Wind Profiler",
    },
    "windcube": {
        "url": "/Users/costanza/data/m2hats_windcube_vad30min_combined.zarr",
        "height": "height",
        "u": "u",
        "v": "v",
        "label": "WindCube VAD",
    },
}

parser = argparse.ArgumentParser(description="Plot a 24-hour wind barb profile from M2HATS Zarr stores")
parser.add_argument("date", help="Date in YYYYMMDD format")
parser.add_argument("-s", "--source", choices=[*SOURCES, "both"], default="both",
                    help="Which store(s) to plot (default: both)")
parser.add_argument("-e", "--every", type=int, default=2,
                    help="Plot every Nth height gate (default: 2)")
args = parser.parse_args()

date = args.date
names = list(SOURCES) if args.source == "both" else [args.source]
start = np.datetime64(f"{date[:4]}-{date[4:6]}-{date[6:]}")


def open_store(url):
    if url.startswith("http"):
        # Remote OSDF store: keep consolidated=True (see CLAUDE.md).
        mapper = fsspec.get_mapper(url)
        return xr.open_zarr(mapper, consolidated=True)
    # Local store was written with consolidated=False.
    return xr.open_zarr(url, consolidated=False)


def load_day(src):
    ds = open_store(src["url"])
    day = ds.sel(time=slice(start, start + np.timedelta64(1, "D") - np.timedelta64(1, "s")))
    if day.sizes["time"] == 0:
        raise SystemExit(f"{src['label']}: no data for {date}; available "
                         f"{ds.time.values[0]} -> {ds.time.values[-1]}")
    # Thin along whatever vertical dim the height variable uses (height vs height_msl).
    zdim = next(d for d in day[src["height"]].dims if d != "time")
    return day.isel({zdim: slice(None, None, args.every)})


fig, axes = plt.subplots(len(names), 1, figsize=(15, 7 * len(names)),
                         sharex=True, squeeze=False)
axes = axes[:, 0]

for ax, name in zip(axes, names):
    src = SOURCES[name]
    day = load_day(src)
    X, Y = np.meshgrid(day.time.values, day[src["height"]].values)
    u, v = day[src["u"]], day[src["v"]]
    # u/v are (time, height); meshgrid is (height, time), so transpose.
    ax.barbs(X, Y, u.values.T, v.values.T, length=5, linewidth=0.5, color='black')
    ax.set_ylabel("Height (m)")
    ax.set_title(f"{src['label']} 24-Hour Vertical Wind Profile, {start}")

ax = axes[-1]
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax.set_xlim(start, start + np.timedelta64(1, "D"))
plt.setp(ax.get_xticklabels(), rotation=45)
ax.set_xlabel(f"Time (UTC) on {start}")
fig.tight_layout()

suffix = {"profiler": "Windprofiles", "windcube": "Windcube_VAD", "both": "Profiler_Windcube"}[args.source]
out = f"/Users/costanza/data/M2HATS_{date}_{suffix}.jpg"
plt.savefig(out)
os.system(f"open {out}")
