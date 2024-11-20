from db             import Database
from airports       import get_airports

rdb = Database(host='127.0.0.1')

def main(file_name):

    station_ids = get_airports(file_name)
    for station in station_ids:
        if station == "LGND":
            continue
        station_data = rdb.getall(station)
        wind_speed = station_data.get('wind_speed_kt')
        wind_gusts = station_data.get('wind_gust_kt')
        wind_dir   = station_data.get('wind_dir_degrees')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description ='Get weather for airports')
    parser.add_argument('--file','-f', nargs='?')
    args = parser.parse_args()
    if not args.file:
        main('airports')
    else:
        main(args.file)
