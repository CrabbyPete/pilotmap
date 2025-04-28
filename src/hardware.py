import time
import random

from log import log

# LED strip configuration:
LED_PIN        = 18          # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL     = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Imports for hordware
hardware = True
try:
    import Adafruit_SSD1306
    import RPi.GPIO as GPIO
    from Adafruit_GPIO  import I2C

except ImportError as e:
    log.error(f"Error:{e} import modules")
    hardware = False
else:
    # Set up the lights sensor
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.IN)

lights = True
try:
    from rpi_ws281x import PixelStrip, Color
except ModuleNotFoundError as e:
    log.error(f"Error:{e} import rpi_ws2812")
    lights = False

class LedStrip:
    def __init__(self, count, brightness=LED_BRIGHTNESS):
        if not lights:
            return

        self.strip = PixelStrip(count,
                                LED_PIN,
                                LED_FREQ_HZ,
                                LED_DMA,
                                LED_INVERT,
                                brightness,
                                LED_CHANNEL)
        self.strip.begin()
        self.number = self.strip.numPixels()

    def set_pixel_color(self, led, color):
        if lights:
            if isinstance(color, int):
                self.strip.setPixelColor(led, color)
            else:
                self.strip.setPixelColor( led, Color(color[0], color[1], color[2]))

    def clear_pixels(self):
        if lights:
            for led in range(self.number):
                self.strip.setPixelColor(led, 0)
            self.show_pixels()

    def show_pixels(self):
        if lights:
            try:
                self.strip.show()
            except Exception as e:
                print("Error:{e} trying to show pixels")

    def set_brightness(self, brightness):
        if lights:
            self.strip.setBrightness(LED_BRIGHTNESS)

    def get_pixel(self, led):
        if lights:
            return self.strip.getPixelColor(led)

    def rainbow(self, times,delay):
        for _ in range(times):
            for i in range(self.number):
                self.set_pixel_color(i, Color(random.randint(0, 255),
                                              random.randint(0, 255),
                                              random.randint(0, 255)))
            self.show_pixels()
            time.sleep(delay)

    def fill(self, color):
        for i in range(self.number):
            self.set_pixel_color(i, color)
        self.show_pixels()



class Display:
    """
    Class to control a single display
    """
    def __init__(self):
        try:
            self.tca = I2C.get_i2c_device(address=0x70)
            self.tca.writeRaw8(1 << 0)
            self.display = Adafruit_SSD1306.SSD1306_128_64(rst=None)
        except Exception as e:
            log.error(f"Error:{e} setting up display")
            self.hardware = False
        else:
            self.hardware = True

    @property
    def width(self):
        if self.hardware:
            return self.display.width
        else:
            return 128

    @property
    def height(self):
        if self.hardware:
            return self.display.height
        else:
            return 64

    def select(self, channel):                 # Used to tell the multiplexer which oled display to send data to.
        if self.hardware:
            self.current_channel = channel
            self.tca.writeRaw8(1 << self.current_channel)

    def dim(self, level=None):
        """
        Dimming routine. 0 = Full Brightness, 1 = low brightness, 2 = medium brightness.
        See https://www.youtube.com/watch?v=hFpXfSnDNSY a$
        :param level: int:
        :return:
        """
        if not self.hardware:
            return

        if not level:
            level = GPIO.input(4)

        if level == 0:
            self.display.command(0x81)                      # SSD1306_SETCONTRAST = 0x81
            self.display.command(255)
            self.display.command(0xDB)                      # SSD1306_SETVCOMDETECT = 0xDB
            self.display.command(255)

        if level == 1 or level == 2:
            self.display.command(0x81)                      # SSD1306_SETCONTRAST = 0x81
            self.display.command(50)

        if level == 1:
            self.display.command(0xDB)                      # SSD1306_SETVCOMDETECT = 0xDB
            self.display.command(50)

    def invert(self, white=False):
        """
        Invert display pixels. Normal = white text on black background.
        :param white:
        :return:
        """
        if not hardware:
            return

        if white:                                 # Inverted = black text on white background #0 = Normal, 1 = Inverted
            self.display.command(0xA7)
        else:
            self.display.command(0xA6)

    def rotate180(self):
        """
        Rotate display 180 degrees to allow mounting of OLED upside down
        """
        if self.hardware:
            self.display.command(0xA0)
            self.display.command(0xC0)

    def clear(self):
        """
        Clear a display
        :return:
        """
        if self.hardware:
            self.select(self.current_channel)
            self.display.clear()

    def show(self, ch, display_image):
        """
        Display wind info on a display
        :param ch: which display
        :param display_image: Image
        :return:
        """
        # Center text vertically and horizontally
        if not self.hardware:
            return

        if ch >= 8:
            return

        self.select(ch)
        self.display.begin()
        self.display.clear()
        self.display.display()

        self.dim()
        self.display.image(display_image)
        self.display.display()


class Switches:
    def __init__(self):
        if not hardware:
            return

        GPIO.setup(0, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 0 to ground for METARS
        GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 5 to ground for TAF + 1 hour
        GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 6 to ground for TAF + 2 hours
        GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 13 to ground for TAF + 3 hours
        GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 19 to ground for TAF + 4 hours
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 26 to ground for TAF + 5 hours
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 21 to ground for TAF + 6 hours
        GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 20 to ground for TAF + 7 hours
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 16 to ground for TAF + 8 hours
        GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 12 to ground for TAF + 9 hours
        GPIO.setup(1, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 1 to ground for TAF + 10 hours
        GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 7 to ground for TAF + 11 hours

    @property
    def state(self):
        pass

    def get(self, number):
        if hardware:
            return GPIO.input(number)
        return 0

