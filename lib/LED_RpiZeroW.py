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
CHANNELS = (RED, GREEN, BLUE)


GPIO.setmode(GPIO.BOARD) # use board pin numbers not broadcom GPIO.setmode(GPIO.BCM)
#NB. BCM 18 = pin 12
#    BCM 24 = pin 18
# https://pinout.xyz/pinout/io_pi_zero#
 
GPIO.setwarnings(True) # for warnings in the case something else may be using pins?

GPIO.setup(CHANNELS, GPIO.OUT)   # set CHANNELS pins as an output

GPIO.output(CHANNELS, GPIO.LOW)  # initially set all off


#Raspberry pi has pulse width modulation (PWM) on all pins so a thread
#  is not needed for flashing leds.

#red = GPIO.PWM(RED, SLOW) #  (channel, frequency)
#red.ChangeFrequency(2)    # where freq is the new frequency in Hz
#red.ChangeDutyCycle(0.5)  # where 0.0 <= dc <= 100.0 is duty cycle (percent time on)
#red.ChangeDutyCycle(20)

#red.start(99)            # arg is duty cycle. 99=mostly on
#red.ChangeDutyCycle(99)
#red.ChangeFrequency(0.1)  


class LEDs():
    def __init__(self, channels, freq, dc=20):
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
    def start(self):
        #do nothing, but so it can be called for compatability
        time.sleep(0.1)
    def flash(self, channels):
        if (int == type(channels)) : self.channels    = (channels,)
        else : self.channels = channels
        for c in self.channels : 
           l = GPIO.PWM(c, self.freq) #  (channel, frequency)
           l.ChangeFrequency(self.freq)   
           l.ChangeDutyCycle(self.dc)  
    def on(self, channels):
        if (int == type(channels)) : self.channels    = (channels,)
        else : self.channels = channels
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
        GPIO.output(CHANNELS, GPIO.LOW)
        #shutoff can be a bit slow and happen after next on signal, so
        time.sleep(0.5)
    def cleanup(self): 
        GPIO.cleanup()  #  GPIO.cleanup( CHANNELS )

