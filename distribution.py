# License GPL 2. Copyright Paul D. Gilbert, 2017

import socket
import logging
import json
import time

import smp

def distributionCheck(update, shutdown, interval, RC_IP, RC_PORT, BT_ID):
    # BT sends RC the cid (cousreID and distritution time) BT has.
    # RC replies with  'ok' indicating there is no update,
    #     or 'none' indicating no course set yet, or with updated raceObj.
    # BT confirms receipt of update with bt# or hostname?  
    
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
                logging.debug('got new raceObj. Writing to file BTraceObj.json')
                # Next could be a message to zoneSignal thread, but having a
                # file means the gadget can recover after reboot without
                # a connection to RC, so write string r to a file
                with open("BTraceObj.json","w") as f: f.write(r) 
                update.set()

                l = smp.snd(s, BT_ID)
                logging.debug("sent  receipt BT " + str(BT_ID))

    	    s.close()

        except :
           #logging.debug('no connection.')
           time.sleep(1)

        time.sleep(interval)

    raise Exception('distributionCheck should not be here.')

