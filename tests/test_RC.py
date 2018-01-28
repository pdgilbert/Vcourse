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
 

   def test_calc(self):

      self.RC.fleetChoice.set('FX')

      z = {'ty': 'stadium', 'fl': 'FX', 'dc': 'street test', 
           'RC.lat': 45.3954, 'RC.lon': -75.67691667,
           'M.lat': 0.0,       'M.lon': 0.0, 
           'S.lat': 0.0,       'S.lon': 0.0, 
           'ax': 59.10105607341163, 'cc': 10.0, 'cl': 0.14092733569247978,
           'll': 30.0, 'sw': 200.0, 'tt': 0.0, 'wn': 10.0}

      self.RC.setparms(z)

      self.assertEqual(z, self.RC.parmsAll(), msg="parmsAll should be "+ str(z))  

      z = ['stadium', 'FX', 'street test',
           45.3954,           -75.67691667,
           0.0,        0.0,
           0.0,        0.0,
           0.14092733569247978, 59.10105607341163, 30.0,  0.0] 

      self.assertEqual(tuple(z), self.RC.parmsTuple(),  msg="parmsTuple should be "+ str(z))  
      
      self.RC.calcA() # uses axis and RC position to calculate S and M
      z[5] =  45.39551583077365
      z[6] = -75.6770153874306 
      z[7] =  45.39672199363244
      z[8] = -75.67414525015809
      self.assertEqual(tuple(z), self.RC.parmsTuple(),  msg="2parmsTuple should be "+ str(z))  

      self.RC.calcM() # uses RC and M positions to calculate cl, S, 
      z[5] =  45.39551583083625
      z[6] = -75.67701538728161
      z[9] =   0.1411600911528002
      z[10]=  59.10110782287024
      self.assertEqual(tuple(z), self.RC.parmsTuple(),  msg="3parmsTuple should be "+ str(z))  

      self.RC.calcS() # uses S and M positions to calculate cl, ax, RC 
      z[3] =  45.39540000006261
      z[4] = -75.67691666964866
      z[9] =   0.1409273283772988
      z[10]=  59.10105607332508
      self.assertEqual(tuple(z), self.RC.parmsTuple(),  msg="4parmsTuple should be "+ str(z))  

   def test_distribute(self):

      self.RC.fleetChoice.set('FX')
      
      self.RC.readRace(fleet='FX', filename ='./RACEPARMS/street0.raceParms')

      # distribute_button does dr.distribute(self.parmsAll(), self.ZTobj)
      self.RC.distribute_button.invoke() 
