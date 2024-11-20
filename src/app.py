import settings

from flask import Flask, Response, request, render_template

from db         import Database
from log        import log
from config     import color
from airports   import get_apinfo

rdb = Database(host='127.0.0.1')

app = Flask(__name__)
app.secret_key = 'ewi90r209fu'

@app.context_processor
def utility_processor():
    def rgbhex(value:tuple):
        return '#%02x%02x%02x' % (value[0], value[1], value[2])
    '''
    def format_price(amount, currency=u'$'):
        return u'{1}{0:.2f}'.format(amount, currency)
    '''
    return dict(rgbhex=rgbhex)

def parse(line):
    """ Parse commands
    :param line:
    :return:
    """
    command = line.split()
    if command[0] == "near":
        return command


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def landing():
    """ Landing page
    """
    context = {'title': 'LiveSectional Home', 'num': 0}
    return render_template('index.html', **context)


@app.route("/ledonoff", methods=["POST"])
def ledonoff():
    num = int(request.form.get('lednum'))

    if "buton" in request.form:
        pass

    elif "butoff" in request.form:
        pass

    elif "butup" in request.form:
        pass

    elif "butall" in request.form:
        pass

    elif "butnone" in request.form:
        pass

    context = {'airports': airports,
               'title': 'Airports Editor',
               'num': num,
               'apinfo_dict': get_apinfo(airports)
               }

    return render_template('apedit.html', **context)

@app.route('/confedit', methods=['GET','POST'])
def configuration():
    if request.method == "GET":
        context = {
            'title': 'Airports Editor',
            'num': 0,
            'color':color,
            'settings': settings,
            # 'ipadd': ipadd,
            'ipaddresses': '',
            'timestr': '',
            'current_timezone': '',
            'update_available': False,
            'update_vers': False,
            'machines':[],
            'map_name':'fred',
        }
        return render_template('confedit.html', **context)



@app.route('/apedit', methods=["GET", "POST"])
def airports():
    """
    Airports Editor
    :return:
    """
    if request.method == "GET":
        with open('airports_ne', 'r') as fyle:
            airports = [line.strip().replace('\n','') for line  in fyle.readlines()]

        context = {'airports': airports,
                   'title': 'Airports Editor',
                   'num': 0,
                   'apinfo_dict': get_apinfo()
                   }

        return render_template('apedit.html', **context)

    elif request.method == "POST":
        try:
            airports = request.form.to_dict().values()
        except Exception as e:
            log.error(e)
            airports = []

        saved_airports = rdb.getall()
        for led, airport in enumerate(airports):
            pass




@app.route("/run/{command}")
def run(command, response: Response):
    """ Run commands to the server eg "near Montauk, NY 20 mile on"
    :param command:
    :return:
    """
    args = command.split()
    if not args[0] in ('near',  # Light stations nearby
                       'home',  # Change color and name of home station
                       'station',  # Change lights for a station
                       'only',  # Only show stations with a particular status eg. VFR
                       'lights',  # Turn lights off or on based on time,
                       'dim',  # Dim the lights to a value
                       'blink'
                       ):
        response.status_code = 404
        return {"detail": "Command not found"}

    if args[0] == 'near':  # Light stations nearby
        pass
    elif args[0] == 'home':  # Change color and name of home station
        pass
    elif args[0] == 'station':  # Change lights for a station
        pass
    elif args[0] == 'only':  # Only show stations with a particular status eg. VFR
        pass
    elif args[0] == 'lights':  # Turn lights off or on based on time,
        pass
    elif args[0] == 'dim':  # Dim the lights to a value
        pass
    elif args[0] == 'blink':  # Blink
        pass


@app.route("/lights/{setting}")
def lights(setting):
    """ Turn on and off lights
    :param setting: str: on or off
    :return:
    """
    if setting == 'on':
        rdb.set_values(dict(lights=1))
    elif setting == 'off':
        rdb.set_values(dict(lights=0))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
