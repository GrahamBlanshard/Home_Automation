#!/usr/bin/env python
##
# Listens for web commands and takes appropriate action
##
# Pins in BCM config mode:
# 4 = Door Relay
##
# Sqlite3 DB created with db/setup.sh
##

###########
# IMPORTS #
###########
import sqlite3
import RPi.GPIO as GPIO
import os
import json
from time import sleep
from flask import Flask
from flask.ext.api import status
from subprocess import check_output

#############
# VARIABLES #
#############
RELAY_PIN = 4 #Teal Wire
DOOR_CMD = "CmdGoesHere" #No External Access, Firewall blocked. Future placeholder for security potentials
VALID_EVENTS = ['ManDoor','GarageDoor','WebListener','DoorReader','Graham','Steph']
DEBUG_FILE = '/home/pi/garage/debug.pi'
DB_PATH = '/home/pi/garage/db/garage.db'
LOG_FILE = open('/home/pi/garage/logs/web_listener.log', 'w+')
PIC_FILE = '/home/pi/garage/pic_req.pi'
PAUSE_FILE = '/home/pi/garage/pic_pause.pi'

##########
# CONFIG #
##########
#Flask
app = Flask(__name__)

#RaspberryPi Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

#############
# FUNCTIONS #
#############
def debug_print(msg):
    "Tests for Debug mode file and prints a message to LOG_FILE if present"
    if os.path.isfile(DEBUG_FILE):
        LOG_FILE.write(msg + '\n' )
        LOG_FILE.flush()

def dbEvent(eSource, eName, eDuration):
    "Store an event in the database"
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()

        values = (eSource,eName,eDuration)
        curs.execute('INSERT INTO events (source,name,duration) VALUES (?,?,?)', values)
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on Insert: %s' % e.args[0] )
    
    conn.commit()
    conn.close()
    debug_print('%s %s %d event stored in database.' % (eSource,eName,eDuration))
    return

def dbSelect(eSource):
    "Execute SELECT statement on database given source name"
    return_data = {'source': eSource}
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()

        curs.execute('SELECT name,duration,etime FROM events WHERE source=\'%s\' ORDER BY ID DESC LIMIT 1' % eSource)
        data = curs.fetchone()
        if data == None:
            return_data['result'] = 0
            return_data['event'] = 'none'
        else:
            return_data['result'] = 0
            return_data['event'] = data[0]
            return_data['duration'] = data[1]
            return_data['time'] = data[2]
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on dbSelect %s:' % e.args[0] )
        return_data['result'] = 1
        return_data['source'] = 'dbSelect'
        return_data['error'] = e.args[0]
        
    conn.close()
    return return_data
    
def dbGarageDoorStatus():
    "Get the last door status event from the database"
    return_data = {'source': 'GarageDoor'}
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()
        curs.execute('SELECT name FROM events WHERE source=\'GarageDoor\' ORDER BY ID DESC LIMIT 1')
        data = curs.fetchone()
        if data == None:
            return_data['result'] = 0
            return_data['event'] = 'none'
        else:
            return_data['result'] = 0
            return_data['event'] = data[0] 
        
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on GarageDoorStatus Query: %s' % e.args[0] )
        return_data['result'] = 1
        return_data['source'] = 'dbGarageDoorStatus'
        return_data['error'] = e.args[0]
        
    conn.close()
    return return_data

def door_status():
    "Retrieve statuses for both doors"
    try:
        statuses = {'items': [dbSelect('ManDoor'),dbSelect('GarageDoor')] }
        return json.dumps(statuses)
    except sqlite3.Error, e:
        LOG_FILE.write('Error %s:' % e.args[0])
        return 'Error %s:' % e.args[0]
		
def door_signal(who):
    "Activate Relay for 500ms, log event"
    dbEvent(who,'Door Signal',0)
    GPIO.output(RELAY_PIN,GPIO.LOW)
    sleep(0.5)
    GPIO.output(RELAY_PIN,GPIO.HIGH)
    return

##################
# FLASK FUNCIONS #
##################
@app.route('/signal/<code>/<who>')
def door_actuate(code, who):
    if code == DOOR_CMD:
        debug_print('Door Command from ' + who + ' authenticated')
        door_signal(who) 
        return 'Done'
    else:
        LOG_FILE.write('Door Command from ' + who + ' failed')
        return json.dumps({'result': 1, 'error': 'Invalid code', 'source': 'signal'}), status.HTTP_401_UNAUTHORIZED

@app.route('/status')
def status_plain():
    debug_print('Status Event')
    return door_status()

@app.route('/query/<source>')
def query_status(source):
    "Query the database for the latest event on given source"
    debug_print('Query for ' + status)
    if source in VALID_EVENTS:
        return dbSelect(source) 
    else:
        return json.dumps({'result': 1, 'error': 'Invalid Event Request', 'source': 'query'}), status.HTTP_406_NOT_ACCEPTABLE
        
@app.route('/open/<code>/<who>')
def door_open(code,who):
    "Open the door from a Closed State"
    return_data = {'source': 'Open'}
    if code == DOOR_CMD:
        if dbGarageDoorStatus()['event'] == 'Close':
            debug_print('Door Open Command from ' + who + ' authenticated')
            door_signal(who)
            return_data['result'] = 0
            return_data['event'] = 'Done'
        else:
            debug_print('Door Open Command from ' + who + ' authenticated. But door is open')
            return_data['event'] = 'Door is already Open'
            return_data['result'] = 0
    else:
        LOG_FILE.write('Door Open Command from ' + who + ' failed')
        return_data['result'] = 1
        return_data['error'] = 'Invalid Auth Code'
    return json.dumps(return_data)

@app.route('/close/<code>/<who>')
def door_close(code,who):
    "Close the door from an Open State"
    return_data = {'source': 'Close'}
    if code == DOOR_CMD:
        if dbGarageDoorStatus()['event'] == 'Open':
            debug_print('Door Close Command from ' + who + ' authenticated')
            door_signal(who)
            return_data['result'] = 0
            return_data['event'] = 'Done'
        else:
            debug_print('Door Close Command from ' + who + ' authenticated. But door is closed')
            return_data['result'] = 0
            return_data['event'] = 'Door is already Closed'
    else:
        LOG_FILE.write('Door Closed Command from ' + who + ' failed')
        return_data['result'] = 1
        return_data['error'] = 'Invalid Code'
    return json.dumps(return_data)

@app.route('/pic')
def take_picture():
    "Instruct the pi to capture a picture"
    return_data = {'source': 'Picture Request', 'event':'Done', 'result': 0}
    open(PIC_FILE,'a').close()
    return json.dumps(return_data)

@app.route('/pause')
def toggle_pause():
    "Toggle picture pausing"
    return_data = {'source': 'Pause Toggle', 'event': 'Done', 'result': 0}
    if os.path.isfile(PAUSE_FILE):
        os.remove(PAUSE_FILE)
        return_data['event'] = 'Off'
    else:
        open(PAUSE_FILE,'a').close()
        return_data['event'] = 'On'

    return json.dumps(return_data)

        
########
# MAIN #
########
if __name__ == '__main__':
    dbEvent('WebListener','Starting',0)
    app.run(host="0.0.0.0")

    #Running now

    dbEvent('WebListener','Stopping',0)
    GPIO.cleanup()
