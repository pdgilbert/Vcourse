# License GPL 2. Copyright Paul D. Gilbert, 2017, 2018
"""Object for distributing and receiving zone infomation to set LEDs.

BT sends RC the cid (cousreID and distritution time) that BT has.
RC replies with  'ok' indicating there is no update,
or 'none' indicating no course set yet, or with an updated zoneObj.
BT confirms receipt of update with BT_ID  

zoneObj and cid should both be valid or both be None. zoneObj should not
have a cid of "none" or None, but transmition requires string "none".

"""


import socket
import logging
import json
import time
import threading
import os  # just for mkdir

import smp

###################################################################
####### this class is used only by BT #######
#######      (see below for RC)       #######
###################################################################

class distributionCheck(threading.Thread):
   """
   Threading object used by BT to check for and load new zone information objects.

   Read config variables  RC_IP, RC_PORT, BT_ID  FLEET from file BTconfig
   in the working directory. 
      IF THE FILE IS NOT AVAILABLE THE PROGRAM WILL FAIL.

   The file is json and can be generated in python by 
      import json
      (edit next line example as required)
      config = {'BT_ID' : 'boat 1', 'FLEET': 'fleet 1', 'RC_IP' : '192.168.1.1', 'RC_PORT' : 9001}
      json.dump(config, open('BTconfig', 'w'))

   The file can also be editted by hand with care to preserve the dict structure.
   """
   
   def __init__(self, update, shutdown):
      threading.Thread.__init__(self)

      config = json.load(open('BTconfig'))   # read config

      self.name='distributionCheck'

      self.FLEET   = config['FLEET']
      self.BT_ID   = config['BT_ID']
      self.RC_IP   = config['RC_IP']
      self.RC_PORT = int(config['RC_PORT'])
      self.update = update
      self.shutdown = shutdown

      self.sleepInterval = 10

      # This loads an active zoneObj if it exists, so gadget is a bit
      # robust to an accidental reboot. (distributionCheck only needs the cid)
      global cid  # see note in BT re zoneSignal and cid
      try :
         with open("activeBTzoneObj.json","r") as f:  zoneObj = json.load(f)
         cid = zoneObj['cid']
      except :
         cid = None

      logging.debug('distributionCheck initialized. cid = ' + str(cid))

   def run(self):
      global cid  # see note in stadiumBT re zoneSignal and cid
      logging.info('distributionCheck started')
      logging.info('   ' + self.BT_ID + ' watching for RC at ' + self.RC_IP + ':' + str(self.RC_PORT))

      while not self.shutdown.is_set():   
          # check RC for update. 
          # Wrapped in try for case when connection fails (wifi out of range).
          #logging.debug('BT check with RC for update.')

          try :
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              s.connect((self.RC_IP, self.RC_PORT))
              
              if cid is None : l = smp.snd(s, self.FLEET + '-none')
              else :           l = smp.snd(s, cid)

              #logging.debug("BT cid " + str(cid))
              
              r = smp.rcv(s) 
              #logging.debug('r ' + str(r))

              if r not in ('ok', 'none') :
                  logging.info('got new zoneObj. Writing to file activeBTzoneObj.json')
                  # note r is just a serialized string (stream) not an object.
                  #logging.debug('r ' + str(r))
                  # Next could be a message to zoneSignal thread, but having a
                  # file means the gadget can recover after reboot without
                  # a connection to RC, so write string r to a file
                  with open("activeBTzoneObj.json","w") as f: f.write(r) 
                  self.update.set()
                  
                  try :
                     with open("activeBTzoneObj.json","r") as f: 
                         cid = (json.load(f))['cid']
                  except :
                     raise RuntimeError("failure setting cid from activeBTzoneObj.json")
                  
                  l = smp.snd(s, self.BT_ID)
                  #logging.debug("sent  receipt BT " + self.BT_ID)

              s.close()

          except :
             #logging.debug('no connection.')
             pass

          time.sleep(self.sleepInterval)

      logging.info('exiting distributionCheck thread.')


###################################################################
####### following classes and variables are used only by RC #######
###################################################################

####### utility ####### 

def VorNone(k, d):
   # return value from a dict d, or None if the key k does not exist.
   if k in d: v = d[k]
   else :     v = None
   return v

#######################

class distributer(threading.Thread):
   """
   Threading object used by RC to listen for BTs checking in.
   
   This thread waits for connections from BTs and pass each to a BThandlerThread.

   It keeps the current zoneObj for each fleet to distribute and should create it
   (BUT currently RCmanager creates zoneObj PROBABLY SHOULD CHANGE THIS).
   It also keeps a quick lists of the cid for those objects.
   It maintains the list BoatList of boats in each fleet.
   It maintains the list distRecvd of boats that have received a distribution.
   RCmanagement.RCmanager uses fleetList, distRecvd and BoatList through a
   distributer (dr) object.

   Config variable RC_IP, RC_PORT are read from file RCconfig in the working 
   directory.  IF THE FILE IS NOT AVAILABLE THE PROGRAM WILL FAIL.
   The file is json and can be generated in python by 
     import json
     (edit next line example as required)
     config = {'RC_IP' : '192.168.1.1', 'RC_PORT' : 9001}
     json.dump(config, open('RCconfig', 'w'))
   The file can also be edited by hand with care to preserve the dict structure.
   """

   def __init__(self, shutdown):
      threading.Thread.__init__(self)

      self.name='distributer'
      self.shutdown=shutdown

      config = json.load(open('RCconfig'))   # read config

      self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.tcpsock.bind((config['RC_IP'], int(config['RC_PORT'])))

      # without timeout the while loop waits indefinitely when no BT connect,
      # so never checks for shutdown.
      self.tcpsock.settimeout(5)
      #logging.debug("Incoming socket timeout " + str(self.tcpsock.gettimeout()))

      #fleets will have a sub-dict for each fleet, eg: 
      #fleets = {'fleetList' : ('FX',), 'FX': {'BoatList':('FX 1',), 'zoneObj':None, 'cid': None, 'distRecvd':('FX 1',)}}
      # RC distribute and status button accesses it through distributer (dr) object.

      try : 
         with open("FleetList.txt") as f:  fleets =  f.read().splitlines()
         fleets = [b.strip() for b in fleets]
         self.fleets = {'fleetList' : fleets}
      except :
         self.fleets = {'fleetList' : ('No fleet',) }

      if not os.path.exists('FLEETS'):  os.makedirs('FLEETS')
      if not os.path.exists('RACEPARMS'):  os.makedirs('RACEPARMS')

      for d in self.fleets['fleetList']:

         if not os.path.exists('FLEETS/' + d):
             os.makedirs('FLEETS/' + d)
         if not os.path.exists('FLEETS/' + d + '/DISTRIBUTEDZONES'):
             os.makedirs('FLEETS/' + d + '/DISTRIBUTEDZONES')


      for d in self.fleets['fleetList']:
         self.fleets.update({d:{'BoatList':(), 'zoneObj':None, 'cid': None, 'distRecvd': None}})
         self.readBoatList(d) 
         self.setdistributionRecvd(d, {})

         #Load active zoneObj's if they exists, to be a bit robust when restarted.
         try :
            with open('FLEETS/' + d + '/activeBTzoneObj.json','r') as f:
                  self.setzoneObj(d, json.load(f))
            logging.info("distributer loaded existing active zoneObj for " + d)
            logging.info("cid is " + self.cid(d))
         except :
            self.setzoneObj(d, None)
            
      logging.info('distributer initialized.')
      logging.debug('    using '+ config['RC_IP'] + ':' + str(config['RC_PORT']))

   def run(self):
      #logging.debug("distributer started.")
      while not  self.shutdown.is_set() :
         try:
            #logging.debug("distributer listening for incoming connections ...")
            self.tcpsock.listen(5)  
            (sock, (ip,port)) = self.tcpsock.accept()
            #next only takes a second, so no need to pass shutdown signal.
            #this only uses fleets (for cid and zoneObj) but self passes access methods
            BThandlerThread(ip, port, sock, self).start()
         except Exception: 
            pass

      logging.info('exiting ' + self.name + ' thread.')
   
   def prt(self):
      print(json.dumps(self.zoneObj, indent=4))
      print('Fleets:')
      print(self.fleetList)
    
   def fleetList(self):
      return self.fleets['fleetList']

   def cid(self, fl):
      return VorNone('cid', self.fleets[fl])

   def setzoneObj(self, fl, zobj):
      self.fleets[fl]['zoneObj'] = zobj
      if zobj is None: self.fleets[fl]['cid'] = None
      else           : self.fleets[fl]['cid']  = zobj['cid']

   def zoneObj(self, fl):
      return VorNone('zoneObj', self.fleets[fl])


   def setdistributionRecvd(self, fl, obj):
      self.fleets[fl]['distRecvd'] = obj

   def updatedistributionRecvd(self, fl, v):
      self.fleets[fl]['distRecvd'].update(v)
      logging.debug('updatedistributionRecvd ' + str(v))

   def distributionRecvd(self, fl):
      return VorNone('distRecvd', self.fleets[fl])
  
   def BoatList(self, fl):
      return VorNone('BoatList', self.fleets[fl])
      
   def readBoatList(self, fl, w=None):
      if w is not None: w.destroy()

      try : 
         with open('FLEETS/' +fl + '/BoatList.txt') as f: bl = f.read().splitlines()
         bl = [b.strip() for b in bl]
      except :
         bl = None   

      logging.debug('BoatList = bl is ' + str(bl))
      self.fleets[fl].update({'BoatList': bl})


   def distribute(self, RC):
      """
        IT might BE BETTER IF THE ARG WAS raceObj and makezoneObj was done
         here or in a stadium module. But probably want raceObj class 
         with methods in stadiumRC first, and stop using globals.

      This works by creating a new version of zoneObj and cid for the fleet. 
      The BThandlerThread compares this cid with that sent by BTs when they connect.
      There is no other "signal" to BThandlerThread or to BTs, 
      it depends on BTs checking in.
      """

      zoneObj = RC.makezoneObj()

      logging.debug('in distributer.distribute(). zoneObj:')
      logging.debug('zoneObj')

      if zoneObj is not None:
          fl = zoneObj['fleet'] 
          self.setzoneObj(fl, zoneObj)  
          self.setdistributionRecvd(fl, {}) # clear dict of boats that have update

          #  distribute is done with zoneObj but write to 
          #  files for restart and for the record.
          with open('FLEETS/' + fl + '/activeBTzoneObj.json', 'w') as f:  
             json.dump(zoneObj, f, indent=4)

          # also write zoneObj to a file, for the record.
          with open('FLEETS/' + fl + '/DISTRIBUTEDZONES/' + zoneObj['cid'] + '.json',"w")  as f:
             json.dump(zoneObj, f, indent=4)
      
      else:
         raise RuntimeError("zoneObj is None. Refusing to distribute.")

class BThandlerThread(threading.Thread):
   """
   Threading object used by RC to handle a BT connection.
   
   Check if BT is current and update with new zoneObj information if not.
   Update global distRecvd when a BT has been updated.
   """
   
# This needs updatedistributionRecvd, cid and zoneObj for each fleet, but
#  passing the whole of  distributer is bigger than needed.

   def __init__(self, ip, port, sock, distributer):
       threading.Thread.__init__(self)
       self.name='BThandler'
       self.ip = ip
       self.port = port
       self.sock = sock
       #self.fleets = fleets
       self.distributer = distributer

   def run(self):        
       #logging.debug('in BThandlerThread.run()')
       #logging.debug(str(self.zoneObj))
       
       #None is not transmitted, so this could be "none", but that should work below
       BTcid = smp.rcv(self.sock)  #zone id that BT has
       #logging.debug(" BTcid " + str(BTcid))
       
       fl = BTcid.split('-')[0]
       #logging.debug(" fl " + str(fl))
       if fl == 'none' : raise RuntimeError('BT fleet is "none".')

       RCcid= self.distributer.cid(fl) #zone id that RC has, possibly None
       
       #logging.debug(" BTcid " + str(BTcid))
       #logging.debug(" RCcid " + str(RCcid))

       if RCcid is None : 
             smp.snd(self.sock, 'none')
             #logging.debug('sent none.')
  
       elif (BTcid == RCcid) :
             smp.snd(self.sock, 'ok')
             #logging.debug('sent ok.')
             
       else :
             #logging.debug('sending new zoneObj to BT')
             smp.snd(self.sock, json.dumps(self.distributer.zoneObj(fl), indent=4))
             logging.debug('new zoneObj sent:')
             bt = smp.rcv(self.sock) 
             logging.debug('  bt:' + str(bt))
             # Possibly need to lock or use semaphore to avoid conflicts?
             self.distributer.updatedistributionRecvd(fl, {bt : time.strftime('%Y-%m-%d %H:%M:%S %Z')})
             logging.debug(' distributionRecvd:' + str(self.distributer.distributionRecvd(fl)))

       self.sock.close()
       #logging.debug('closed socket and exiting thread ' + self.name)

   
   
   
   
   
   
   
 

   
