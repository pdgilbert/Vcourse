# need 
#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_RegUtils

import unittest
import os

from RegUtils import *

# initiate variables and file directories

#NB Registration files are in tmp/ but actual changes are made on BT-1 gizmo
# which can get it out of sync with Registration  Boatlist files, etc.

tmp = '/tmp/Vcourse/'

g = tmp + 'gizmoList.txt'
if os.path.exists(g): os.remove(g)

g = tmp + 'unassignedGizmos.txt'
if os.path.exists(g): os.remove(g)

if not os.path.exists(tmp):  os.makedirs(tmp)

fleets = {
   "49er"   : {"RC_PORT": "9001", "RC_IP": "10.42.0.254"}, 
   "FX"     : {"RC_PORT": "9001", "RC_IP": "10.42.0.254"} }

with open(tmp + 'FleetListRC.json','w') as f: json.dump(fleets, f, indent=4)

z = initiate(path=tmp)
z['gizmoList'].append('BT-1')
z['unassignedGizmos'].append('BT-1')


class TestRegUtilstMethods(unittest.TestCase):

   #def setUp(self):
   #    self.widget = Widget('The widget')
   #
   #def tearDown(self):
   #    self.widget.dispose()

   #def tearDown(self):
   #  os.rmdir(tmp)

   def setUp(self):
      z = initiate(path=tmp)
      self.fleets    = z['fleets']
      self.fleetList = z['fleetList']
      self.gizmoList = z['gizmoList']
      self.unassignedGizmos = z['unassignedGizmos']


   def test_setup(self):
      self.assertEqual(["49er", "FX"], self.fleetList,  msg='fleetList should be ["49er", "FX"].')  
      self.assertEqual(['BT-1'], self.gizmoList.values,  msg='gizmoList should be ["BT-1"].')  
      self.assertEqual(['BT-1'], self.unassignedGizmos.values,  msg='unassignedGizmos should be ["BT-1"].')  


   def test_syncdList(self):
  
      # syncdList is suppose to be unique, so re-adding should not change value
      z = 'BT-1'
      self.gizmoList.append(z)
      self.unassignedGizmos.append(z)
      self.assertEqual([z], self.gizmoList.values,         msg="gizmoList should be ['BT-1'].")  
      self.assertEqual([z], self.unassignedGizmos.values,  msg="unassignedGizmos should be [('BT-1'].")  

      self.gizmoList.append('BT-2')
      self.unassignedGizmos.append('BT-2')
      self.assertEqual(['BT-1', 'BT-2'], self.gizmoList.values,        msg="gizmoList should be ['BT-1', 'BT-2'].")  
      self.assertEqual(['BT-1', 'BT-2'], self.unassignedGizmos.values, msg="unassignedGizmos should be ['BT-1', 'BT-2'].")  

      self.unassignedGizmos.remove('BT-2')
      self.assertEqual(['BT-1'], self.unassignedGizmos.values, msg="unassignedGizmos should be ['BT-1'].")  


   def test_utilities(self):
      #NB Registration files are in tmp/ but actual changes are made on BT-1 gizmo
      w = tkinter.Tk()
      z = RegistrationGUI(w)
      fleetChoice      = z['fleetChoice']
      sailNumberChoice = z['sailNumberChoice']
      status           = z['status']

      newBoatSetup('100', 'FX', 'BT-1', t=None)
      self.assertEqual(['100',], BoatList('FX'),      msg=" BoatList should be ['100'].")  
      self.assertEqual('100', sailNumberChoice.get(), msg=" GUI Sail #  should be '100'.")  
      self.assertEqual('FX',   fleetChoice.get(),     msg=" GUI Fleet   should be 'FX'.")  
      
      chgSail('101', t=None)
      self.assertEqual(['101',], BoatList('FX'),  msg=" BoatList should be ['101'].")  
      
      chgFleet('49er', t=None)
      self.assertEqual([],       BoatList('FX'),   msg=" BoatList should be [].")  
      self.assertEqual(['101',], BoatList('49er'), msg=" BoatList should be ['101'].")  

      checkOut()
      self.assertEqual(['101',], checkedOut('49er'), msg=" checkedOut should be ['101'].")
      statusSet()
      self.assertEqual('Out', status.get(), msg=" status should be 'Out'.")

      checkIn()
      self.assertEqual([], checkedOut('49er'), msg=" checkedOut should be [].")
      statusSet()
      self.assertEqual('In', status.get(), msg=" status should be 'In'.")

      #try :
      #   with open('BoatHostMap.json') as f:  fleets['BoatHostMap'] = json.load(f)
      #except :
      #   fleets['BoatHostMap'] = {}


#  bl = syncdList('FLEETS/' +fl + '/BoatList.txt') 
#  fleets[fl]['BoatList'] = bl
#  fleets[fl]['BoatList'].values
#  fleets[fl]['BoatList'].append('boat 100')
#  fleets[fl]['BoatList'].remove('boat 100')
 
### ALSO CHECK setRC, set... , chg...
