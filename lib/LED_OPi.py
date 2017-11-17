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
CHANNELS = (RED, GREEN, BLUE)

#  Orange equivalent??
#GPIO.setwarnings(True) # for warnings in the case something else may be using pins?

GPIO.init()

for c in CHANNELS:  GPIO.setcfg(c,   GPIO.OUTPUT)   # set pins as an output

for c in CHANNELS:  GPIO.output(c, GPIO.LOW)        # initially set all off

# It would be possible to have a flashing object per colour, but that means a
# loop thread for each colour, and each colour has to be turned off individually.
# An object for all leds seems simpler.

class LEDs(threading.Thread):
    def __init__(self, channels, freq, dc=20):
        threading.Thread.__init__(self)
        if not (0.0 < freq) :
          raise Exception('freq should be in Hz (0.0 < freq)')
        if not (0.0 <= dc <= 100.0) :
          raise Exception('dc should be in percentage points (0.0 <= dc <= 100.0)')
        if (int == type(channels)) : self.ALLchannels    = (channels,)
        else : self.ALLchannels = channels
        self.freq  = freq
        self.dc    = dc # duty cycle = percent of time on
        # ont, offt = seconds on and off, these add to freq which is in Hz
        self.ont  = self.freq * self.dc / 100
        self.offt = self.freq - self.ont
        self.stoprequest = threading.Event()
    def run(self):
        self.FLASH = False
        while not self.stoprequest.isSet():
            if self.FLASH :
               for c in self.channels : GPIO.output(c, GPIO.HIGH)
               time.sleep(self.ont)   # ?? non -blocking
               for c in self.channels : GPIO.output(c, GPIO.LOW)
               time.sleep(self.offt)
            else :
               # on and off not affected by loop, only flashing
               time.sleep(0.5)
    def flash(self, channels):
        if (int == type(channels)) : self.channels    = (channels,)
        else : self.channels = channels
        self.FLASH = True
    def on(self, channels):
        if (int == type(channels)) : self.channels    = (channels,)
        else : self.channels = channels
        self.FLASH = False
        for c in self.channels : GPIO.output(c, GPIO.HIGH)
    def ALLchannel(self): return self.ALLchannels
    def channel(self)   : return self.channels
    def frequency(self) : return self.freq
    def DutyCycle(self) : return self.dc
    def ChangeFrequency(self, freq):
        self.freq  = freq
        self.ont  = self.freq * self.dc / 100
        self.offt = self.freq - self.ont
    def ChangeDutyCycle(self, dc):
        self.dc  = dc
        self.ont  = self.freq * self.dc / 100
        self.offt = self.freq - self.ont
    def off(self): 
        self.FLASH = False
        for c in self.ALLchannels : GPIO.output(c, GPIO.LOW)
    def join(self): 
        # join should not be called from outside because not all implementations
	# of the class need threads. Use cleanup() instead.
        self.off()
        self.stoprequest.set()
    def cleanup(self): 
        #  Orange equivalent of ?
        # GPIO.cleanup()  # GPIO.cleanup(RED)   GPIO.cleanup( CHANNELS )
        self.join()

