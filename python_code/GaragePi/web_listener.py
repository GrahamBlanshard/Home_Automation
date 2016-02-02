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

##########
# CONFIG #
##########
#Flask
app = Flask(__name__)

#SQL
conn=sqlite3.connect('db/garage.db')
curs=conn.cursor()

#RaspberryPi Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

#############
# FUNCTIONS #
#############
def door_status():
	try:
		statuses = ""
		curs.execute('SELECT source,name,etime FROM events WHERE source=\'ManDoor\' ORDER BY ID DESC LIMIT 5')
		data = curs.fetchone()
		if data == None:
			statuses += 'No Man Door events to report'
		else:
			statuses += data[0] + ' last state = `' + data[1] + '` at ' + data[2]

                statuses += '<br />'

		curs.execute('SELECT source,name,etime FROM events WHERE source=\'GarageDoor\' ORDER BY ID DESC LIMIT 5',)
		data = curs.fetchone()
		if data == None:
			statuses += 'No Garage Door events to report'
		else:
			statuses += data[0] + ' last state = `' + data[1] + '` at ' + data[2]
			
		return statuses
	except sqlite3.Error, e:
		return 'Error %s:' % e.args[0]
		
def door_signal(who):
	values = (who,'Door Signal')
	curs.execute('INSERT INTO events (source,name) VALUES (?,?)', values)
	conn.commit()
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

########
# MAIN #
########
if __name__ == '__main__':
	curs.execute('INSERT INTO events (source,name) VALUES (?,?)',('Pi','Starting'))
	conn.commit()
	app.run(host="0.0.0.0")
	GPIO.cleanup()
	curs.execute('INSERT INTO events (source,name) VALUES (?,?)',('Pi','Stopping'))
	conn.commit()
	if conn:
		conn.close()
