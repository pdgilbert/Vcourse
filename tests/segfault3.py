#!/usr/bin/python3

# This test needs Raspberry Pi hardware

# need  export PYTHONPATH=/path/to/Vcourse/lib

import RPi.GPIO as GPIO
import time

#  GPIO.cleanup()
#  quit()

RED    = 12
GREEN  = 16
BLUE   = 18  # not currently used

SLOW     = 0.5
MEDIUM   = 1.0 # can miss this with quick look
FAST     = 2.0
VERYFAST = 4.0

CHANNELS = (RED, GREEN, BLUE)
GPIO.setmode(GPIO.BOARD) # use board pin numbers n
GPIO.setwarnings(True) # for warnings 

GPIO.setup(CHANNELS, GPIO.OUT)   # set CHANNELS pins as an output
GPIO.output(CHANNELS, GPIO.LOW)  # initially set all off

red = GPIO.PWM(RED, SLOW) #  (channel, frequency)
green = GPIO.PWM(GREEN, SLOW) 
blue = GPIO.PWM(BLUE, SLOW) 

def  off(x ='')    : 
   print('no light '    + str(x))
   red.stop()
   green.stop()
   blue.stop()
   GPIO.output(CHANNELS, GPIO.LOW)
   #shutoff can be a bit slow and happen after next on signal, so
   time.sleep(0.5)

def  bound(x ='')  : 
   print('zone  red '   + str(x))
   red.stop()
   green.stop()
   blue.stop()
   GPIO.output(CHANNELS, GPIO.LOW)
   red.start(99)
   #red.ChangeDutyCycle(99)
   red.ChangeFrequency(0.1)  

def  warn(x ='')   : 
   print('flash red '   + str(x))
   red.stop()
   green.stop()
   blue.stop()
   GPIO.output(CHANNELS, GPIO.LOW)
   red.start(20)
   red.ChangeFrequency(FAST)

# possibly repeat following 2 or 3 times
bound()
warn()
off()

#after a few seconds
#>>> Segmentation fault
