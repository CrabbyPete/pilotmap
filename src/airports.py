import json
import requests


from log import log
from db import Database

db = Database()


def get_apinfo(airports=None):
    """
    Create a dict of airport information
    :param airport:
    :return:
    """
    info = dict()
    if not airports:
        with open('airports', 'r') as fyle:
            airports = [line.strip().replace('\n','') for line  in fyle.readlines()]

    for airport in airports:
        if not airport.startswith('K'):
            continue
        try:
            name = db.get(airport,'name').split(',')
            info[airport] = [name[0], name[1]]
        except Exception as e:
            log.error(f"Error:{e} for {airport}")

    return info


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
            log.error(f"Error {e} translating json:{reply.text}")
    return {}


if __name__ == '__main__':
      apinfo = get_apinfo({})