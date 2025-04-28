import time

from db             import Database
from log            import log
from PIL            import Image, ImageDraw, ImageFont

from airports       import get_airports
from hardware       import Display


# Load fonts. Install font package --> sudo apt-get install ttf-mscorefonts-installer
# Also see; https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil for info
# Arrows.ttf downloaded from https://www.1001fonts.com/arrows-font.html#styles
fontsize = 24
fontindex = 0                                   # Font selected may have various versions that are indexed.
backcolor = 0                                   # 0 = Black, background color for OLED display. Shouldn't need to change
fontcolor = 255                                 # 255 = White, font color for OLED display. Shouldn't need to change
displays = 8

try:
    boldfont = ImageFont.truetype('LiberationSerif-Bold.ttf', fontsize, 0)
    regfont  = ImageFont.truetype('LiberationSerif-Regular.ttf', fontsize, 0)
    arrows   = ImageFont.truetype('Arrows.ttf', fontsize+2, 0)
except Exception as e:
    log.error(f"Error:{e} loading fonts")


def winddir(wndir=0):
    """
    Using the arrows.ttf font return arrow to represent wind direction at airport
    :param wndir: wind direction in degrees
    :return: char representation of an arrow
    """
    if (338 <= wndir <= 360) or (1 <= wndir <= 22):
        return 'd'                              # wind blowing from the north (pointing down)
    elif 23 <= wndir <= 67:
        return 'f'                              # wind blowing from the north-east (pointing lower-left)
    elif 68 <= wndir <= 113:
        return 'b'                              # wind blowing from the east (pointing left)
    elif 114 <= wndir <= 159:
        return 'e'                              # wind blowing from the south-east (pointing upper-left)
    elif 160 <= wndir <= 205:
        return 'c'                              # wind blowing from the south (pointing up)
    elif 206 <= wndir <= 251:
        return 'g'                              # wind blowing from the south-west (pointing upper-right)
    elif 252 <= wndir <= 297:
        return 'a'                              # wind blowing from the west (pointing right)
    elif 298 <= wndir <= 337:
        return 'h'                              # wind blowing from the north-west (pointing lower-right)
    else:
        return ''


rdb = Database()

try:
    oleds = Display()
    image = Image.new('1', (oleds.width, oleds.height))      # Make sure to create image with mode '1' for 1-bit color.
    draw = ImageDraw.Draw(image)
except Exception as e:
    log.error("Error:{e} trying to initialize display")


def draw_display(wind, use_arrows=True):
    """
    Draw a display from wind data
    :param: draw: Draw
    :param wind: dict: wind data
    :param width: oled width
    :param height: oled height
    :return: None
    """
    offset = 3
    draw.rectangle((0, 0, oleds.width-1, oleds.height-1), outline=0, fill=1)
    x1, y1, x2, y2 = 0, 0, oleds.width, oleds.height                    # Create boundaries of display

    # Draw wind direction using arrows
    if direction := wind.get('direction'):
        if use_arrows:
            try:
                arrow_direction = winddir(int(direction))   # Make sure it an int for direction
            except Exception as e:
                log.error(f"Error:{e} getting wind direction {direction}")
                return
            else:
                draw.text((96, 37), arrow_direction, font=arrows, outline=255, fill=0)  # Lower right of oled

            if wind['speed'] == -1:
                wind['speed'] = "Not reported"
            else:
                wind['speed'] = f"{wind['speed']} kts"

            txt = wind['station'] + '\n' + wind['speed']

        else:
            speed = wind.get('speed')
            gusts = wind.get('gusts')
            direction = "{:03d}".format(direction)

            if not speed:
                txt = f"{wind['station']}\r\n Calm"
            elif not gusts:
                txt=f"{wind['station']}\r\n{direction}'@RB'{speed}kts"
            else:
                txt=f"{wind['station']}\r\n{direction}'VRB@'{speed}g{gusts}"
    else:
        txt=f"{wind['station']}\r\nWind Not Reported"

    _, _, w, h = draw.textbbox((0, 0), txt, font=regfont)   # Get textsize of what is to be displayed
    x = (x2 - x1 - w)/2 + x1                                # Calculate center for text
    y = (y2 - y1 - h)/2 + y1 - offset

    # Draw the text to buffer
    draw.text((x, y), txt, align='center', font=regfont, fill=0)
    return


def main(file_name):
    """
    Main function to show wind on displays
    :param file_name: airport file
    :return: None
    """
    station_ids = get_airports(file_name)
    while True:
        winds = []
        for station in station_ids:
            if station == "LGND":
                continue
            station_data = rdb.hgetall(station)

            wind_gusts = station_data.get('wind_gust_kt')
            wind_dir   = station_data.get('wind_dir_degrees')
            wind_speed = station_data.get('wind_speed_kt')
            if not wind_speed:
                winds.append({'station': station, 'speed': -1, 'gusts': wind_gusts, 'direction': wind_dir})
            else:
                winds.append({'station': station, 'speed': int(wind_speed), 'gusts': wind_gusts, 'direction': wind_dir})

        winds = sorted(winds, key=lambda x: x['speed'], reverse=True)
        for number, wind in enumerate(winds):
            draw_display(wind)
            oleds.show(number, image)

        log.info(winds)
        time.sleep(60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description ='Get weather for airports')
    parser.add_argument('--file', '-f', nargs='?')
    args = parser.parse_args()
    if not args.file:
        main('airports')
    else:
        main(args.file)
