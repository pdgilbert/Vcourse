# License GPL 2. Copyright Paul D. Gilbert, 2017

#   generic part of LED control

import subprocess
import time
import logging

try:
   hw = str(subprocess.check_output("grep Hardware /proc/cpuinfo", shell=True))
except:
   try:
     hw = str(subprocess.check_output("grep vendor_id /proc/cpuinfo", shell=True))
   except RuntimeError:
     logging.critical("Error hardware not recognized.")
     raise  Exception('Error hardware not recognized.')

if "BCM2835" "Allwinner sun8i Family" in hw :
   import LED_RpiZeroW   as gpio                   # Raspbian / Raspberry Pi Zero W
elif "Allwinner sun8i Family" in hw :
   import LED_OPi       as gpio                  # Armbian  / Orange Pi Zero
elif "GenuineIntel" in hw :
   import LED_simulate  as gpio                  # my laptop
else  :
   logging.critical("Error hardware not recognized.")
   raise  Exception('Error hardware not recognized.')


SLOW     = 0.5
MEDIUM   = 1.0 # can miss this with quick look
FAST     = 2.0
VERYFAST = 4.0

RED    =  gpio.RED
GREEN  =  gpio.GREEN
BLUE   =  gpio.BLUE 
CHANNELS = gpio.CHANNELS


#leds = gpio.LEDs(CHANNELS, SLOW, 20) #  (all channels, frequency, dc)

leds = gpio.LEDs(CHANNELS, SLOW) #  (all channel, frequency) duty cycle default
leds.start()

#leds.on(RED)
#leds.off()
#leds.flash(RED)
#leds.flash(CHANNELS)
#leds.ChangeFrequency(2)    # where freq is the new frequency in Hz
#leds.ChangeDutyCycle(0.5)  # where 0.0 <= dc <= 100.0 is duty cycle (percent time on)
#leds.ChangeDutyCycle(20)
#leds.off()
#leds.join()  # shut down thread

#threading.activeCount()
#threading.currentThread()
#threading.enumerate()

def  off(x ='')    : 
   print('no light '    + str(x))
   leds.off()
   #shutoff can be a bit slow and happen after next on signal, so
   time.sleep(0.5)

def  bound(x ='')  : 
   print('zone  red '   + str(x))
   leds.off()  
   leds.on(RED)

def  warn(x ='')   : 
   print('flash red '   + str(x))
   leds.off()  
   leds.ChangeDutyCycle(20)     
   leds.ChangeFrequency(FAST)  
   leds.flash(RED)

def  center(x ='') : 
   print('flash green ' + str(x))
   leds.off()  
   leds.ChangeDutyCycle(20)            
   leds.ChangeFrequency(FAST)  
   leds.flash(GREEN)

def  update(x ='') : 
   print('flash all lights ' + str(x))
   leds.off()  
   leds.ChangeDutyCycle(20)            
   leds.ChangeFrequency(FAST)  
   leds.flash((RED, GREEN))
   time.sleep(20)
   leds.off()  

def  cleanup(x ='') :
   logging.info('cleanup GPIO for shutdown ' + str(x))
   leds.off()
   leds.cleanup()  # cleanup GPIO and shut down threads


def  systemProblem(x ='')  : 
   print('system problem blue'   + str(x))
   logging.warning('system problem blue'   + str(x))
   leds.off()  
   leds.on(BLUE)

