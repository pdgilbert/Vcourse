# License GPL 2. Copyright Paul D. Gilbert, 2017, 2018
"""Define stadium zone for BT."""

import logging
import time
import threading

import LEDs 

class zoneSignal(threading.Thread):
   """This thread class reads the gps and does calculations to set LED signals."""

   def __init__(self, zoneObj, stoprequest, GPScon, t):
      threading.Thread.__init__(self)
      self.name='stadium.zoneSignal'
      self.stoprequest = stoprequest

      self.GPScon = GPScon
      self.t = t

      # compare makezoneObj()  in stadiumRC
      #cid        = zoneObj['cid']
      #courseDesc = zoneObj['courseDesc']
      #zoneType   = zoneObj['zoneType']
      #distributionTime =zoneObj['distributionTime']
      #length     = zoneObj['length']
      #axis       = zoneObj['axis']
      #S          = zoneObj['S']
      #M          = zoneObj['M']
      self.dom        = zoneObj['dom']
      self.LtoR       = zoneObj['LtoR']
      self.b          = zoneObj['b']
      self.boundL     = zoneObj['boundL']
      self.boundR     = zoneObj['boundR']
      self.warnL      = zoneObj['warnL']
      self.warnR      = zoneObj['warnR']
      self.centerL    = zoneObj['centerL']
      self.centerR    = zoneObj['centerR']

      #logging.info('  new cid: %s',  cid)
      #logging.debug('new course axis:  %f',  axis)
      #logging.debug('new course S %f,%f: ', S[0], S[1])

      logging.info('stadium.zoneSignal initialized.')

   def run(self):
      logging.info('stadium.zoneSignal started.')

      sk =0 # skip counter for recording track

      while not self.stoprequest.is_set():   

         # run main signal setting loop here
         #logging.debug('checking zone status.')
         
         p = self.GPScon.getGPS()
         
         if p is None:
            logging.info('p is None.')
            tr = 'No GPS fix. LED status  noGPSfix'
            LEDs.setLEDs('noGPSfix', x='. No GPS fix.')
         else:
            #logging.info('p is ' + str(p.lat))
            
            # this is a in y = a + b * x
            if self.dom : a = p.lat - self.b * p.lon 
            else        : a = p.lon - self.b * p.lat
                             
            # LtoR, # True if bounds increase left to right
             
            if self.LtoR :
               if   self.boundL  >  a                 : now = ('bound',  'LtoR boundL') 
               elif self.warnL   >  a                 : now = ('warn',   'LtoR warnL' )
               elif self.centerL <= a <= self.centerR : now = ('center', 'LtoR center')
               elif                 a >  self.boundR  : now = ('bound',  'LtoR boundR')
               elif                 a >  self.warnR   : now = ('warn',   'LtoR warnR' )
               else                                   : now = ('off',    'LtoR'       )
            else :
               if   self.boundR   > a                 : now = ('bound',  'boundR')
               elif self.warnR    > a                 : now = ('warn',   'warnR' )
               elif self.centerR <= a <= self.centerL : now = ('center', 'center')
               elif                 a >  self.boundL  : now = ('bound',  'boundL')
               elif                 a >  self.warnL   : now = ('warn',   'warnL' )
               else                                    : now = ('off',    ''      )

            ps= '  @ ' +  str(p.lat) + '  ' + str(p.lon)  # only for debugging
            LEDs.setLEDs(now[0], now[1]+ ps)
            tr = str(p.lat) + ' ' + str(p.lon) + ' @ ' + p.time +' LED status ' + now[0]

         # record track. p.time comes from the gps. 
         # If fractional seconds are available I think they will be printed,
         #   but for now all seem to be .000.
         #   This may be something that can be set on the gps ?
         # Record only every 5 second so modulo in next depends on sleep 
         #   time. Record frequency impacts track file size.
         
         if sk is 0 : self.t.write(tr + '\n' )
         sk = (sk + 1) % 50  
   
         time.sleep(0.1) #0.5 worked but is a bit slow

      self.stoprequest.clear()
      logging.info('Exiting stadium.zoneSignal thread, for new course update or shutdown')

