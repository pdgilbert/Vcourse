# License GPL 2. Copyright Paul D. Gilbert, 2017

# simulate LED signal hardware by simple print statements

import time
import logging
import threading

RED    =  12
GREEN  =  16
BLUE   =  18  

# Raspberry Pi has PWM hardware. This simulation code follows 
# Orange Pi more closely, and spawns process mainly to handle flashing.

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
               for c in self.channels : print(str(c) + ' flash.')
               time.sleep(self.ont)   # ?? non -blocking
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
        for c in self.channels : print(str(c) + ' on.')
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
        for c in self.ALLchannels : print(str(c) + ' off.')
    def join(self):  
        # join should not be called from outside because not all implementations
        # of the class need threads. Use cleanup() instead.
        self.off()
        self.stoprequest.set()
    def cleanup(self): 
        print('cleanup for shutdown ')
        self.join()

