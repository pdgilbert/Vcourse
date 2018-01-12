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


def CallOut(callout, request, conf=None, timeout=5) :

   if request not in ("flash", "report config", "flash, report config", "requestBTconfig"):
         raise Exception("request '" + request + "' to " + str(callout) + " not recognized.")
   
   sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Internet, UDP
   sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
   sockUDP.settimeout(timeout)

   # double colon separate callout::request
   txt = callout +"::"+ request
   sockUDP.sendto(txt.encode('utf-8'), ('<broadcast>', 5005)) #UDP_IP, PORT
   sockUDP.close()

   if   request == "flash" :                   return None
   elif request == "report config" :           (bt, conf) = ReportBTconfig(callout)
   elif request == "flash, report config" :    (bt, conf) = ReportBTconfig(callout)
   elif request == "requestBTconfig" :         (bt, conf) = requestBTconfig(callout, str(conf))

   print (bt)   
   print (str(conf) ) 

   return (bt, conf)

def Listen() :
   socketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
   socketTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   socketTCP.bind(("10.42.0.254", 9005) ) #Registration IP, port
   #socketTCP.settimeout(10)
   socketTCP.listen(5)  
   return socketTCP

def splitConf(mes):
   z = mes.split('::')
   bt = z.pop(0)   
   conf = eval(z[0]) # str to dict
   return (bt, conf)


def ReportBTconfig(callout) :
   # listen for response but then confirm for correct callout
   try :
      socketTCP = Listen()
      (sock, (ip,port)) = socketTCP.accept()
      mes = smp.rcv(sock) 
      print (mes)   
   except :
       raise Exception('no response from ' + str(callout))
   finally :
      sock.close()
      socketTCP.close()

   (bt, cf) = splitConf(mes)

   if bt != cf['BT_ID']  :
       raise Exception('Code error, reporting is messed up. Config "BT_ID" is not bt!')

   if not (callout == cf['BT_ID'] or callout == cf['hn'] ) :
       raise Exception('incorrect gizmo. Not reporting.')

   return (bt, cf)

def requestBTconfig(hn, conf) :
   # listen for request and confirm it is from correct hostname
   try :
      socketTCP = Listen()
      (sock, (ip,port)) = socketTCP.accept()        
      mes = smp.rcv(sock) 
      (bt, cf) = splitConf(mes)
      print('cf is ' + str(cf))
      if hn != cf['hn'] :
         raise Exception('incorrect gizmo. Not resetting.')
      #logging.debug('mes ' + str(mes))
      l   = smp.snd(sock, str(conf))  
      echo = smp.rcv(sock) 
      (bt, cf) = splitConf(echo)
   except :
      raise Exception('no TCP connection from' + str(hn))
   finally :
      sock.close()
      socketTCP.close()

   print('cf is ' + str(cf))
   if hn != cf['hn'] :
      raise Exception('Code error, resetting is messed up. Config "hn" is not hn!')

   if bt != cf['BT_ID'] :
      raise Exception('Code error, resetting is messed up. Config "BT_ID" is not bt!')

   return (bt, cf)
