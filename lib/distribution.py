# License GPL 2. Copyright Paul D. Gilbert, 2017

# BT sends RC the cid (cousreID and distritution time) BT has.
# RC replies with  'ok' indicating there is no update,
#     or 'none' indicating no course set yet, or with updated raceObj.
# BT confirms receipt of update with bt# or hostname?  

import socket
#import logging
import json
import time
import threading

import smp

#logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

def distributionCheck(update, shutdown, interval, RC_IP, RC_PORT, BT_ID):
    # this function is used by BT

    print('distributionCheck starting')

    while True:
        if shutdown.wait(0.1):    # effectively sleep too
           print('shutting down distributionCheck thread.')
           return() 
        
        # check RC for update. 
        # Wrapped in try for case when connection fails (wifi out of range).
        #logging.debug('BT check with RC for update.')

        try :
    	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    	    s.connect((RC_IP, RC_PORT))
    	    
    	    try :
    	       with open("BTraceObj.json","r") as f:  raceObj = json.load(f)
    	       cid = raceObj['cid']
    	    except :
    	       cid = 'none'
    	    
    	    l = smp.snd(s, cid)
    	    #logging.debug("BT cid " + str(cid))
    	    
    	    r = smp.rcv(s) 
    	    #logging.debug('r ' + str(r))

    	    if not (r in ('ok', 'none')) :
                #logging.debug('got new raceObj. Writing to file BTraceObj.json')
                # Next could be a message to zoneSignal thread, but having a
                # file means the gadget can recover after reboot without
                # a connection to RC, so write string r to a file
                with open("BTraceObj.json","w") as f: f.write(r) 
                update.set()

                l = smp.snd(s, BT_ID)
                #logging.debug("sent  receipt BT " + str(BT_ID))

    	    s.close()

        except :
           #logging.debug('no connection.')
           time.sleep(1)

        time.sleep(interval)

    raise Exception('distributionCheck should not be here.')


####### following are used by RC #######

def distributer(dist):
   # wait for connections from BTs and pass each to a BThandlerThread.
   print('distributer starting. Using RC_IP ' + str(dist.RC_IP) + ':' +str(dist.RC_PORT))
   
   tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   tcpsock.bind((dist.RC_IP, dist.RC_PORT))

   while True:
       # often not getting shutdown signal. Seems to work better when a BT has connected. FIX
       if dist.shutdown.wait(0.01): # blocking for interval !! 
          print('shutting down distributionHandler thread.')
          return() 
       tcpsock.listen(5)  # STALLS HERE LISTENING WITH NO CONNECTIONS, SO NEVER LOOPS  TO shutdown.
       #logging.debug("Waiting for incoming connections on "  + dist.RC_IP + ":" + str(dist.RC_PORT) + " ...")
       (conn, (ip,port)) = tcpsock.accept()
       #logging.debug('Got connection from ' + ip + ':' + str(port))
       BThandlerThread(ip,port,conn, dist).start()

   raise Exception('distributionHandler should not be here.')

class BThandlerThread(threading.Thread):
   # handle a connection from a BT. Check if BT is current and update if not.
   # NB BThandlerThread needs a dist object, not just raceObj, 
   # because it uses dist.received() te record back to "global" dist.

   def __init__(self,ip,port,sock, dist):
       threading.Thread.__init__(self)
       self.ip = ip
       self.port = port
       self.sock = sock
       self.dist = dist
   
   def run(self):
       import smp
       import json
        
       #course id that RC has
       if (self.dist.raceObj == None ) : 
          RCcid = 'none'
       else :
          RCcid = self.dist.raceObj['cid']
       
       BTcid = smp.rcv(self.sock)  #course id that BT has
       
       #logging.debug(" BTcid " + str(BTcid))
       #logging.debug(" RCcid " + str(RCcid))

       if (self.dist.raceObj == None ) : 
             smp.snd(self.sock, 'none')
             #logging.debug('sent none.')

       elif (BTcid == RCcid) :
             smp.snd(self.sock, 'ok')
             #logging.debug('sent ok.')
             
       else :
             #logging.debug('sending new raceObj to BT')
             smp.snd(self.sock, json.dumps(self.dist.raceObj, indent=4))
             #logging.debug('new raceObj sent:')
             bt = smp.rcv(self.sock) 
             #logging.debug('ADD BT_ID TO LIST. ' + bt)
             self.dist.received( bt, time.strftime('%Y-%m-%d %H:%M:%S %Z'))
 

       self.sock.close()
       #logging.debug('closed socket and closing thread.')

class distribution():

   def __init__(self, shutdown, RC_IP, RC_PORT, raceObj, raceObjReceived):
      self.shutdown = shutdown
      self.RC_IP = RC_IP
      self.RC_PORT = RC_PORT
      self.raceObj = raceObj
      self.raceObjReceived = raceObjReceived
   
   def prt(self):
      print(json.dumps(self.raceObj, indent=4))
      print('Received by:')
      print(self.raceObjReceived)

   def newRace(self, newraceObj):
      # should be called by distribute but for now called by makeRaceObj
      #  which uses global parameters.
      self.raceObj.clear()
      self.raceObj.update(newraceObj)

   def received(self, bt, tm):
      self.raceObjReceived.update({str(bt) : tm})
   
   def distribute(self):  #, newraceObj):
      # This works by creating a new version of RaceObj, the BThandlerThread
      # compares the cid of this with that sent by BT when they connect.
      # There is no "signal" to distributionHandler or BTs. It depends on them checking in.
            
      #print(json.dumps(self.raceObj, indent=4))
   
      # clear dict of boats that have update
      self.raceObjReceived.clear()
   
      # write raceObj [NOT and also global object info] to a file, for the record, but distribute is done with raceObj
      with open('distributedCourses/raceObj' + self.raceObj['cid'] + '.json',"w") as f:
         f.write("\n")
         f.write("raceObj:\n")
         json.dump(self.raceObj, f, indent=4)
         #Race = { 'fl':fl, 'dc':dc, 'ty':ty, 'cl':cl, 'ax':ax, 'll':ll, 'sw':sw, 
         #       'RC.lat':RC.lat, 'RC.lon':RC.lon, 'S.lat':S.lat, 'S.lon':S.lon, 'M.lat':M.lat, 'M.lon':M.lon,
         #       'wn':wn, 'cc':cc, 'tt':tt }
         #f.write("\n")
         #f.write("Race:\n")
         #json.dump(Race, f, indent=4)

   
   
   
   
   
   
   
   
 

   
