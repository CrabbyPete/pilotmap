import json
import requests

from log import log
from db import Database

db = Database()


def get_airport_info(airports=None):
    """
    Create a dict of airport information
    :param airports:
    :return:
    """
    info = dict()
    if not airports:
        with open('airports', 'r') as fyle:
            airports = [line.strip().replace('\n', '') for line in fyle.readlines()]

    for airport in airports:
        if airport in ("NULL", "LGND", ""):
            continue
        try:
            name = db.hget(airport, 'name').split(',')
            info[airport] = [name[0], name[1]]
        except Exception as e:
            log.error(f"Error:{e} for {airport}")

    return info


def get_airport(station):
    """ Get the name of the airport
    :param station:
    :return: str: airport name
    """
    # url = f"https://aviationweather.gov/api/data/airport?ids={station}&format=json"
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"
    try:
        reply = requests.get(url)
    except Exception as e:
        log.error(f"Error:{e} trying to open {url}")

    else:
        if reply.ok:
            try:
                data = json.loads(reply.text)
                if isinstance(data, list):
                    return data[0]
            except Exception as e:
                log.error(f"Error {e} translating json:{reply.text}")
    return {}


def get_airports(file_name='airports'):
    with open(file_name) as fyle:
        station_ids = fyle.read().split('\n')
    return station_ids


if __name__ == '__main__':
    apinfo = get_apinfo({})
