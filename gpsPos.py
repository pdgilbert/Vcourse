# License GPL 2. Copyright Paul D. Gilbert, 2017

# PUT INTO UNIT TESTING
#from gpsPos import gpsPos
#pt = gpsPos.gpsPos(45.395676, -75.676829)
#pt = gpsPos(100.395676, -75.676829)
#pt = gpsPos(45.395676, -275.676829)
#pt2 = gpsPos.move(pt, 240, 1.0)
#gpsPos.nm(pt, pt2)  
# if not (1.0 == gpsPos.nm(pt, pt2).distance)  then something is wrong

#  p = gpsPos.getGPS()

# gpsPos.heading(gpsPos(44.20978198674271, -76.51016279425306), 
#                gpsPos(44.20144865340938, -76.53029941039073))  # 240 

# gpsPos.heading(gpsPos(44.209853494402275, -76.51003278266177),
#                gpsPos(44.1980683813825,   -76.526474280851))   # 225 

# gpsPos.heading(gpsPos(44.209853494402275, -76.51092055733824),
#                gpsPos(44.22163860742205,  -76.52736205552748))  # 315

# gpsPos.heading(gpsPos(44.21048983959772, -76.51092055733824),
#                gpsPos(44.2222749526175,  -76.49447888150982))   #045

# gpsPos.heading(gpsPos(44.21048983959772, -76.51003278266177),
#                gpsPos(44.198704726577944, -76.49359110683335))  # 135

# gpsPos.heading(gpsPos(0, -76.51003278266177),
#                gpsPos(0, -76.49359110683335))  # 90

# gpsPos.heading(gpsPos(44.21048983959772,  0),
#                gpsPos(44.198704726577944, 0))  # 1380

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
        if (lat != None) :
           if not (-90 <= lat <= 90):
              raise ValueError("must have  -90 <=  latitude <= 90")
        
        if (lng != None) :
           if not (-180 <= lng <= 180):
              raise ValueError("must have  -180 <= longitude <= 180")
        
        self.lat = lat
        self.lng = lng

    def nm(self, x):
        #nm N and E  between two gpsPos, self and x
        if not isinstance(x, gpsPos):
           raise ValueError("x must be a gpsPos object")

        latScale = 60.0  #  nm per degree lat
        lngScale = 60.0 * math.cos(math.radians(self.lat))  #  nm per degree long at current latitude
        
        N = (x.lat - self.lat) * latScale
        E = (x.lng - self.lng) * lngScale
        distance = math.sqrt(math.pow(N,2) + math.pow(E,2))
        return distance
    
    @classmethod
    def getGPS(cls):
      import gpsd
      p = gpsd.get_current()
      return(gpsPos(p.position()[0], p.position()[1]))

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

        lng = (distance * math.cos(math.radians(theta)) / lngScale) + pt.lng
        lat = (distance * math.sin(math.radians(theta)) / latScale) + pt.lat

        return cls(lat, lng)

    @classmethod
    def heading(cls, pt, target):
        # return heading (degrees T) from gps position pt to gps position target
        # N is +ve y,  E is +ve x. Math angle is counterclockwise (counter compass).
	# tan(y/x) cannot ditinguish NE from SW or NW from SE. atan2(y, x) does.
        Dy =   target.lat - pt.lat
        Dx =  (target.lng - pt.lng) * math.cos(math.radians(pt.lat)) 
        if (Dx == 0) and (Dy == 0) :
           raise ValueError("pt and target are the same points. No heading.")
        h = (90 - math.degrees(math.atan2(Dy , Dx))) % 360
        return h
