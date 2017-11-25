# License GPL 2. Copyright Paul D. Gilbert, 2017

# BT sends RC the cid (cousreID and distritution time) BT has.
# RC replies with  'ok' indicating there is no update,
#     or 'none' indicating no course set yet, or with updated zoneObj.
# BT confirms receipt of update with BT_ID  

# zoneObj and cid should both be valid or both be None. cid should not be "none"
# nor should zoneObj  have a cid of "none" or None.
# But transmition requires string "none".

import socket
import logging
import json
import time
import threading

import smp

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

####### this class is used only by BT #######

class distributionCheck(threading.Thread):
   # this thread class is used by BT
  
   def __init__(self, RC_IP, RC_PORT, BT_ID, update, shutdown):
      threading.Thread.__init__(self)
      #RC_IP, RC_PORT could be read here from config rather than passed
      self.name='distributionCheck'

      self.RC_IP   = RC_IP
      self.RC_PORT = RC_PORT
      self.BT_ID   = BT_ID
      self.update = update
      self.shutdown = shutdown

      self.sleepInterval = 10

      #THIS WOULD BE CLEANER IF JSON ALWAYS HAD 'none' rather than None
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
      logging.info('distributionCheck starting')
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

class distributer(threading.Thread):
   # Wait for connections from BTs and pass each to a BThandlerThread.
   # Maintain zoneObj.
   # Maintain list distRecvd of boats that have received a distribution.
   
   #RC_IP, RC_PORT could be read here from config rather than passed
   def __init__(self, RC_IP, RC_PORT, shutdown):
      threading.Thread.__init__(self)

      self.name='distributer'
      logging.info('distributer starting. Using RC_IP ' + str(RC_IP) + ':' +str(RC_PORT))
      
      self.shutdown=shutdown
      self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.tcpsock.bind((RC_IP, RC_PORT))
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
   # handle a connection from a BT. Check if BT is current and update if not.

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

       #course id that RC has
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

   
   
   
   
   
   
   
 

   
