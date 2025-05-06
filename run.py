import argparse
from get_prono import getPronoFile
from read_prono import datasetToProno
import json

def main():
    parser = argparse.ArgumentParser(description="Download and read Pronomar netcdf forecast run and convert into a5 json, optionally upload to database")
    parser.add_argument('-u', '--upload', action='store_true', help='Upload to database')
    parser.add_argument('-o', '--output', required=False, help='Save result into file. If not set, will print to stdout')
    parser.add_argument('-s', '--skip_download', action='store_true', help='Skip download')    

    args = parser.parse_args()

    # download
    if not args.skip_download:
        getPronoFile()
    
    # read
    series_prono = datasetToProno(upload=args.upload)
    if args.output:
        json.dump(series_prono, open(args.output,"w",encoding="utf-8"), indent=2)
    else:
        print(json.dumps(series_prono, indent=2))

if __name__ == "__main__":
    main()
