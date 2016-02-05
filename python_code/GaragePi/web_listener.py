#!/usr/bin/env python
##
# Listens for web commands and takes appropriate action
##
# Pins in BCM config mode:
# 17 = Door Relay
##
# Sqlite3 DB created with db/setup.sh
##
###########
# IMPORTS #
###########
from flask import Flask
import sqlite3
import RPi.GPIO as GPIO
from time import sleep

#############
# VARIABLES #
#############
RELAY_PIN = 17 #Teal Wire
DOOR_CMD = "CmdGoesHere" #No External Access, Firewall blocked. Future placeholder for security potentials
VALID_EVENTS = ['ManDoor','GarageDoor','WebListener','DoorReader','Graham','Steph']

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
def dbEvent(eSource, eName):
    "Store an event in the database"
    try:
        conn=sqlite3.connect('db/garage.db')
        curs=conn.cursor()

        values = (eSource,eName)
        curs.execute('INSERT INTO events (source,name) VALUES (?,?)', values)
        conn.commit()
        conn.close()
    except sqlite3.Error, e:
        print 'Error on Insert: %s' % e.args[0]

    return


def dbSelect(eSource):
    "Execute SELECT statement on database given source name"
    try:
	conn=sqlite3.connect('db/garage.db')
        curs=conn.cursor()

        curs.execute('SELECT source,name,etime FROM events WHERE source=\'%s\' ORDER BY ID DESC LIMIT 1' % eSource)
        data = curs.fetchone()
        if data == None:
            return 'No %s events to report' % eSource
        else:
            return data[0] + ' last state = `' + data[1] + '` at ' + data[2]
	conn.close()
    except sqlite3.Error, e:
	return 'Error %s:' % e.args[0]

def door_status():
    "Retreive statuses for both doors"
    try:
        statuses = dbSelect('ManDoor') 
        statuses += '<br />'
        statuses += dbSelect('GarageDoor')
        return statuses
    except sqlite3.Error, e:
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
def status(code, who):
    if code == DOOR_CMD:
        door_signal(who) 
        return 'Done'
    else:
        return 'Err: Invalid code'

@app.route('/status')
def status_plain():
    return door_status()

@app.route('/query/<source>')
def query_status(source):
    "Query the database for the latest event on given source"
    if source in VALID_EVENTS:
        return dbSelect(source) 
    else:
        return 'Invalid Event Request'

########
# MAIN #
########
if __name__ == '__main__':
    dbEvent('WebListener','Starting')
    app.run(host="0.0.0.0")

    #Running now

    dbEvent('WebListener','Stopping')
    GPIO.cleanup()
