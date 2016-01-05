#!/usr/bin/env python
# Checks the sensors for a door event. Logs it to the database
#
# Pins in BCM config mode:
# 24 = Door Sensor
##
# Sqlite3 DB created with db/setup.sh
##
# Uses pytz : `sudo pip install pytz`
##

import sqlite3
import RPi.GPIO as GPIO
import datetime
import time
import pytz

#########
# SETUP #
#########
#Variable Setup
MAN_DOOR_PIN = 24
quit = False
LOOP_DELAY = 1 #sec

#Database Setup
conn=sqlite3.connect('db/garage.db')
curs=conn.cursor()

#RaspberryPi Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MAN_DOOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Script Variables
manDoorState = None #None = closed, time = open

#############
# FUNCTIONS #
#############
def now():
	"Get current datetime with America/Regina timezone"
	return datetime.datetime.now(pytz.timezone('America/Regina'))

def dbEvent(eSource, eName):
    "Store an event in the database"
	values = (eSource,eName)
    curs.execute('INSERT INTO events (source,name) VALUES (?,?)', values)
	conn.commit()
    return

def readableDate(start,end):
    "Returns a readable string of time"
    time_delta = end - start
    return str(time_delta.total_seconds()) + ' seconds'

#######
# RUN #
#######
while not quit:
	try:
	#Check Door Pin Statuses
	#Man Door
		if GPIO.input(MAN_DOOR_PIN):
			if manDoorState is None:
				dbEvent('Man Door','Open')	
				manDoorState = now() 
				print 'ManDoor opened @ ' +  str(manDoorState)
		else:
			if not manDoorState is None:
				delta_time = readableDate(manDoorState, now())
				dbEvent('Man Door','Close ' + delta_time )
				manDoorState = None
				print 'ManDoor closed. Open for ' + delta_time
	#Garage Door

	#Finish
		time.sleep(LOOP_DELAY)
	except KeyboardInterrupt:
		quit = True

###########
# CLEANUP #
###########
conn.close()
GPIO.cleanup()
