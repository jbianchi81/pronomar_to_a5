import  xarray as xr
from pandas import DataFrame
from typing import List, TypedDict
import json
from datetime import datetime
import yaml
import os
from a5client import Crud
import argparse

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config/default.yml")
config = yaml.load(open(config_path,"r",encoding="utf-8"),Loader=yaml.CLoader)

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
    df['timestart'] = df['time'].dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return df[["timestart",stat_name]].rename(columns={stat_name:"valor"}).to_dict(orient="records")

def parseForecastDate(title : str) -> datetime:
    return datetime(int(title[0:4]),int(title[4:6]),int(title[6:8]), int(title[9:11]))

def datasetToProno(filename : str = None, points : List[PointMap] = None, cal_id : int = default_cal_id, upload = False, **kwargs) -> Corrida:
    if filename is None:
        filename = os.path.join(script_dir, config["source"]["local_file_path"])
    if points is None:
        if "points" in config:
            points = config["points"]
        else:
            points = default_points
    dataset = openDataset(filename)
    forecast_date = parseForecastDate(dataset.title)
    series_prono = []
    for point in points:
        series_prono.extend(extractPronosAtPoint(dataset, point["lon"], point["lat"], series_id = point["series_id"], **kwargs))
    corrida = {
        "$schema": "https://raw.githubusercontent.com/jbianchi81/alerta5DBIO/refs/heads/master/public/schemas/a5/corrida.yml",
        "cal_id": cal_id,
        "forecast_date": "%s.000Z" % forecast_date.isoformat(),
        "series": series_prono
    }
    if upload:
        crud = Crud(config["dest"]["url"],config["dest"]["token"])
        response = crud.createCorrida(corrida)
        return response
    else:
        return corrida

def main():
    parser = argparse.ArgumentParser(description="Read netcdf prono and convert into a5 json, optionally upload to database")
    parser.add_argument('-u', '--upload', action='store_true', help='Upload to database')
    parser.add_argument('-o', '--output', required=False, help='Save result into file. If not set, will print to stdout')

    args = parser.parse_args()

    series_prono = datasetToProno(upload=args.upload)
    if args.output:
        json.dump(series_prono, open(args.output,"w",encoding="utf-8"), indent=2)
    else:
        print(json.dumps(series_prono, indent=2))

if __name__ == "__main__":
    main()
