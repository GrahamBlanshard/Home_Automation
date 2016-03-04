#!/usr/bin/env python
##
# Listens for web commands and takes appropriate action
##
# Pins in BCM config mode:
# 4 = Door Relay
##
# Sqlite3 DB created with db/setup.sh
##
# Latest Revision
# - Feb. 25 - Debug updates
# - Mar.  3 - Json responses in prep for Mobile App
#           - Open/Close functionality instead of direct signal
##
# JSON Format
# result : int    - 0 or 1 for failure/success
# data   : string - readable data responses
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
LOG_FILE = open('/home/pi/garage/logs/garage.log', 'w+')

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
        LOG_FILE.write( msg + '\n' )
        LOG_FILE.flush()

def dbEvent(eSource, eName):
    "Store an event in the database"
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()

        values = (eSource,eName)
        curs.execute('INSERT INTO events (source,name) VALUES (?,?)', values)
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on Insert: %s' % e.args[0] )
    
    conn.commit()
    conn.close()
    debug_print('%s %s event stored in database.' % (eSource,eName))
    return

def dbSelect(eSource):
    "Execute SELECT statement on database given source name"
    return_data = json.loads({'result': 0, 'data': "Error on dbSelect"})
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()

        curs.execute('SELECT source,name,etime FROM events WHERE source=\'%s\' ORDER BY ID DESC LIMIT 1' % eSource)
        data = curs.fetchone()
        if data == None:
            return_data['result'] = 1
            return_data['data'] = 'No %s events to report' % eSource
        else:
            return_data['result':] = 1
            return_data['data'] = data[0] + ' last state = `' + data[1] + '` at ' + data[2]
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on dbSelect %s:' % e.args[0] )
        return_data['data'] = 'Error %s:' % e.args[0]
        
    conn.close()
    return return_data
    
def dbGarageDoorStatus():
    "Get the last door status event from the database"
    return_data = json.loads({'result': 0, 'data': 'Error querying door status'})
    try:
        conn=sqlite3.connect(DB_PATH)
        curs=conn.cursor()
        curs.execute('SELECT name FROM events WHERE source=\'GarageDoor\' ORDER BY ID DESC LIMIT 1'
        data = curs.fetchone()
        if data == None:
            return_data['result']  = 1
            return_data['data'] = 'No Door Status to Return'
        else:
            return_data['result'] = 1
            if 'Open' in data[0]:
                return_data['data'] = 'Open'
            else:
                return_data['data'] = 'Closed'
        
    except sqlite3.Error, e:
        LOG_FILE.write( 'Error on GarageDoorStatus Query: %s' % e.args[0] )
        return_data['data'] = 'Error on GarageDoorStatus Query: %s' % e.args[0]
        
    conn.close()
    return return_data

def door_status():
    "Retrieve statuses for both doors"
    try:
        statuses = json.dumps(dbSelect('ManDoor')) 
        statuses += '<br />'
        statuses += json.dumps(dbSelect('GarageDoor'))
        return statuses
    except sqlite3.Error, e:
        LOG_FILE.write('Error %s:' % e.args[0])
        return 'Error %s:' % e.args[0]
		
def door_signal(who):
    "Activate Relay for 500ms, log event"
    dbEvent(who,'Door Signal')
    GPIO.output(RELAY_PIN,GPIO.LOW)
    sleep(0.5)
    GPIO.output(RELAY_PIN,GPIO.HIGH)
    return

##################
# FLASK FUNCIONS #
##################
@app.route('/signal/<code>/<who>')
def door_signal(code, who):
    if code == DOOR_CMD:
        debug_print('Door Command from %s authenticated', who)
        door_signal(who) 
        return 'Done'
    else:
        LOG_FILE.write('Door Command from %s failed', who)
        return 'Err: Invalid code', status.HTTP_401_UNAUTHORIZED

@app.route('/status')
def status_plain():
    debug_print('Status Event')
    return door_status()

@app.route('/query/<source>')
def query_status(source):
    "Query the database for the latest event on given source"
    debug_print('Query for %s' % status)
    if source in VALID_EVENTS:
        return dbSelect(source) 
    else:
        return json.dumps(json.loads({'result': 0, 'data': 'Invalid Event Request'})), status.HTTP_406_NOT_ACCEPTABLE
        
@app.route('/open/<code>/<who>')
def door_open(code,who):
    "Open the door from a Closed State"
    return_data = json.loads({'result': 0, 'data':'Invalid Request'})
    if code == DOOR_CMD:
        if dbGarageDoorStatus()['data'] == 'Closed':
            debug_print('Door Open Command from %s authenticated' % who)
            door_signal(who)
            return_data['result'] = 1
            return_data['data'] = 'Done'
            return json.dumps(return_data)
        else:
            debug_print('Door Open Command from %s authenticated. But door is open' % who)
            return_data['data'] = 'Door is already Open'
            return json.dumps(return_data), status.HTTP_406_NOT_ACCEPTABLE
    else:
        LOG_FILE.write('Door Open Command from %s failed', who)
        return_data['data'] = 'Err: Invalid Code'
        return json.dumps(return_data), status.HTTP_401_UNAUTHORIZED

@app.route('/close/<code>/<who>')
def door_close(code,who):
    "Close the door from an Open State"
    return_data = json.loads({'result': 0, 'data':'Invalid Request'})
    if code == DOOR_CMD:
        if dbGarageDoorStatus()['data'] == 'Open':
            debug_print('Door Close Command from %s authenticated' % who)
            door_signal(who)
            return_data['result'] = 1
            return_data['data'] = 'Done'
            return json.dumps(return_data)
        else:
            debug_print('Door Close Command from %s authenticated. But door is closed' % who)
            return_data['data'] = 'Door is already Closed'
            return json.dumps(return_data), status.HTTP_406_NOT_ACCEPTABLE
    else:
        LOG_FILE.write('Door Closed Command from %s failed', who)
        return_data['data']  = 'Err: Invalid Code'
        return json.dumps(return_data), status.HTTP_401_UNAUTHORIZED
        
########
# MAIN #
########
if __name__ == '__main__':
    dbEvent('WebListener','Starting')
    app.run(host="0.0.0.0")

    #Running now

    dbEvent('WebListener','Stopping')
    GPIO.cleanup()
