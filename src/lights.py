import time
import arrow


from db         import Database
from log        import log
from pytz       import timezone, UnknownTimeZoneError
from leds       import LedStrip
from config     import color, conditions
from suntime    import Sun


rdb = Database(host='127.0.0.1')
strip = LedStrip(183)
strip.clear_pixels()

def dim(data,value):
    red = data[0] - ((value * data[0])/100)
    if red < 0:
        red = 0

    grn = data[1] - ((value * data[1])/100)
    if grn < 0:
        grn = 0

    blu = data[2] - ((value * data[2])/100)
    if blu < 0:
        blu = 0

    data =[red,grn,blu]
    return data

def brighten(led:tuple, value:int):
    """ Change the brightness of an individual LED
    :param leds: 3 color set of rgb to work with
    :param value: value to change each for brightness
    :return: set of new rgb values
    """
    ratio = abs(value)/100.
    if value < 0:
        r = led[0] - led[0] * ratio
        r = 0 if r < 0 else r

        g = led[1] - led[1] * ratio
        g = 0 if g < 0 else g

        b = led[2] - led[2] * ratio
        b = 0 if b < 0 else b

    else:
        r = led[0] + led[0] * ratio
        r = 255 if r > 255 else r

        g = led[1] + led[1] * ratio
        g = 255 if r > 255 else g

        b = led[2] + led[2] * ratio
        b = 255 if b > 255 else b

    return (r, b, g)

def get_condition(wx_list:list):
    for wx in wx_list:
        for condition, values in conditions.items():
            if wx in values:
                return condition


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

    # First pass find the LGND tags, and populate them
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
            #rdb.set_values('lights',)
            legend_index += 1

    # Loop forever to light each LED
    while True:
        # Check the status of the stations by color
        for led, station in enumerate(station_ids):
            if station in ("NONE", "NULL", "LGND", ""):
                continue

            station_data = rdb.getall(station)
            flight_category = station_data.get('flight_category')
            wx_string = station_data.get('wx_string')
            if wx_string:
                wx_condition = get_condition(wx_string.split())
                led_color = color.dict(wx_condition)
            elif flight_category:
                led_color = legend[flight_category]
            else:
                led_color = color.nowx

            lng = station_data.get('longitude')
            lat = station_data.get('latitude')
            if lat and lng:
                tz = station_data.get('timezone')
                if tz:
                    now = arrow.now(tz)
                    sun = Sun(float(lat),float(lng))
                    try:
                        sun_rise = sun.get_sunrise_time(time_zone=timezone(tz))
                        sun_set  = sun.get_sunset_time(time_zone=timezone(tz))
                        if sun_rise > now.datetime < sun_set:
                            led_color = brighten(led_color, -50)
                    except UnknownTimeZoneError:
                        pass

            strip.set_pixel_color(led, led_color)

        while True:
            strip.show_pixels()

            # Don't change any other led for 30 seconds as we check which to blink
            sleep = 0

            # Save the current color for each blinking led
            try:
                saved_color = [(led, strip.get_pixel(led))  for led in rdb.get_values('blink')]
            except Exception as e:
                log.error(e)
                break

            for led in rdb.get_values('blink'):
                if strip.get_pixel(led):
                    strip.set_pixel_color(led, 0)
                else:
                    strip.set_pixel_color(led, saved_color[led])
            time.sleep(5)
            sleep += 5
            if sleep > 30:
                break
            log.info("stop blink")

        time.sleep(60)


if __name__ == "__main__":
    main()