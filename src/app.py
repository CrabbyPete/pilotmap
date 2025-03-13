import os
import sys
import wget
import json
import time
import socket
import shutil
import logging
import zipfile
import requests
import subprocess

import folium
import folium.plugins
from folium.features import DivIcon

import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse

from logzero   import logger
from itertools import islice
from datetime  import datetime
from flask     import Flask, render_template, request, flash, redirect, send_file, Response

# Local imports
import admin
import config
from log  import log as logger
from db import Database
from colors import Colors
from airports import get_airport_info
from weather import weather

LED_OFF = True
LED_ON  = False

rdb = Database('192.168.1.163')
color = Colors(rdb)

"""
from leds import LedStrip

try:
    from leds import Color
except ImportError as e:
    def Color(r,g,b):
        return r,g,b
"""


PATH = '.'
airports_file  = f'{PATH}/airports'
airports_bkup  = f'{PATH}/airports-bkup'
settings_file  = f'{PATH}/settings.py'
settings_bkup  = f'{PATH}/settings-bkup.py'
heatmap_file   = f'{PATH}/hmdata'
local_ftp_file = f'{PATH}/lsinfo.txt'

settings    = {}
airports    = []
hmdata      = []
datalist    = []
newlist     = []
ipaddresses = []
current_timezone = ''
loc         = {}
machines    = []
lat_list    = []
lon_list    = []
max_lat     = ''
min_lat     = ''
max_lon     = ''
min_lon     = ''

max_api_airports = 300

# Settings for web based file updating
src         = f'{PATH}/'                        # Main directory, /NeoSectional
dest        = f'{PATH}/backup/previousversion'  # Directory to store currently run version of software
verfilename = 'version.py'                      # Version Filename
zipfilename = 'ls.zip'                          # File that holds the names of all the files that need to be updated
source_path = 'http://www.livesectional.com/liveupdate/neoupdate/'
target_path = f'{PATH}/'

update_available = 0                            # 0 = No update available, 1 = Yes update available
update_vers = "4.000"                           # initiate variable

# Used to capture station information for airport id decode for tooltip display in web pages.
apinfo_dict = {}
orig_apurl  = "https://aviationweather.gov/api/data/stationinfo?format=xml&ids="

#Used to display weather and airport locations on a map
led_map_dict = {}
led_map_url = "https://aviationweather.gov/api/data/metar?format=xml&hours=2.5&ids="

now = datetime.now()
timestr = (now.strftime("%H:%M:%S - %b %d, %Y"))
delay_time = 5                  # Delay in seconds between checking for internet availablility.
num = 0                         # initialize num for airports editor
ipadd = ''


#strip = LedStrip(config.LED_COUNT)


# Initiate flash session
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

map_name = admin.map_name
version = admin.version

logger.info("Settings and Flask Have Been Setup")


# Routes for Map Display - Testing
@app.route('/map1', methods=["GET", "POST"])
def map1():
    start_coords = (35.1738, -111.6541)
    folium_map = folium.Map(location=start_coords,
                            zoom_start = 6,
                            height='80%',
                            width='100%',
                            control_scale = True,
                            zoom_control = True,
                            tiles = 'OpenStreetMap')

    folium_map.add_child(folium.LatLngPopup())
    folium_map.add_child(folium.ClickForMarker(popup='Marker'))
    folium.plugins.Geocoder().add_to(folium_map)

    folium.TileLayer('http://wms.chartbundle.com/tms/1.0.0/sec/{z}/{x}/{y}.png?origin=nw',
                     attr='chartbundle.com', name='ChartBundle Sectional').add_to(folium_map)

    folium.TileLayer('Stamen Terrain', name='Stamen Terrain').add_to(folium_map)
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(folium_map)
    # other mapping code (e.g. lines, markers etc.)
    folium.LayerControl().add_to(folium_map)

    folium_map.save(f'{PATH}/templates/map.html')
    return render_template('mapedit.html', title='Map', num = 5)


@app.route('/touchscr', methods=["GET", "POST"])
def touchscr():
    return render_template('touchscr.html',
                           title = 'Touch Screen',
                           num = 5,
                           machines = machines,
                           ipadd = ipadd)


@app.route('/open_console', methods=["GET", "POST"])
def open_console():
    console_ips = []
    with open(f"{PATH}/console_ip.txt", "r") as file:
        for line in (file.readlines() [-1:]):
            line = line.rstrip()
            console_ips.append(line)
    logger.info("Opening open_console in separate window")
    return render_template('open_console.html',
                           urls = console_ips,
                           title = 'Display Console Output-'+version, num = 5,
                           machines = machines,
                           ipadd = ipadd,
                           timestr = timestr)


@app.route('/stream_log', methods=["GET", "POST"])
def stream_log():
    """
    # Routes to display logfile live, and hopefully for a dashboard
    :return:
    """
    global ipadd
    global timestr
    logger.info("Opening stream_log in separate window")
    return render_template('stream_log.html',
                           title = 'Display Logfile-'+version,
                           num = 5,
                           machines = machines,
                           ipadd = ipadd,
                           timestr = timestr)


@app.route('/stream_log1', methods=["GET", "POST"])
def stream_log1():
    def generate():
        with open(f'{PATH}/logfile.log') as f:
            while True:
                yield "{}\n".format(f.read())
                time.sleep(1)

    return app.response_class(generate(), mimetype='text/plain')


@app.route('/test_for_update', methods=["GET", "POST"])
def test_for_update():
    """
     Route to manually check for update using menu item
    :return:
    """
    global update_available
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
    testupdate()

    if update_available == 0:
        flash('No Update Available')

    elif update_available == 1:
        flash('UPDATE AVAILABLE, Use Map Utilities to Update')

    else:
        flash('New Image Available -  Use Map Utilities to Download')

    logger.info('Checking to see if there is an update available')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


@app.route('/update_info', methods=["GET", "POST"])
def update_info():
    """
    Route to update Software if one is available and user chooses to update
    :return:
    """
    global ipadd
    global timestr
    with open(f"{PATH}/update_info.txt","r") as file:
        content = file.readlines()
        logger.debug(content)
    return render_template("update_info.html",
                           content = content,
                           title = 'Update Info-'+version, num = 5,
                           machines = machines,
                           ipadd = ipadd,
                           timestr = timestr)


@app.route('/update', methods=["GET", "POST"])
def update():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
    updatefiles()
    flash('Software has been updated to v' + update_vers)
    logger.info('Updated Software to version ' + update_vers)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


@app.route('/update_page', methods=["GET", "POST"])
def update_page():
    global ipadd
    global timestr
    return render_template("update_page.html", title = 'Software Update Information-'+version, num = 5, machines = machines, ipadd = ipadd, timestr = timestr)


# Route to display map's airports on a digital map.
@app.route('/led_map', methods=["GET", "POST"])
def led_map():
    global hmdata
    global airports
    global led_map_dict
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global timestr
    global version
    global map_name
    global current_timezone

    templateData = {
        'title': 'LiveSectional Map-'+version,
        'hmdata': hmdata,
        'airports': airports,
        'settings': settings,
        'ipadd': ipadd,
        'strip': strip,
        'ipaddresses': ipaddresses,
        'num': num,
        'apinfo_dict': apinfo_dict,
        'led_map_dict': led_map_dict,
        'timestr': timestr,
        'version': version,
        'update_available': update_available,
        'update_vers': update_vers,
        'current_timezone': current_timezone,
        'machines': machines,
        'map_name':map_name,
        'max_lat': max_lat,
        'min_lat': min_lat,
        'max_lon': max_lon,
        'min_lon': min_lon,
    }

    # Update flight categories
    get_led_map_info()

    points = []
    title_coords = (max_lat,(float(max_lon)+float(min_lon))/2)
    start_coords = ((float(max_lat)+float(min_lat))/2, (float(max_lon)+float(min_lon))/2)

    # Initialize Map
    folium_map = folium.Map(location=start_coords,
                            zoom_start = 5,
                            height='100%',
                            width='100%',
                            control_scale = True,
                            zoom_control = True,
                            tiles = 'OpenStreetMap')

    # Place map within bounds of screen
    folium_map.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Set Marker Color by Flight Category
    for j,led_ap in enumerate(led_map_dict):
        if led_map_dict[led_ap][2] == "VFR":
            color = 'green'
        elif led_map_dict[led_ap][2] == "MVFR":
            color = 'blue'
        elif led_map_dict[led_ap][2] == "IFR":
            color = 'red'
        elif led_map_dict[led_ap][2] == "LIFR":
            color = 'violet'
        else:
            color = 'black'

        # Get Pin Number to display in popup
        if led_ap in airports:
            pin_num = airports.index(led_ap)
        else:
            pin_num = None

        try:
            pop_url = '<a href="https://nfdc.faa.gov/nfdcApps/services/ajv5/airportDisplay.jsp?airportId='+led_ap+'"target="_blank">'
            popup = pop_url+"<b>"+led_ap+"</b><br>"+apinfo_dict[led_ap][0]+',&nbsp'+apinfo_dict[led_ap][1] \
                    +"</a><br>Pin&nbspNumber&nbsp=&nbsp"+str(pin_num)+"<br><b><font size=+2 color="+color+">"+led_map_dict[led_ap][2]+"</font></b>"
        except:
            pop_url = ""
            popup = ""
            pass

        # Add airport markers with proper color to denote flight category
        folium.CircleMarker(
            radius=7,
            fill=True,
            color=color,
            location=[led_map_dict[led_ap][0], led_map_dict[led_ap][1]],
            popup=popup,
            tooltip=str(led_ap)+"<br>Pin "+str(pin_num),
            weight=6,
        ).add_to(folium_map)

    # Add lines between airports. Must make lat/lons floats otherwise recursion error occurs.
    for pin_ap in airports:
        if pin_ap in led_map_dict:
            pin_index = airports.index(pin_ap)
            points.insert(pin_index, [float(led_map_dict[pin_ap][0]), float(led_map_dict[pin_ap][1])])

    logger.debug(points)
    folium.PolyLine(points, color='grey', weight=2.5, opacity=1, dash_array='10').add_to(folium_map)

    # Add Title to the top of the map
    folium.map.Marker(
        title_coords,
        icon=DivIcon( icon_size=(500,36),
                      icon_anchor=(150,64),
                      html='<div style="font-size: 24pt"><b>LiveSectional Map Layout</b></div>',
                      )
    ).add_to(folium_map)

    # Extra features to add if desired
    folium_map.add_child(folium.LatLngPopup())
    folium.plugins.Geocoder().add_to(folium_map)

    folium.plugins.Fullscreen(
        position="topright",
        title="Full Screen",
        title_cancel="Exit Full Screen",
        force_separate_button=True,
    ).add_to(folium_map)

    folium.TileLayer('http://wms.chartbundle.com/tms/1.0.0/sec/{z}/{x}/{y}.png?origin=nw', attr='chartbundle.com', name='ChartBundle Sectional').add_to(folium_map)
    folium.TileLayer('Stamen Terrain', name='Stamen Terrain').add_to(folium_map)
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(folium_map)
    folium.LayerControl().add_to(folium_map)

    folium_map.save(f'{PATH}/templates/map.html')
    logger.info("Opening led_map in separate window")
    return render_template('led_map.html', **templateData)


# Route to expand RPI's file system.
@app.route('/expandfs', methods=["GET", "POST"])
def expandfs():
    global hmdata
    global airports
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global timestr
    global version
    global map_name
    global current_timezone

    if request.method == "POST":
        os.system('sudo raspi-config --expand-rootfs')
        flash('File System has been expanded')
        flash('NOTE: Select "Reboot RPI" from "Map Functions" Menu for changes to take affect')

        return redirect('expandfs')

    else:
        templateData = {
            'title': 'Expand File System-'+version,
            'hmdata': hmdata,
            'airports': airports,
            'settings': settings,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'num': num,
            'apinfo_dict': apinfo_dict,
            'timestr': timestr,
            'version': version,
            'map_name':map_name,
            'update_available': update_available,
            'update_vers': update_vers,
            'current_timezone': current_timezone,
            'machines': machines
        }
        logger.info("Opening expand file system page")
        return render_template('expandfs.html', **templateData)


# Route to display and change Time Zone information.
@app.route('/tzset', methods=["GET", "POST"])
def tzset():
    global hmdata
    global airports
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global timestr
    global version
    global map_name
    global current_timezone

    timestr = datetime.now().strftime("%H:%M:%S - %b %d, %Y")
    currtzinfolist = []

    if request.method == "POST":
        timezone = request.form['tzselected']
        flash('Timezone set to ' + timezone)
        flash('NOTE: Select "Reboot RPI" from "Map Functions" Menu for changes to take affect')
        os.system('sudo timedatectl set-timezone ' + timezone)
        return redirect('tzset')

    tzlist = subprocess.run(['timedatectl', 'list-timezones'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    tzoptionlist = tzlist.split()

    currtzinfo = subprocess.run(['timedatectl', 'status'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    tztemp = currtzinfo.split('\n')
    for j in range(len(tztemp)):
        if j==0 or j==1 or j==3:
            currtzinfolist.append(tztemp[j])
    current_timezone = tztemp[3]

    templateData = {
        'title': 'Timezone Set-'+version,
        'hmdata': hmdata,
        'airports': airports,
        'settings': settings,
        'ipadd': ipadd,
        'strip': strip,
        'ipaddresses': ipaddresses,
        'num': num,
        'apinfo_dict': apinfo_dict,
        'timestr': timestr,
        'version': version,
        'map_name':map_name,
        'update_available': update_available,
        'update_vers': update_vers,
        'tzoptionlist': tzoptionlist,
        'currtzinfolist': currtzinfolist,
        'current_timezone': current_timezone,
        'machines': machines
    }

    logger.info("Opening Time Zone Set page")
    return render_template('tzset.html', **templateData)


# Route to display system information.
@app.route('/yield')
def yindex():
    def inner():
        proc = subprocess.Popen(
            [f'{PATH}//info-v4.py'],             # 'dmesg' call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline,b''):
            time.sleep(.01)                           # Don't need this just shows the text streaming
            line = line.decode("utf-8")
            yield line.strip() + '<br/>\n'

    logger.info("Opening yeild to display system info in separate window")
    return Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show this info.


# Route to create QR Code to display next to map so user can use an app to control the map
@app.route('/qrcode', methods=["GET", "POST"])
def qrcode():
    global ipadd
    qraddress = 'http://' + ipadd.strip() + ':5000/lsremote'
    logger.info("Opening qrcode in separate window")
    return render_template('qrcode.html', qraddress = qraddress)


#Routes for homepage
@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index ():
    global hmdata
    global airports
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global version
    global map_name

    timestr = datetime.now().strftime("%H:%M:%S - %b %d, %Y")

    templateData = {
        'title': 'LiveSectional Home-'+version,
        'hmdata': hmdata,
        'airports': airports,
        'settings': settings,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'num': num,
        'apinfo_dict': apinfo_dict,
        'timestr': timestr,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'version': version,
        'machines': machines,
        'map_name':map_name
    }

    #    flash(machines) # Debug
    logger.info("Opening Home Page/Index")
    return render_template('index.html', **templateData)


# Routes to download airports, logfile.log and config.py to local computer
@app.route('/download_ap', methods=["GET", "POST"])
def downloadairports ():
    logger.info("Downloaded Airport File")
    path = "airports"
    return send_file(path, as_attachment=True)


@app.route('/download_cf', methods=["GET", "POST"])
def downloadconfig ():
    logger.info("Downloaded Config File")
    path = "config.py"
    return send_file(path, as_attachment=True)


@app.route('/download_log', methods=["GET", "POST"])
def downloadlog ():
    logger.info("Downloaded Logfile")
    path = "logfile.log"
    return send_file(path, as_attachment=True)


@app.route('/download_hm', methods=["GET", "POST"])
def downloadhm ():
    logger.info("Downloaded Heat Map data file")
    path = "hmdata"
    return send_file(path, as_attachment=True)


# Routes for Heat Map Editor
@app.route("/hmedit", methods=["GET", "POST"])
def hmedit():
    logger.info("Opening hmedit.html")
    #global strip
    global num
    global ipadd
    global ipaddresses
    global map_name

    timestr  = datetime.now().strftime("%H:%M:%S - %b %d, %Y")
    readhmdata(heatmap_file)  # read Heat Map data file
    logger.debug(ipadd)  # debug to display ip address on console

    templateData = {
        'title': 'Heat Map Editor-'+version,
        'hmdata': hmdata,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines,
        'map_name':map_name
    }
    return render_template('hmedit.html', **templateData)


@app.route("/hmpost", methods=["GET", "POST"])
def handle_hmpost_request():
    logger.info("Saving Heat Map Data File")
    global hmdata
    #global strip
    global num
    global ipadd
    global ipaddresses
    global timestr
    newlist = []

    if request.method == "POST":
        data = request.form.to_dict()
        logger.debug(data)  # debug

        j = 0
        for key in data:
            value = data.get(key)

            if value == '':
                value = '0'

            newlist.append(airports[j] + " " + value)
            j += 1

        writehmdata(newlist, heatmap_file)
        get_apinfo()

    flash('Heat Map Data Successfully Saved')
    return redirect("hmedit")


# Import a file to populate Heat Map Data. Must Save Airports to keep
@app.route("/importhm", methods=["GET", "POST"])
def importhm():
    logger.info("Importing Heat Map File")
    global ipaddresses
    global airports
    global timestr
    global hmdata
    hmdata = []

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect(f'{PATH}/hmedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect(f'{PATH}/hmedit')

    filedata = file.read()
    tmphmdata = bytes.decode(filedata)
    logger.debug(tmphmdata)
    hmdata = tmphmdata.split('\n')
    hmdata.pop()
    logger.debug(hmdata)

    templateData = {
        'title': 'Heat Map Editor-'+version,
        'hmdata': hmdata,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines
    }
    flash('Heat Map Imported - Click "Save Heat Map File" to save')
    return render_template("hmedit.html", **templateData)

"""
# Routes for Airport Editor
@app.route("/apedit", methods=["GET", "POST"])
def apedit():
    logger.info("Opening apedit.html")
    global airports
    global num
    global ipadd
    global ipaddresses
    global map_name

    timestr = datetime.now().strftime("%H:%M:%S - %b %d, %Y")

    readairports(airports_file)  # Read airports file.

    logger.debug(ipadd)  # debug to display ip address on console
    templateData = {
        'title': 'Airports Editor-'+version,
        'airports': airports,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': get_airport_info(), # PJD apinfo_dict,
        'machines': machines,
        'map_name':map_name
    }
    return render_template('apedit.html', **templateData)
"""
@app.route('/apedit', methods=["GET", "POST"])
def airports():
    """
    Airports Editor
    :return:
    """
    if request.method == "GET":
        with open('airports', 'r') as fyle:
            airports = [line.strip().replace('\n','') for line  in fyle.readlines()]
    elif request.method == "POST":
            airports = request.form.to_dict().values()
            with open('airports', 'w') as fyle:
                for airport in airports:
                    fyle.write(f"{airport}\r\n")

            command = "sudo systemctl start weather"
            ok = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            command = "sudo systemctl restart lights"
            ok = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    apinfo_dict = get_airport_info(airports)
    templateData = {
        'title': 'Airports Editor-'+version,
        'airports': airports,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines,
        'map_name':map_name
    }

    return render_template('apedit.html', **templateData)





@app.route("/numap", methods=["GET", "POST"])
def numap():
    logger.info("Updating Number of Airports in airport file")
    global ipaddresses
    global airports
    global timestr

    if request.method == "POST":
        numap = int(request.form["numofap"])
        print (numap)

    readairports(airports_file)

    newnum = numap - int(len(airports))
    if newnum < 0:
        airports = airports[:newnum]
    else:
        for n in range(len(airports), numap):
            airports.append("NULL")

    templateData = {
        'title': 'Airports Editor-'+version,
        'airports': airports,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines
    }

    flash('Number of LEDs Updated - Click "Save Airports" to save.')
    return render_template('apedit.html', **templateData)


@app.route("/appost", methods=["GET", "POST"])
def handle_appost_request():
    logger.info("Saving Airport File")
    global airports
    global hmdata
    #global strip
    global num
    global ipadd
    global ipaddresses

    if request.method == "POST":
        data = request.form.to_dict()
        logging.debug(data)  # debug
        writeairports(data, airports_file)

        readairports(airports_file)
        get_apinfo()  # decode airports to get city and state to display

        # update size and data of hmdata based on saved airports file.
        readhmdata(heatmap_file)  # get heat map data to update with newly edited airports file
        if len(hmdata) > len(airports):  # adjust size of hmdata list if length is larger than airports
            num = len(hmdata) - len(airports)
            hmdata = hmdata[:-num]

        elif len(hmdata) < len(airports):  # adjust size of hmdata list if length is smaller than airports
            for n in range(len(hmdata), len(airports)):
                hmdata.append('NULL 0')

        for index, airport in enumerate(airports):  # now that both lists are same length, be sure the data matches
            ap, *_ = hmdata[index].split()
            if ap != airport:
                hmdata[index] = (airport + ' 0')  # save changed airport and assign zero landings to it in hmdata
        writehmdata(hmdata, heatmap_file)

    flash('Airports Successfully Saved')
    return redirect("apedit")


@app.route("/ledonoff", methods=["GET", "POST"])
def ledonoff():
    logger.info("Controlling LED's on/off")
    global airports
    #global strip
    global num
    global ipadd
    global ipaddresses
    global timestr

    """
    for i in range(strip.number):
        strip.set_pixel_color(i, Color(0,0,0))
    strip.show_pixels()
    """

    if request.method == "POST":
        readairports(airports_file)

        if "buton" in request.form:
            num = int(request.form['lednum'])
            logger.info("LED " + str(num) + " On")
            color.switch_led(num,LED_ON)
            #strip.set_pixel_color(num, Color(155,155,155))
            #strip.show_pixels()
            flash('LED ' + str(num) + ' On')

        elif "butoff" in request.form:
            num = int(request.form['lednum'])
            logger.info("LED " + str(num) + " Off")
            color.switch_led(num, LED_OFF)
            #strip.set_pixel_color(num, Color(0,0,0))
            #strip.show_pixels()
            flash('LED ' + str(num) + ' Off')

        elif "butup" in request.form:
            logger.info("LED UP")
            num = int(request.form['lednum'])
            #strip.set_pixel_color(num, Color(0,0,0))
            num = num + 1

            if num > len(airports):
                num = len(airports)

            #strip.set_pixel_color(num, Color(155,155,155))
            #strip.show_pixels()
            flash('LED ' + str(num) + ' should be On')

        elif "butdown" in request.form:
            logger.info("LED DOWN")
            num = int(request.form['lednum'])
            color.switch_led(num, LED_OFF)
            #strip.set_pixel_color(num, Color(0,0,0))

            num = num - 1
            if num < 0:
                num = 0

            color.switch_led(num, LED_ON)
            #strip.set_pixel_color(num, Color(155,155,155))
            #strip.show_pixels()
            flash('LED ' + str(num) + ' should be On')

        elif "butall" in request.form:
            logger.info("LED All ON")
            num = int(request.form['lednum'])

            for num in range(len(airports)):
                color.switch_led(num, LED_ON)
                #strip.set_pixel_color(num, Color(155,155,155))
            #strip.show_pixels()
            flash('All LEDs should be On')
            num=0

        elif "butnone" in request.form:
            logger.info("LED All OFF")
            num = int(request.form['lednum'])

            for num in range(len(airports)):
                color.switch_led(num, LED_OFF)
                #strip.set_pixel_color(num, Color(0,0,0))
            #strip.show_pixels()
            flash('All LEDs should be Off')
            num=0

        else:  # if tab is pressed
            logger.info("LED Edited")
            num = int(request.form['lednum'])
            flash('LED ' + str(num) + ' Edited')

    templateData = {
        'title': 'Airports File Editor-'+version,
        'airports': airports,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines
    }

    return render_template("apedit.html", **templateData)


# Import a file to populate airports. Must Save Airports to keep
@app.route("/importap", methods=["GET", "POST"])
def importap():
    logger.info("Importing Airports File")
    global ipaddresses
    global airports
    global timestr

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect(f'{PATH}/apedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect(f'{PATH}/apedit')

    filedata = file.read()
    fdata = bytes.decode(filedata)
    logger.debug(fdata)
    airports = fdata.split('\n')
    airports.pop()
    logger.debug(airports)

    templateData = {
        'title': 'Airports Editor-'+version,
        'airports': airports,
        'ipadd': ipadd,
        #'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'apinfo_dict': apinfo_dict,
        'machines': machines
    }
    flash('Airports Imported - Click "Save Airports" to save')
    return render_template("apedit.html", **templateData)


# Routes for Config Editor
@app.route("/confedit", methods=["GET", "POST"])
def confedit():
    logger.info("Opening confedit.html")
    global ipaddresses
    global ipadd
    global timestr
    global settings
    global map_name

    now = datetime.now()
    timestr = (now.strftime("%H:%M:%S - %b %d, %Y"))

    logger.debug(ipadd)  # debug

    # change rgb code to hex for html color picker
    color_vfr_hex = rgb2hex(settings["color_vfr"])
    color_mvfr_hex = rgb2hex(settings["color_mvfr"])
    color_ifr_hex = rgb2hex(settings["color_ifr"])
    color_lifr_hex = rgb2hex(settings["color_lifr"])
    color_nowx_hex = rgb2hex(settings["color_nowx"])
    color_black_hex = rgb2hex(settings["color_black"])
    color_lghtn_hex = rgb2hex(settings["color_lghtn"])
    color_snow1_hex = rgb2hex(settings["color_snow1"])
    color_snow2_hex = rgb2hex(settings["color_snow2"])
    color_rain1_hex = rgb2hex(settings["color_rain1"])
    color_rain2_hex = rgb2hex(settings["color_rain2"])
    color_frrain1_hex = rgb2hex(settings["color_frrain1"])
    color_frrain2_hex = rgb2hex(settings["color_frrain2"])
    color_dustsandash1_hex = rgb2hex(settings["color_dustsandash1"])
    color_dustsandash2_hex = rgb2hex(settings["color_dustsandash2"])
    color_fog1_hex = rgb2hex(settings["color_fog1"])
    color_fog2_hex = rgb2hex(settings["color_fog2"])
    color_homeport_hex = rgb2hex(settings["color_homeport"])

    # color picker for transitional wipes
    fade_color1_hex = rgb2hex(settings["fade_color1"])
    allsame_color1_hex = rgb2hex(settings["allsame_color1"])
    allsame_color2_hex = rgb2hex(settings["allsame_color2"])
    shuffle_color1_hex = rgb2hex(settings["shuffle_color1"])
    shuffle_color2_hex = rgb2hex(settings["shuffle_color2"])
    radar_color1_hex = rgb2hex(settings["radar_color1"])
    radar_color2_hex = rgb2hex(settings["radar_color2"])
    circle_color1_hex = rgb2hex(settings["circle_color1"])
    circle_color2_hex = rgb2hex(settings["circle_color2"])
    square_color1_hex = rgb2hex(settings["square_color1"])
    square_color2_hex = rgb2hex(settings["square_color2"])
    updn_color1_hex = rgb2hex(settings["updn_color1"])
    updn_color2_hex = rgb2hex(settings["updn_color2"])
    morse_color1_hex = rgb2hex(settings["morse_color1"])
    morse_color2_hex = rgb2hex(settings["morse_color2"])
    rabbit_color1_hex = rgb2hex(settings["rabbit_color1"])
    rabbit_color2_hex = rgb2hex(settings["rabbit_color2"])
    checker_color1_hex = rgb2hex(settings["checker_color1"])
    checker_color2_hex = rgb2hex(settings["checker_color2"])


    # Pass data to html document
    templateData = {
        'title': 'Settings Editor-'+version,
        'settings': settings,
        'ipadd': ipadd,
        'ipaddresses': ipaddresses,
        'timestr': timestr,
        'num': num,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'machines': machines,
        'map_name':map_name,

        # Color Picker Variables to pass
        'color_vfr_hex': color_vfr_hex,
        'color_mvfr_hex': color_mvfr_hex,
        'color_ifr_hex': color_ifr_hex,
        'color_lifr_hex': color_lifr_hex,
        'color_nowx_hex': color_nowx_hex,
        'color_black_hex': color_black_hex,
        'color_lghtn_hex': color_lghtn_hex,
        'color_snow1_hex': color_snow1_hex,
        'color_snow2_hex': color_snow2_hex,
        'color_rain1_hex': color_rain1_hex,
        'color_rain2_hex': color_rain2_hex,
        'color_frrain1_hex': color_frrain1_hex,
        'color_frrain2_hex': color_frrain2_hex,
        'color_dustsandash1_hex': color_dustsandash1_hex,
        'color_dustsandash2_hex': color_dustsandash2_hex,
        'color_fog1_hex': color_fog1_hex,
        'color_fog2_hex': color_fog2_hex,
        'color_homeport_hex': color_homeport_hex,

        # Color Picker Variables to pass
        'fade_color1_hex': fade_color1_hex,
        'allsame_color1_hex': allsame_color1_hex,
        'allsame_color2_hex': allsame_color2_hex,
        'shuffle_color1_hex': shuffle_color1_hex,
        'shuffle_color2_hex': shuffle_color2_hex,
        'radar_color1_hex': radar_color1_hex,
        'radar_color2_hex': radar_color2_hex,
        'circle_color1_hex': circle_color1_hex,
        'circle_color2_hex': circle_color2_hex,
        'square_color1_hex': square_color1_hex,
        'square_color2_hex': square_color2_hex,
        'updn_color1_hex': updn_color1_hex,
        'updn_color2_hex': updn_color2_hex,
        'morse_color1_hex': morse_color1_hex,
        'morse_color2_hex': morse_color2_hex,
        'rabbit_color1_hex': rabbit_color1_hex,
        'rabbit_color2_hex': rabbit_color2_hex,
        'checker_color1_hex': checker_color1_hex,
        'checker_color2_hex': checker_color2_hex
    }
    return render_template('confedit.html', **templateData)


@app.route("/post", methods=["GET", "POST"])
def handle_post_request():
    logger.info("Saving Config File")
    global ipaddresses
    global timestr

    if request.method == "POST":
        data = request.form.to_dict()

        # convert hex value back to rgb string value for storage
        data["color_vfr"] = str(hex2rgb(data["color_vfr"]))
        data["color_mvfr"] = str(hex2rgb(data["color_mvfr"]))
        data["color_ifr"] = str(hex2rgb(data["color_ifr"]))
        data["color_lifr"] = str(hex2rgb(data["color_lifr"]))
        data["color_nowx"] = str(hex2rgb(data["color_nowx"]))
        data["color_black"] = str(hex2rgb(data["color_black"]))
        data["color_lghtn"] = str(hex2rgb(data["color_lghtn"]))
        data["color_snow1"] = str(hex2rgb(data["color_snow1"]))
        data["color_snow2"] = str(hex2rgb(data["color_snow2"]))
        data["color_rain1"] = str(hex2rgb(data["color_rain1"]))
        data["color_rain2"] = str(hex2rgb(data["color_rain2"]))
        data["color_frrain1"] = str(hex2rgb(data["color_frrain1"]))
        data["color_frrain2"] = str(hex2rgb(data["color_frrain2"]))
        data["color_dustsandash1"] = str(hex2rgb(data["color_dustsandash1"]))
        data["color_dustsandash2"] = str(hex2rgb(data["color_dustsandash2"]))
        data["color_fog1"] = str(hex2rgb(data["color_fog1"]))
        data["color_fog2"] = str(hex2rgb(data["color_fog2"]))
        data["color_homeport"] = str(hex2rgb(data["color_homeport"]))

        # convert hex value back to rgb string value for storage for Transitional wipes
        data["fade_color1"] = str(hex2rgb(data["fade_color1"]))
        data["allsame_color1"] = str(hex2rgb(data["allsame_color1"]))
        data["allsame_color2"] = str(hex2rgb(data["allsame_color2"]))
        data["shuffle_color1"] = str(hex2rgb(data["shuffle_color1"]))
        data["shuffle_color2"] = str(hex2rgb(data["shuffle_color2"]))
        data["radar_color1"] = str(hex2rgb(data["radar_color1"]))
        data["radar_color2"] = str(hex2rgb(data["radar_color2"]))
        data["circle_color1"] = str(hex2rgb(data["circle_color1"]))
        data["circle_color2"] = str(hex2rgb(data["circle_color2"]))
        data["square_color1"] = str(hex2rgb(data["square_color1"]))
        data["square_color2"] = str(hex2rgb(data["square_color2"]))
        data["updn_color1"] = str(hex2rgb(data["updn_color1"]))
        data["updn_color2"] = str(hex2rgb(data["updn_color2"]))
        data["morse_color1"] = str(hex2rgb(data["morse_color1"]))
        data["morse_color2"] = str(hex2rgb(data["morse_color2"]))
        data["rabbit_color1"] = str(hex2rgb(data["rabbit_color1"]))
        data["rabbit_color2"] = str(hex2rgb(data["rabbit_color2"]))
        data["checker_color1"] = str(hex2rgb(data["checker_color1"]))
        data["checker_color2"] = str(hex2rgb(data["checker_color2"]))

        # check and fix data with leading zeros.
        for key in data:
            if data[key]=='0' or data[key]=='00':
                data[key] = '0'

            elif data[key][:1] == '0':  # Check if first character is a 0. i.e. 01, 02 etc.
                data[key] = data[key].lstrip('0')  # if so, then strip the leading zero before writing to file.

        writeconf(data, settings_file)
        readconf(settings_file)
        flash('Settings Successfully Saved')

        url = request.referrer
        if url is None:
            url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

        temp = url.split('/')
        return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Routes for LSREMOTE - Allow Mobile Device Remote. Thank
@app.route('/lsremote', methods=["GET", "POST"])
def confeditmobile():
    logger.info("Opening lsremote.html")
    global ipaddresses
    global ipadd
    global timestr
    global settings

    now = datetime.now()
    timestr = (now.strftime("%H:%M:%S - %b %d, %Y"))

    logger.debug(ipadd)  # debug

    # change rgb code to hex for html color picker
    color_vfr_hex = rgb2hex(settings["color_vfr"])
    color_mvfr_hex = rgb2hex(settings["color_mvfr"])
    color_ifr_hex = rgb2hex(settings["color_ifr"])
    color_lifr_hex = rgb2hex(settings["color_lifr"])
    color_nowx_hex = rgb2hex(settings["color_nowx"])
    color_black_hex = rgb2hex(settings["color_black"])
    color_lghtn_hex = rgb2hex(settings["color_lghtn"])
    color_snow1_hex = rgb2hex(settings["color_snow1"])
    color_snow2_hex = rgb2hex(settings["color_snow2"])
    color_rain1_hex = rgb2hex(settings["color_rain1"])
    color_rain2_hex = rgb2hex(settings["color_rain2"])
    color_frrain1_hex = rgb2hex(settings["color_frrain1"])
    color_frrain2_hex = rgb2hex(settings["color_frrain2"])
    color_dustsandash1_hex = rgb2hex(settings["color_dustsandash1"])
    color_dustsandash2_hex = rgb2hex(settings["color_dustsandash2"])
    color_fog1_hex = rgb2hex(settings["color_fog1"])
    color_fog2_hex = rgb2hex(settings["color_fog2"])
    color_homeport_hex = rgb2hex(settings["color_homeport"])

    # color picker for transitional wipes
    fade_color1_hex = rgb2hex(settings["fade_color1"])
    allsame_color1_hex = rgb2hex(settings["allsame_color1"])
    allsame_color2_hex = rgb2hex(settings["allsame_color2"])
    shuffle_color1_hex = rgb2hex(settings["shuffle_color1"])
    shuffle_color2_hex = rgb2hex(settings["shuffle_color2"])
    radar_color1_hex = rgb2hex(settings["radar_color1"])
    radar_color2_hex = rgb2hex(settings["radar_color2"])
    circle_color1_hex = rgb2hex(settings["circle_color1"])
    circle_color2_hex = rgb2hex(settings["circle_color2"])
    square_color1_hex = rgb2hex(settings["square_color1"])
    square_color2_hex = rgb2hex(settings["square_color2"])
    updn_color1_hex = rgb2hex(settings["updn_color1"])
    updn_color2_hex = rgb2hex(settings["updn_color2"])
    morse_color1_hex = rgb2hex(settings["morse_color1"])
    morse_color2_hex = rgb2hex(settings["morse_color2"])
    rabbit_color1_hex = rgb2hex(settings["rabbit_color1"])
    rabbit_color2_hex = rgb2hex(settings["rabbit_color2"])
    checker_color1_hex = rgb2hex(settings["checker_color1"])
    checker_color2_hex = rgb2hex(settings["checker_color2"])

    # Pass data to html document
    templateData = {
        'title': 'Settings Editor-'+version,
        'settings': settings,
        'ipadd': ipadd,
        'ipaddresses': ipaddresses,
        'num': num,
        'timestr': timestr,
        'current_timezone': current_timezone,
        'update_available': update_available,
        'update_vers': update_vers,
        'machines': machines,

        # Color Picker Variables to pass
        'color_vfr_hex'  : color_vfr_hex,
        'color_mvfr_hex' : color_mvfr_hex,
        'color_ifr_hex'  : color_ifr_hex,
        'color_lifr_hex' : color_lifr_hex,
        'color_nowx_hex' : color_nowx_hex,
        'color_black_hex': color_black_hex,
        'color_lghtn_hex': color_lghtn_hex,
        'color_snow1_hex': color_snow1_hex,
        'color_snow2_hex': color_snow2_hex,
        'color_rain1_hex': color_rain1_hex,
        'color_rain2_hex': color_rain2_hex,
        'color_frrain1_hex': color_frrain1_hex,
        'color_frrain2_hex': color_frrain2_hex,
        'color_dustsandash1_hex': color_dustsandash1_hex,
        'color_dustsandash2_hex': color_dustsandash2_hex,
        'color_fog1_hex': color_fog1_hex,
        'color_fog2_hex': color_fog2_hex,
        'color_homeport_hex': color_homeport_hex,

        # Color Picker Variables to pass
        'fade_color1_hex': fade_color1_hex,
        'allsame_color1_hex': allsame_color1_hex,
        'allsame_color2_hex': allsame_color2_hex,
        'shuffle_color1_hex': shuffle_color1_hex,
        'shuffle_color2_hex': shuffle_color2_hex,
        'radar_color1_hex': radar_color1_hex,
        'radar_color2_hex': radar_color2_hex,
        'circle_color1_hex': circle_color1_hex,
        'circle_color2_hex': circle_color2_hex,
        'square_color1_hex': square_color1_hex,
        'square_color2_hex': square_color2_hex,
        'updn_color1_hex': updn_color1_hex,
        'updn_color2_hex': updn_color2_hex,
        'morse_color1_hex': morse_color1_hex,
        'morse_color2_hex': morse_color2_hex,
        'rabbit_color1_hex': rabbit_color1_hex,
        'rabbit_color2_hex': rabbit_color2_hex,
        'checker_color1_hex': checker_color1_hex,
        'checker_color2_hex': checker_color2_hex
    }
    return render_template('lsremote.html', **templateData)


# Import Config file. Must Save Config File to make permenant
@app.route("/importconf", methods=["GET", "POST"])
def importconf():
    logger.info("Importing Config File")
    global ipaddresses
    global airports
    global settings
    global timestr
    tmp_settings = []

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect(f'{PATH}/confedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect(f'{PATH}/confedit')

    filedata = file.read()
    fdata = bytes.decode(filedata)
    logger.debug(fdata)
    tmp_settings = fdata.split('\n')

    for set_line in tmp_settings:
        if set_line[0:1]=="#" or set_line[0:1]=="\n" or set_line[0:1]=="":
            pass
        else:
            (key, val) = set_line.split("=",1)
            val = val.split("#",1)
            val = val[0]
            key = key.strip()
            val = str(val.strip())
            settings[(key)] = val

    logger.debug(settings)
    flash('Config File Imported - Click "Save Config File" to save')
    return redirect(f'{PATH}/confedit')


# Restore config.py settings
@app.route("/restoreconf", methods=["GET", "POST"])
def restoreconf():
    logger.info("Restoring Config Settings")
    readconf(settings_file)  # read config file
    return redirect(f'{PATH}/confedit')


# Loads the profile into the Settings Editor, but does not save it.
@app.route("/profiles", methods=["GET", "POST"])
def profiles():
    global settings
    config_profiles = {'b1': 'config-basic.py', 'b2': 'config-basic2.py', 'b3': 'config-basic3.py', 'a1': 'config-advanced-1oled.py', 'a2': 'config-advanced-lcd.py', 'a3': 'config-advanced-8oledsrs.py', 'a4': 'config-advanced-lcdrs.py'}

    req_profile = request.form['profile']
    print(req_profile)
    print(config_profiles)
    tmp_profile = config_profiles[req_profile]
    stored_profile = f'{PATH}//profiles/' + tmp_profile

    flash(tmp_profile + ' Profile Loaded. Review And Tweak The Settings As Desired. Must Be Saved!')
    readconf(stored_profile)    # read profile config file
    logger.info("Loading a Profile into Settings Editor")
    return redirect('confedit')


# Route for Reboot of RPI
@app.route("/reboot1", methods=["GET", "POST"])
def reboot1():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
    #    flash("Rebooting Map ")
    logger.info("Rebooting Map from " + url)
    os.system('sudo shutdown -r now')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to startup map and displays
@app.route("/startup1", methods=["GET", "POST"])
def startup1():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  #Use index if called from URL and not page.

    temp = url.split('/')
    logger.info("Startup Map from " + url)
    os.system('sudo python3 .//startup.py run &')
    flash("Map Turned On ")
    time.sleep(1)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.



# Route to turn off the map and displays
@app.route("/shutdown1", methods=["GET", "POST"])
def shutdown1():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index' #Use index if called from URL and not page.

    temp = url.split('/')
    logger.info("Shutoff Map from " + url)
    """
    os.system(f"ps -ef | grep {PATH}/metar-display-v4.py' | awk '/{print $2/}' | xargs sudo kill")
    os.system(f"ps -ef | grep {PATH}/metar-v4.py' | awk '{print $2}' | xargs sudo kill")
    os.system(f"ps -ef | grep {PATH}/check-display.py' | awk '{print $2}' | xargs sudo kill")
    os.system('sudo python3 ./shutoff.py &')
    """
    flash("Map Turned Off ")
    time.sleep(1)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to power down the RPI
@app.route("/shutoffnow1", methods=["GET", "POST"])
def shutoffnow1():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
    #   flash("RPI is Shutting Down ")
    logger.info("Shutdown RPI from " + url)
    os.system('sudo shutdown -h now')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to run LED test
@app.route("/testled", methods=["GET", "POST"])
def testled():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  #Use index if called from URL and not page.

    temp = url.split('/')

    #    flash("Testing LED's")
    logger.info("Running testled.py from " + url)
    os.system('sudo python3 ./testled.py')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to run OLED test
@app.route("/testoled", methods=["GET", "POST"])
def testoled():
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index' # Use index if called from URL and not page.

    temp = url.split('/')
    if config.displayused!=1 or config.oledused!=1:
        return redirect(temp[3])  # temp[3] holds name of page that called this route.

    #    flash("Testing OLEDs ")
    logger.info("Running testoled.py from " + url)
    os.system('sudo python3 ./testoled.py')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


#############
# Functions #
#############

# create backup of config.py
def copy():
    logger.debug('In Copy Config file Routine')
    f = open(settings_file, "r")
    contents = f.read()
    f.close()

    f = open(settings_bkup, "w+")
    f.write(contents)
    f.close()


# open and read config.py into settings dictionary
def readconf(config_file):
    logger.debug('In ReadConf Routine')
    try:
        with open(config_file) as f:
            for line in f:
                if line[0] == "#" or line[0] == "\n":
                    pass
                else:
                    (key, val) = line.split("=",1)
                    val = val.split("#",1)
                    val = val[0]
                    key = key.strip()
                    val = str(val.strip())
                    logger.debug(key + ", " + val)  # debug
                    settings[(key)] = val
            logger.debug(settings)  # debug
    except IOError as error:
        logger.error('Config file could not be loaded.')
        logger.error(error)

# write config.py file
def writeconf(settings, file):
    logger.debug('In WriteConf Routine')
    f = open(file, "w+")
    f.write('#config.py - use web based configurator to make changes unless you are comfortable doing it manually')
    f.write('\n\n')
    for key in settings:
        #        logger.debug(key, settings[key]) # debug
        f.write(key + " = " + settings[key])
        f.write('\n')
    f.close()

# write airports file
def writeairports(settings, file):
    logger.debug('In WriteAirports Routine')
    f = open(file, "w")  # "w+")
    #       print(settings)
    for key in settings:
        value = settings.get(key)
        logger.debug(value)  # debug
        f.write(value)
        f.write('\n')
    f.close()

# Read airports file
def readairports(airports_file):
    logger.debug('In ReadAirports Routine')
    global airports
    airports = []
    try:
        with open(airports_file) as f:
            for line in f:
                airports.append(line.rstrip())
            logger.debug(airports)  # debug
    except IOError as error:
        logger.error('Airports file could not be loaded.')
        logger.error(error)

# Read heat map file
def readhmdata(hmdata_file):
    logger.debug('In ReadHMdata Routine')
    global hmdata
    hmdata = []
    try:
        with open(hmdata_file) as f:
            for line in f:
                hmdata.append(line.rstrip())
            logger.debug(hmdata)  # debug
    except IOError as error:
        logger.error('Heat Map File Not Available. Creating Default Heat Map File')
        logger.error(error)

        for airport in airports:
            hmdata.append(airport + " 0")
        print (hmdata)  # debug
        writehmdata(hmdata, heatmap_file)

# Write heat map file
def writehmdata(hmdata,heatmap_file):
    logger.debug('In WriteHMdata Routine')
    f = open(heatmap_file, "w+")

    for key in hmdata:
        logger.debug(key)  # debug
        f.write(key)
        f.write('\n')
    f.close()

#####################################################
# routine to capture airport information and pass along to web pages.
#####################################################
def get_led_map_info():
    logger.debug('In get_led_map_info Routine')

    global led_map_url
    global led_map_dict
    global lat_list
    global lon_list
    global max_lat
    global min_lat
    global max_lon
    global min_lon

    readairports(airports_file)  # Read airports file.
    airports_count = len(airports)
    lmu_tmp = led_map_url

    print ("Number of airports in the list: ", airports_count)

    tmp_ap = airports_count
    tmp_start = 0
    tmp_end = max_api_airports

    while (tmp_ap >= 0):

        print ("tmp_start: ", tmp_start) # debug
        print ("tmp_ap: ", tmp_ap) # debug
        print ("tmp_end: ", tmp_end) # debug
        print(airports[tmp_start]) # debug

        for airportcode in islice(airports, tmp_start, tmp_end):
            lmu_tmp = lmu_tmp + airportcode + ","
        lmu_tmp = lmu_tmp[:-1]
        logger.debug(lmu_tmp) # debug url if neccessary

        while True:  # check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            try:
                content = urllib.request.urlopen(lmu_tmp).read()
                logger.info('Internet Available')
                logger.info(lmu_tmp)
                break
            except:
                logger.warning('xxxxxxxxxxxFAA Data Not Available')
                logger.warning(lmu_tmp)
                time.sleep(delay_time)
                content = ''
                pass

        if content  == b'':  # if FAA data not available bypass getting apinfo
            return

        root = ET.fromstring(content)  # Process XML data returned from FAA

        for led_map_info in root.iter('METAR'):
            stationId = led_map_info.find('station_id').text

            try:
                lat = led_map_info.find('latitude').text
                lon = led_map_info.find('longitude').text
            except:
                lat = '0'
                lon = '0'

            lat_list.append(lat)
            lon_list.append(lon)

            if led_map_info.find('flight_category') is None:
                fl_cat = 'Not Reported'
            else:
                fl_cat = led_map_info.find('flight_category').text
            led_map_dict[stationId] = [lat,lon,fl_cat]

        tmp_ap = tmp_ap - max_api_airports
        tmp_start = tmp_start + max_api_airports + 1
        tmp_end = tmp_end + max_api_airports
        lmu_tmp = led_map_url

    max_lat = max(lat_list)
    min_lat = min(lat_list)
    max_lon = max(lon_list)
    min_lon = min(lon_list)

# routine to capture airport information and pass along to web pages.

def get_apinfo():
    logger.debug('In Get_Apinfo Routine')

    global orig_apurl
    global apinfo_dict

    airports_count = len(airports)

    print ("Number of airports in the list: ", airports_count)
    apurl = orig_apurl  # Assign base FAA url to temp variable
    tmp_ap = airports_count
    tmp_start = 0
    tmp_end = max_api_airports

    while tmp_ap >= 0:
        print ("tmp_start: ", tmp_start)
        print ("tmp_ap: ", tmp_ap)
        print ("tmp_end: ", tmp_end)

        for airportcode in islice(airports, tmp_start, tmp_end):
            apurl = apurl + airportcode + ","

        #apurl = apurl[:-1]
        #        print ("URL string: ", apurl)
        internet_tries = 10 # number of times to try to access the internet before quitting the script.
        internet_test = True

        while internet_test:  # check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            try:
                #                s.connect(("8.8.8.8", 80))
                content = urllib.request.urlopen(apurl).read()
                logger.info('Internet Available')
                logger.info(apurl)
                break
            except:
                logger.warning("\033[1;32;40m>>>>>>>> FAA Data Not Available <<<<<<<< - Attempts Left: " + str(internet_tries) + "\033[0;0m\n")
                logger.warning(apurl)
                time.sleep(delay_time)
                content = ''
                internet_tries -= 1
                if internet_tries <= 0:
                    internet_test = False
                    print("\n\033[1;32;40mNo Internet - Type 'ctrl-c' then 'sudo raspi-config' to setup WiFi\033[0;0m\n")
                    sys.exit()
                pass

        if content == '':  # if FAA data not available bypass getting apinfo
            return

        root = ET.fromstring(content)  # Process XML data returned from FAA

        for apinfo in root.iter('Station'):
            stationId = apinfo.find('station_id').text

            if stationId[0] != 'K':
                site = apinfo.find('site').text
                country = apinfo.find('country').text
                apinfo_dict[stationId] = [site,country]

            else:
                site = apinfo.find('site').text
                state = apinfo.find('state').text
                apinfo_dict[stationId] = [site,state]

        tmp_ap = tmp_ap - max_api_airports
        tmp_start = tmp_start + max_api_airports + 1
        tmp_end = tmp_end + max_api_airports
        apurl = orig_apurl

    #print (content)
    content2 = content.decode()
    file = open("temp123.xml", "w")
    file.write(content2)
    file.close()


# rgb and hex routines
def rgb2hex(rgb):
    logger.debug(rgb)
    (r,g,b) = eval(rgb)
    hex = '#%02x%02x%02x' % (r, g, b)
    return hex


def hex2rgb(value):  # from; https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))


# functions for updating software via web
def delfile(filename):
    try:
        os.remove(target_path + filename)
        logger.info('Deleted ' + filename)
    except:
        logger.error("Error while deleting file ", target_path + filename)


def unzipfile(filename):
    with zipfile.ZipFile(target_path + filename, 'r') as zip_ref:
        zip_ref.extractall(target_path)
    logger.info('Unzipped ls.zip')


def copytoprevdir(src, dest):
    shutil.rmtree(dest)
    shutil.copytree(src,dest)
    logger.info('Copied current version to ../previousversion')


def dlftpfile(url, filename):
    wget.download(url, filename)
    print('\n')
    logger.info('Downloaded ' + filename + ' from neoupdate')


def updatefiles():
    copytoprevdir(src, dest)                       # This copies current version to ../previousversion before updating files.
    dlftpfile(source_path + zipfilename, target_path + zipfilename) # Download zip file that contains updated files
    unzipfile(zipfilename)                         # Unzip files and overwrite existing older files
    delfile(zipfilename)                           # Delete zip file
    logger.info('Updated New Files')


def checkforupdate():
    global update_vers
    #    get_loc()
    #    print(loc)  # debug

    dlftpfile(source_path + verfilename, target_path + verfilename)  # download version file from neoupdate

    with open(target_path + verfilename) as file:  # Read version number of latest version
        update_vers = file.read()

    logger.info('Latest Version = ' + str(update_vers) + ' - ' + 'Current Version = ' + str(admin.version))

    delfile(verfilename)  # Delete the downloaded version file.
    logger.info('Checked for Software Update')

    if float(admin.version[1:])<float(admin.min_update_ver):  # Check to see if a newer Image is available
        return "image"

    if float(update_vers) > float(admin.version[1:]):  # Strip leading 'v' can compare as floats to determine if an update available.
        return True
    else:
        return False


def testupdate():
    # Check to see if an newer version of the software is available, and update if user so chooses
    global update_available
    if checkforupdate() == True:
        logger.info('Update Available')
        update_available = 1                    # Update is available

    elif checkforupdate() == False:
        logger.info('No Updates Available')
        update_available = 0                    # No update available

    elif checkforupdate() == "image":
        logger.info('Newer Image Available for Download')
        update_available = 2                    # Newer image available


# May be used to display user location on map in user interface. - TESTING Not working consistently, not used
def get_loc():
    loc_data = {}
    global loc

    url_loc = 'https://extreme-ip-lookup.com/json/'
    r = requests.get(url_loc)
    data = json.loads(r.content.decode())

    ip_data = data['query']
    loc_data['city'] = data['city']
    loc_data['region'] = data['region']
    loc_data['lat'] = data['lat']
    loc_data['lon'] = data['lon']
    loc[ip_data] = loc_data


def setup():
    """
    Set up everything.
    """
    internet_tries = 10 # number of times to try to access the internet before quitting the script.

    # Display active IP address for builder to open up web browser to configure.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Get system info and display
    python_ver = ("Python Version = " + sys.version)
    logger.info(python_ver)
    print()
    print(python_ver)
    print('LiveSectional Version - ' + version)
    print("\033[1;32;40m***********************************************")
    print("       My IP Address is = "+ s.getsockname()[0])
    print("***********************************************")
    print("  Configure your LiveSectional by opening a   ")
    print("    browser to http://"+ s.getsockname()[0]+":5000")
    print("***********************************************")
    print("\033[0;0m\n")
    print("Raspberry Pi System Time - " + timestr)

    # Load files and back up the airports file, then run flask templates

    ## This code is obsolete, but left here for prosperity's sake.
    ##    if useip2ftp ==  1:
    ##        exec(compile(open(".//ftp-v4.py", "rb").read(), ".//ftp-v4.py", 'exec'))  #Get latest ip's to display in editors
    ##        logger.info("Storing " + str(ipaddresses) + " on ftp server")

    copy()  # make backup of config file
    readconf(settings_file)  # read config file
    readairports(airports_file)  # read airports
    get_apinfo()  # decode airports to get city and state of each airport
    get_led_map_info() # get airport location in lat lon and flight category
    readhmdata(heatmap_file)  # get Heat Map data

    """
    if admin.use_scan_network == 1:
        print("One Moment - Scanning for Other LiveSectional Maps on Local Network")
        machines = scan_network.scan_network()
        print(machines) # Debug
    """

    logger.info("IP Address = " + s.getsockname()[0])
    logger.info("Starting Flask Session")

"""
This code use to be in __main__. It needs to be run outside of main because with a uwsgi server, main never gets
called
"""
setup()
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


