# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Raspbian / Raspberry Pi Zero W LED signal hardware control."""

__version__ = '0.0.3'

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



# https://pinout.xyz/pinout/io_pi_zero#

# using  board pin numbers not broadcom numbers  GPIO.BCM vs GPIO.BOARD
RED    =  12                                    #    18        pin 12
GREEN  =  16                                    #    23        pin 16
BLUE   =  18                                    #    24        pin 18  

#Raspberry pi has pulse width modulation (PWM) on all pins so a thread
#  is not needed for flashing leds.


#red = GPIO.PWM(RED, 0.5) #  (channel, frequency)
#red.start(0)            # arg is duty cycle. 99=mostly on
#red.ChangeFrequency(2)  
#red.ChangeDutyCycle(0.5)
#red.ChangeDutyCycle(20)
#red.stop()
#red.start(99)           
#red.stop()

# off() works on all initialized channels
# on() and flash() work only on a single specified channel

class LEDs():
    def __init__(self, channels, freq, dc):
        if not (0.0 < freq) :
          raise Exception('freq should be in Hz (0.0 < freq)')
        if not (0.0 <= dc <= 100.0) :
          raise Exception('dc should be in percentage points (0.0 <= dc <= 100.0)')
        if not isinstance(channels, tuple) : 
          raise Exception('channels should specify all channels')
        self.channels = channels
        self.freq  = freq
        self.dc    = dc # duty cycle = percent of time on
    def start(self):
        #also need this call for compatability (other objects start thread)
        GPIO.setmode(GPIO.BOARD)  
        GPIO.setwarnings(True) # warnings if something else may be using pins
        GPIO.setup((RED, GREEN, BLUE), GPIO.OUT)   # set as outputs
        GPIO.output((RED, GREEN, BLUE), GPIO.LOW)  # initially set all off
        self.PWmanagers = {RED : GPIO.PWM(RED,   self.dc), 
                         GREEN : GPIO.PWM(GREEN, self.dc), 
                          BLUE : GPIO.PWM(BLUE,  self.dc)}
        for c in self.channels : self.PWmanagers[c].start(0) #dc=0 implies off
        for c in self.channels :self. PWmanagers[c].ChangeFrequency(2) 
    def flash(self, ch, freq=None, dc=None):
        if ch not in self.channels :
          raise Exception('ch must be in initialized channels')
        if freq is None: self.PWmanagers[ch].ChangeFrequency(self.freq)
        else :           
           self.PWmanagers[ch].ChangeFrequency(freq)
           self.freq = freq
        if  dc  is None: self.PWmanagers[ch].start(self.dc)
        else :       
           self.dc   = dc
           self.PWmanagers[ch].start(dc)
    def on(self, ch):
        if ch not in self.channels :
          raise Exception('ch must be in initialized channels')
        self.PWmanagers[ch].start(99)
    def info(self) :
        print('initialized channels ' + str( self.channels))
        print('frequency  ' + str( self.freq))
        print('duty cycle ' + str( self.dc))
    def off(self): 
        for c in self.channels : self.PWmanagers[c].ChangeDutyCycle(0) 
        #shutoff can be a bit slow and happen after next turn on signal, 
        # so sleep, but this would not work for a thread
        time.sleep(0.5)
    def cleanup(self): 
        self.off()
        GPIO.cleanup()  

#leds = LEDs((RED, GREEN, BLUE), 2, 20) #  (channels, frequency, dc)
#leds.start()
#leds.on(RED)
#leds.off()
#leds.flash(RED)
#leds.flash(RED, 2, 0.1)
#leds.flash(RED, 2, 20)
#leds.off()
#leds.cleanup()

