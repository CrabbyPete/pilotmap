from db             import Database
from airports       import get_airports
from display        import Display


rdb = Database(host='127.0.0.1')
oleds = Display(0)

def main(file_name):

    station_ids = get_airports(file_name)
    winds = []
    for station in station_ids:
        if station == "LGND":
            continue
        station_data = rdb.getall(station)
        wind_speed = int(station_data.get('wind_speed_kt',0))
        wind_gusts = station_data.get('wind_gust_kt',0)
        wind_dir   = station_data.get('wind_dir_degrees')
        winds.append({'station':station, 'speed':wind_speed, 'gusts': wind_gusts, 'direction': wind_dir})

    winds = sorted(winds, key=lambda x:x['speed'], reverse=True)
    for number, wind in enumerate(winds):
        oleds.oled(number,wind)




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description ='Get weather for airports')
    parser.add_argument('--file','-f', nargs='?')
    args = parser.parse_args()
    if not args.file:
        main('airports')
    else:
        main(args.file)
