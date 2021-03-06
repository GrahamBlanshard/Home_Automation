#!/usr/bin/env python
##
# Checks the sensors for a door event. Logs it to the database
##
# Pins in BCM config mode:
# 25 = Man Door Sensor
# 24 = Garage Door Sensor
##
# Sqlite3 DB created with db/setup.sh
##
# Uses 
#    pytz :  `sudo pip install pytz`
#    pynma : (https://github.com/uskr/pynma)
##

###########
# IMPORTS #
###########
import sqlite3
import RPi.GPIO as GPIO
import datetime
import time
import picamera
import pytz
import pynma
import os

#############
# VARIABLES #
#############
#GPIO Pins
MAN_DOOR_PIN = 25       #Blue Wire
GARAGE_DOOR_PIN = 24    #Purple Wire

#Loop Control
LOOP_DELAY = 1          #sec
QUIT = False

DEBUG_FILE = '/home/pi/garage/debug.pi'
DB_PATH = '/home/pi/garage/db/garage.db'
LOG_FILE = open('/home/pi/garage/logs/door_reader.log', 'w+')
PIC_FILE = '/home/pi/garage/pic_req.pi'
PAUSE_FILE = '/home/pi/garage/pic_pause.pi'

manDoorState = None     #None = closed, time = open
garageDoorState = None  #None = closed, time = open
savepicdir = '/home/pi/garage/pics/'

##########
# CONFIG #
##########
#NotifyMyAndroid Setup
NMA_API_KEY = "SuperTopSecret" #Your NMA API key goes here!
manNotified = False
garageNotified = False
NMA_DELAY_SEC = 300     #5 minutes
NMA_LATE_START = 0      #Midnight	
NMA_LATE_END = 5        #5AM
nma = pynma.PyNMA(NMA_API_KEY)

#RaspberryPi Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MAN_DOOR_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GARAGE_DOOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Camera Setup
camera = picamera.PiCamera()
camera.vflip = False
camera.hflip = False
camera.resolution = (1366,768)
camera.quality = 100
camera.exposure_mode = 'sports'

#############
# FUNCTIONS #
#############
def debug_print(msg):
    "Tests for Debug mode file and prints a message to LOG_FILE if present"
    if os.path.isfile(DEBUG_FILE):
        LOG_FILE.write( msg + '\n' )
        LOG_FILE.flush()

def now():
    "Get current datetime with America/Regina timezone"
    return datetime.datetime.now(pytz.timezone('America/Regina'))

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
    debug_print('%s %s %d event stored in database' % (eSource, eName, eDuration))
    return

def totalSeconds(start,end):
    "Returns a seconds between events"
    time_delta = end - start
    return int(time_delta.total_seconds())

def makepicdir(savepath):
    "Tests and creates the picture directory"
    try:
        os.stat(savepath)
    except:
        os.mkdir(savepath)
    return

def sendAndroidNotify(event,desc,priority):
    "Send a message to Android"
    nma.push("GaragePi", event, desc, "http://172.16.1.76:5000/status",priority) #172.16.1.76 is statically assigned on my network
    return

def capture_photo(currTime):
    "Capture a picture to the storage directory when not in pause mode"
    if Not os.path.isfile(PAUSE_FILE):
      savedir = savepicdir + "%04d%02d%02d/" % (currTime.year, currTime.month, currTime.day)
      savefilename = savedir + 'garage-' + "%02d%02d%02d.jpg" % (currTime.hour, currTime.minute, currTime.second)
      makepicdir(savedir)
      camera.capture(savefilename)
    return

#######
# RUN #
#######
dbEvent('DoorReader','Starting', 0)
while not QUIT:
    debug_print('Loop Iteration')
    try:
    #Man Door - Pin Status
        if GPIO.input(MAN_DOOR_PIN): #Open Door
            if manDoorState is None:
                dbEvent('ManDoor','Open', 0)
                manDoorState = now()
            
                #Test time, if its too late warn me with NMA!
                if manDoorState.hour >= NMA_LATE_START and manDoorState.hour <= NMA_LATE_END:
                    sendAndroidNotify('Man Door Opened','Your garage has been opened late!',2)

            else: #Door Open for >1 iteration
		currTime = now()
		debug_print('ManDoor still open')

                #Each iteration this door is open, take a picture
                capture_photo(currTime) 
                
                #Send Notify MessageA if over time limit
                delta = currTime - manDoorState
                if delta.total_seconds() > NMA_DELAY_SEC and not manNotified:
                    sendAndroidNotify('Man Door Left Open','Man Door has been left open!',1)
                    manNotified = True

        else: #Door close state
            if not manDoorState is None:
                delta_time = totalSeconds(manDoorState, now())
                dbEvent('ManDoor','Close', delta_time )
            manDoorState = None
            manNotified = False
            
    #Garage Door - Pin Status
        if GPIO.input(GARAGE_DOOR_PIN): #Door Open
            if garageDoorState is None:
                dbEvent('GarageDoor','Open', 0)
                garageDoorState = now() 

                #Test time, if its too late warn me!
                if garageDoorState.hour >= NMA_LATE_START and garageDoorState.hour <= NMA_LATE_END:
                    sendAndroidNotify('Garage Door Opened','Your garage has been opened late!',2)

            else: #Door open for >1 iteration
                debug_print('Garage Door Still Open')

                #Send Notify if over limit
                currTime = now()
                delta = currTime - garageDoorState
                if delta.total_seconds() > NMA_DELAY_SEC and not garageNotified:
                    sendAndroidNotify('Garage Door Left Open','Garage Door has been left open!',1)
                    garageNotified = True

        else: #Door close state
            if not garageDoorState is None:
                delta_time = totalSeconds(garageDoorState, now())
                dbEvent('GarageDoor','Close', delta_time )

            garageDoorState = None
            garageNotified = False

    #End of Pin checks
    #Check for Picture Request
        if os.path.isfile(PIC_FILE):
            debug_print("Photo Request Received")
            capture_photo(now())
            os.remove(PIC_FILE)
            
        time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
	QUIT = True

#Loop finished - clean up program
dbEvent('DoorReader','Stopping',0)
GPIO.cleanup()
camera.close()

