# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Object for overall race management, not specific to a zoneType."""

import logging
import json
import tkinter
from tkinter import filedialog
import time
import gpsd
import math

from joblib import Parallel, delayed # for parallel requests to remote gps

from gpsPos import gpsPos
from gpsPos import gpsConnection

import stadium

config = json.load(open('GPSconfig'))   
GPS_HOST = config['GPS_HOST']      # typically "127.0.0.1"
GPS_PORT = int(config['GPS_PORT']) # 2947 is default


# position below means a gpsPos object.
# left and right looking up the course, from race committee (RC) to windward mark (M)
# these global variables should have values as displayed on RaceWindow screen

# set initial default race parameters
#  Could save last on exit and reload ?

ty   = 'stadium'    # zone type
fl   = 'no fleet'   # fleet
dc   = 'race 1'     # description

RC   = gpsPos(44.210171667,-76.51047667) # RC position (default Pen. shoal)
S    = gpsPos(0,0)  # start line center position
M    = gpsPos(0,0)  # windward mark position 

cl   = 1.0          # course length (nm)
ax   = 240          # course bearing (degrees)
ll   = 100          # start line length (m)
tt   = 0            # target start time

#def makeZoneTypeObj():       #Zone Type Obj
if   ty == 'stadium' :  ZTobj = stadium.stadium() 
elif ty == 'NoCourse':  ZTobj =    NoCourse()      


#########################    Utility  Functions     ######################### 

def But(w, text='x', command='') :
   b = tkinter.Button(w, text=text,  command=command)
   b.pack(side=tkinter.LEFT, padx=5, pady=5)
   return(b)

def Drop(w, options=['zero', 'one', 'two'], default=0) :
   v = tkinter.StringVar(w)
   v.set(options[default]) 
   b = tkinter.OptionMenu(w, v, *options)
   b.pack()
   return v


#########################    Main  Window  Functions     ######################### 

def getRCgps():
   # update global RC and write to screen
   global  RC
   RC = gpsConnection(GPS_HOST, GPS_PORT).getGPS()
   if RC == None :
      RC   = gpsPos(90.0, 0.0)  # this is really an error condition
      logging.info('attempted gpsd connection '   + str(GPS_HOST) + ':' +  str(GPS_PORT))
      logging.info('gpsd connection failed. No RC automatic position available.')
   writeRCWindow()

#################### MAKE THIS A CLASS AS FOR STADIUM  ####################
def defnRCWindow(w, dr):
   # fields on RC Window main page
   # NB This functionand the next two (writeRCWindow and readRCWindow) MUST be
   #    co-ordinated if fields are changed !!!
   global ents, zoneChoice

   w.wm_title("RC Management")
   #w.bind('<Return>', (lambda event, e=ents: readRaceWindow(e)))   
   w.bind('<Return>', (lambda event : readRCWindow()))   
   
   row = tkinter.Frame(w)
   lab = tkinter.Label(row, width=15, text="Zone Type", anchor='w')
   lab.pack(side=tkinter.LEFT)
   zoneChoice = Drop(row, options=['stadium', 'NoCourse'], default = 0)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   fldLabels = [
 	'fleet', 
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
   ents = entries
  
   But(w,  text='get RC GPS',     command=(lambda : getRCgps()))
   But(w,  text='calc using\n RC & axis',           command=calcA)
   But(w,  text='calc using\n RC & mark',           command=calcM)
   But(w,  text='calc using start\n center & mark', command=calcS)
   But(w,  text='distribute',  command=(lambda :  dr.distribute(makezoneObj())))
   But(w,  text='update\nStatus',
                      command=(lambda : updateStatus(w, dr.distributionRecvd())))
   But(w, text='extra',        command=(lambda : extraWindow()))

   writeRCWindow()


def writeRCWindow():
   # re-write screen with current  global variables
   global ents
   
   zoneChoice.set(ty)

   for i in range (0, len(ents)):
      ents[i].delete(0, tkinter.END)

   i = 0
   for v in (fl, dc, RC.lat, RC.lon, S.lat, S.lon, M.lat, M.lon, cl, ax, ll, tt):
      ents[i].insert(10, str(v))
      i += 1


def readRCWindow():
   # update globals from screen
   # using global ents and zoneChoice for entries
   global  ty, fl, RC, S, M, dc, ty, cl, ax, ll, tt
   
   ty = zoneChoice.get()

   fl = str(ents[0].get())
   dc = str(ents[1].get())
   RC = gpsPos(float(ents[2].get()),  float(ents[3].get()))
   S  = gpsPos(float(ents[4].get()),  float(ents[5].get()))
   M  = gpsPos(float(ents[6].get()), float(ents[7].get()))
   cl = float(ents[8].get()) 
   ax = float(ents[9].get()) 
   ll = float(ents[10].get()) 
   tt = float(ents[11].get()) 

#  THIS IS NOT CLEAN YET. NEED PARTS FROM STADIUM AND PARTS FROM RC
def makezoneObj():
   # This  syncronizes globals dist, generates zoneObj, calls distribute
   # info to pass to stadiumBT (boat gadget) for calculations.
   # Info for stadiumBT is all in gps positions as that is the best for the
   # boats' calculation of what indicators should go on.
   # The same info is used by plot but is convert to nm in plot.
      
   # base on current screen values so ensure correct values in globals
   readRCWindow() 

   # y = a + b * x
   # b = (y_1 - y_2) / (x_1 - x_2)
   # a = y_1 - b * x_1
   
   # 0 or 180 axis would give infinite slope is x is longitude, 
   # so depending on the axis treat domain as longitude (dom=True)
   # or treat domain as latitude (dom=False)
   if        45 <= ax <= 135 : dom = True
   elif     225 <= ax <= 315 : dom = True
   else                      : dom = False

   # These are positions at intersection of the start line extension and one of
   # the lines parallel to axis used for switching indicators (LEDs) on boats.

   w = ZTobj.sw / 1852  # stadium width in nm
   perp = (ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line.
   #                         This is bearing used for extensions of starting line

   # Two positions on axis (S and M) give slope b.
   if dom : b = (M.lat - S.lat) / (M.lon - S.lon)
   else   : b = (M.lon - S.lon) / (M.lat - S.lat)

   if dom :
      if   45 <= ax <= 135 : LtoR = False
      else                 : LtoR = True  # 225 <= ax <= 315 
   else :
      if   135 <= ax <= 225 : LtoR = False 
      else                  : LtoR = True #(315 <= ax <= 360) | (0 <= ax <= 45)
  
   def a(p):
      if dom : a = p.lat - b * p.lon 
      else   : a = p.lon - b * p.lat
      return a

   # cl, M and S are not needed in the for stadiumBT calculations but
   #  are nice for debugging.
   
   courseDesc = 'arbitrary'
   distributionTime = time.strftime('%Y-%m-%d_%H:%M:%S_%Z')
   cid = fl + '-' + dc + '-' +  distributionTime
   
   r = {
      'cid'       : cid,
      'courseDesc'       : dc,
      'zoneType'         : 'stadium',
      'distributionTime' : distributionTime,
      'length' :  cl,  # course length
      'axis'   :  ax,  # axis (degrees)
      'S'      :  (S.lat, S.lon),  # position of center of start line
      'M'      :  (M.lat, M.lon),  # position of windward mark
      'dom'    :  dom, # domain, function of long (true) or latitude (False)
      'LtoR'   :  LtoR, # True if bounds increase left to right
      'b'      :   b,  # slope constant
      'boundL' :  a(gpsPos.move(S, perp,   w/2 )),                  # constant a for left  boundary
      'boundR' :  a(gpsPos.move(S, perp,  -w/2 )),                  # constant a for right boundary
      'warnL'  :  a(gpsPos.move(S, perp,  (w/2 - ZTobj.wn/1852) )), # constant a for left  warning
      'warnR'  :  a(gpsPos.move(S, perp, -(w/2 - ZTobj.wn/1852) )), # constant a for right warning
      'centerL':  a(gpsPos.move(S, perp,  ZTobj.cc/(2*1852) )),     # constant a for left  center
      'centerR':  a(gpsPos.move(S, perp, -ZTobj.cc/(2*1852) ))      # constant a for right center
      }

   #check
   if r['dom'] :
      if        not LtoR : 
         if not ( r['boundR']  < r['warnR'] < r['centerR']  <
	          r['centerL'] < r['warnL'] < r['boundL'] ) :
	          raise ValueError("something is messed up in 45 <= ax <= 135.")
      elif       LtoR : 
         if not ( r['boundL']  < r['warnL'] < r['centerL']  <
	          r['centerR'] < r['warnR'] < r['boundR'] ) :
	          raise ValueError("something is messed up in 225 <= ax <= 315.")
      else :  raise ValueError("something is messed up in dom=True.")
   
   if not  r['dom'] :
      if        not LtoR : 
         if not ( r['boundR']  < r['warnR'] < r['centerR']  <
	          r['centerL'] < r['warnL'] < r['boundL'] ) :
	          raise ValueError("something is messed up in 135 <= ax <= 225.")
      elif     LtoR : 
         if not ( r['boundL']  < r['warnL'] < r['centerL']  <
	          r['centerR'] < r['warnR'] < r['boundR'] ) :
	          raise ValueError("something is messed up in (315 <= ax <= 360) | (0 <= ax <= 45).")
      else :  raise ValueError("something is messed up in dom=False.")

   return r

def calcA():
   # calculate race parameters using axis,
   #   RC position as right end of start line, perp to axis and line length to get center 
   #   of start line; axis and  course length, to get mark;
   #   axis, stadium width, and warning width to get boundaries and warning lines;
   #   axis, center of start, and center width to get center indicator lines.

   global  S, M

   readRCWindow() # re-read current global variables from screen data
   
   perp = (ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line

   # center of starting line from RC position (right end), perp, and line length
   #  half line length in nm. 1 nm = 1852 m
   S = gpsPos.move(RC, perp, ll / (2 * 1852))

   # windward mark from center of starting line, axis, and course length   
   M = gpsPos.move(S, ax, cl)
   
   writeRCWindow() # re-write screen with current globals

def calcM():
   # calculate race parameters using RC position and mark M to get course length, aprox axis, then adjust
   #   axis (ax) by a correction angle for S to M rather than RC to M,
   #   assuming RC on starboard end of line. Then calculate as in calcA, excluding M. 

   global  ax, S, cl

   readRCWindow() # re-read current global variables from screen data
   
   cl = RC.nm(M)  # course length using RC to M.

   correction = math.degrees(math.asin(ll /(2* 1852 * cl)))
   #logging.debug('correction' + str(correction))
   h   = gpsPos.heading(RC, M)

   #now ax is bearing RC to point 1/2 line length right of M, RC on starboard end of line.
   ax  = (h + correction)  % 360 #

   perp = (ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line

   # center of starting line from RC position (right end), perp, and line length
   #  half line length in nm. 1 nm = 1852 m
   S = gpsPos.move(RC, perp, ll / (2 * 1852))
   
   writeRCWindow() # re-write screen with current globals


def calcS():
   # calculate race parameters using center of start line and mark M to 
   #  get course length (cl), axis (ax) , and RC position on starboard end of line.

   global  ax, RC, cl

   readRCWindow() # re-read current global variables from screen data
   
   cl = S.nm(M)  # course length using S to M.

   ax = gpsPos.heading(S, M)

   perp = (ax - 90 ) % 360 # bearing RC to pin, RC on starboard end of line
   
   RC = gpsPos.move(S, perp, -ll / (2 * 1852))
   
   writeRCWindow() # re-write screen with current globals


#########################       Extra  Window            ######################### 

def zoneTypeParms(w):
   global ZTobj
   w.destroy()
   ZTobj.edit()


def writeRaceFile(w, filename = None):
   # no calc
   w.destroy()

   readRCWindow() #sync globals from screen
   if filename is None : 
      #t = tkinter.Toplevel()
      filename =  filedialog.asksaveasfile(mode="w",  defaultextension=".raceParms",
          initialdir = "", title = "enter file name to save",
          filetypes = (("race parameters","*.raceParms"),("all files","*.*")))
   if filename is None: # i.e. cancel clicked in dialog
      return
   filename.close() # use json.dump() below, but above opened the file
   filename = str(filename.name)

   try : 
      Race = {'ty':ty,  'fl':fl, 'dc':dc, 'cl':cl, 'ax':ax, 'll':ll, 
      'RC.lat':RC.lat, 'RC.lon':RC.lon, 'S.lat':S.lat, 'S.lon':S.lon, 
      'M.lat':M.lat, 'M.lon':M.lon, 'tt':tt }
      
      Race.update( ZTobj.parms() )
 
      with open(filename, "w") as f:  json.dump(Race, f)
   except :
      raise Exception('error writing race parameters to file ' + str(filename))

def readRaceFile(w, filename = None):
   global  fl, dc, ty, cl, ax, ll, sw, RC, S, M, wn, cc, tt
   w.destroy()

   if filename is None : 
      filename =  filedialog.askopenfilename(initialdir = "",
                         title = "choose file",
                     filetypes = (("race parameters","*.raceParms"),("all files","*.*")))

   if filename is "": # i.e. cancel clicked in dialog
      return

   with open(filename) as f:  RF = json.load(f)   

   try : 
      fl   = RF['fl']
      dc   = RF['dc']
      ty   = RF['ty']
      cl   = RF['cl']
      ax   = RF['ax']
      ll   = RF['ll']
      RC   = gpsPos(RF['RC.lat'], RF['RC.lon'])
      S    = gpsPos(RF[ 'S.lat'], RF[ 'S.lon'])
      M    = gpsPos(RF[ 'M.lat'], RF[ 'M.lon'])
      tt   = RF['tt']

      ZTobj.setparms(RF)  # setparms() only uses 'sw', 'wn', 'cc'
   except :
      raise Exception('error defining race parameters from file ' + filename)

   writeRCWindow() #sync screen from globals



def readBoatList(w=None):
   global  BoatList

   if w is not None: w.destroy()

   try : 
      with open("BoatList") as f:  BoatList =  f.read().splitlines()
      BoatList = [b.strip() for b in BoatList]
   except :
      BoatList = None   

readBoatList()


# foo is only used for final option 2 step in plotWindow() but unfortunately must
# be global or it cannot be pickled.

def foo(n,h,p):
   return((n, gpsConnection(h,p).getGPS()))

def plotWindow(x, option=1):
   # note that plot is based on gps and line length. NOT YET. CHANGE USE OF cl
   #      Changing axis or course length  NOT YET. CHANGE USE OF cl without re-calc does not change plot.
   #      This allows manual override of gps point (ie don't re-calc)

   import math

   global  cl, ax, ll, sw, RC, S, M, wn, cc, tt

   x.destroy()

   readRCWindow() #sync globals from screen

   t = tkinter.Toplevel()
   t.wm_title(fl + '  ' + dc)

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
   lonScale = 60.0 * math.cos(math.radians(RC.lat)) #   nm per degree long

   #z    = cl /latScale  # course length in degrees (aprox )
   z    = cl   # course length in nm

   scale = 0.4 * canvas_height / z # pix/nm, course length is 0.4 of plot height

   #plot window top left is (0,0), bottom right is (canvas_height, canvas_width)
   # so +ve x is to right (as usual) but +ve y is down (not usual)
   # Use canvas center as start line center, so shift everything in degrees
   #   by start line cemter, that is subtract (Shift.lon, Shift.lat), 
   #  and then to plot shift to canvas center, that is add (x0, y0).
   Shift = S  # degrees lon and lat

   x0 = int(canvas_width  / 2) # pix
   y0 = int(canvas_height / 2) # pix

   # Start line center to mark
   # This is M as used for course calc, not current position of mark boat
   x = x0 + ((M.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
   y = y0 - ((M.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0
   w.create_line(x0, y0, x, y , fill="#476042", width=1)
   w.create_text(x, y, text="M")  # M position on plot

   # Indicate axis at mid point 
   x = x0 + ((M.lon - Shift.lon) * lonScale * scale / 2) 
   y = y0 - ((M.lat - Shift.lat) * latScale * scale / 2)
   w.create_text(x, y, text=str(int(ax))+'T')  # ax on plot

   #w.create_line(0, 0, 50, 20,      fill="#476042", width=3)

   # start line center (0,0)  to RC
   # This is RC as used for course calc, not current position of mark boat
   x = x0 + ((RC.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
   y = y0 - ((RC.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0

   w.create_line(x0, y0, x, y, fill="#476042", width=3)
   w.create_text(x, y, text="RC") # RC position on plot

   # other half of start line to pin
   x = x0 - ((RC.lon - Shift.lon) * lonScale * scale)  # pix, shifted by x0
   y = y0 + ((RC.lat - Shift.lat) * latScale * scale)  # pix, shifted by x0
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
      pts = Parallel(n_jobs=len(gpsList))(delayed(foo)(f[0], f[1], f[2]) for f in gpsList)

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
      #for f in gpsList :
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

def updateStatus(w, revd):
   
   t = tkinter.Toplevel(w)
   t.wm_title("Update Status")
   logging.debug('revd:')
   logging.debug(str(revd))

   for f in revd :
      row = tkinter.Frame(t)
      lab = tkinter.Label(row, width=30, text=f + ' ' + str(revd[f]), anchor='w')
      row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
      lab.pack(side=tkinter.LEFT)

   if  BoatList == None : 
      bl = 'boat list not available.'
   else :
      bl = ''
   
   row = tkinter.Frame(t)
   lab = tkinter.Label(row, width=30, text=' Not Updated: ' + bl, anchor='w')
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=2)
   lab.pack(side=tkinter.LEFT)

   if (BoatList != None) : 
      for f in BoatList :
         if f not in  revd :
            row = tkinter.Frame(t)
            lab = tkinter.Label(row, width=30, text='*** ' + f , anchor='w')
            row.pack(side=tkinter.TOP, fill=tkinter.X, padx=2, pady=0)
            lab.pack(side=tkinter.LEFT)


def extraWindow():
   t = tkinter.Toplevel()
   t.wm_title("Extra Options")

   But(t, text='Set Zone\nType Parms',   command=(lambda : zoneTypeParms(t)))
   But(t, text='Save\nRace Parms',       command=(lambda : writeRaceFile(t)))
   But(t, text='Load Saved\nRace Parms', command=(lambda : readRaceFile(t)))
   But(t, text='Re-read\n BoatList',     command=(lambda : readBoatList(t)))
   But(t, text='plot',                   command=(lambda : plotWindow(t)))
   But(t, text='plot with\n boats',      command=(lambda : plotWindow(t,2)))
   But(t, text='more...',                command=(lambda : extraMoreWindow(t)))

######################### Extra Options  'More...'  Window ######################### 

def gpsWindow(w):   
   w.destroy()

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


   for f in gpsList :
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


def readgpsList(w=None):
   global  gpsList

   if w is not None: w.destroy()

   gpsList = []
   try : 
      with open("gpsList") as f:
         for i in f.readlines():
            l =  i.split()
            gpsList.append( (l[0], l[1], l[2]) )
   except :
      gpsList = None   

readgpsList()


def extraMoreWindow(w):
   w.destroy()

   def debugWindow(w):
     w.destroy()

     print('globals')
     for f in (cl, ax, ll, RC, S, M, tt): print(f)
     print()
     print('Zone parms:')
     print(ZTobj.parms())
     print('zoneObj')
     dr.prt()
     print('threads')
     print(str(threading.enumerate()))
     #print('dr.distributionRecvd()')
     #print(dr.distributionRecvd())
     print('distribution.distRecvd')
     print(distribution.distRecvd)

   t = tkinter.Toplevel()
   t.wm_title("More Extra Options")

   But(t, text='other\n GPS',       command=(lambda : gpsWindow(t)))
   But(t, text='Re-read\n gpsList', command=(lambda : readgpsList(t)))
   But(t, text='debugInfo',         command=(lambda : debugWindow(t)))
