import gzip
import json
import requests
import xmltodict

from db  import Database
from log import log

db = Database()


def get_metars():
    """ Get the daily metars file from the FAA weather site
    :return:
    """

    files = ['metars.cache.xml.gz']   # ['tafs.cache.xml.gz'] #
    url = "https://aviationweather.gov/data/cache/{}"
    for faa_file in files:
        try:
            reply = requests.get(url.format(faa_file), stream=True)
        except Exception as e:
            log.error(f"Exception:{e} opening url {url}")
            return None

        if not reply.ok:
            log.error(f"Error getting metar file {faa_file}:{reply.reason}")
            return None

        try:
            with open(faa_file, '+wb') as fyle:
                for data in reply.iter_content(chunk_size=1024):
                    fyle.write(data)

        except Exception as e:
            log.error(f"Error downloading metar file {faa_file}:{e}")
            return None

        try:
            with gzip.open(faa_file, mode='rb') as fyle:
                xml_data = fyle.read()
        except Exception as e:
            log.error(f"Error unzipping metar file {faa_file}:{e}")

        metars = xmltodict.parse(xml_data)
        metars = metars.get('response').get('data').get('METAR')
        index = {}
        for metar in metars:
            index[metar['station_id']] = metar

        return index

def get_airport(station):
    """ Get the name of the airport
    :param station:
    :return: str: airport name
    """
    #url = f"https://aviationweather.gov/api/data/airport?ids={station}&format=json"
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
    reply = requests.get(url)
    if reply.ok:
        try:
            data = json.loads(reply.text)
            if isinstance(data, list):
                return data[0]
        except Exception as e:
            pass
            #log.error(f"Error {e} translating json:{data}")
    return {}


def get_station(station):
    """ Get info for a particular station
    :param station:
    :return:
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


def main():
    """
    Main routine. Schedule to run every 15 minutes
    :return: None
    """

    # Open the aiport file, each line represents an LED on the board
    with open('airports') as fyle:
        station_ids = fyle.read().split('\n')

    # Get the latest METAR data from the API
    metar_data = get_metars()

    # Set the LEDs for each value
    for led, station in enumerate(station_ids):
        airport = get_airport(station)
        if station in ("NULL", "LGND", ""):
            continue

        try:
            station_data = metar_data[station]
            if 'name' not in station_data.keys():
                station_data['name'] = airport.get('name')

            station_data["led"] = led
        except KeyError as e:
            station_data = get_station(station)
            if not station_data:
                log.error(f"Station {station} not in metar data")
                continue
            if isinstance(station_data, list):
                station_data = station_data[0]

        # Store the data you want in to the database
        try:
            db.put(station, station_data)
            db.geo_add('stations', (station_data.get('longitude'), station_data.get('latitude'), station))
        except Exception as e:
            log.error(f"Error:{e} putting {station_data} for station {station} in the db")


if __name__ == "__main__":
    main()
