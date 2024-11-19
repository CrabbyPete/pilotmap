import smbus2
import Adafruit_SSD1306
import RPi.GPIO as GPIO


from PIL            import Image, ImageDraw, ImageFont
from Adafruit_GPIO  import I2C


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

boldfont = ImageFont.truetype('LiberationSerif-Bold.ttf', fontsize, 0)
regfont  = ImageFont.truetype('LiberationSerif-Regular.ttf', fontsize, 0)
arrows   = ImageFont.truetype('Arrows.ttf', fontsize, 0)


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


def main():
    display = Display(1)
    display.clear()



if __name__ == "__main__":
    main()

