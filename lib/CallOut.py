# License GPL 2. Copyright Paul D. Gilbert, 2018
"""
This module is used by Registration for communication with BTs at regatta check in/out and
for BT configuration. callout can be gizmone hostname (BT-#)  or boat ID (sail #)
but for "requestBTconfig" it should be a gizmone hostname (BT-#) since the  boat ID (sail #) may 
be getting changed. 

All requests start with a UDP broadcast by Registration, since BT addresses are not known. 
If the BT needs to respond it will initiate a TCP connection to Registration. This seems a bit
convoluted sometimes: when Registration needs to send a whole new configuration to a gizmo it
sends a "requestBTconfig" telling the BT to request a new configuration. The alternative would
require BT to run a process listening for TCP connections.

UDP broadcasts are prepended with 'all', 'bt,fl' or 'hn' separated by '::' from the request,
so BTs can determine if it is intended for them.
This is not needed on individual TCP connections.
"""
import socket
import smp
import logging
import atexit

sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Internet, UDP
sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sockUDP.settimeout(5)
atexit.register(sockUDP.close)

sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
sockTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sockTCP.bind(("10.42.0.254", 9006) ) #Registration IP, port
sockTCP.settimeout(5)
sockTCP.listen(5)  
atexit.register(sockTCP.close)


def splitConf(mes):
   (btfl, z) = mes.split('::')
   conf = eval(z) # str to dict
   (bt,fl) = btfl.split(',')
   return (bt, fl, conf)

def CallOut(callout, request, conf=None, timeout=5) :  #timeout NOT BEING USED
   """
   In cases where a response is not expected this function returns None.
   In cases where a response is expected this function returns a BTconfig dict with
   the additional element 'hn' indicating the gizmo hostname.
   In the case  a response is expected but BT does not respond the hn value is set None.
   
   Following should all be True

   CallOut("BT-1",      "flash")  is None  # callout is hn
   CallOut("boat 1,FX", "flash")  is None  # callout is bt,fl
   CallOut("all",       "flash")  is None  # callout is all


   """
   global sockUDP, sockTCP
   if request not in ("flash",    "report config", "flash, report config", 
                      "checkout", "checkin",       "requestBTconfig",  "setRC",  "setREG"):
         raise Exception("request '" + request + "' to " + str(callout) + " not recognized.")
   
   # double colon separate callout::request[::conf]
   # callout can be a hn or bt,fl combination
   txt = callout +"::" + request

   # For broadcasts flash, checkin, checkout and report config there is no conf to appended.
   # For broadcasts setRC and setREG the conf appended here is used.
   # For broadcasts requestBTconfig the conf appended here is not used and instead
   # the same conf is passed to requestBTconfig() to be sent by TCP. This is to
   # ensuree it is actually received.

   if conf is not None : txt = txt + "::" + str(conf)
   print(txt)
   sockUDP.sendto(txt.encode('utf-8'), ('<broadcast>', 5005)) #UDP_IP, PORT

   # Above did requests that broadcast only, like "setRC", so now just return for those.
   # Check in/out is just a broadcast to flash LEDs. Bookkeeping about in or out
   # is kept at registration not sent to BT.

   if   request == "flash" :                   return None
   elif request == "checkout" :                return None
   elif request == "checkin" :                 return None
   elif request == "setRC" :                   return None
   elif request == "setREG" :                  return None
   elif request == "report config" :           return ReportBTconfig(callout)
   elif request == "flash, report config" :    return ReportBTconfig(callout)
   elif request == "requestBTconfig" :         return requestBTconfig(callout, str(conf))
   else : return None


def ReportBTconfig(callout) :
   """
   Listen for response but then confirm the BTconfig is for correct callout.
   This does not send a BTconfig update.
   """
   global sockTCP
   try :
      (sock, (ip,port)) = sockTCP.accept()
      mes = smp.rcv(sock) 
      logging.debug('mes')
      logging.debug(str(mes))
      sock.close()
   except :
      return({'BT_ID': callout, 'hn': None})

   cf = eval(mes) # str to dict

   btfl = cf['BT_ID'] + ',' + cf['FLEET']
   logging.debug(callout)
   logging.debug(btfl)
   logging.debug(callout == btfl)
   if not (callout == btfl or callout == cf['hn'] ) :
       raise Exception('incorrect gizmo. Not reporting.')

   return cf

def requestBTconfig(callout, conf) :
   """
   Listen for request and verify it is from the correct callout
   hostname or bt,fl,  then send conf (a full or partial BTconfig 
   update) via the TCP connection. (Beware that  bt,fl may be
   changing so the verification has to be with the old values. 
   The conf is a dict which updates some elements of BTconfig.
   """
   global sockTCP
   logging.debug('in requestBTconfig, conf:')
   logging.debug(str(conf))
   try :
      logging.debug('in requestBTconfig, try')
      logging.debug('conf: '+ str(conf))
      (sock, (ip,port)) = sockTCP.accept()        
      # get response to the UDP broadcast. This will have the old BTconfig.
      mes = smp.rcv(sock) 
      logging.debug('in requestBTconfig, mes:')
      logging.debug(mes)
      oldcf = eval(mes) # str to dict
      logging.debug('in requestBTconfig, oldcf:')
      logging.debug(oldcf)
      btfl = oldcf['BT_ID'] + ',' + oldcf['FLEET']

      if not (callout == btfl or callout == oldcf['hn'] ) :
         logging.info(callout == btfl or callout == oldcf['hn'] )  
         logging.info(callout)  
         logging.info(btfl)  
         logging.info(oldcf['hn'] )  
         raise Exception('incorrect gizmo. Not resetting.')

      logging.debug('in requestBTconfig, about to send new conf:')
      logging.debug(str(conf))
      # send new 
      l   = smp.snd(sock, str(conf))  
      logging.debug('in requestBTconfig, getting echo.')
      echo = smp.rcv(sock) 
      logging.debug('in requestBTconfig, echo:')
      logging.debug(str(echo))
      cf = eval(echo) # str to dict
      logging.debug(str(cf))
      sock.close()
   except :
      cf = eval(conf)
      cf.update({'hn': None})
      return cf

   return cf
