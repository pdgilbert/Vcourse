# License GPL 2. Copyright Paul D. Gilbert, 2017, 2018
"""Simulate LED signal hardware by simple print statements."""

import time
import logging
import threading

RED    =  101
GREEN  =  102
BLUE   =  103 

# Raspberry Pi has PWM hardware. This simulation code follows 
# Orange Pi more closely, and spawns process mainly to handle flashing.

# off() works on all initialized channels
# on() and flash() work only on a single specified channel

class LEDs(threading.Thread):
    def __init__(self, channels, freq, dc):
        threading.Thread.__init__(self)
        self.name='simulate LEDs controller'
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
        self.ont  = (1/self.freq) * (self.dc / 100)
        self.offt = (1/self.freq) - self.ont
        self.FLASH = {RED : False, GREEN : False, BLUE : False}
    def run(self):
        logging.info('LEDs run() started.')
        logging.debug(threading.enumerate())
        while not self.stoprequest.isSet():
            if self.FLASH[RED]   :
               print(' flash RED at ' + str(self.freq) + ' Hz, ' + str(self.dc) + ' dc')
            if self.FLASH[GREEN] : 
               print(' flash GREEN at ' + str(self.freq) + ' Hz, ' + str(self.dc) + ' dc')
            if self.FLASH[BLUE]  : 
               print(' flash BLUE at ' + str(self.freq) + ' Hz, ' + str(self.dc) + ' dc')
            time.sleep(self.ont)   # ?? non -blocking
            time.sleep(self.offt)
            # on and off not affected by loop, only flashing
            time.sleep(2)
        self.off()
        logging.info('LEDs run() exiting.')
    def flash(self, ch, freq=None, dc=None):
        if not ch in self.channels :
          raise Exception('ch must be in initialized channels')
        if freq is not None:
           self.freq = freq
           self.ont  = (1/self.freq) * (self.dc / 100)
           self.offt = (1/self.freq) - self.ont
        if  dc  is not None:
           self.dc   = dc
           self.ont  = (1/self.freq) * (self.dc / 100)
           self.offt = (1/self.freq) - self.ont
        self.FLASH[ch] = True
    def on(self, ch):
        if not ch in self.channels :
          raise Exception('ch must be in initialized channels')
        self.FLASH[ch] = False
        print(str(ch) + ' on.')
    def info(self) :
        print('initialized channels ' + str( self.channels))
        print('frequency  ' + str( self.freq))
        print('duty cycle ' + str( self.dc))
    def off(self): 
        for c in self.channels :
           self.FLASH[c] = False
           print(str(c) + ' off.')
    # join() should not be called from outside because not all implementations
    # of the class need threads. Use cleanup() instead.
    def cleanup(self): 
        logging.info('LEDs cleanup() for shutdown.')
        self.stoprequest.set()
        #self.join() ??

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
