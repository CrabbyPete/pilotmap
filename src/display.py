import pdb
import smbus2
import Adafruit_SSD1306
import RPi.GPIO as GPIO

from db             import Database
from PIL            import Image, ImageDraw, ImageFont
from Adafruit_GPIO  import I2C
from airports       import get_airports


# Set up the lights sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)

# Set up the OLED driver
disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)    # 128x64 or 128x32 - disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# This is the multiplexor. You need to set it before you write to the display
TCA_ADDR = 0x70                                     # Use cmd i2cdetect -y 1 to ensure multiplexer shows up at addr 0x70
tca = I2C.get_i2c_device(address=TCA_ADDR)

bus = smbus2.SMBus(1)                               # From smbus2 set bus number

#Create blank image for drawing.
width = disp.width
height = disp.height

image = Image.new('1', (width, height))             # Make sure to create image with mode '1' for 1-bit color.
draw = ImageDraw.Draw(image)

#Load fonts. Install font package --> sudo apt-get install ttf-mscorefonts-installer
#Also see; https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil for info
#Arrows.ttf downloaded from https://www.1001fonts.com/arrows-font.html#styles
fontsize = 24
fontindex = 0                                   # Font selected may have various versions that are indexed. 0 = Normal. Leave at 0 unless you know otherwise.
backcolor = 0                                   # 0 = Black, background color for OLED display. Shouldn't need to change
fontcolor = 255                                 # 255 = White, font color for OLED display. Shouldn't need to change
displays = 8

boldfont = ImageFont.truetype('LiberationSerif-Bold.ttf', fontsize, 0)
regfont  = ImageFont.truetype('LiberationSerif-Regular.ttf', fontsize, 0)
arrows   = ImageFont.truetype('Arrows.ttf', fontsize, 0)


def winddir(wndir=0):                           #Using the arrows.ttf font return arrow to represent wind direction at airport
    if (338 <= wndir <= 360) or (1 <= wndir <= 22): #8 arrows representing 45 degrees each around the compass.
        return 'd'                              #wind blowing from the north (pointing down)
    elif 23 <= wndir <= 67:
        return 'f'                              #wind blowing from the north-east (pointing lower-left)
    elif 68 <= wndir <= 113:
        return 'b'                              #wind blowing from the east (pointing left)
    elif 114 <= wndir <= 159:
        return 'e'                              #wind blowing from the south-east (pointing upper-left)
    elif 160 <= wndir <= 205:
        return 'c'                              #wind blowing from the south (pointing up)
    elif 206 <= wndir <= 251:
        return 'g'                              #wind blowing from the south-west (pointing upper-right)
    elif 252 <= wndir <= 297:
        return 'a'                              #wind blowing from the west (pointing right)
    elif 298 <= wndir <= 337:
        return 'h'                              #wind blowing from the north-west (pointing lower-right)
    else:
        return ''


class Display:
    """
    Class to control a single display
    """
    def __init__(self, channel):
        self.current_channel = channel
        self.select(channel)

    def select(self, channel):                 # Used to tell the multiplexer which oled display to send data to.
        self.current_channel = channel
        tca.writeRaw8(1 << self.current_channel)

    def dim(self, level=0):                         #Dimming routine. 0 = Full Brightness, 1 = low brightness, 2 = medium brightness. See https://www.youtube.com/watch?v=hFpXfSnDNSY a$
        if level == 0:                              #https://github.com/adafruit/Adafruit_Python_SSD1306/blob/master/Adafruit_SSD1306/SSD1306.py for more info.
            disp.command(0x81)                      #SSD1306_SETCONTRAST = 0x81
            disp.command(255)
            disp.command(0xDB)                      #SSD1306_SETVCOMDETECT = 0xDB
            disp.command(255)

        if level == 1 or level == 2:
            disp.command(0x81)                      #SSD1306_SETCONTRAST = 0x81
            disp.command(50)

        if level == 1:
            disp.command(0xDB)                      #SSD1306_SETVCOMDETECT = 0xDB
            disp.command(50)


    def invert(self, white=False):                  #Invert display pixels. Normal = white text on black background.
        if white:                                   #Inverted = black text on white background #0 = Normal, 1 = Inverted
            disp.command(0xA7)
        else:
            disp.command(0xA6)

    def rotate180(self):                            # Rotate display 180 degrees to allow mounting of OLED upside down
        disp.command(0xA0)
        disp.command(0xC0)

    def clear(self):
        self.select(self.current_channel)
        draw.rectangle((0,0,width-1,height-1), outline=0, fill=0)
        disp.image(image)
        disp.display()

    def show(self, image):
        disp.display()

    def oled(self, ch, wind):                        # Center text vertically and horizontally
        if ch >= displays:
            return

        offset = 3
        self.select(ch)

        disp.begin()
        disp.clear()
        disp.display()

        self.dim(0)                                  # Set brightness, 0 = Full bright, 1 = medium bright, 2 = low brightdef oledcenter(txt): #Center text vertically and horizontally
        draw.rectangle((0, 0, width-1, height-1), outline=0, fill=1) # Blank the display
        x1, y1, x2, y2 = 0, 0, width, height        #create boundaries of display
        if direction := wind.get('direction'):
            # Draw wind direction using arrows
            arrowdir = winddir(int(direction))                 #get proper proper arrow to display
            draw.text((96, 37), arrowdir, font=arrows, outline=255, fill=0) #lower right of oled

        txt = wind['station'] +'\n'+ str(wind['speed']) + ' kts'
        w, h = draw.textsize(txt, font=regfont)        #get textsize of what is to be displayed
        x = (x2 - x1 - w)/2 + x1                    #calculate center for text
        y = (y2 - y1 - h)/2 + y1 - offset

        draw.text((x, y), txt, align='center', font=regfont, fill=0) #Draw the text to buffer
        disp.image(image)                           #Display image
        disp.display()                              #display text in buffer


if __name__ == "__main__":
    ch = 1
    wind = {'station': 'KNJK', 'speed': 7, 'gusts': 0, 'direction': '250'}
    oled = Display(1)
    oled.oled(ch, wind)

