# License GPL 2. Copyright Paul D. Gilbert, 2017, 2018
"""Generic part of LED control.

Turn LEDs off, on solid, or flashing corresponding to a specified state. 
The states are those determined by zones on the course, that is 'off', 
'bound', 'warn', 'center', 'update', 'noGPSfix',  or 'systemProblem'.
There is a also 'checkout' and 'checkin' used for Registration

The primary function call is to setLEDs(nw, x =''), where nw is 
the state and x is a (mainly debugging) string written to stdout.

This module is intended to work with a hardware specific module for 
controlling GPIO pins. (Currently LED_RpiZeroW for a Raspian on a
Raspberry Pi ZeroW,  LED_OPi for Armbian on an Orange Pi Zero, or
LED_simulate for simulating on an Intel based machine.)

Some hardware specific modules require threading to implement LED
flashing, This is necessary when PWM is not available. Flashing would
require a separate thread for each LED to allow separate control.
That is not implemented, so flashing control (frequency and duty cycle)
are set the same for all LEDs. 
With PWM it would be possible to flash differently, but that also seems
hard to visually distinguish.

"""

import subprocess
import time
import logging

if not hasattr(subprocess, "run") :
   # this workaround for old Raspian subprocess which does not have .run
   Hardware =  "BCM2835"

else :
   hw  = subprocess.run("grep Hardware /proc/cpuinfo", shell=True, stdout=subprocess.PIPE)

   if not 0 == hw.returncode :
      hw = subprocess.run("grep part /proc/cpuinfo", shell=True, stdout=subprocess.PIPE)

   if not 0 == hw.returncode :
      hw = subprocess.run("grep vendor_id /proc/cpuinfo", shell=True, stdout=subprocess.PIPE)

   if not 0 == hw.returncode :
      logging.critical('Error hardware test non-zero return code.')
      raise  Exception('Error hardware test non-zero return code.')

   Hardware =  str(hw.stdout)

if "BCM2835"  in Hardware :                     
   # Raspbian / Raspberry Pi Zero W
   logging.info("importing LED_RpiZeroW")
   import LED_RpiZeroW   as gpio          
elif "Allwinner" in Hardware  or "0xc07" in Hardware  or "0xd03" in Hardware : 
   #Armbian/Orange Pi Zero & Lite, Pi Zero Plus
   logging.info("importing LED_OPi") 
   import LED_OPi       as gpio 
elif "GenuineIntel" in Hardware :
   # my laptop
   logging.info("importing LED_simulate")
   import LED_simulate  as gpio              
else  :
   logging.critical('Error hardware not recognized.')
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

def  checkout(x ='') : 
   print('blue, red, green, all, green ' + str(x))
   leds.off()  
   leds.on(BLUE)   
   time.sleep(0.5)
   leds.off()  
   leds.on(RED)
   time.sleep(0.5)
   leds.off()  
   leds.on(GREEN)
   time.sleep(0.5)
   leds.off()  
   leds.on(BLUE)   
   leds.on(RED)
   leds.on(GREEN)
   time.sleep(0.5)
   leds.off()  
   leds.on(GREEN)
   time.sleep(1)
   leds.off()  

def  checkin(x ='') : 
   print('red 1 sec flash ' + str(x))
   leds.off()  
   leds.on(RED)   
   time.sleep(1)
   leds.off()  

def  ok(x ='') : 
   print('green 1/3 sec flash ' + str(x))
   leds.off()  
   leds.on(GREEN)   
   time.sleep(0.3)
   leds.off()  

# Old status is needed because PWM flickers too fast if constantly 
# reset, so set only on change

status = 'off'
# 'off' 'bound' 'warn' 'center' 'update' 'noGPSfix' 'systemProblem' 

# beware, I think "from LEDs import setLEDs" will fail because 
#  this needs global status.

def  setLEDs(nw, x ='')  : 
   """
   Set state of LEDs and return None.

   Possible state settings are 'off', 'bound', 'warn', 'center', 'update', 
   'noGPSfix',  'systemProblem', or 'checkout'.
   """
   
   global status
   if not status == nw :
      if   nw == 'off'           : off(x)
      elif nw == 'bound'         : bound(x)
      elif nw == 'warn'          : warn(x)
      elif nw == 'center'        : center(x)
      elif nw == 'update'        : update(x)
      elif nw == 'noGPSfix'      : noGPSfix(x)
      elif nw == 'systemProblem' : systemProblem(x)
      elif nw == 'checkout'      : checkout(x)    # for Registration
      elif nw == 'checkin'       : checkin(x)     # for Registration
      elif nw == 'ok'            : ok(x)          # for Registration
      else :
         raise ValueError(
         "LED now status ('" +nw+ "') incorrect value.\nOld status is '" +status+ "'. x is'" +x+ "'.")

      status = nw
