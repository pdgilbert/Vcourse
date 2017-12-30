# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Object for overall race management, not specific to a zoneType."""

import logging
import json
import tkinter
from tkinter import filedialog
import time
import gpsd
import math

import os  # just for mkdir

from joblib import Parallel, delayed # for parallel requests to remote gps

from gpsPos import gpsPos
from gpsPos import gpsConnection

import stadiumRC as stadium
import stadium2RC as stadium2

config = json.load(open('GPSconfig'))   
GPS_HOST = config['GPS_HOST']      # typically "127.0.0.1"
GPS_PORT = int(config['GPS_PORT']) # 2947 is default


# FLEETS sets options in drop down menu. To change the menu it seems to be
# necessary to restart, so a re-read button is not usable.
try : 
   with open("FleetList.txt") as f:  FLEETS =  f.read().splitlines()
   FLEETS = [b.strip() for b in FLEETS]
except :
   FLEETS = 'No fleet'   

if not os.path.exists('FLEETS'):  os.makedirs('FLEETS')
if not os.path.exists('RACEPARMS'):  os.makedirs('RACEPARMS')

for d in FLEETS:
   if not os.path.exists('FLEETS/' + d):
             os.makedirs('FLEETS/' + d)
   if not os.path.exists('FLEETS/' + d + '/DISTRIBUTEDZONES'):
             os.makedirs('FLEETS/' + d + '/DISTRIBUTEDZONES')

#########################    Utility  Functions     ######################### 

def But(w, text='x', command='') :
   b = tkinter.Button(w, text=text,  command=command)
   b.pack(side=tkinter.LEFT, padx=5, pady=5)
   return(b)

def Drop(w, options=['zero', 'one', 'two'], default=0) :
   v = tkinter.StringVar(w)
   v.set(options[default]) 
   b = tkinter.OptionMenu(w, v, *options)
   b.pack(side=tkinter.LEFT)
   return v


# foo is only used for option 2 step in plotWindow() but unfortunately must
# be global or it cannot be pickled for parallel operation.

def foo(n,h,p): return((n, gpsConnection(h,p).getGPS()))

#########################  RCmanager class and  Main  Window     ######################### 

# NOT SURE IF THIS SHOULD BE A CLASS OBJECT. THERE WILL ONLY BE ONE INSTANCE.

class RCmanager():
   def __init__(self, w, dr):
      """RC Management main control window and parameters."""

      # Initial default parameters. Could save last on exit and reload ?
      self.ty   = 'stadium2'    # zone type
      self.fleets   = FLEETS   # FleetList
      self.fl   = self.fleets[0]                # default fleet
      self.dc   = 'race 1'     # description

      #         position below means a gpsPos object.
      self.RC   = gpsPos(44.210171667,-76.51047667) # RC position (default Pen. shoal)
      self.S    = gpsPos(0,0)  # start line center position
      self.M    = gpsPos(0,0)  # windward mark position 

      self.cl   = 1.0          # course length (nm)
      self.ax   = 240          # course bearing (degrees)
      self.ll   = 100          # start line length (m)
      self.tt   = 0            # target start time
      
      #Zone Type Obj
      if   self.ty == 'stadium'  :  self.ZTobj = stadium.stadium() 
      elif self.ty == 'stadium2' :  self.ZTobj = stadium2.stadium2()      
      elif self.ty == 'NoCourse' :  self.ZTobj =    NoCourse()      
      else                       :  self.ZTobj =    NoCourse()      

      w.wm_title("RC Management")
      #w.bind('<Return>', (lambda event, e=ents: readRaceWindow(e)))   
      w.bind('<Return>', (lambda event : self.readRCWindow()))   
      
      # NB writeRCWindow and readRCWindow MUST be with this co-ordinated if fields are changed!!!

      row = tkinter.Frame(w)
      tkinter.Label(row, width=10, text="Zone Type", anchor='w').pack(side=tkinter.LEFT)
      self.zoneChoice = Drop(row, options=['stadium', 'stadium2', 'NoCourse'], default = 0)
      But(row,  text='calc   \n  using',           command=self.calc)
      self.calcChoice = Drop(row, options=['RC & axis', 'RC & mark', 'start center\n& mark'])
      row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

      row = tkinter.Frame(w)
      tkinter.Label(row, width=10, text="fleet", anchor='w').pack(side=tkinter.LEFT)
      self.fleetChoice = Drop(row, options=self.fleets, default = 0)
      row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

      fldLabels = [
                       'description', 
                       'RC       latitude',
                       'RC      longitude',
                       'start center lat.', 
                       'start center lon.',
                       'mark 1 latitude',  
                       'mark 1 longitude', 
                       'length (nm)', 
                       'axis (degrees)',   
                       'start line length (m)',
                       'Target start time']
      entries = []
      i = 0
      for f in fldLabels:
         row = tkinter.Frame(w)
         lab = tkinter.Label(row, width=15, text=f, anchor='w')
         #if calculated[i]:
         e = tkinter.Entry(row, bg = "white")
         #else:
         #   e = tkinter.Entry(row, bg = "grey")
         row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
         lab.pack(side=tkinter.LEFT)
         e.pack(side=tkinter.RIGHT, expand=tkinter.YES, fill=tkinter.X)
         entries.append((e))
         i += 1
      self.ents = entries
     
      But(w,  text='get RC GPS',                       command=self.getRCgps)
      But(w,  text='distribute',     command=(lambda : dr.distribute(self.makezoneObj())))
      But(w,  text='update\nStatus', command=(lambda : self.updateStatus(w, dr.distributionRecvd())))
      But(w, text='extra',           command=(lambda : extraWindow(self, dr)))

      self.writeRCWindow()

      self.readgpsList()  # this could be in an extra object
      self.readBoatList() # only current fleet


   def parms(self):  
      self.readRCWindow() # Ensure using current screen values.

      return {'ty':self.ty, 'fl':self.fl, 'dc':self.dc, 
          'RC.lat' : self.RC.lat, 'RC.lon' : self.RC.lon, 
           'S.lat' : self.S.lat,   'S.lon' : self.S.lon,
           'M.lat' : self.M.lat,   'M.lon' : self.M.lon,
          'cl':self.cl, 'ax':self.ax, 'll':self.ll, 'tt':self.tt}


   def parmsTuple(self):  
      return (self.ty, self.fl, self.dc, self.RC.lat,  self.RC.lon, self.S.lat,  self.S.lon, 
              self.M.lat, self.M.lon, self.cl,  self.ax,  self.ll,  self.tt)

   #def ty(self):     return self.ty

   def setparms(self, nw):
      self.ty   = nw['ty']  
      self.fl   = nw['fl']        
      self.dc   = nw['dc']        

      self.RC   = gpsPos(nw['RC.lat'],  nw['RC.lon'])
      self.S    = gpsPos(nw[ 'S.lat'],  nw[ 'S.lon'])
      self.M    = gpsPos(nw[ 'M.lat'],  nw[ 'M.lon'])

      self.cl   = nw['cl']
      self.ax   = nw['ax']
      self.ll   = nw['ll']
      self.tt   = nw['tt']


   def writeRCWindow(self):
      """re-write screen with current parameters."""
      
      self.zoneChoice.set(self.ty)
      self.fleetChoice.set(self.fl)

      prms = self.parmsTuple() # includes ty and fl alraedy set above

      if not len(self.ents) == (len(prms) - 2):
         raise Exception('Something is wrong. length of entries is not equal length of parms.')

      # (dc, RC.lat, RC.lon, S.lat, S.lon, M.lat, M.lon, cl, ax, ll, tt)

      def refresh(e, l, v):        # entry, length, string
         self.ents[e].delete(0, tkinter.END)
         self.ents[e].insert(l, v)
     
      for i in range (0, len(self.ents)): refresh(i, 10, str(prms[i+2]))


   def readRCWindow(self):
      """Update current parameters from screen."""
      
      self.ty = self.zoneChoice.get()
      self.fl = self.fleetChoice.get()
      self.readBoatList() # new fleet

      self.dc = str(self.ents[0].get())
      self.RC = gpsPos(float(self.ents[1].get()),  float(self.ents[2].get()))
      self.S  = gpsPos(float(self.ents[3].get()),  float(self.ents[4].get()))
      self.M  = gpsPos(float(self.ents[5].get()),  float(self.ents[6].get()))
      self.cl = float(self.ents[7].get()) 
      self.ax = float(self.ents[8].get()) 
      self.ll = float(self.ents[9].get()) 
      self.tt = float(self.ents[10].get()) 

   def getRCgps(self):
      """Update RC position from gps and write to screen."""

      self.RC = gpsConnection(GPS_HOST, GPS_PORT).getGPS()
      if self.RC == None :
         self.RC   = gpsPos(90.0, 0.0)  # this is really an error condition
         logging.info('attempted gpsd connection '   + str(GPS_HOST) + ':' +  str(GPS_PORT))
         logging.info('gpsd connection failed. No RC automatic position available.')
      self.writeRCWindow()

   def calc(self):
      """Calculate race parameters""" 

      ch = self.calcChoice.get()

      if   ch == 'RC & axis'            : self.calcA()
      elif ch == 'RC & mark'            : self.calcM()
      elif ch == 'start center\n& mark' : self.calcS()
      else :
         raise Exception('Something is wrong. calcChoice not recognized.')

   def calcA(self):
      """
      Calculate race parameters using axis and RC position as The right end of start line. 
      Perp to axis and line length are used to get the center of the start line; 
      axis and course length, to get mark.
      """
      self.readRCWindow() # re-read parameters from screen data
      
      perp = (self.ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line

      # center of starting line from RC position (right end), perp, and line length
      #  half line length in nm. 1 nm = 1852 m
      self.S = gpsPos.move(self.RC, perp, self.ll / (2 * 1852))

      # windward mark from center of starting line, axis, and course length   
      self.M = gpsPos.move(self.S, self.ax, self.cl)
      
      self.writeRCWindow() # re-write screen with new parameters

   def calcM(self):
      """
      Calculate race parameters using RC position and mark M to get course length.
      Aprox axis, then adjust axis (ax) by a correction angle for S to M rather than RC to M.
      Assuming RC is on starboard end of line. Then calculate as in calcA (excluding M).
      """
      self.readRCWindow() # re-read parameters from screen data
      
      self.cl = self.RC.nm(self.M)  # course length using RC to M.

      correction = math.degrees(math.asin(self.ll /(2* 1852 * self.cl)))
      #logging.debug('correction' + str(correction))
      h   = gpsPos.heading(self.RC, self.M)

      #now ax is bearing RC to point 1/2 line length right of M, RC on starboard end of line.
      self.ax  = (h + correction)  % 360 #

      perp = (self.ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line

      # center of starting line from RC position (right end), perp, and line length
      #  half line length in nm. 1 nm = 1852 m
      self.S = gpsPos.move(self.RC, perp, self.ll / (2 * 1852))
      
      self.writeRCWindow() # re-write screen with new parameters


   def calcS(self):
      """
      Calculate race parameters using center of start line and mark M to 
      get course length (cl), axis (ax) , and RC position on starboard end of line.
      """
      self.readRCWindow() # re-read parameters from screen data
      
      self.cl = self.S.nm(self.M)  # course length using S to M.

      self.ax = gpsPos.heading(self.S, self.M)

      perp = (self.ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line
      
      self.RC = gpsPos.move(self.S, perp, -self.ll / (2 * 1852))
      
      self.writeRCWindow() # re-write screen with new parameters


   ###### following methods COULD BE in a separate 'extra' object ######

   def updateStatus(self, w, revd):
      # if w is not None: w.destroy()  Do not destroy when button is on main window
     
      t = tkinter.Toplevel(w)
      t.wm_title("Update Status")
      logging.debug('revd:')
      logging.debug(str(revd))

      for f in revd :
         row = tkinter.Frame(t)
         lab = tkinter.Label(row, width=30, text=f + ' ' + str(revd[f]), anchor='w')
         row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
         lab.pack(side=tkinter.LEFT)

      if  self.BoatList is None : 
         bl = 'boat list not available.'
      else :
         bl = ''
      
      row = tkinter.Frame(t)
      lab = tkinter.Label(row, width=30, text=' Not Updated: ' + bl, anchor='w')
      row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=2)
      lab.pack(side=tkinter.LEFT)

      if (self.BoatList is not None) : 
         for f in self.BoatList :
            if f not in  revd :
               row = tkinter.Frame(t)
               lab = tkinter.Label(row, width=30, text='*** ' + f , anchor='w')
               row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
               lab.pack(side=tkinter.LEFT)


   def readBoatList(self, w=None):
      if w is not None: w.destroy()

      logging.info('readBoatList()   FLEETS/' + self.fl + '/BoatList.txt')
      try : 
         with open('FLEETS/' + self.fl + '/BoatList.txt') as f: bl = f.read().splitlines()
         bl = [b.strip() for b in bl]
      except :
         bl = None   

      logging.info('self.BoatList = bl is ' + str(bl))
      self.BoatList = bl


   def writeRaceFile(self, w=None, filename = None):
      if w is not None: w.destroy()  # destroy calling menu so it does not have to be manually closed

      self.readRCWindow() #sync parameters from screen

      if filename is None : 
         filename =  filedialog.asksaveasfile(mode="w",  defaultextension=".raceParms",
             initialdir = "RACEPARMS/", title = "enter file name to save",
             filetypes = (("race parameters","*.raceParms"),("all files","*.*")))

      if filename is None:  return   # i.e. cancel clicked in dialog

      filename.close() # use json.dump() below, but above opened the file
      filename = str(filename.name)

      try : 
         Race = self.parms()
         Race.update( self.ZTobj.parms() )
    
         with open(filename, "w") as f:  json.dump(Race, f)
      except :
         raise Exception('error writing race parameters to file ' + str(filename))



   def readRaceFile(self, w=None, filename = None):
      if w is not None: w.destroy()

      if filename is None : 
         filename =  filedialog.askopenfilename(initialdir = "RACEPARMS/",
                            title = "choose file",
                        filetypes = (("race parameters","*.raceParms"),("all files","*.*")))

      if filename is "":  return   # i.e. cancel clicked in dialog

      with open(filename) as f:  RF = json.load(f)   

      try : 
         self.setparms(RF)        # only uses RC parms
         self.ZTobj.setparms(RF)  # only uses zone parms
      except :
         raise Exception('error defining race parameters from file ' + filename)

      self.writeRCWindow() #sync screen with new parameters



   def gpsWindow(self, w=None):   
      if w is not None: w.destroy()

      t = tkinter.Toplevel()
      t.wm_title("Other GPS Status    lat    lon")

      # THIS WOULD BE FASTER BUT NEEDS gpsd TO HANDLE MULTIPLE CONNECTIONS
      ## Put next in a parallel loop, since each must wait for timeout on many that 
      ## are out of range
      #pts = Parallel(n_jobs=len(gpsList))(delayed(foo)(f[0], f[1], f[2]) for f in gpsList)
      #
      #for pt in pts :
      #   row = tkinter.Frame(t)
      #   if pt[1] is None : 
      #      logging.info(pt[0] + '       no gps connection.' )
      #      lab = tkinter.Label(row, width=30, text=pt[0] + '   *****' , anchor='w')
      #   else :
      #      logging.info(pt[0] + ' ' + str(pt[1].lat) + ' ' +str(pt[1].lon))
      #      lab = tkinter.Label(row, width=50, text=pt[0] + '   ' + 
      #                  str(pt[1].lat) + '  '  + str(pt[1].lon) , anchor='w')
      #   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
      #   lab.pack(side=tkinter.LEFT)


      for f in self.gpsList :
         row = tkinter.Frame(t)
         logging.info('gpsWindow connect ' + f[0] +' ' + f[1] +':'+ f[2])
         pt = gpsConnection(f[1], f[2]).getGPS()
         if pt is None : 
            logging.info('       no gps connection.' )
            lab = tkinter.Label(row, width=30, text=f[0] + '   *****' , anchor='w')
         else :
            logging.info('       ' + str(pt.lat) + ' ' +str(pt.lon))
            lab = tkinter.Label(row, width=50, text=f[0] + '   ' + 
                        str(pt.lat) + '  '  + str(pt.lon) , anchor='w')
         row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
         lab.pack(side=tkinter.LEFT)

   
   def readgpsList(self, w=None):
      if w is not None: w.destroy()

      self.gpsList = []
      try : 
         with open("gpsList.txt") as f:
            for i in f.readlines():
               l =  i.split()
               self.gpsList.append( (l[0], l[1], l[2]) )
      except :
         self.gpsList = None   


   def plotWindow(self, x=None, option=1):
      """Plot is based on S, M positions and line length, not  cl. The object state is not changed."""
      import math

      if x is not None: x.destroy()

      #self.readRCWindow() #sync parameters from screen (should not be needed)

      t = tkinter.Toplevel()
      t.wm_title(self.fl + '  ' + self.dc)

      canvas_width  = 400
      canvas_height = 400
      w = tkinter.Canvas(t,  width=canvas_width, height=canvas_height)
      w.pack()
      w.create_text(canvas_width / 2,     2,            text="N")
      w.create_text(canvas_width / 2, canvas_height-2,  text="S")
      w.create_text(canvas_width,     canvas_height /2, text="E")
      w.create_text(     0,           canvas_height /2, text="W")

      # This cross should be right angles in the center, other than for
      # any difference in the screen horizontal vs vertical per pixael.
      #w.create_line(0, 0, canvas_width, canvas_height, fill="#476042", width=1)
      #w.create_line(0, canvas_height, canvas_width, 0, fill="#476042", width=1)

      #  plot coordinates need to be done in (scaled) nm. Tried to do them in
      #  degrees (gps coordinates) but there is too much skew because a degree
      #  longitude is too much less distance than a degree latitude.

      latScale = 60.0  #  nm per degree lat
      lonScale = 60.0 * math.cos(math.radians(self.RC.lat)) #   nm per degree long

      # self.cl /latScale  # course length in degrees (aprox )
      # self.cl   # course length in nm

      scale = 0.4 * canvas_height / self.cl #  pix/nm, course length is 0.4 of plot height

      #plot window top left is (0,0), bottom right is (canvas_height, canvas_width)
      # so +ve x is to right (as usual) but +ve y is down (not usual)
      # Use canvas center as start line center, so shift everything in degrees
      #   by start line cemter, that is subtract (Shift.lon, Shift.lat), 
      #  and then to plot shift to canvas center, that is add (x0, y0).
      Shift = self.S  # degrees lon and lat

      x0 = int(canvas_width  / 2) # pix
      y0 = int(canvas_height / 2) # pix

      # Start line center to mark
      # This is M as used for course calc, not current position of mark boat
      x = x0 + ((self.M.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
      y = y0 - ((self.M.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0
      w.create_line(x0, y0, x, y , fill="#476042", width=1)
      w.create_text(x, y, text="M")  # M position on plot

      # Indicate axis at mid point 
      x = x0 + ((self.M.lon - Shift.lon) * lonScale * scale / 2) 
      y = y0 - ((self.M.lat - Shift.lat) * latScale * scale / 2)
      w.create_text(x, y, text=str(int(self.ax))+'T')  # ax on plot

      #w.create_line(0, 0, 50, 20,      fill="#476042", width=3)

      # start line center (0,0)  to RCself.
      # This is RC as used for course calc, not current position of mark boat
      x = x0 + ((self.RC.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
      y = y0 - ((self.RC.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0

      w.create_line(x0, y0, x, y, fill="#476042", width=3)
      w.create_text(x, y, text="RC") # RC position on plot

      # other half of start line to pin
      x = x0 - ((self.RC.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
      y = y0 + ((self.RC.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0
      w.create_line(x0, y0, x, y, fill="#476042", width=3)

      if option == 2 :
         # NB this does not work correctly (I think  because gpsd use a global stream).
         # This is actual RC from current gps
         p = gpsConnection(GPS_HOST, GPS_PORT).getGPS()
         x = x0 + ((p.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
         y = y0 - ((p.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0
         w.create_text(x, y, text="<RC>") # actual RC gps position on plot

         # Put next in a parallel loop, since each must wait for timeout on many that 
         # are out of range

         # n_jobs = number of processes 
         pts = Parallel(n_jobs=len(self.gpsList))(delayed(foo)(f[0], f[1], f[2]) for f in self.gpsList)

         for p in pts :
           if p[1] is not None : 
               x = x0 + ((p[1].lon - Shift.lon) * lonScale * scale) 
               y = y0 - ((p[1].lat - Shift.lat) * latScale * scale) 
               w.create_text(x, y, text='<' +p[0] +'>') # put gps position on plot
               logging.debug(p[0] +'  ' + str(p[1].lat) + ' ' + str(p[1].lon))
           else :
               logging.debug(p[0] +'  None' )
               pass

         #pts = []
         #for f in self.gpsList :
         #       p = gpsConnection(f[1], f[2]).getGPS()
         #   if p is not None : 
         #      pts.append((f[0], p))
         #   else :
         #      pass
         #
         #for p in pts :
         #      x = x0 + ((p[1].lon - Shift.lon) * lonScale * scale) 
         #      y = y0 - ((p[1].lat - Shift.lat) * latScale * scale) 
         #      w.create_text(x, y, text='<' +p[0] +'>') # put gps position on plot



   def makezoneObj(self):
      """
      Generate the zoneObj for distribution to boats for calculating LED signals.
      
      Part of the final zoneObj passed to boats is calculated by RCmanager.makezoneObj()
      and part by ZTobj.makezoneObj().
      """ 


      # Ensure parameters  correspond to current screen values.
      self.readRCWindow() # this shoud be automatic and not needed !!!

      # y = a + b * x
      # b = (y_1 - y_2) / (x_1 - x_2)
      # a = y_1 - b * x_1
      
      # 0 or 180 axis would give infinite slope is x is longitude, 
      # so depending on the axis treat domain as longitude (dom=True)
      # or treat domain as latitude (dom=False)
      if        45 <= self.ax <= 135 : dom = True
      elif     225 <= self.ax <= 315 : dom = True
      else                      : dom = False

      if dom :
         if   45 <= self.ax <= 135  : LtoR = False
         else                       : LtoR = True  # 225 <= self.ax <= 315 
      else :
         if   135 <= self.ax <= 225 : LtoR = False 
         else                       : LtoR = True #(315 <= self.ax <= 360) | (0 <= self.ax <= 45)

      # cl, M and S are not needed the for stadiumBT calculations but
      #  are nice for debugging.
      
      distributionTime = time.strftime('%Y-%m-%d_%H:%M:%S_%Z')

      # left and right looking up the course, from race committee (RC) to windward mark (M)

      rRC = {
         'cid'       : self.fl + '-' + self.dc + '-' +  distributionTime,
         'courseDesc'       : self.dc,
         'zoneType'         : self.ty,
         'fleet'            : self.fl,
         'distributionTime' : distributionTime,
         'length' :  self.cl,  # course length
         'axis'   :  self.ax,  # axis (degrees)
         'S'      :  (self.S.lat, self.S.lon),  # position of center of start line
         'M'      :  (self.M.lat, self.M.lon),  # position of windward mark
         'dom'    :  dom, # domain, function of long (true) or latitude (False)
         'LtoR'   :  LtoR, # True if bounds increase left to right
         }

      r = self.ZTobj.makezoneObj(rRC)  # this adds zone specific parts and returns complete r

      if not self.ZTobj.verifyzoneObj(r) :
         raise Exception('error verifying zoneObj.')
         return None
      else :
         return r

#########################       Extra  Window            ######################### 
######################### (possibly be an object too?)   ######################### 

def extraWindow(RCobj, dr):
   t = tkinter.Toplevel()
   t.wm_title("Extra Options")

   But(t, text='Set Zone\nType Parms',   command=(lambda : RCobj.ZTobj.edit(t)))
   But(t, text='Save\nRace Parms',       command=(lambda : RCobj.writeRaceFile(t)))
   But(t, text='Load Saved\nRace Parms', command=(lambda : RCobj.readRaceFile(t)))
   But(t, text='Re-read\n BoatList',     command=(lambda : RCobj.readBoatList(t)))
   But(t, text='plot',                   command=(lambda : RCobj.plotWindow(t)))
   But(t, text='plot with\n boats',      command=(lambda : RCobj.plotWindow(t, 2)))
   But(t, text='more...',                command=(lambda : extraMoreWindow(t, RCobj, dr)))




######################### Extra Options  'More...'  Window ######################### 
######################### (possibly be an object too?)   ######################### 

def extraMoreWindow(w, RCobj, dr):
   w.destroy()

   def debugWindow(w):
     w.destroy()

     print('debugWindow')
     print('RCobj.parms')
     #for f in (RCobj.cl, RCobj.ax, RCobj.ll, RCobj.RC, RCobj.S, RCobj.M, RCobj.tt): print(f)
     print(RCobj.parms())
     print()
     print('Zone parms:')
     print(RCobj.ZTobj.parms())
     print('zoneObj')
     dr.prt()
     #print('threads')
     #print(str(threading.enumerate()))
     print('dr.distributionRecvd()')
     print(dr.distributionRecvd())

   t = tkinter.Toplevel()
   t.wm_title("More Extra Options")

   But(t, text='other\n GPS',       command=(lambda : RCobj.gpsWindow(t)))
   But(t, text='Re-read\n gpsList', command=(lambda : RCobj.readgpsList(t)))
   But(t, text='debugInfo',         command=(lambda : debugWindow(t)))


