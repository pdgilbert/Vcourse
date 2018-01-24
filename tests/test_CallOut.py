# need 
#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_CallOut

import unittest
import time

from CallOut import CallOut

# This needs a (sim) BT to respond

class TestCallOutMethods(unittest.TestCase):

   #def setUp(self):
   #    self.pt = gpsPos(45.395676, -75.676829)

   #def setUp(self):
   #    self.widget = Widget('The widget')
   #
   #def tearDown(self):
   #    self.widget.dispose()


   def test_CallOut_flash(self):

 
      self.assertIsNone(CallOut("BT-1",  "flash"),
                   msg="CallOut 'flash' to hostname should return None.")  
 
      self.assertIsNone(CallOut("boat 1,FX",  "flash"),
                   msg="CallOut 'flash' to bt,fl should return None.")  
 
      self.assertIsNone(CallOut("all",  "flash"),
                   msg="CallOut 'flash' to all should return None.")  

      self.assertIsNone(CallOut("noGizmo",  "flash"),
                    msg="CallOut 'flash' should return None even when gizmo does not respond.")  
  

   def test_CallOut_misc(self):

      self.assertIsNone(CallOut("all",  "checkout"),
                   msg="CallOut 'checkout' to all should return None.")  

      self.assertIsNone(CallOut("all",  "checkin"),
                   msg="CallOut 'checkin' to all should return None.")  

      # NOTE THIS WILL CHANGE VALUE FOR ANY RUNNING BT
      v = {"RC_IP": "10.42.0.254", "RC_PORT": "9001"}
      self.assertIsNone(CallOut("all",  "setRC", conf=v),
                   msg="CallOut 'setRC' to all should return None.")  

      # NOTE THIS WILL CHANGE VALUE FOR ANY RUNNING BT
      v = {"REG_IP": "10.42.0.254", "REG_PORT": "9006"}
      self.assertIsNone(CallOut("all",  "setREG"),
                   msg="CallOut 'setREG' to all should return None.")  
 

   def test_CallOut_ReportBTconfig(self):

      self.assertIsNone(CallOut("noGizmo",  "report config")['hn'],
                   msg="CallOut 'report config' should return hn None when there is no response.")  

      # These tests needs BT-1 running CallOutRespond

      origBTconfig = CallOut("BT-1",  "report config")

      self.assertIsNotNone(origBTconfig['hn'],
                   msg="CallOut 'report config' no response from BT-1. Following tests will fail.")  

      # NOTE THIS IS USING "boat 1b" and "fleet 2"
      v = {"BT_ID": "boat 1b", "FLEET": "fleet 2", "RC_IP": "10.42.0.254", "RC_PORT": "9001", "hn": "BT-1"}

      btfl = origBTconfig["BT_ID"] + ',' + origBTconfig["FLEET"]

      self.assertEqual(origBTconfig, CallOut(btfl,  "report config"),
                   msg="CallOut 'report config' should return BTconfig dict." +\
                       "Possibly CallOutRespond is crashed on BT-1.")  



   def test_CallOut_requestBTconfig(self):

      v = {"BT_ID": "noGizmo2"}

      self.assertIsNone(CallOut("noGizmo",  "requestBTconfig", conf=v)['hn'],
                   msg="CallOut 'requestBTconfig' should return hn None when there is no response.")  

      # These tests needs BT-1 running CallOutRespond

      orig = CallOut("BT-1",  "report config")

      self.assertIsNotNone(orig['hn'],
                   msg="CallOut 'report config' no response from BT-1. Following tests will fail.")  


      v = orig
      v.update({"BT_ID": "newBoat"})
      new = CallOut("BT-1",  "requestBTconfig", conf=v)

      self.assertIsNotNone(new['hn'], msg="CallOut 'requestBTconfig' no response from BT-1."+\
                       "Error in BT_ID change test. Possibly CallOutRespond is crashed on BT-1.")  

      self.assertEqual(v, new,
                   msg="CallOut 'requestBTconfig' should return new BTconfig with BT_ID change."+\
                       "Error in BT_ID change test. Possibly CallOutRespond is crashed on BT-1.")
      

      time.sleep(5) # restart of BT after config change seems to interfere with UPD reception.
      v.update({"FLEET": "fleet 2"})
      new = CallOut("BT-1",  "requestBTconfig", conf=v)

      self.assertIsNotNone(new['hn'], msg="CallOut 'requestBTconfig' no response from BT-1."+\
                                          "Error in FLEET change test.")  

      self.assertEqual(v, new,
                   msg="CallOut 'requestBTconfig' should return new BTconfig with FLEET change."+\
                       "Error in FLEET change test. Possibly CallOutRespond is crashed on BT-1.")
      


      time.sleep(5) # restart of BT after config change seems to interfere with UPD reception.
      new = CallOut("BT-1",  "requestBTconfig", conf=orig)

      self.assertIsNotNone(new['hn'], msg="CallOut 'requestBTconfig' no response from BT-1."+\
                                          "Error resetting back to original.")  

      self.assertEqual(orig, new,
                   msg="CallOut 'requestBTconfig' should return new BTconfig set back to original."+\
                       "Error resetting. Possibly CallOutRespond is crashed on BT-1.")


