# License GPL 2. Copyright Paul D. Gilbert, 2017
"""Object for stadium race."""

import tkinter


class stadium():
   def __init__(self):

      # Initial default parameters. Could save last on exit and reload ?
      self.sw   = 200          # stadium width (m)
      self.wn   = 20           # distance (m) from boundary at which warning is indicated
      self.cc   = 20           # width (m) around center axis where center is  indicated 

      self.fldLabels = [
                       'stadium width (m)',                     
                       'warning width (m)',
                       'center width (m)']

   def parms(self):  return {'sw' : self.sw,  'wn' : self.wn,  'cc' : self.cc }
   def sw(self):     return self.sw
   def wn(self):     return self.wn
   def cc(self):     return self.cc

   def setparms(self, nw):
      self.sw   = nw['sw']  
      self.wn   = nw['wn']        
      self.cc   = nw['cc']        
  

   def edit(self, w=None):
      if w is not None : w.destroy() # to destroy calling menu window

      def readEntries():
         self.sw = float(entries[0].get())
         self.wn = float(entries[1].get()) 
         self.cc = float(entries[2].get()) 
         t.destroy()

      t = tkinter.Toplevel()
      t.wm_title("Stadium Parameters")
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

