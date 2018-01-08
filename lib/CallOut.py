# License GPL 2. Copyright Paul D. Gilbert, 2018

import socket

#callout = "BT-1"  # hostname
#callout = "FX-1"  # boat id

# for registration
#request = "flash"
#request = "send address"
#request = "flash and send address"
#request = "load BTconfig"  #TCP

# for maintenance
#request = "load RCaddress"  #TCP or UDP to a fleet(s)?
#request = "load GPSconfig" #TCP
#request = "load runAtBoot" #TCP

def CallOut(callout, request, timeout=10) :
   #callout can be gizmone hostname (BT-#)  or boat ID (sail #)
   # expecting returned BTconfig

   sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Internet, UDP
   sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

   # double colon separate callout::request
   print(callout +"::"+ request)
   sockUDP.sendto((callout +"::"+ request).encode('utf-8'), ('<broadcast>', 5005)) #UDP_IP, PORT

   sockUDP.settimeout(timeout)

   try :
      mes, btADDR= sockUDP.recvfrom(1024, 0) 
   except :
      raise Exception('no response from' + str(callout))

   mes = mes.decode()

   print (mes, btADDR)   
   sockUDP.close()

   z = mes.split('::')
   bt = z.pop(0)   
   conf = eval(z[0])

   print (bt)   
   print (btADDR)   
   print (str(conf) )  
   return (bt, btADDR, conf)

def SendBTconfig(btADDR, conf) :
   try :
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
      s.connect((btADDR[0], btADDR[1])) #IP, port
      
      l = smp.snd(s, 'BTconfig-' + str(conf)) # json serialize
      
      #r = smp.rcv(s) 
      #logging.debug('r ' + str(r))
   except :
      raise Exception('no TCP connection to' + str(btADDR))

   return None
