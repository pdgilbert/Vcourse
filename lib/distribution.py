# License GPL 2. Copyright Paul D. Gilbert, 2017

# BT sends RC the cid (cousreID and distritution time) BT has.
# RC replies with  'ok' indicating there is no update,
#     or 'none' indicating no course set yet, or with updated raceObj.
# BT confirms receipt of update with bt# or hostname?  

import socket
import logging
import json
import time
import threading

import smp

def distributionCheck(update, shutdown, interval, RC_IP, RC_PORT, BT_ID):
    # this function is used by BT

    print('distributionCheck starting')

    while True:
        if shutdown.wait(0.1):    # effectively sleep too
           print('shutting down distributionCheck thread.')
           return() 
        
        # check RC for update. 
        # Wrapped in try for case when connection fails (wifi out of range).
        #logging.debug('check RC for update.')

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

class BThandlerThread(threading.Thread):
   # handle a connection from a BT. Check if BT is current and update if not.

   def __init__(self,ip,port,sock):
       threading.Thread.__init__(self)
       self.ip = ip
       self.port = port
       self.sock = sock
       #logging.debug(" New thread started for "+ip+":"+str(port))
   
   def run(self):
       import smp
       import json
       
       global raceObjReceived
 
       #course id that RC has
       if (raceObj == None ) : 
          RCcid = 'none'
       else :
          RCcid = raceObj['cid']
       
       BTcid = smp.rcv(self.sock)  #course id that BT has
       
       #logging.debug(" BTcid " + str(BTcid))
       #logging.debug(" RCcid " + str(RCcid))

       if (raceObj == None ) : 
             smp.snd(self.sock, 'none')
             #logging.debug('sent none.')

       elif (BTcid == RCcid) :
             smp.snd(self.sock, 'ok')
             #logging.debug('sent ok.')
             
       else :
             #logging.debug('sending new raceObj to BT')
             smp.snd(self.sock, json.dumps(raceObj, indent=4))
             #logging.debug('new raceObj sent:')
             r = smp.rcv(self.sock) 
             logging.debug('ADD BT_ID TO LIST. ' + r)
             raceObjReceived[r] = time.strftime('%Y-%m-%d %H:%M:%S %Z')
 

       self.sock.close()
       #logging.debug('closed socket and closing thread.')


def distributionHandler(shutdown, RC_IP, RC_PORT):
   # wait for connections from BTs and pass each to a BThandlerThread.
   logging.debug('distributionHandler starting')
      
   tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   tcpsock.bind((RC_IP, RC_PORT))

   while True:
       # often not getting shutdown signal. Seems to work better when a BT has connected. FIX
       if shutdown.wait(0.01): # blocking for interval !! 
          logging.debug('shutting down distributionHandler thread.')
          return() 
       tcpsock.listen(5)  # STALLS HERE LISTENING WITH NO CONNECTIONS, SO NEVER LOOPS  TO shutdown.
       #logging.debug("Waiting for incoming connections on "  + RC_IP + ":" + str(RC_PORT) + " ...")
       (conn, (ip,port)) = tcpsock.accept()
       #logging.debug('Got connection from ' + ip + ':' + str(port))
       BThandlerThread(ip,port,conn).start()

   logging.debug('distributionHandler should not be here.')

