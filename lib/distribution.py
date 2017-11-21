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

#logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

def distributionCheck(update, shutdown, interval, RC_IP, RC_PORT, BT_ID):
    # this function is used by BT

    logging.info('distributionCheck starting')
    logging.info('   ' + BT_ID + ' watching for RC at ' + RC_IP + ':' + str(RC_PORT))

    while True:
        if shutdown.wait(0.1):    # effectively sleep too
           logging.info('shutting down distributionCheck thread.')
           return() 
        
        # check RC for update. 
        # Wrapped in try for case when connection fails (wifi out of range).
        logging.debug('BT check with RC for update.')

        try :
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((RC_IP, RC_PORT))
            
            try :
               with open("BTzoneObj.json","r") as f:  zoneObj = json.load(f)
               cid = zoneObj['cid']
            except :
               cid = 'none'
            
            l = smp.snd(s, cid)
            #logging.debug("BT cid " + str(cid))
            
            r = smp.rcv(s) 
            logging.debug('r ' + str(r))

            if not (r in ('ok', 'none')) :
                logging.info('got new zoneObj. Writing to file BTzoneObj.json')
                # Next could be a message to zoneSignal thread, but having a
                # file means the gadget can recover after reboot without
                # a connection to RC, so write string r to a file
                with open("BTzoneObj.json","w") as f: f.write(r) 
                update.set()

                l = smp.snd(s, BT_ID)
                logging.debug("sent  receipt BT " + str(BT_ID))

            s.close()

        except :
           #logging.debug('no connection.')
           time.sleep(1)

        time.sleep(interval)

    raise Exception('distributionCheck should not be here.')


####### following used by RC #######

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
      self.distRecvd = {}
      
   def run(self):
      logging.debug("distributer started.")
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
  
   def distributionRecvd(self):
      return self.distRecvd
   
   def prt(self):
      print(json.dumps(self.zoneObj, indent=4))
      print('Received by:')
      print(self.distRecvd)
   
   def addRecvd(self, bt, tm):  # may need queue or something else for this
      self.distRecvd.update({str(bt) : tm})
   
   def distribute(self, zoneObj):
      #  IT might BE BETTER IF THE ARG WAS raceObj and makezoneObj was done
      #    here or in a stadium nodule. But probably want raceObj class 
      #    with methods in stadiumRC first, and stop using globals.
      # This works by creating a new version of zoneObj, the BThandlerThread
      # compares the cid of this with that sent by BTs when they connect.
      # There is no other "signal" to BThandlerThread or to BTs. 
      # It depends on BTs checking in.
      logging.debug('in distributer.distribute(), zoneObj:')
      logging.debug(str(zoneObj))

      self.zoneObj = zoneObj   
      self.distRecvd = {}    # clear dict of boats that have update
            
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
       #logging.debug('in BThandlerThread init')
       self.ip = ip
       self.port = port
       self.sock = sock
       self.zoneObj = zoneObj
   def run(self):        
       logging.debug('in BThandlerThread.run()')
       logging.debug(str(self.zoneObj))

       #course id that RC has
       if self.zoneObj is None : 
             RCcid = 'none'
       elif self.zoneObj['cid'] is None : 
             RCcid = 'none'
       else :
             RCcid = self.zoneObj['cid']
       
       BTcid = smp.rcv(self.sock)  #course id that BT has
       
       logging.debug(" BTcid " + str(BTcid))
       logging.debug(" RCcid " + str(RCcid))

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
             logging.debug('ADD BT_ID TO LIST. ' + bt)
             #dr.addRecvd( bt, time.strftime('%Y-%m-%d %H:%M:%S %Z'))
 
       self.sock.close()
       logging.debug('closed socket and exiting thread ' + self.name)

   
   
   
   
   
   
   
 

   
