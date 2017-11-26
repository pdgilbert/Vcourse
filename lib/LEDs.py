# License GPL 2. Copyright Paul D. Gilbert, 2017

#   generic part of LED control

# leds are off, on solid, or flashing. Flashing control (frequency and 
# duty cycle) are set the same for all leds. With PWM it would be possible
# to flash diferently, but that seems to hard to visually distinguish. 
# The thread versions, which are used when PWM is not available, would
# require a separate thread for each led to allow separate control.
# That is not implemented.

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

if "BCM2835"  in hw :
   logging.info("importing LED_RpiZeroW")
   import LED_RpiZeroW   as gpio                 # Raspbian / Raspberry Pi Zero W
elif "Allwinner sun8i Family" in hw :
   logging.info("importing LED_OPi")
   import LED_OPi       as gpio                  # Armbian  / Orange Pi Zero
elif "GenuineIntel" in hw :
   logging.info("importing LED_simulate")
   import LED_simulate  as gpio                  # my laptop
else  :
   logging.critical("Error hardware not recognized.")
   raise  Exception('Error hardware not recognized.')

# flash speed in Hz
SLOW     = 0.5  
MEDIUM   = 1.0 # can miss this with quick look
FAST     = 2.0
VERYFAST = 4.0

# pins are set in hardware specific modules
RED    =  gpio.RED
GREEN  =  gpio.GREEN
BLUE   =  gpio.BLUE 

# flash speed and duty cycle are first set here but can be
# reset in arguments to flash().

leds = gpio.LEDs((RED, GREEN, BLUE), FAST, 20) #  (channels, frequency, dc)
leds.start()  #initalize

#leds.on(RED)
#leds.off()
#leds.flash(RED)
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

def  bound(x ='')  : 
   print('zone  red '   + str(x))
   leds.off()  
   leds.on(RED)

def  warn(x ='')   : 
   print('flash red '   + str(x))
   leds.off()  
   leds.flash(RED)   #, FAST, 20)

def  center(x ='') : 
   print('flash green ' + str(x))
   leds.off()  
   leds.flash(GREEN)   #, FAST, 20)

def  update(x ='') : 
   print('flash all lights ' + str(x))
   leds.off()  
   leds.flash(RED)   #, FAST, 20)
   leds.flash(GREEN)   #, FAST, 20)
   time.sleep(20)
   leds.off()  

def  cleanup(x ='') :
   logging.info('cleanup GPIO for shutdown ' + str(x))
   leds.cleanup()  # cleanup GPIO and shut down threads

def  noGPSfix(x ='')  : 
   print('flash blue'   + str(x))
   leds.off()  
   leds.flash(BLUE)   #, FAST, 20)

def  systemProblem(x ='')  : 
   print('system problem blue'   + str(x))
   logging.warning('system problem blue'   + str(x))
   leds.off()  
   leds.on(BLUE)


# Old status is needed because PWM flickers too fast if constantly 
# reset, so set only on change

status = 'off'
# 'off' 'bound' 'warn' 'center' 'update' 'noGPSfix' 'systemProblem' 

# beware, I think "from LEDs import setLEDs" will fail because 
#  this needs global status.

def  setLEDs(nw, x ='')  : 
   global status
   if not status == nw :
      if   nw == 'off'           : off(x)
      elif nw == 'bound'         : bound(x)
      elif nw == 'warn'          : warn(x)
      elif nw == 'center'        : center(x)
      elif nw == 'update'        : update(x)
      elif nw == 'noGPSfix'      : noGPSfix(x)
      elif nw == 'systemProblem' : systemProblem(x)
      else :
         raise ValueError(
         "LED now status ('" +nw+ "') incorrect value.\nOld status is '" +status+ "'. x is'" +x+ "'.")

      status = nw
