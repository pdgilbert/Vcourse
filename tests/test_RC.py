# need 
#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_RC

import unittest
import time
import threading
#import signal
import tkinter

import distribution
import RCmanagement

# This needs a (sim) BT-1 to respond

class TestRCMethods(unittest.TestCase):

   def setUp(self):
      self.shutdown = threading.Event()
      
      dr = distribution.distributer(self.shutdown)
      dr.start() 
      
      race = tkinter.Tk()
      RCmanagement.initiate() #THIS NEEDS PATH TO CONFIG FILES IF NOT CWD
      self.RC = RCmanagement.RCmanager(race, dr)

      #    self.widget = Widget('The widget')
      #
      
   def tearDown(self):
      self.shutdown.set()  # to exit threads
      time.sleep(5)   # wait as long as socket timeout in distributionHandler
      
      #    self.widget.dispose()


   def test_RC(self):

      self.RC.fleetChoice.set('FX')
      
      self.assertEqual('FX', self.RC.fleetChoice.get(),
                   msg="fleetChoice.get() should return FX'.")  
 
  

   def test_distribute(self):

      self.RC.fleetChoice.set('FX')
      
      self.assertEqual('FX', self.RC.fleetChoice.get(),
                   msg="fleetChoice.get() should return FX'.")  

      self.RC.readRace(fleet='FX', filename ='./RACEPARMS/street0.raceParms')

      # distribute_button does dr.distribute(self.parmsAll(), self.ZTobj)
      self.RC.distribute_button.invoke() 
