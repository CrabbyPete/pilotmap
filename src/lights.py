import time

from db     import Database
from log    import log
from leds   import LedStrip
from config import color


db = Database(host='127.0.0.1')
strip = LedStrip()


def main():
    with open('airports') as fyle:
        station_ids = fyle.read().split('\n')

    legend = {"VFR":None,
              "MVFR":None,
              "IFR": None,
              "LIFR": None,
              "INVALID": None
              }

    # First pass find the LGND tags, and poplate them
    legend_index = 0
    for led, station in enumerate(station_ids):
        if station == "LGND":
            if legend_index == 0:
                strip.set_pixel_color(led, color.vfr)
                legend["VFR"] = color.vfr
            elif legend_index == 1:
                strip.set_pixel_color(led, color.mvfr)
                legend["MVFR"] = color.mvfr
            elif legend_index == 2:
                strip.set_pixel_color(led, color.ifr)
                legend["IFR"] = color.ifr
            elif legend_index == 3:
                strip.set_pixel_color(led, color.lifr)
                legend["LIFR"] = color.lifr
            elif legend_index == 4:
                strip.set_pixel_color(led, color.nowx)
                legend["INVALID"] = color.nowx
                break
            legend_index += 1

    while True:
        for led, station in enumerate(station_ids):
            if station in ("NONE", "NULL", "LGND", ""):
                continue

            flight_category = db.get(station, 'flight_category')
            if flight_category:
                strip.set_pixel_color(led, legend[flight_category])
            else:
                log.info(f"No flight_category for station {station}, led {led}")
                strip.set_pixel_color(led, legend["INVALID"])

        time.sleep(60)


if __name__ == "__main__":
    main()