#Reads the NC port from magnetic door switch and blinks the LED when detected
import RPi.GPIO as GPIO
import time

#Var setup
rPin = 24
wPin = 18
hbPin = 23
pulse = False
quit = False

#RPi GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(rPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wPin, GPIO.OUT)
GPIO.setup(hbPin, GPIO.OUT)

while not quit:
        try:
                #Heartbeat
                pulse = not pulse

                if pulse:
                        GPIO.output(hbPin,GPIO.LOW)
                else:
                        GPIO.output(hbPin,GPIO.HIGH)

                if not GPIO.input(rPin):
                        GPIO.output(wPin,GPIO.HIGH)
                else:
                        GPIO.output(wPin,GPIO.LOW)

                time.sleep(0.5)
        except KeyboardInterrupt:
                quit = True

GPIO.cleanup()
