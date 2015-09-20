#Custom code for blinking Red & Green LEDs on Raspberry Pi
# LEDs wired through the respective pins in series with 270ohm resistor
# Blinks at a rate of 1 per second


import RPi.GPIO as GPIO
import time

#Blinking
def blinkRed():
        blink(12)
        return

def blinkGrn():
        blink(16)
        return

def blink(pin):
        GPIO.output(pin,GPIO.HIGH)
        time.sleep(1)
        GPIO.output(pin,GPIO.LOW)
        return

#GO GO GO
#Use Board Numbers
GPIO.setmode(GPIO.BOARD)

#Setup output channels
GPIO.setwarnings(False)
GPIO.setup(12,GPIO.OUT)
GPIO.setup(16,GPIO.OUT)

for i in range (0,25):
        blinkRed()
        blinkGrn()

GPIO.cleanup()
