import  xarray as xr
from pandas import DataFrame
from typing import List, TypedDict
import json
from datetime import datetime

## tipos y defaults

class PointMap(TypedDict):
    series_id : int
    lon : float
    lat : float

default_points : List[PointMap] = [
    {   # SFER (Lujan)
        "series_id": 6066,
        "lat": -34.5,
        "lon": -58.375
    },
    {   # NPAL (Uruguay)
        "series_id": 6071, 
        "lat": -34.25,
        "lon": -58.125
    }
]

class Pronostico(TypedDict):
    timestart : str
    valor : float

class SerieProno(TypedDict):
    series_table : str
    series_id : int
    qualifier : str
    pronosticos : List[Pronostico]

class Corrida(TypedDict):
    cal_id : int
    forecast_date : str
    series : List[SerieProno]

default_cal_id = 707

# funciones

def openDataset(filename : str, mask_name : str = "mask_rho", var_name : str = "zeta") -> xr.Dataset:
    ds = xr.open_dataset(filename)
    if mask_name is not None:
        # apply mask
        m = ds[mask_name]
        mask = m == 1
        zeta = ds[var_name]
        masked_var = zeta.where(mask)
        masked_var_name = "%s_masked" % var_name
        ds[masked_var_name] = masked_var
    return ds

def extractPronosAtPoint(dataset : xr.Dataset, lon : float, lat : float, lat_coor : str = "lat_rho", lon_coor : str = "lon_rho", value_column : str = "zeta_masked", time_column : str = "time", stats : List[str] = ['min', 'median', 'max'], series_id : int = None) -> List[SerieProno]:
    # Select nearest point
    timeseries = dataset.sel({lat_coor: lat, lon_coor: lon}, method="nearest")
    # Extract time series for a specific variable
    ts = timeseries[value_column]
    # Convert to Pandas for easier manipulation (optional)
    ts_df = ts.to_dataframe()
    # print(ts_df)
    aggregated = ts_df[[value_column]].groupby(level=time_column).agg(stats)
    # print(aggregated)
    pronos = []
    for stat in stats:
        pronos.append({
            "series_table": "series",
            "series_id": series_id,
            "qualifier": stat,
            "pronosticos": extractStat(aggregated, stat, value_column, time_column)
        })
    return pronos

def extractStat(aggregated_df: DataFrame, stat_name : str, value_column :str = "zeta_masked", time_column : str = "time") -> List[Pronostico]:
    df = aggregated_df[value_column][stat_name].reset_index()
    df['timestart'] = df['time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f').str.rstrip('0').str.rstrip('.')
    return df[["timestart",stat_name]].rename(columns={stat_name:"valor"}).to_dict(orient="records")

def datasetToProno(filename : str, points : List[PointMap] = default_points, cal_id : int = default_cal_id, **kwargs) -> Corrida:
    dataset = openDataset(filename)
    forecast_date = datetime(int(dataset.title[0:4]),int(dataset.title[5:6]),int(dataset.title[7:8]), int(dataset.title[10:11]))
    series_prono = []
    for point in points:
        series_prono.extend(extractPronosAtPoint(dataset, point["lon"], point["lat"], series_id = point["series_id"], **kwargs))
    return {
        "$schema": "https://raw.githubusercontent.com/jbianchi81/alerta5DBIO/refs/heads/master/public/schemas/a5/corrida.yml",
        "cal_id": cal_id,
        "forecast_date": forecast_date.isoformat(),
        "series": series_prono
    }

if __name__ == "__main__":
    series_prono = datasetToProno("data/prono.00.nc", default_points)
    print(json.dumps(series_prono, indent=2))
