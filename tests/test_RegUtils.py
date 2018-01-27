# need 
#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_RegUtils
#python3   tests/test_RegUtils.py

import unittest
import os
import time
import shutil

from RegUtils import *

# initiate variables and file directories

#NB Registration files are in tmp/ but actual changes are made on BT-1 gizmo
# which can get it out of sync with Registration  Boatlist files, etc.

tmp = '/tmp/Vcourse/'
if os.path.exists(tmp) : shutil.rmtree(tmp) #cleanup from previous run !!!
os.makedirs(tmp)


# Following is a one-time initialization used for all tests.
 
fleets = {
   "49er"   : {"RC_PORT": "9001", "RC_IP": "10.42.0.254"}, 
   "FX"     : {"RC_PORT": "9001", "RC_IP": "10.42.0.254"} }

with open(tmp + 'FleetListRC.json','w') as f: json.dump(fleets, f, indent=4)

z = initiate(path=tmp)
fleets    = z['fleets']
fleetList = z['fleetList']

gizmoList = z['gizmoList']
gizmoList.append('BT-1')

unassignedGizmos = z['unassignedGizmos']
unassignedGizmos.append('BT-1')

# need to first set BTconfig on BT-1 (manually) to
# {"RC_PORT": "9001", "BT_ID": "unassigned", "FLEET": "", "RC_IP": "10.42.0.254"}
# or maybe 
# {"RC_PORT": "9001", "BT_ID": "100", "FLEET": "FX", "RC_IP": "10.42.0.254"}
# also works?
# and start CallOutRespond on BT-1

class TestRegUtilstMethods(unittest.TestCase):

   #def setUp(self):
   #    self.widget = Widget('The widget')
   #
   
   #def tearDown(self):
   #   print('end tearDown()')

   #def tearDown(self):
   #  os.rmdir(tmp)

   #def setUp(self):
   #   print('end setup()')


   def test_setup(self):
      self.assertEqual(["49er", "FX"], fleetList,  msg='fleetList should be ["49er", "FX"].')  
      self.assertEqual(['BT-1'], gizmoList.values,  msg='gizmoList should be ["BT-1"].')  
      self.assertEqual(['BT-1'], unassignedGizmos.values,  msg='unassignedGizmos should be ["BT-1"].')  

   def test_syncdList(self):
  
      # syncdList is suppose to be unique, so re-adding should not change value
      z = 'BT-1'
      gizmoList.append(z)
      unassignedGizmos.append(z)
      self.assertEqual([z], gizmoList.values,         msg="gizmoList should be ['BT-1'].")  
      self.assertEqual([z], unassignedGizmos.values,  msg="unassignedGizmos should be [('BT-1'].")  

      gizmoList.append('BT-2')
      unassignedGizmos.append('BT-2')
      self.assertEqual(['BT-1', 'BT-2'], gizmoList.values,        msg="gizmoList should be ['BT-1', 'BT-2'].")  
      self.assertEqual(['BT-1', 'BT-2'], unassignedGizmos.values, msg="unassignedGizmos should be ['BT-1', 'BT-2'].")  

      unassignedGizmos.remove('BT-2')
      self.assertEqual(['BT-1'], unassignedGizmos.values, msg="unassignedGizmos should be ['BT-1'].")  

   def test_gizmo(self):
      w = tkinter.Tk()
      z = RegistrationGUI(w)
      fleetChoice      = z['fleetChoice']
      sailNumberChoice = z['sailNumberChoice']

      z = callForGizmo('BT-1', t=None)
      self.assertEqual('BT-1', z['hn'],
        msg="callForGizmo should have hn ='BT-1'\n"+\
            "Did BT-1 LED flash green?   If not:\n" +\
            "Check wifi connection from Registration to BT-1.\n" +\
            "Check CallOutRespond is running on BT-1 and has 'unassigned' configuration.")  

   def test_utilities(self):
      #NB Registration files are in tmp/ but actual changes are made on BT-1 gizmo
      w = tkinter.Tk()
      z = RegistrationGUI(w)
      fleetChoice      = z['fleetChoice']
      sailNumberChoice = z['sailNumberChoice']
      status           = z['status']

      newBoatSetup('100', 'FX', 'BT-1', t=None)
      self.assertEqual(['100',], BoatList('FX'),      msg=" BoatList should be ['100'].\n"+\
        "Did BT-1 LED flash green?   If not:\n" +\
        "Check wifi connection from Registration to BT-1.\n" +\
        "Check CallOutRespond is running on BT-1 and has 'unassigned' configuration.")  

      self.assertEqual('100', sailNumberChoice.get(), msg=" GUI Sail #  should be '100'.")  
      self.assertEqual('FX',   fleetChoice.get(),     msg=" GUI Fleet   should be 'FX'.")  
      
      # when this is too quick there is a TCP connection refused problem
      time.sleep(5)
      
      chgSail('101', t=None)
      self.assertEqual(['101',], BoatList('FX'),  msg=" BoatList should be ['101'].")  
      
      time.sleep(5)

      chgFleet('49er', t=None)
      self.assertEqual([],       BoatList('FX'),   msg=" BoatList should be [].")  
      self.assertEqual(['101',], BoatList('49er'), msg=" BoatList should be ['101'].")  
      
      time.sleep(5)

      #  these tests are not working. 
      #  file /tmp/Vcourse/FLEETS/49er/checkedOut.txt  not written either.
      checkOut()
      self.assertEqual(['101',], fleets['49er']['checkedOut'].values, 
                                                     msg=" checkedOut value should be ['101'].")
      self.assertEqual(['101',], checkedOut('49er'), msg=" checkedOut() give ['101'].")

      statusSet()
      self.assertEqual('Out', status.get(), msg=" status should be 'Out'.")
    
      time.sleep(5)

      checkIn()
      self.assertEqual([], checkedOut('49er'), msg=" checkedOut should be [].")

      statusSet()
      self.assertEqual('In ', status.get(), msg=" status should be 'In'.")

      z = fleets['BoatHostMap']
      self.assertEqual({'BT-1': '101'}, z, msg=" 'BoatHostMap' should be {'BT-1': '101'}.")
      
      time.sleep(5)
      
      # this should reset BT-1 to 'unassigned' if no test fails and it gets here
      # NOT CERTAIN TESTS ARE RUN IN ORDER
      rmBoat('101', '49er', t=None)
      

### ALSO CHECK setRC, setREG ...

if __name__ == '__main__':

    unittest.main()

