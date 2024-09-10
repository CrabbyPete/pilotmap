import json
import uvicorn

from fastapi            import FastAPI, Response
from starlette.status   import HTTP_404_NOT_FOUND, HTTP_200_OK


from db import Database

rdb = Database(host='127.0.0.1')
app = FastAPI()


def parse(line):
    """ Parse commands
    :param line:
    :return:
    """
    command = line.split()
    if command[0] == "near":
        return command



@app.post("/run/{command}")
def run(command,response: Response):
    """ Run commands to the server eg "near Montauk, NY 20 mile on"
    :param line:
    :return:
    """
    args = command.split()
    if not args[0] in ('near',              # Light stations nearby
                        'home',              # Change color and name of home station
                        'station',           # Change lights for a station
                        'only',              # Only show stations with a particular status eg. VFR
                        'lights',            # Turn lights off or on based on time,
                        'dim',               # Dim the lights to a value
                        'blink'
                ):
        response.status_code = HTTP_404_NOT_FOUND
        return {"detail": "Command not found"}

    if args[0] == 'near':               # Light stations nearby
        pass
    elif args[0] == 'home':              # Change color and name of home station
        pass
    elif args[0] == 'station':           # Change lights for a station
        pass
    elif args[0] == 'only':              # Only show stations with a particular status eg. VFR
        pass
    elif args[0] == 'lights':            # Turn lights off or on based on time,
        pass
    elif args[0] == 'dim':               # Dim the lights to a value
        pass
    elif args[0] == 'blink':             # Blink
        pass


@app.get("/lights/{setting}")
def lights(setting):
    """ Turn on and off lights
    :param line:
    :return:
    """
    if setting == 'on':
        rdb.set_values(lights = 1)
    elif setting == 'off':
        rdb.set_value(lights = 0)


@app.get("/")
def home():
    """ Execute commands sent.
    :param station:
    :return:
    """


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
