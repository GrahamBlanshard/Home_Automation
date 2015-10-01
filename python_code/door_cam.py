# Waits for a signal from the magnetic door switch then snaps a picture
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

pic_done = 5

#RPi GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(readyPin, GPIO.OUT)
GPIO.setup(writingPin, GPIO.OUT)

while not quit:
        try:
                if not GPIO.input(rPin) and pic_done > 5:
                        pic_done = 0
                        GPIO.output(readyPin, GPIO.LOW)
                        GPIO.output(writingPin, GPIO.HIGH)
                        camera.capture('image.jpg')
                        print "Pic captured!"
                        GPIO.output(writingPin,GPIO.LOW)
                else:
                        pic_done = pic_done + 1

                if pic_done > 10:
                        pic_done = 10
                        GPIO.output(readyPin, GPIO.HIGH)

                time.sleep(0.5)
        except KeyboardInterrupt:
                quit = True

GPIO.cleanup()
