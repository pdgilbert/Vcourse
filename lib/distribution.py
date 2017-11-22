# License GPL 2. Copyright Paul D. Gilbert, 2017

# BT sends RC the cid (cousreID and distritution time) BT has.
# RC replies with  'ok' indicating there is no update,
#     or 'none' indicating no course set yet, or with updated zoneObj.
# BT confirms receipt of update with BT_ID  

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

      self.sleepInterval = 5

      #THIS WOULD BE CLEANER IF JSON ALWAYS HAD 'none' rather than None
      # This loads an active zoneObj if it exists, so gadget is a bit
      # robust to an accidental reboot. (distributionCheck only needs the cid)
      global cid
      try :
         with open("activeBTzoneObj.json","r") as f:  zoneObj = json.load(f)
         cid = zoneObj['cid']
      except :
         cid = 'none'

      if cid is None :  cid = 'none'
     logging.debug('distributionCheck initialized. cid = ' + cid)

   def run(self):
      logging.info('distributionCheck starting')
      logging.info('   ' + self.BT_ID + ' watching for RC at ' + self.RC_IP + ':' + str(self.RC_PORT))

      while not self.shutdown.isSet():   
          # check RC for update. 
          # Wrapped in try for case when connection fails (wifi out of range).
          logging.debug('BT check with RC for update.')

          try :
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              s.connect((self.RC_IP, self.RC_PORT))
              
              l = smp.snd(s, cid)
              logging.debug("BT cid " + str(cid))
              
              r = smp.rcv(s) 
              logging.debug('r ' + str(r))

              if not (r in ('ok', 'none')) :
                  logging.info('got new zoneObj. Writing to file activeBTzoneObj.json')
                  # Next could be a message to zoneSignal thread, but having a
                  # file means the gadget can recover after reboot without
                  # a connection to RC, so write string r to a file
                  with open("activeBTzoneObj.json","w") as f: f.write(r) 
                  self.update.set()

                  l = smp.snd(s, self.BT_ID)
                  logging.debug("sent  receipt BT " + str(self.BT_ID))

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
      self.zoneObj = { 'cid' : None }
      
   def run(self):
      #logging.debug("distributer started.")
      while not  self.shutdown.wait(0.01): # blocking for interval
         try:
            #logging.debug("distributer listening for incoming connections ...")
            self.tcpsock.listen(5)  
            (sock, (ip,port)) = self.tcpsock.accept()
            #these only take a second, so not need to pass shutdown signal.
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
      #    here or in a stadium mdule. But probably want raceObj class 
      #    with methods in stadiumRC first, and stop using globals.
      # This works by creating a new version of zoneObj, the BThandlerThread
      # compares the cid of this with that sent by BTs when they connect.
      # There is no other "signal" to BThandlerThread or to BTs. 
      # It depends on BTs checking in.
      #logging.debug('in distributer.distribute(), zoneObj:')
      #logging.debug(str(zoneObj))

      self.zoneObj = zoneObj   
      global distRecvd
      distRecvd = {}    # clear dict of boats that have update
            
      #print(json.dumps(self.zoneObj, indent=4))
   
      # write zoneObj to a file, for the record, but distribute is done with zoneObj
      with open('distributedCourses/zoneObj-' + self.zoneObj['cid'] + '.json',"w") as f:
         f.write("\n")
         f.write("zoneObj:\n")
         json.dump(self.zoneObj, f, indent=4)


class BThandlerThread(threading.Thread):
   # handle a connection from a BT. Check if BT is current and update if not.
   # NB BThandlerThread needs a dist object, not just zoneObj, 
   # because it uses dist.addRecvd() te record back to distributer.

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
             RCcid = 'none'
       elif self.zoneObj['cid'] is None : 
             RCcid = 'none'
       else :
             RCcid = self.zoneObj['cid']
       
       BTcid = smp.rcv(self.sock)  #course id that BT has
       
       #logging.debug(" BTcid " + str(BTcid))
       #logging.debug(" RCcid " + str(RCcid))

       if self.zoneObj is None : 
             smp.snd(self.sock, 'none')
             #logging.debug('sent none.')

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

   
   
   
   
   
   
   
 

   
