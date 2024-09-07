import time

from db     import Database
from log    import log
from leds   import LedStrip
from config import color


rdb = Database(host='127.0.0.1')
strip = LedStrip()


def main():
    """
    Main program to manage the lights
    :return:
    """
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
        # Check if the lights are off
        if not rdb.get_value('lights'):
            strip.clear_pixels()
            time.sleep(30)
            continue

        # Otherwise check the status of the stations by color
        for led, station in enumerate(station_ids):
                if station in ("NONE", "NULL", "LGND", ""):
                    continue

                flight_category = rdb.get(station, 'flight_category')
                if flight_category:
                    strip.set_pixel_color(led, legend[flight_category])
                else:
                    log.info(f"No flight_category for station {station}, led {led}")
                    strip.set_pixel_color(led, (255,255,255))

        while True:
            # Don't change any other led for 30 seconds as we check which to blink
            sleep = 0

            # Save the current color for each blinking led
            saved_color = [strip.get_pixel_color(led)  for led in rdb.get_values('blink')]
            for led in rdb.get_values('blink'):
                if strip.get_pixel_color(led):
                    strip.set_pixel_color(led, 0)
                else:
                    strip.set_pixel_color(led, saved_color[led])
            time.sleep(5)
            sleep += 5
            if sleep > 30:
                break


if __name__ == "__main__":
    main()