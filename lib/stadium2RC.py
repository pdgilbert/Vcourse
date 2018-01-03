# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Object for stadium2 race."""

import tkinter
from gpsPos import gpsPos

class stadium2():
   def __init__(self):

      # Initial default parameters. Could save last on exit and reload ?
      self.setparmsDefault()

      self.fldLabels = [
                       'stadium width (m)',                     
                       'warning width (m)',
                       'center width (m)']

   def parms(self):  return {'sw' : self.sw,  'wn' : self.wn,  'cc' : self.cc }
   def sw(self):     return self.sw
   def wn(self):     return self.wn
   def cc(self):     return self.cc

   def setparms(self, nw):
      # reset only if provided
      if 'sw' in nw : self.sw = nw['sw']  
      if 'wn' in nw : self.wn = nw['wn']        
      if 'cc' in nw : self.cc = nw['cc']        
  
   def setparmsDefault(self):
      self.sw   = 200   # stadium width (m)
      self.wn   = 20    # distance (m) from boundary at which warning is indicated
      self.cc   = 20    # width (m) around center axis where center is  indicated 

   def edit(self, w=None):
      if w is not None : w.destroy() # to destroy calling menu window

      def readEntries():
         self.sw = float(entries[0].get())
         self.wn = float(entries[1].get()) 
         self.cc = float(entries[2].get()) 
         t.destroy()

      t = tkinter.Toplevel()
      t.wm_title("Stadium2 Parameters")
      entries = []
      i = 0
      for f in self.fldLabels:
         row = tkinter.Frame(t)
         lab = tkinter.Label(row, width=15, text=f, anchor='w')
         e = tkinter.Entry(row, bg = "white")
         row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
         lab.pack(side=tkinter.LEFT)
         e.pack(side=tkinter.RIGHT, expand=tkinter.YES, fill=tkinter.X)
         entries.append((e))
         i += 1
      entries[0].insert(10, str(self.sw))
      entries[1].insert(10, str(self.wn))
      entries[2].insert(10, str(self.cc))
      b = tkinter.Button(t, text='save',  command=readEntries)
      b.pack(side=tkinter.RIGHT, padx=5, pady=5)

   def makezoneObj(self, r):
      """
      Add stadium2 specific parts to the zoneObj for distribution to boats for calculating LED signals.
      """
      LtoR = r["LtoR"]
      dom  = r["dom"]
      S    = r["S"]
      S    = gpsPos(S[0], S[1])
      M    = r["M"]
      M    = gpsPos(M[0], M[1])

      # y = a + b * x
      # b = (y_1 - y_2) / (x_1 - x_2)
      # a = y_1 - b * x_1

      # Use positions at intersection of the start line extension and one of
      # the lines parallel to axis used for switching indicators (LEDs) on boats.
     
      def a(p):
         if dom : a = p.lat - b * p.lon 
         else   : a = p.lon - b * p.lat
         return a

      # Two positions on axis (S and M) give slope b.
      if dom : b = (M.lat - S.lat) / (M.lon - S.lon)
      else   : b = (M.lon - S.lon) / (M.lat - S.lat)

      w = self.sw / 1852  # stadium width in nm

      perp = (r["axis"] - 90 ) % 360 # bearing RC to pin, RC on starboard end of line.
      #                         This is bearing used for extensions of starting line

      r.update( {
         'b'      :   b,                                              # slope constant
         'boundL' :  a(gpsPos.move(S, perp,   w/2 )),                 # constant a for left  boundary
         'boundR' :  a(gpsPos.move(S, perp,  -w/2 )),                 # constant a for right boundary
         'warnL'  :  a(gpsPos.move(S, perp,  (w/2 - self.wn/1852) )), # constant a for left  warning
         'warnR'  :  a(gpsPos.move(S, perp, -(w/2 - self.wn/1852) )), # constant a for right warning
         'centerL':  a(gpsPos.move(S, perp,  self.cc/(2*1852) )),     # constant a for left  center
         'centerR':  a(gpsPos.move(S, perp, -self.cc/(2*1852) ))      # constant a for right center
         } )

      return r


   def verifyzoneObj(self, r):
      """check zoneOb and return True or raise exceptions in which case nothing is returned."""

      LtoR = r["LtoR"]
      dom  = r["dom"]
      
      if dom :
         if        not LtoR : 
            if not ( r['boundR']  < r['warnR'] < r['centerR']  <
                                 r['centerL'] < r['warnL'] < r['boundL'] ) :
                                 raise ValueError("something is messed up in 45 <= ax <= 135.")
         elif       LtoR : 
            if not ( r['boundL']  < r['warnL'] < r['centerL']  <
                                 r['centerR'] < r['warnR'] < r['boundR'] ) :
                                 raise ValueError("something is messed up in 225 <= ax <= 315.")
         else :  
                                 raise ValueError("something is messed up in dom=True.")
      
      if not  dom :
         if        not LtoR : 
            if not ( r['boundR']  < r['warnR'] < r['centerR']  <
                                 r['centerL'] < r['warnL'] < r['boundL'] ) :
                                 raise ValueError("something is messed up in 135 <= ax <= 225.")
         elif     LtoR : 
            if not ( r['boundL']  < r['warnL'] < r['centerL']  <
                                 r['centerR'] < r['warnR'] < r['boundR'] ) :
                                 raise ValueError("something is messed up in (315 <= ax <= 360) | (0 <= ax <= 45).")
         else :  
                                 raise ValueError("something is messed up in dom=False.")

      return True
