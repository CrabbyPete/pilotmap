


from datetime  import datetime
from flask     import Flask, render_template, request

# Local imports
import admin

from log  import log
from db import Database
from colors import Colors

LED_OFF = True
LED_ON  = False

rdb = Database('192.168.1.163')
color = Colors(rdb)


# Initiate flash session
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

map_name = admin.map_name
version = admin.version


#Routes for homepage
@app.route('/', methods=["GET", "POST"])
def index ():
    return render_template('index.html')

#Routes for homepage
@app.route('/settings', methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return render_template('settings.html')
    form = request.form
    return render_template('settings.html')




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


