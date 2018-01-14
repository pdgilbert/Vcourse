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

UDP broadcasts are prepended with bt or hn :: so BTs can determine if it is intended for them.
This is not needed on individual TCP connections.

   callout = "BT-1"  # hostname
   callout = "FX-1"  # boat id

    for registration
   request = "flash" 
   request = "report config"    #start TCP to listen
   request = "requestBTconfig"  #start TCP to listen, this is a request to set new BTconfig

   request = "flash, report config"

    for maintenance
   request = "load Registration address" #UDP
   request = "load RCaddress" #UDP to a fleet(s)?
   request = "load GPSconfig" #TCP
   request = "load runAtBoot" #TCP

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
sockTCP.settimeout(10)
sockTCP.listen(5)  
atexit.register(sockTCP.close)


def splitConf(mes):
   z = mes.split('::')
   bt = z.pop(0)   
   conf = eval(z[0]) # str to dict
   return (bt, conf)

def CallOut(callout, request, conf=None, timeout=5) :  #timeout NOT BEING USED
   global sockUDP, sockTCP
   if request not in ("flash",    "report config", "flash, report config", 
                      "checkout", "checkin",       "requestBTconfig",  "setRC"):
         raise Exception("request '" + request + "' to " + str(callout) + " not recognized.")
   
   # double colon separate callout::request[::conf]
   txt = callout +"::" + request
   if conf is not None : txt = txt + "::" + str(conf)
   sockUDP.sendto(txt.encode('utf-8'), ('<broadcast>', 5005)) #UDP_IP, PORT

   # Above did requests that broadcast only, like "setRC", so now just return for those.
   # Check in/out is just a broadcast to flash LEDs. Bookkeeping about in or out
   # is kept at registration not sent to BT.

   if   request == "flash" :                   return None
   elif request == "checkout" :                return None
   elif request == "checkin" :                 return None
   elif request == "setRC" :                   return None
   elif request == "report config" :           conf = ReportBTconfig(callout)
   elif request == "flash, report config" :    conf = ReportBTconfig(callout)
   elif request == "requestBTconfig" :         conf = requestBTconfig(callout, str(conf))

   bt = conf['BT_ID']
   return (bt, conf)


def ReportBTconfig(callout) :
   # listen for response but then confirm for correct callout
   global sockTCP
   try :
      (sock, (ip,port)) = sockTCP.accept()
      mes = smp.rcv(sock) 
      sock.close()
   except :
       raise Exception('no response from ' + str(callout))

   cf = eval(mes) # str to dict

   if not (callout == cf['BT_ID'] or callout == cf['hn'] ) :
       raise Exception('incorrect gizmo. Not reporting.')

   return cf

def requestBTconfig(hn, conf) :
   # listen for request and confirm it is from correct hostname
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
      raise Exception('no TCP connection from' + str(hn))

   if hn != cf['hn'] :
      raise Exception('Code error, resetting is messed up. Config "hn" is not hn!')

   return cf
