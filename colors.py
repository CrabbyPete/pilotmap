from config import color
from db import Database

rdb = Database()

class Colors:
    colors = {}
    def __init__(self):
        for k,v in color:
            self.colors[k] = str(v)
        rdb.put('colors', self.colors)

    def all(self):
        return rdb.members('colors')

    def get(self,color):
        return rdb.get('colors', color)


color_state = Colors()
for m in color_state.all():
    print(color_state.get(m))
