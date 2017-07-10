# License GPL 2. Copyright Paul D. Gilbert, 2017

# PUT INTO UNIT TESTING
#pt = gpsPos(45.395676, -75.676829)
#pt = gpsPos(100.395676, -75.676829)
#pt = gpsPos(45.395676, -275.676829)
#pt2 = gpsPos.move(pt, 240, 1.0)
#gpsPos.nm(pt, pt2)  
# if not (1.0 == gpsPos.nm(pt, pt2).distance)  then something is wrong

#  p = gpsPos.getGPS()

import gpsd
import math

class gpsPos(object):
    """a 2-tuple of gps latitude and longitude in decimal degrees

    Attributes:
        lat: A float  -90 <=  lat <= 90
        lng: A float  -180 <= lng <= 180
    """
    
    def latitude(self) : return self.lat
    
    def longitude(self): return self.lng

    def __init__(self, lat, lng):
        if not (-90 <= lat <= 90):
           raise ValueError("must have  -90 <=  latitude <= 90")
        
        if not (-180 <= lng <= 180):
           raise ValueError("must have  -180 <= longitude <= 180")
        
        self.lat = lat
        self.lng = lng

    def nm(self, x):
        #nm N and E  between two gpsPos, self and x
        if not isinstance(x, gpsPos):
           raise ValueError("x must be a gpsPos object")

        #  nm per degree lat
        #latScale = 60.0
	#  nm per degree long at current latitude                  
        lngScale = 60.0 * math.cos(math.radians(self.lat)) 
        
        N = (x.lat - self.lat) * latScale
        E = (x.lng - self.lng) * lngScale
        distance = math.sqrt(math.pow(N,2) + math.pow(E,2))
        return {'N' : N, 'E' : E, 'distance' : distance}

    @classmethod
    def move(cls, pt, axis, distance):
        # return gps coordinates of position which is
        #  distance (nm) from pt at bearing axis
   
        # theta angle relative to E and counter clockwise (counter compass)
        #   gives correct signs for lat and long shift
        theta = (90 - axis) % 360

        latScale = 60.0  # nm per degree lat
        # nm per degree long at pt latitude
        lngScale = 60.0 * math.cos(math.radians(pt.lat)) 
        # SOMETHING IS STILL WRONG WITH LNGSCALE (WORKS BETTER AT 60)

        lng = (distance * math.cos(math.radians(theta)) / lngScale) + pt.lng
        lat = (distance * math.sin(math.radians(theta)) / latScale) + pt.lat

        return cls(lat, lng)
    
    @classmethod
    def getGPS(cls):
      import gpsd
      p = gpsd.get_current()
      return(gpsPos(p.position()[0], p.position()[1]))
