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
    logging.critical("Error importing RPi.GPIO!  Wrong hardware? or possibly need root privileges.")
    raise Exception('LED_piZeroW module will not work without RPi.GPIO.')


#logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

RED    = 12
GREEN  = 16
BLUE   = 18  # not currently used

SLOW     = 0.5
MEDIUM   = 1.0 # can miss this with quick look
FAST     = 2.0
VERYFAST = 4.0

CHANNELS = (RED, GREEN, BLUE)


GPIO.setmode(GPIO.BOARD) # use board pin numbers not broadcom GPIO.setmode(GPIO.BCM)
#NB. BCM 18 = pin 12
#    BCM 24 = pin 18
# https://pinout.xyz/pinout/io_pi_zero#
 
GPIO.setwarnings(True) # for warnings in the case something else may be using pins?

#GPIO.setup(RED,GPIO.OUT)        # set pin 12 as an output
GPIO.setup(CHANNELS, GPIO.OUT)   # set CHANNELS pins as an output

#GPIO.output(12,GPIO.LOW)
GPIO.output(CHANNELS, GPIO.LOW)  # initially set all off


#pulse width modulation (PWM)

red = GPIO.PWM(RED, SLOW) #  (channel, frequency)
#red.ChangeFrequency(2)    # where freq is the new frequency in Hz
#red.ChangeDutyCycle(0.5)  # where 0.0 <= dc <= 100.0 is duty cycle (percent time on)
#red.ChangeDutyCycle(20)

green = GPIO.PWM(GREEN, SLOW) 
#green.ChangeDutyCycle(20)

blue = GPIO.PWM(BLUE, SLOW) 
#blue.ChangeDutyCycle(20)


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
   off()  
   #GPIO.output(RED,   GPIO.HIGH)
   red.start(99)            # arg is duty cycle. 99=mostly on
   #red.ChangeDutyCycle(99)
   red.ChangeFrequency(0.1)  

def  warn(x ='')   : 
   print('flash red '   + str(x))
   off()  
   red.start(20)             # arg is duty cycle..
   red.ChangeFrequency(FAST)  # where freq is the new frequency in Hz

def  center(x ='') : 
   print('flash green ' + str(x))
   off()  
   green.start(1)            # arg is suppose to be dc, but I'm not sure it is.
   green.ChangeDutyCycle(20)
   green.ChangeFrequency(FAST)  # where freq is the new frequency in Hz

def  update(x ='') : 
   print('flash all lights ' + str(x))
   off()  
   red.start(20)            # arg is suppose to be dc, but I'm not sure it is.
   green.start(20)            # arg is suppose to be dc, but I'm not sure it is.
   red.ChangeFrequency(FAST)  # where freq is the new frequency in Hz
   green.ChangeFrequency(FAST)  # where freq is the new frequency in Hz
   time.sleep(20)
   off()  

def  cleanup(x ='') :
   logging.info('cleanup GPIO for shutdown ' + str(x))
   # this cleans up GPIO.setup too
   GPIO.cleanup()  # GPIO.cleanup(RED)   GPIO.cleanup( CHANNELS )

def  systemProblem(x ='')  : 
   print('system problem blue'   + str(x))
   logging.warning('system problem blue'   + str(x))
   off()  
   blue.start(99)            # arg is duty cycle. 99=mostly on
   blue.ChangeFrequency(0.1)  

