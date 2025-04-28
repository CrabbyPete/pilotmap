import gzip
import arrow
import requests
import xmltodict

from timezonefinder import TimezoneFinder

from db             import Database
from log            import log
from airports       import get_airports, get_airport


rdb = Database()


def get_metars():
    """ Get the daily metars file from the FAA weather site
    :return: dict: metars data
    """

    files = ['metars.cache.xml.gz', 'tafs.cache.xml.gz']
    url = "https://aviationweather.gov/data/cache/{}"
    index = {}

    for number, faa_file in enumerate(files):
        try:
            reply = requests.get(url.format(faa_file), stream=True)
        except Exception as e:
            log.error(f"Exception:{e} opening url {url}")
            continue

        if not reply.ok:
            log.error(f"Error getting metar file {faa_file}:{reply.reason}")
            continue

        try:
            with open(faa_file, '+wb') as fyle:
                for data in reply.iter_content(chunk_size=1024):
                    fyle.write(data)

        except Exception as e:
            log.error(f"Error downloading metar file {faa_file}:{e}")
            continue

        try:
            with gzip.open(faa_file, mode='rb') as fyle:
                xml_data = fyle.read()
        except Exception as e:
            log.error(f"Error unzipping metar file {faa_file}:{e}")
            continue

        metars = xmltodict.parse(xml_data)

        if number == 0:
            metars = metars.get('response').get('data').get('METAR')

            for metar in metars:
                index[metar['station_id']] = metar
        else:
            tafs = metars.get('response').get('data').get('TAF')
            for taf in tafs:
                if 'wx_string' in taf:
                    index[taf['station_id']]['wx_string'] = taf['wx_string']

    return index


def get_station(station):
    """ Get info for a particular station
    :param station:
    :return: dict: metars data
    """
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=xml&hours=3"
    reply = requests.get(url)
    if reply.ok:
        try:
            metars = xmltodict.parse(reply.text)
        except Exception as e:
            log.error(f"Error parsing METARs data:{e}")
            return []
        metars = metars.get('response').get('data').get('METAR')
        return metars


def weather(file_name=None):
    """
    Main routine. Schedule to run every 5 minutes
    :param: file_name: str: airport file
    :return: None
    """
    log.info(f"Starting at {arrow.now()}")
    tf = TimezoneFinder()

    # Open the aiport file, each line represents an LED on the board
    station_ids = get_airports(file_name)

    # Get the latest METAR data from the API
    metar_data = get_metars()

    # Ignore Legend values
    for led, station in enumerate(station_ids):
        if station in ("NULL", "LGND", ""):
            continue
        airport = get_airport(station)

        try:
            station_data = metar_data[station]
            if 'name' not in station_data.keys():
                station_data['name'] = airport.get('name')

            station_data["led"] = led

        except KeyError:
            station_data = get_station(station)
            if not station_data:
                log.error(f"Station {station} not in metar data")
                continue

            if isinstance(station_data, list):
                station_data = station_data[0]

        # Get the timezone for the longitude and latitude
        lng = station_data.get('longitude')
        lat = station_data.get('latitude')
        if lat and lng:
            timezone = tf.timezone_at(lng=float(lng), lat=float(lat))
            if timezone:
                station_data['timezone'] = timezone

        # Store the data you want in to the database
        try:
            rdb.put(station, station_data)
        except Exception as e:
            log.error(f"Error:{e} putting {station_data} for station {station} in the db")

        try:
            rdb.geoadd('stations', (station_data.get('longitude'), station_data.get('latitude'), station))
        except Exception as e:
            log.error(f"Error:{e} putting {station_data} geodata for station {station} in the db")

    log.info(f"Ending at {arrow.now()}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description ='Get weather for airports')
    parser.add_argument('--file', '-f', nargs='?')
    args = parser.parse_args()
    if not args.file:
        weather('./airports')
    else:
        weather(args.file)
