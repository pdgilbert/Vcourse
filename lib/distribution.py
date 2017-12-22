# License GPL 2. Copyright Paul D. Gilbert, 2017
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

import smp

####### this class is used only by BT #######

# Read config variable RC_IP, RC_PORT, BT_ID  from file BTconfig
# in the working directory. 
#    IF THE FILE IS NOT AVAILABLE THE PROGRAM WILL FAIL.
#The file is json and can be generated in python by 
# import json
#  (edit next line example as required)
# config = {'BT_ID' : 'boat 1', 'RC_IP' : '192.168.1.1', 'RC_PORT' : 9001}
# json.dump(config, open('BTconfig', 'w'))
# The file can also be editted by hand with care to preserve the dict structure.

class distributionCheck(threading.Thread):
   """Threading object used by BT to check for and load new zone information objects."""
   
   def __init__(self, update, shutdown):
      threading.Thread.__init__(self)

      config = json.load(open('BTconfig'))   # read config

      self.name='distributionCheck'

      self.BT_ID   = config['BT_ID']
      self.RC_IP   = config['RC_IP']
      self.RC_PORT = int(config['RC_PORT'])
      self.update = update
      self.shutdown = shutdown

      self.sleepInterval = 10

      # This loads an active zoneObj if it exists, so gadget is a bit
      # robust to an accidental reboot. (distributionCheck only needs the cid)
      global cid  # see note in stadiumBT re zoneSignal and cid
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
              
              if cid is None : l = smp.snd(s, 'none')
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


####### following classes and variables are used only by RC #######

# Having distRecvd global to the module is so that BThandler 
# threads can append to it, and distributer thread can clear it,
# and status button can access it.

distRecvd = {}

# Read config variable RC_IP, RC_PORT  from file RCconfig
# in the working directory. 
#    IF THE FILE IS NOT AVAILABLE THE PROGRAM WILL FAIL.
#The file is json and can be generated in python by 
# import json
#  (edit next line example as required)
# config = {'RC_IP' : '192.168.1.1', 'RC_PORT' : 9001}
# json.dump(config, open('RCconfig', 'w'))
# The file can also be editted by hand with care to preserve the dict structure.

class distributer(threading.Thread):
   """
   Threading object used by RC to listen for BTs checking in.
   
   This thread waits for connections from BTs and pass each to a BThandlerThread.
   It keeps the current zoneObj to distribute.
   It maintains the list distRecvd of boats that have received a distribution.
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

      # This loads an active zoneObj if it exists, to be a bit
      # robust when restarted
      global cid  # see note in stadiumBT re zoneSignal and cid
      try :
         with open("activeBTzoneObj.json","r") as f:  self.zoneObj = json.load(f)
         cid = self.zoneObj['cid']
         logging.info("distributer loaded existing active zoneObj.")
      except :
         self.zoneObj = None
         cid =  None
      
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
            BThandlerThread(ip, port, sock, self.zoneObj).start()
         except Exception: 
            pass

      logging.info('exiting ' + self.name + ' thread.')
   
   def prt(self):
      print(json.dumps(self.zoneObj, indent=4))
      print('Received by:')
      global distRecvd
      print(distRecvd)
  
   def distributionRecvd(self):
      global distRecvd
      return distRecvd
      
   def distribute(self, zoneObj):
      #  IT might BE BETTER IF THE ARG WAS raceObj and makezoneObj was done
      #    here or in a stadium module. But probably want raceObj class 
      #    with methods in stadiumRC first, and stop using globals.

      # This works by creating a new version of zoneObj, the BThandlerThread
      # compares the cid of this with that sent by BTs when they connect.
      # There is no other "signal" to BThandlerThread or to BTs. 
      # It depends on BTs checking in.
      #logging.debug('in distributer.distribute(), zoneObj:')
      #logging.debug(str(zoneObj))

      if zoneObj is not None:
          self.zoneObj = zoneObj   
          global distRecvd
          distRecvd = {}    # clear dict of boats that have update

          #  distribute is done with zoneObj but ...
                   
          # but write zoneObj to activeBTzoneObj.json file for load on restart
          with open("activeBTzoneObj.json","w") as f:  
             json.dump(self.zoneObj, f, indent=4)

          # also write zoneObj to a file, for the record.
          with open('distributedzoneObj/' + self.zoneObj['cid'] + '.json',"w")  as f:
             json.dump(self.zoneObj, f, indent=4)

          # consider also writing race obj here, for debug and/or reload
      
      else:
         raise RuntimeError("zoneObj is None. Refusing to distribute.")

class BThandlerThread(threading.Thread):
   """
   Threading object used by RC to handle a BT connection.
   
   Check if BT is current and update with new zoneObj information if not.
   Update global distRecvd when a BT has been updated.
   """

   def __init__(self, ip, port, sock, zoneObj):
       threading.Thread.__init__(self)
       self.name='BThandler'
       self.ip = ip
       self.port = port
       self.sock = sock
       self.zoneObj = zoneObj
   def run(self):        
       #logging.debug('in BThandlerThread.run()')
       #logging.debug(str(self.zoneObj))

       #course (zone) id that RC has
       if self.zoneObj is None :
                RCcid = None
       else :   RCcid = self.zoneObj['cid']

       #  eventually remove this check for empty cid
       if RCcid is None: 
          raise Exception('BThandlerThread intercepted old RCcid is None')
       
       #None is not transmitted, so this could be "none", but that should work below
       BTcid = smp.rcv(self.sock)  #course id that BT has
       
       #logging.debug(" BTcid " + str(BTcid))
       #logging.debug(" RCcid " + str(RCcid))

       if self.zoneObj is None : 
             smp.snd(self.sock, 'none')
             #logging.debug('sent none.')
             if RCcid is not None :
                raise Exception('something is wrong. zoneObj is None and RCcid is not.')
  
       # this should be redundant, if zoneObj is None then cid should be too.
       elif RCcid is None :
             smp.snd(self.sock, 'none') # note this is not {"cid": "none"}

       elif (BTcid == RCcid) :
             smp.snd(self.sock, 'ok')
             #logging.debug('sent ok.')
             
       else :
             #logging.debug('sending new zoneObj to BT')
             smp.snd(self.sock, json.dumps(self.zoneObj, indent=4))
             #logging.debug('new zoneObj sent:')
             bt = smp.rcv(self.sock) 
             # This uses module global variable since distributer() needs
             # to write (clear) it and it needs to persist after this thread.
             # Possibly need to lock or use semaphore to avoid conflicts?
             global distRecvd
             distRecvd.update({bt : time.strftime('%Y-%m-%d %H:%M:%S %Z')})

       self.sock.close()
       #logging.debug('closed socket and exiting thread ' + self.name)

   
   
   
   
   
   
   
 

   
