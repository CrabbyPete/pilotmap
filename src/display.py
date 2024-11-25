import time
import Adafruit_SSD1306
import RPi.GPIO as GPIO

from db             import Database
from log            import log
from PIL            import Image, ImageDraw, ImageFont
from Adafruit_GPIO  import I2C
from airports       import get_airports


# Set up the lights sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)


# Load fonts. Install font package --> sudo apt-get install ttf-mscorefonts-installer
# Also see; https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil for info
# Arrows.ttf downloaded from https://www.1001fonts.com/arrows-font.html#styles
fontsize = 24
fontindex = 0                                   # Font selected may have various versions that are indexed.
backcolor = 0                                   # 0 = Black, background color for OLED display. Shouldn't need to change
fontcolor = 255                                 # 255 = White, font color for OLED display. Shouldn't need to change
displays = 8

boldfont = ImageFont.truetype('LiberationSerif-Bold.ttf', fontsize, 0)
regfont  = ImageFont.truetype('LiberationSerif-Regular.ttf', fontsize, 0)
arrows   = ImageFont.truetype('Arrows.ttf', fontsize+2, 0)


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


class Display:
    """
    Class to control a single display
    """
    width = None
    height = None
    disp = None
    tca = None
    available = False

    def __init__(self, channel):

        try:
            self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)    # 128x64 or 128x32
        except Exception as e:
            log.error(f"Error: {e} initializing OLED displays")
            return
        self.available = True
        self.width = self.disp.width
        self.height = self.disp.height
        """
        This is the multiplexor. You need to set it before you write to the display
        Use cmd i2cdetect -y 1 to ensure multiplexer shows up at addr 0x70
        """
        self.tca = I2C.get_i2c_device(address=0x70)              #
        self.current_channel = channel
        self.select(channel)

    def select(self, channel):                 # Used to tell the multiplexer which oled display to send data to.
        self.current_channel = channel
        self.tca.writeRaw8(1 << self.current_channel)

    def dim(self, level=None):
        """
        Dimming routine. 0 = Full Brightness, 1 = low brightness, 2 = medium brightness.
        See https://www.youtube.com/watch?v=hFpXfSnDNSY a$
        :param level: int:
        :return:
        """
        if not level:
            level = GPIO.input(4)

        if level == 0:
            self.disp.command(0x81)                      # SSD1306_SETCONTRAST = 0x81
            self.disp.command(255)
            self.disp.command(0xDB)                      # SSD1306_SETVCOMDETECT = 0xDB
            self.disp.command(255)

        if level == 1 or level == 2:
            self.disp.command(0x81)                      # SSD1306_SETCONTRAST = 0x81
            self.disp.command(50)

        if level == 1:
            self.disp.command(0xDB)                      # SSD1306_SETVCOMDETECT = 0xDB
            self.disp.command(50)

    def invert(self, white=False):
        """
        Invert display pixels. Normal = white text on black background.
        :param white:
        :return:
        """
        if white:                                 # Inverted = black text on white background #0 = Normal, 1 = Inverted
            self.disp.command(0xA7)
        else:
            self.disp.command(0xA6)

    def rotate180(self):
        """
        Rotate display 180 degrees to allow mounting of OLED upside down
        """
        self.disp.command(0xA0)
        self.disp.command(0xC0)

    def clear(self):
        """
        Clear a display
        :return:
        """
        self.select(self.current_channel)
        self.disp.clear()

    def show(self, ch, display_image):
        """
        Display wind info on a display
        :param ch: which display
        :param display_image: Image
        :return:
        """
        # Center text vertically and horizontally
        if ch >= displays:
            return

        self.select(ch)
        self.disp.clear()
        self.disp.display()

        self.dim()
        self.disp.image(display_image)
        self.disp.display()


rdb = Database(host='127.0.0.1')
oleds = Display(0)


def draw_display(draw, wind, width, height):
    """
    Draw a display from wind data
    :param: draw: Draw
    :param wind: dict: wind data
    :param width: oled width
    :param height: oled height
    :return: None
    """
    offset = 3
    draw.rectangle((0, 0, width-1, height-1), outline=0, fill=1)
    x1, y1, x2, y2 = 0, 0, width, height                    # Create boundaries of display

    # Draw wind direction using arrows
    if direction := wind.get('direction'):
        try:
            arrow_direction = winddir(int(direction))   # Make sure its an int for direction
        except Exception as e:
            log.error(f"Error:{e} getting wind direction {direction}")
        else:
            draw.text((96, 37), arrow_direction, font=arrows, outline=255, fill=0)  # Lower right of oled

    if wind['speed'] == -1:
        wind['speed'] = "Not reported"
    else:
        wind['speed'] = f"{wind['speed']} kts"

    txt = wind['station'] + '\n' + wind['speed']
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
    if oleds.available:
        image = Image.new('1', (oleds.width, oleds.height))         # Make sure to create image with mode '1' for 1-bit color.
        draw = ImageDraw.Draw(image)

    while True:
        winds = []
        for station in station_ids:
            if station == "LGND":
                continue
            station_data = rdb.getall(station)

            wind_gusts = station_data.get('wind_gust_kt')
            wind_dir   = station_data.get('wind_dir_degrees')
            wind_speed = station_data.get('wind_speed_kt')
            if not wind_speed:
                winds.append({'station': station, 'speed': -1, 'gusts': wind_gusts, 'direction': wind_dir})
            else:
                winds.append({'station': station, 'speed': int(wind_speed), 'gusts': wind_gusts, 'direction': wind_dir})

        winds = sorted(winds, key=lambda x: x['speed'], reverse=True)
        for number, wind in enumerate(winds):
            if oleds.available:
                draw_display(draw, wind, oleds.width, oleds.height)
                oleds.show(number, image)
            else:
                log.info(wind)

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
