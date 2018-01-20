# License GPL 2. Copyright Paul D. Gilbert, 2018
"""
This module is used by Registration for communication with BTs at regatta checkout and
BT configuration. callout can be gizmone hostname (BT-#)  or boat ID (sail #)
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

   callout = "BT-1"       # hostname
   callout = "boat 1,FX"  # boat id,fl
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
   """
   global sockUDP, sockTCP
   if request not in ("flash",    "report config", "flash, report config", 
                      "checkout", "checkin",       "requestBTconfig",  "setRC",  "setREG"):
         raise Exception("request '" + request + "' to " + str(callout) + " not recognized.")
   
   # double colon separate callout::request[::conf]
   # callout can be a hn or bt,fl combination
   txt = callout +"::" + request
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

   return None


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

def requestBTconfig(hn, conf) :
   """
   Listen for request and confirm it is from correct hostname
   then send a BTconfig (partial) update
   """
   global sockTCP
   try :
      (sock, (ip,port)) = sockTCP.accept()        
      mes = smp.rcv(sock) 
      cf = eval(mes) # str to dict

      if hn != cf['hn'] : raise Exception('incorrect gizmo. Not resetting.')

      logging.debug(str(conf))
      l   = smp.snd(sock, str(conf))  
      echo = smp.rcv(sock) 
      cf = eval(echo) # str to dict
      logging.debug(str(cf))
      sock.close()
   except :
      cf = eval(conf)
      cf.update({'hn': None})
      return cf

   if hn != cf['hn'] :
      raise Exception('Code error, resetting is messed up. Config "hn" is not hn!')

   return cf
