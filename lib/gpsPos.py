# License GPL 2. Copyright Paul D. Gilbert, 2017, 2018
"""Object for defining a GPS position and operation with it."""


#It is possible to use something like gps2net on a phone and connect to it,
# but python gpsd expects json format data while gps2net supplies raw NMEA0183.
# Thus it is necessary to run gpsd to talk to the phone and translate:
#[sudo] gpsd -S 2950 tcp://192.168.2.195:6000  # uses 127.0.0.1 port 2950
#[sudo] gpsd -S 2950 tcp://10.42.0.101:6000    # uses 127.0.0.1 port 2950
#[sudo] gpsd -S 2949 tcp://10.42.0.74:6000     # uses 127.0.0.1 port 2949

# but NB: python gpsd supports only one connection at a time (in one session)

import gpsd
import math
import logging

class gpsConnection():
   def __init__(self, host="127.0.0.1", port=2947):
      """Define and return a gpsConnection object. (really a fake.)"""
      # The connection is a global in gpsd, and is simply left in place.
      # This only works if there is a reconnect each time there is a change,
      # which is what happens with stadiumRC. To actually work properly the
      # conncetion has to be part of the object, but that requires changes in gpsd.
      self.host  = host
      self.port  = int(port)
      try:
         gpsd.connect(host=self.host, port=self.port) 
      except:
         logging.info('Cannot connect to GPS at ' + self.host + ':' + str(self.port))
         # do not kill the thread, it may be temporary

   def getGPS(self):
      """Get the current GPS position and return a gpsPos object."""
      try:
         p = gpsd.get_current()
      except:
         try:
            logging.debug('getGPS attempting reconnect.' )
            gpsd.connect(host=self.host, port=self.port) # re-connect
            p = gpsd.get_current()
         except:
            return(None)
      logging.debug('getGPS:' + str(p.lat) + ' ' + str(p.lon) )
      if (p.lat, p.lon) == (0, 0) : return(None) # occassional error result in gpsd
      return(gpsPos(p.lat, p.lon, p.time))

class gpsPos():
    def __init__(self, lat, lon, time=None):
        """Define and return a gpsPos object."""
        if lat is not None :
           if not (-90 <= lat <= 90):
              raise ValueError("must have  -90 <=  latitude <= 90")
        
        if lon is not None :
           if not (-180 <= lon <= 180):
              raise ValueError("must have  -180 <= longitude <= 180")
        
        if time is None : time = '' 
        
        self.lat  = lat  # A float  -90 <=  lat <= 90
        self.lon  = lon  # A float  -180 <= lon <= 180
        self.time = time 
    
    def latitude(self) :
       """Extract the latitude from a gpsPos object."""
       return self.lat
    
    def longitude(self):
       """Extract the longitude from a gpsPos object."""
       return self.lon
    
    def nm(self, x):
        """Calculate the distance in nautical miles to another gpsPos object."""
        #nm N and E  between two gpsPos, self and x
        if not isinstance(x, gpsPos):
           raise ValueError("x must be a gpsPos object")
        
        latScale = 60.0  #  nm per degree lat
        lonScale = 60.0 * math.cos(math.radians(self.lat))  #  nm per degree long at current latitude
        
        N = (x.lat - self.lat) * latScale
        E = (x.lon - self.lon) * lonScale
        distance = math.sqrt(math.pow(N,2) + math.pow(E,2))
        return distance
    
    @classmethod
    def move(cls, pt, axis, distance):
        """Return gpsPos object at distance (nm) from pt at bearing axis."""
        
        # theta angle relative to E and counter clockwise (counter compass)
        #   gives correct signs for lat and long shift
        theta = (90 - axis) % 360
        
        latScale = 60.0  # nm per degree lat
        # nm per degree long at pt latitude
        lonScale = 60.0 * math.cos(math.radians(pt.lat)) 
        
        lon = (distance * math.cos(math.radians(theta)) / lonScale) + pt.lon
        lat = (distance * math.sin(math.radians(theta)) / latScale) + pt.lat
        
        return cls(lat, lon)
    
    @classmethod
    def heading(cls, pt, target):
        """Return heading (degrees T) from gpsPos object pt to gpsPos target."""
 
        # N is +ve y,  E is +ve x. Math angle is counterclockwise (counter compass).
	# tan(y/x) cannot ditinguish NE from SW or NW from SE. atan2(y, x) does.
        Dy =   target.lat - pt.lat
        Dx =  (target.lon - pt.lon) * math.cos(math.radians(pt.lat)) 
        if (Dx == 0) and (Dy == 0) :
           raise ValueError("pt and target are the same points. No heading.")
        h = (90 - math.degrees(math.atan2(Dy , Dx))) % 360
        return h

