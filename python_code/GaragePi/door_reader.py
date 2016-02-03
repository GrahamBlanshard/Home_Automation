#!/usr/bin/env python
##
# Checks the sensors for a door event. Logs it to the database
##
# Pins in BCM config mode:
# 24 = Man Door Sensor
# 25 = Garage Door Sensor
##
# Sqlite3 DB created with db/setup.sh
##
# Uses pytz : `sudo pip install pytz`
##

import sqlite3
import RPi.GPIO as GPIO
import datetime
import time
import picamera
import pytz
import os

#########
# SETUP #
#########

#Variable Setup
MAN_DOOR_PIN = 24       #Purple Wire
GARAGE_DOOR_PIN = 25    #Blue Wire
LOOP_DELAY = 1          #sec
QUIT = False
manDoorState = None     #None = closed, time = open
garageDoorState = None  #None = closed, time = open
savepicdir = './pics/'

#Database Setup
conn=sqlite3.connect('db/garage.db')
curs=conn.cursor()

#RaspberryPi Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MAN_DOOR_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GARAGE_DOOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Camera Setup
camera = picamera.PiCamera()
camera.vflip = True
camera.hflip = True
camera.resolution = (1366,768)
camera.quality = 100

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

def makepicdir(savepath):
    "Tests and creates the picture directory"
    try:
        os.stat(savepath)
    except:
        os.mkdir(savepath)
	
#######
# RUN #
#######
dbEvent('DoorReader','Starting')
while not QUIT:
    try:
    #Man Door - Pin Status
        if GPIO.input(MAN_DOOR_PIN):
            if manDoorState is None:
                dbEvent('ManDoor','Open')
                manDoorState = now()
                print 'Man Door open'
            else:
		currTime = datetime.datetime.now()
                savedir = savepicdir + "%04d%02d%02d/" % (currTime.year, currTime.month, currTime.day)
                savefilename = savedir + 'garage-' + "%02d%02d%02d.jpg" % (currTime.hour, currTime.minute, currTime.second)
                makepicdir(savedir)
                camera.capture(savefilename)
        else:
            if not manDoorState is None:
                delta_time = readableDate(manDoorState, now())
                dbEvent('ManDoor','Close ' + delta_time )
                manDoorState = None
                print 'Man Door Closed'
            
    #Garage Door - Pin Status
        if GPIO.input(GARAGE_DOOR_PIN):
            if garageDoorState is None:
                dbEvent('GarageDoor','Open')	
                garageDoorState = now() 
                print 'Garage Door Open'
        else:
            if not garageDoorState is None:
                delta_time = readableDate(garageDoorState, now())
                dbEvent('GarageDoor','Close ' + delta_time )
                garageDoorState = None
                print 'Garage Door Closed'
    #Finish
        time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
	QUIT = true

dbEvent('DoorReader','Stopping')
conn.close()
GPIO.cleanup()
camera.close()
############
# END MAIN #
############
