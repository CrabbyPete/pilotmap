
import pickle

from config import color
from log import log

class Colors:
    def __init__(self, rdb):
        self.rdb = rdb
        self.reset()

    def __iter__(self):
        colors = self.rdb.getall('color')

    def get(self, clr):
        clr = self.rdb.hget('color', clr)
        try:
            color_val = eval(clr)
        except Exception as e:
            log.error(f"Error:{e} trying to eval({clr}")
            return (0,0,0)
        return color_val

    def put(self, clr, value):
        self.rdb.hset('color', clr, str(value))

    def restore(self, clr):
        self.rdb.hset('color',clr, str(getattr(color,clr)))

    def reset(self):
        for k,v in color:
            print(k,v)
            try:
                self.rdb.hset('color', k, str(v))
            except Exception as e:
                log.error(f"Error:{e} adding {k}:{v}")

    def is_off(self, led):
        """
        Is an led turned off
        :param led:
        :return:
        """
        if self.rdb.sismember('off_leds',led):
            return True
        else:
            return False

    def switch_led(self, led, off:bool):
        """
        Used to notify not to turn off an led
        :param led: int: which led to turn off
        :return:
        """
        if off:
            self.rdb.sadd('off_leds', led)
        else:
            self.rdb.srem('off_leds', led)


if __name__ == "__main__":
    from db import Database
    rdb = Database()
    colors = Colors(rdb)
    colors.restore('black')
    c = colors.get('homeport')
    for c, value in color:
        print(c,value)
    value = colors.get('black')
    print(value)
    colors.switch_led(1,True)
    colors.switch_led(2,True)
    colors.switch_led(1,False)
    print(colors.is_off(2))
    print(colors.is_off(1))