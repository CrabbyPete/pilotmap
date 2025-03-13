import time
import arrow
import signal

from pytz       import timezone, UnknownTimeZoneError
from suntime    import Sun

from db         import Database
from log        import log
from leds       import LedStrip
from colors     import Colors
from config     import color, conditions
from airports   import get_airports


rdb = Database()
colors = Colors(rdb)

strip = LedStrip(183)
strip.clear_pixels()


def brighten(led:tuple, value:int):
    """ Change the brightness of an individual LED
    :param leds: 3 color set of rgb to work with
    :param value: value to change each for brightness
    :return: set of new rgb values
    """
    ratio = abs(value)/100.
    if value < 0:
        try:
            red = led[0] - int(led[0] * ratio)
            red = 0 if red < 0 else red

            green = led[1] - int(led[1] * ratio)
            green = 0 if green < 0 else green

            blue = led[2] - int(led[2] * ratio)
            blue = 0 if blue < 0 else blue
        except Exception as e:
            log.error(e)

    else:
        red = led[0] + int(led[0] * ratio)
        red = 255 if red > 255 else red

        green = led[1] + int(led[1] * ratio)
        green = 255 if green > 255 else green

        blue = led[2] + int(led[2] * ratio)
        blue = 255 if blue > 255 else blue

    return red, green, blue


def get_condition(wx_list:list):
    for wx in wx_list:
        for condition, values in conditions.items():
            if wx in values:
                return condition


time_to_die = False

def signal_handler(signum, frame):
    global time_to_die
    log.info(f"Signal:{signum}")
    time_to_die = True


def set_light(led, color_str):
    if colors.is_off(led):
        clr = (0,0,0)

    elif isinstance(color_str,tuple): # Brighten and dim send a straight tuple
        clr = color_str

    else:
        try:
            clr = colors.get(color_str)
        except Exception as e:
            log.error(f"Error:{e} getting color:{color_str}")

    if clr:
        strip.set_pixel_color(led, clr)


def main(file_name):
    """
    Main program to manage the lights
    :return:
    """
    station_ids = get_airports(file_name)

    legend = {"VFR":None,
              "MVFR":None,
              "IFR": None,
              "LIFR": None,
              "INVALID": None
              }

    # First pass find the LGND tags, and populate them
    legend_index = 0
    for led, station in enumerate(station_ids):

        if station == "LGND":
            if legend_index == 0:
                set_light(led, 'vfr')
                legend["VFR"] = 'vfr'
            elif legend_index == 1:
                set_light(led, 'mvfr')
                legend["MVFR"] = 'mvfr'
            elif legend_index == 2:
                set_light(led, 'ifr')
                legend["IFR"] = 'ifr'
            elif legend_index == 3:
                set_light(led, 'lifr')
                legend["LIFR"] = 'lifr'
            elif legend_index == 4:
                set_light(led, 'nowx')
                legend["INVALID"] = 'nowx'
                break
            legend_index += 1

    # Loop forever to light each LED
    while not time_to_die:
        blink = []

        # Check the status of the stations by color
        for led, station in enumerate(station_ids):
            if station in ("NONE", "NULL", "LGND", ""):
                continue

            station_data = rdb.hgetall(station)
            flight_category = station_data.get('flight_category')
            if flight_category:
                led_color = legend[flight_category]
            else:
                led_color = 'nowx'

            wx_string = station_data.get('wx_string')
            if wx_string:
                wx_condition = get_condition(wx_string.split())
                led_color = color.dict(wx_condition)
                blink.append(led)

            lng = station_data.get('longitude')
            lat = station_data.get('latitude')
            tz = station_data.get('timezone')
            if isinstance(led_color,str):
                led_color = colors.get(led_color)

            if lat and lng and tz:
                now = arrow.now(tz)
                sun = Sun(float(lat),float(lng))
                try:
                    sun_rise = sun.get_sunrise_time(time_zone=timezone(tz))
                    sun_set  = sun.get_sunset_time(time_zone=timezone(tz))

                    if now.datetime > sun_set or now.datetime < sun_rise:
                        led_color = brighten(led_color, -75)
                    else:
                        led_color = brighten(led_color, -50)

                except UnknownTimeZoneError:
                    pass
            else:
                led_color = brighten(led_color, -50)

            log.info(f"Light:{led}={led_color}")
            set_light(led, led_color)

        saved_colors = [strip.get_pixel(led) for led in blink]

        sleep = 0
        # Don't change any other led for 30 seconds as we check which to blink
        while not time_to_die:
            strip.show_pixels()
            for index, led in enumerate(blink):
                if strip.get_pixel(led) == 0:
                    set_light(led, saved_colors[index])
                else:
                    set_light(led, 0)

            time.sleep(.5)
            sleep += .5
            if sleep > 30:
                break

    # You got a signal to die
    strip.clear_pixels()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description ='Get weather for airports')
    parser.add_argument('--file','-f', nargs='?')
    args = parser.parse_args()
    if not args.file:
        main('airports')
    else:
        main(args.file)
