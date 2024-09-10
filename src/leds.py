import time
import random


# LED strip configuration:
LED_PIN        = 18          # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL     = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

'''
def Color(r, g, b):
    """
    The code has Color all over, but never defined. It just returns a set to pass back to the
    Adafruit library calls
    """
    return int("0x{:02x}{:02x}{:02x}".format(r, g, b), 16)
'''
try:
    from rpi_ws281x import PixelStrip, Color

    class LedStrip:
        def __init__(self, count, brightness=LED_BRIGHTNESS):
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
            if isinstance(color, int):
                self.strip.setPixelColor(led, color)
            else:
                self.strip.setPixelColor( led, Color(color[0], color[1], color[2]))

        def clear_pixels(self):
            for led in range(self.number):
                self.strip.setPixelColor(led, 0)
            self.show_pixels()

        def show_pixels(self):
            try:
                self.strip.show()
            except Exception as e:
                print("Error:{e} trying to show pixels")

        def set_brightness(self, brightness):
            self.strip.setBrightness(LED_BRIGHTNESS)

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

except ModuleNotFoundError as e:
    class LedStrip:
        def __init__(self):
            self.strip = []
            self.number = 100

        def set_pixel_color(self, led, color):
            return

        def clear_pixels(self):
            return

        def show_pixels(self):
            return

        def set_brightness(self, brightness):
            return

        def rainbow(self, times,delay):
            return

        def fill(self, color):
            return

