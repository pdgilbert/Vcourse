#https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
#https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/
#https://pythonhosted.org/RPIO/pwm_py.html

#To discover the Raspberry Pi board revision:
#GPIO.RPI_INFO['P1_REVISION']
#To discover the version of RPi.GPIO:
#GPIO.VERSION

import time
import logging

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  Wrong hardware? or possibly need root privileges.")
    raise Exception('LED_piZeroW module will not work without RPi.GPIO.')


logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

RED    = 12
GREEN  = 16
BLUE   = 18  # not currently used

SLOW     = 0.5
MEDIUM   = 1.0
FAST     = 2.0
VERYFAST = 4.0

CHANNELS = (RED, GREEN, BLUE)


GPIO.setmode(GPIO.BOARD) # use board pin numbers not broadcom GPIO.setmode(GPIO.BCM)
#NB. BCM 18 = pin 12
#    BCM 24 = pin 18
# https://pinout.xyz/pinout/io_pi_zero#
 
#GPIO.setwarnings(False) # for warnings in the case something else may be using pins?

#GPIO.setup(RED,GPIO.OUT)        # set pin 12 as an output
GPIO.setup(CHANNELS, GPIO.OUT)   # set CHANNELS pins as an output

#GPIO.output(12,GPIO.LOW)
GPIO.output(CHANNELS, GPIO.LOW)  # initially set all off


#pulse width modulation (PWM)

red = GPIO.PWM(RED, SLOW) #  (channel, frequency)
#red.ChangeFrequency(2)    # where freq is the new frequency in Hz
#red.ChangeDutyCycle(0.5)  # where 0.0 <= dc <= 100.0 is duty cycle (percent time on)
red.ChangeDutyCycle(20)

green = GPIO.PWM(GREEN, SLOW) 
green.ChangeDutyCycle(20)

blue = GPIO.PWM(BLUE, SLOW) 
blue.ChangeDutyCycle(20)


def  bound(x ='')  : 
   logging.debug('zone  red '   + str(x))
   GPIO.output(CHANNELS, GPIO.LOW)  # sets all CHANNELS to GPIO.LOW first
   GPIO.output(RED,   GPIO.HIGH)

def  warn(x ='')   : 
   logging.debug('flash red '   + str(x))
   GPIO.output(CHANNELS, GPIO.LOW) 
   red.start(1)            # arg is suppose to be dc, but I'm not sure it is.
   red.ChangeFrequency(FAST)  # where freq is the new frequency in Hz

def  center(x ='') : 
   logging.debug('flash green ' + str(x))
   GPIO.output(CHANNELS, GPIO.LOW)  
   green.start(1)            # arg is suppose to be dc, but I'm not sure it is.
   green.ChangeFrequency(MEDIUM)  # where freq is the new frequency in Hz

def  off(x ='')    : 
   logging.debug('no light '    + str(x))
   red.stop()
   green.stop()
   blue.stop()
   GPIO.output(CHANNELS, GPIO.LOW) 

def  update(x ='') : 
   logging.debug('flash all lights ' + str(x))
   GPIO.output(CHANNELS, GPIO.LOW)  
   red.start(1)            # arg is suppose to be dc, but I'm not sure it is.
   green.start(1)            # arg is suppose to be dc, but I'm not sure it is.
   red.ChangeFrequency(FAST)  # where freq is the new frequency in Hz
   green.ChangeFrequency(FAST)  # where freq is the new frequency in Hz
   time.sleep(20)
   off()  

def  cleanup(x ='') :
   logging.debug('cleanup for shutdown ' + str(x))
   # this cleans up GPIO.setup too
   GPIO.cleanup()  # GPIO.cleanup(RED)   GPIO.cleanup( CHANNELS )

def  systemProblem(x ='')  : 
   logging.debug('system problem blue'   + str(x))
   GPIO.output(CHANNELS, GPIO.LOW)  # sets all CHANNELS to GPIO.LOW first
   GPIO.output(BLUE,   GPIO.HIGH)

