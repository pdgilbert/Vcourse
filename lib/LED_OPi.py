# License GPL 2. Copyright Paul D. Gilbert, 2017
#  Arbian / Orange Pi  LEDs

#CAN WE DO THIS WITHOUT ROOT
#http://linux-sunxi.org/GPIO

# pinout
#http://codelectron.com/blink-leds-using-orange-pi-zero-gpio-and-python/
#https://oshlab.com/orange-pi-zero-pinout/
#http://www.orangepi.org/orangepibbsen/forum.php?mod=viewthread&tid=148&page=13
#http://www.instructables.com/id/Orange-Pi-One-Python-GPIO-basic/
#includes enabling spidev:
#https://forum.armbian.com/topic/3084-orange-pi-zero-python-gpio-library/
#PWM
#http://www.orangepi.org/orangepibbsen/forum.php?mod=viewthread&tid=1153&highlight=PWM

#  pyA20.gpio / Orange equivalent??
#To discover the Raspberry Pi board revision:
#GPIO.RPI_INFO['P1_REVISION']
#To discover the version of RPi.GPIO:
#GPIO.VERSION

import time
import logging
import threading

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

try:
    from pyA20.gpio import gpio as GPIO
    from pyA20.gpio import port
except RuntimeError:
    logging.critical("Error importing pyA20.gpio!  Wrong hardware? or possibly need root privileges.")
    raise Exception('LED_OpiZero module will not work without pyA20.gpio.')


#logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

RED    = port.PA7   # pin 12
GREEN  = port.PA19  # pin 16
BLUE   = port.PA18  # pin 18  


#GPIO.init()
#for c in (RED, GREEN, BLUE):  GPIO.setcfg(c, GPIO.OUTPUT) #set pins as output
#for c in (RED, GREEN, BLUE):  GPIO.output(c, GPIO.LOW)    #init all off
#GPIO.output(RED, GPIO.HIGH)
#GPIO.output(RED, GPIO.LOW)
#GPIO.output(GREEN, GPIO.HIGH)
#GPIO.output(GREEN, GPIO.LOW)
#GPIO.output(BLUE, GPIO.HIGH)
#GPIO.output(BLUE, GPIO.LOW)

# It would be possible to have a flashing object per colour, but that means a
# loop thread for each colour, and each colour has to be turned off individually.
# An object for all leds seems simpler.

# off() works on all initialized channels
# on() and flash() work only on a single specified channel

class LEDs(threading.Thread):
    def __init__(self, channels, freq, dc):
        threading.Thread.__init__(self)
        logging.debug('LEDs init.')
        if not (0.0 < freq) :
          raise Exception('freq should be in Hz (0.0 < freq)')
        if not (0.0 <= dc <= 100.0) :
          raise Exception('dc should be in percentage points (0.0 <= dc <= 100.0)')
        if not isinstance(channels, tuple) : 
          raise Exception('channels should specify all channels')
        self.channels = channels
        # Thread loop uses only ont and offt, but freq and dc are kept in order
        #   to recalculate if the other is changed.
        self.freq  = freq
        self.dc    = dc # duty cycle = percent of time on
        self.stoprequest = threading.Event()
        # ont, offt = seconds on and off, these add to freq which is in Hz
        self.ont  = self.freq * self.dc / 100
        self.offt = self.freq - self.ont
        self.FLASH = {RED : False, GREEN : False, BLUE : False}
    def run(self):
        logging.debug('LEDs run().')
        logging.debug(threading.enumerate())
        #GPIO.setwarnings(True) # Orange equivalent??
        GPIO.init()
        for c in self.channels:  GPIO.setcfg(c, GPIO.OUTPUT) #set pins as output
        for c in self.channels:  GPIO.output(c, GPIO.LOW)    #init all off
        # ont, offt = seconds on and off, these add to freq which is in Hz
        while not self.stoprequest.isSet():
            if self.FLASH[RED]   : GPIO.output(RED,   GPIO.HIGH)
            if self.FLASH[GREEN] : GPIO.output(GREEN, GPIO.HIGH)
            if self.FLASH[BLUE]  : GPIO.output(BLUE,  GPIO.HIGH)
            time.sleep(self.ont)   
            if self.FLASH[RED]   : GPIO.output(RED,   GPIO.LOW)
            if self.FLASH[GREEN] : GPIO.output(GREEN, GPIO.LOW)
            if self.FLASH[BLUE]  : GPIO.output(BLUE,  GPIO.LOW)
            time.sleep(self.offt)
        # on and off not affected by loop, only flashing
        # but the loop is going always. 
        # Loop could be slowed down with sleep if no leds are flashing
        logging.debug('in LEDs run(), off() for shutting down.')
        self.off()
        logging.debug('in LEDs run(), shutting down.')
    def flash(self, ch, freq=None, dc=None):
        if not ch in self.channels :
          raise Exception('ch must be in initialized channels')
        if freq is not None:
           self.freq = freq
           self.ont  = self.freq * self.dc / 100
           self.offt = self.freq - self.ont
        if  dc  is not None:
           self.dc   = dc
           self.ont  = self.freq * self.dc / 100
           self.offt = self.freq - self.ont
        self.FLASH[ch] = True
    def on(self, ch):
        if not ch in self.channels :
          raise Exception('ch must be in initialized channels')
        self.FLASH[ch] = False
        GPIO.output(ch, GPIO.HIGH)
    def info(self) :
        print('initialized channels ' + str( self.channels))
        print('frequency  ' + str( self.freq))
        print('duty cycle ' + str( self.dc))
    def off(self): 
        for c in self.channels :
           self.FLASH[c] = False
           GPIO.output(c, GPIO.LOW)
    def join(self): 
        # join should not be called from outside because not all implementations
	# of the class need threads. Use cleanup() instead.
        self.stoprequest.set()
    def cleanup(self): 
        #  Orange equivalent of ?
        # GPIO.cleanup()  # GPIO.cleanup(RED)   GPIO.cleanup( CHANNELS )
        logging.debug('in LEDs cleanup().')
        logging.debug(threading.enumerate())
        self.join()

#leds = LEDs((RED, GREEN, BLUE), 2, 20) #  (channels, frequency, dc)
#leds.start()
#leds.on(RED)
#leds.on(BLUE)
#leds.on(GREEN)
#leds.off()
#leds.flash(RED)
#leds.flash(GREEN)
#leds.flash(BLUE)
#leds.flash(RED, 2, 0.1)
#leds.flash(RED, 2, 20)
#leds.off()
#leds.cleanup()
