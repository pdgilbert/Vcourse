# License GPL 2. Copyright Paul D. Gilbert, 2017

import socket
import os.path
import logging
import json

import smp

# read from config file   FIX
#RC_IP = 'xxx.xxx.xxx.xxx' 
RC_PORT = 9001

BT_ID = socket.gethostname()


def distributionCheck(update, shutdown, interval):
    # BT sends RC the cid (cousreID and distritution time) BT has.
    # RC replies with  'ok' indicating there is no update,
    #     or 'none' indicating no course set yet, or with updated raceObj.
    # BT confirms receipt of update with bt# or hostname?  
    
    logging.debug('distributionCheck starting')

    while True:
        if shutdown.wait(interval):    # effectively sleep too
           logging.debug('shutting down distributionCheck thread.')
           return() 
        
        # check RC for update
        #logging.debug('check RC for update.')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((RC_IP, RC_PORT))
        
        if os.path.isfile("BTraceObj.json"):
           with open("BTraceObj.json","r") as f:  raceObj = json.load(f)
           cid = str(raceObj['courseID']) + ' ' + raceObj['distributionTime']
        else :
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
        #logging.debug('connection closed')

    logging.debug('distributionCheck should not be here.')

