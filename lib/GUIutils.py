import tkinter

#########################    Utility  Functions     ######################### 

def But(w, text='x', command='') :
   b = tkinter.Button(w, text=text,  command=command)
   b.pack(side=tkinter.LEFT, padx=5, pady=5)
   return(b)

def Drop(w, options=['zero', 'one', 'two'], default=0, command=None, font=("Helvetica", 10)) :
   #command below needs to accept the selection, which is passed to it,
   # eg,  self.readRCWindow() will be passes (self, 'FX')
   v = tkinter.StringVar(w)
   v.set(options[default]) 

   if command is None : b = tkinter.OptionMenu(w, v, *options)
   else :               b = tkinter.OptionMenu(w, v, *options,  command=command)
   b.config(font=font)
   b.pack(side=tkinter.LEFT)
   #b.config(font=("Helvetica", 10)) does not reset, default on next call does the reset
   return v

def ROW(t, text, width=30, ebg=None, pad=5):
   #ebg None means no entry field, otherwise color of entry field bg.
   row = tkinter.Frame(t)
   lab = tkinter.Label(row, width=width, text=text, anchor='w')
   if ebg is None :
      e = None
   else :
      e = tkinter.Entry(row, bg = ebg)
      e.pack(side=tkinter.RIGHT, expand=tkinter.YES, fill=tkinter.X)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=pad, pady=pad)
   lab.pack(side=tkinter.LEFT)
   return e


# foo is only used for option 2 step in plotWindow() but unfortunately must
# be global or it cannot be pickled for parallel operation.

def foo(n,h,p): return((n, gpsConnection(h,p).getGPS()))


def tkWarning(text, w= None):
   if w is not None : w.destroy()
   logging.info('**** WARNING ***' + str(text))
   t = tkinter.Toplevel()
   t.wm_title("**** WARNING ***")
   row = tkinter.Frame(t)
   tkinter.Label(row, width=40, text=str(text), anchor='w').pack(side=tkinter.LEFT)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

