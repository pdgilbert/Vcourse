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
   
   def __init__(self, update, shutdown, path='./'):
      threading.Thread.__init__(self)

      config = json.load(open(path + 'BTconfig'))   # read config

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
         with open(path + "activeBTzoneObj.json","r") as f:  zoneObj = json.load(f)
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

              if r in ('error') :
                  logging.info('cid / fleet error')
                  l = smp.snd(s, self.BT_ID)
                  raise RuntimeError("failure. RC not recognizing cid / fleet.")
              
              elif r not in ('ok', 'none') :
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

   def __init__(self, shutdown, path='./'):
      threading.Thread.__init__(self)

      self.name='distributer'
      self.shutdown=shutdown

      with open(path + 'RCconfig') as f: config = json.load(f)   # read config

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
         with open(path + "FleetList.txt") as f:  fleets =  f.read().splitlines()
         fleets = [b.strip() for b in fleets]
         self.fleets = {'fleetList' : fleets}
      except :
         self.fleets = {'fleetList' : ('No fleet',) }

      if not os.path.exists(path + 'FLEETS'):  os.makedirs(path + 'FLEETS')
      if not os.path.exists(path + 'RACEPARMS'):  os.makedirs(path + 'RACEPARMS')

      for d in self.fleets['fleetList']:

         if not os.path.exists(path + 'FLEETS/' + d):
             os.makedirs(path + 'FLEETS/' + d)
         if not os.path.exists(path + 'FLEETS/' + d + '/DISTRIBUTEDZONES'):
             os.makedirs(path + 'FLEETS/' + d + '/DISTRIBUTEDZONES')


      for d in self.fleets['fleetList']:
         self.fleets.update({d:{'BoatList':(), 'zoneObj':None, 'cid': None, 'distRecvd': None}})
         self.readBoatList(d) 
         self.setdistributionRecvd(d, {})

         #Load active zoneObj's if they exists, to be a bit robust when restarted.
         try :
            with open(path + 'FLEETS/' + d + '/activeBTzoneObj.json','r') as f:
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
            BThandlerThread(sock, self).start()
         except Exception: 
            pass

      self.tcpsock.close()
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


   def makezoneObj(self, parms, ZTobj):
      """
      Generate the zoneObj for distribution to boats for calculating LED signals.
      
      Part of the final zoneObj passed to boats is calculated by RCmanager.makezoneObj()
      and part by ZTobj.makezoneObj().
      """ 
      #parms = self.parmsAll()
      #ZTobj = self.ZTobj

      if parms['fl']  not in self.fleetList() :
         raise Exception('Attempting to distribute to non-existing fleet.\nFirst select fleet.')
         #tkWarning("Attempting to distribute to non-existing fleet.\nFirst select fleet.")
         return None

      ax = parms['ax']

      # Ensure parameters  correspond to current screen values.
      # readRCWindow() # this shoud be automatic and not needed !!!

      # y = a + b * x
      # b = (y_1 - y_2) / (x_1 - x_2)
      # a = y_1 - b * x_1
      
      # 0 or 180 axis would give infinite slope is x is longitude, 
      # so depending on the axis treat domain as longitude (dom=True)
      # or treat domain as latitude (dom=False)
      if        45 <= ax <= 135 : dom = True
      elif     225 <= ax <= 315 : dom = True
      else                               : dom = False

      if dom :
         if   45 <= ax <= 135  : LtoR = False
         else                       : LtoR = True  # 225 <= ax <= 315 
      else :
         if   135 <= ax <= 225 : LtoR = False 
         else                       : LtoR = True #(315 <= ax <= 360) | (0 <= ax <= 45)

      
      distributionTime = time.strftime('%Y-%m-%d_%H:%M:%S_%Z')

      # left and right looking up the course, from race committee (RC) to windward mark (M)

      rRC = parms
      rRC.update({
         'cid'       : parms['fl'] + '-' + parms['dc'] + '-' +  distributionTime,
         'courseDesc'       : parms['dc'],
         'zoneType'         : parms['ty'],
         'fleet'            : parms['fl'],
         'distributionTime' : distributionTime,
         'axis'   :  ax,  # axis (degrees)
         'dom'    :  dom, # domain, function of long (true) or latitude (False)
         'LtoR'   :  LtoR, # True if bounds increase left to right
         })

      r = ZTobj.makezoneObj(rRC)  # this adds zone specific parts and returns complete r


      if not ZTobj.verifyzoneObj(r) :
         raise Exception('error verifying zoneObj.')
         return None
      else :
         return r



   def distribute(self, parms, ZTobj):
      """
        IT might BE BETTER IF THE ARG WAS raceObj and makezoneObj was done
         here or in a stadium module. But probably want raceObj class 
         with methods in stadiumRC first, and stop using globals.

      This works by creating a new version of zoneObj and cid for the fleet. 
      The BThandlerThread compares this cid with that sent by BTs when they connect.
      There is no other "signal" to BThandlerThread or to BTs, 
      it depends on BTs checking in.
      """

      zoneObj = self.makezoneObj(parms, ZTobj)

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

   def __init__(self, sock, distributer):
       threading.Thread.__init__(self)
       self.name='BThandler'
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
       if  fl  not in self.distributer.fleetList() :
          smp.snd(self.sock, 'error')
          bt = smp.rcv(self.sock) 
          raise RuntimeError('BT ' + str(bt) + ' fleet is ' + str(fl))
       
       
       #if fl == 'none' : raise RuntimeError('BT fleet is "none".')

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

   
   
   
   
   
   
   
 

   
