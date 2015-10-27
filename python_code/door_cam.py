# Captures a picture every 3 seconds while the door is in an "Open" state
#
# LED Support:
# Green LED on BCM pin 23 signals when it is ready for a new pic
# Red LED on BCM pin 18 signals when a pic is saving
# Small delay between pics added so it doesn't go hog wild
# quit with ctrl-c

import RPi.GPIO as GPIO
import time
import picamera

#Var setup
rPin = 24
readyPin = 23
writingPin = 18
quit = False

#Camera Setup
camera = picamera.PiCamera()
camera.vflip = True

pic_delay = 0
TIME_DELAY = 6

#RPi GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(readyPin, GPIO.OUT)
GPIO.setup(writingPin, GPIO.OUT)

while not quit:
        try:
                if GPIO.input(rPin):
			pic_delay += 1
                        GPIO.output(readyPin, GPIO.LOW)
			if pic_delay > TIME_DELAY:
                        	GPIO.output(writingPin, GPIO.HIGH)
                        	camera.capture('image.jpg')
                        	print "Pic captured! " + time.ctime()
                        	GPIO.output(writingPin,GPIO.LOW)
				pic_delay = 0

              	if not GPIO.input(rPin): 
			pic_delay = 0
                        GPIO.output(readyPin, GPIO.HIGH)

                time.sleep(0.5)
        except KeyboardInterrupt:
                quit = True

GPIO.cleanup()
