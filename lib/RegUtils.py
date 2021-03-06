# License GPL 2. Copyright Paul D. Gilbert, 2018
"""
This is the main code for the Gcheckout program.
"""

import tkinter
from tkinter import ttk
from tkinter import messagebox

import signal
import logging
import json
import sys # just for exit
import os  # just for mkdir and getcwd

from GUIutils import *
from CallOut import CallOut


################# pseudo DB ################
class syncdList():
    """
    Define and maintain a list with txtfile copy on change.
    The purpose of this is to be able to reload values on program restart.
    The values will be a list of unique entries.
    """
    def __init__(self, txtfile):
       self.txtfile  = txtfile
       
       try : 
          with open(self.txtfile) as f:  values =  f.read().splitlines()
          values = [b.strip()  for b in  values]
       except :
          values = []
       
       
       # insure unique sorted values
       values = list(set(values))
       values.sort()
       
       self.values  = values 
    
    def append(self, x) :
       """Add to the list and save."""
       self.values.append(x)
       self.values  = list(set(self.values))
       self.values.sort()
       self._save()
    
    def remove(self, x) :
       """Add to the list and save."""
       self.values  = list(set(self.values)) 
       if x in self.values : self.values.remove(x) # MESSAGE NOT IN??
       self._save()
    
    def _save(self) :
       try : 
          with open(self.txtfile, 'w') as f: 
               for g in self.values : f.write(str(g) + "\n")  # txt lines not json
       except :
          tkWarning("Failed saving " + txtfile)


##########    Utilities   ########### 


def BoatList(fl)   : return fleets[fl]['BoatList'].values

def checkedOut(fl) : return fleets[fl]['checkedOut'].values

def setAllRC(t=None): 
   # This is to all boats in all fleets by UDP !!
   if t is not None: t.destroy()

   for fl in fleetList:
      rc =  fl + "::" + str({x: fleets[fl][x] for x in ('RC_IP', 'RC_PORT')})
      logging.debug(rc)
      CallOut('all', 'setRC', conf=rc, timeout=20)

def setREG(t=None): 
   # This is to all by UDP !!
   if t is not None: t.destroy()

   #REG = ("10.42.0.254", 9006) # Gcheckout IP and port, should not be hard coded
   # This is also read in CallOut.py. It should probably only be done there, but
   # that will require changes in CallOut handling of txt in broadcast.
   path = './'
   with open(path + 'REGconfig','r') as f: config =  json.load(f)
   #REG = (config['REG_HOST'], config['REG_PORT'])

   CallOut('all', 'setREG', conf=config, timeout=20)


def updateBoatHostMap(bt, hn):
   """
   This is an overall dict, not by fleet, of {hn : bt} which get updated whenever there is a
   checkout or change. There is little attempt to insure accuracy as the list is not really needed,
   but it may be useful if a gizmo  goes missing. Entries are not deleted, only updated, so it
   will remain reasonably accurate even when gizmos are checked in.
   The map should be a bijection, but there is a small risk of duplicate sail numbers in
   different fleets, so hn is used as the key. 
   """
   global fleets
   fleets['BoatHostMap'].update({hn:bt})

   try : 
      with open('BoatHostMap.json', 'w') as f: json.dump(fleets['BoatHostMap'], f, indent=4)
   except :
      logging.info("Gcheckout failed to save BoatHostMap.json." )
      logging.info("BoatHostMap:" )
      logging.info(fleets['BoatHostMap'])

def newBoatSetup(bt, fl, hn, t=None):
   """
   Set BTconfig on an unassigned gizmo  and update files.
   Note args bt, fl, and hn come from the new boat dialog, so they need to
   be set in main window.
   This does "requetBTconfig" to a single boat, so BT calls back by tcp. 
   """
   global fleets, sailNumberChoice, fleetChoice, gizmo, unassignedGizmos
   if t is not None: t.destroy()

   # important to change BT first. 
   # If it fails then do not change unassignedGizmos, 'BoatList', ...  or gizmo cannot be contacted
   cf = {'BT_ID': bt, 'FLEET': fl, 'RC_IP': fleets[fl]['RC_IP'], 'RC_PORT': fleets[fl]['RC_PORT'] }
      
   logging.debug('in newBoatSetup cf '+ str(cf))
   conf = CallOut(hn, "requestBTconfig", conf=cf, timeout=10)
   logging.debug('conf '+ str(conf))

   if conf['hn'] is  None :    # no response
      tkWarning("gizmo not responding.\n %s number not added." % (bt))
      return None
   else:
      if bt in BoatList(fl): 
         tkWarning("%s is already in fleet %s.\nNot adding, but configuring new gizmo." % (bt, fl))
      else:
         fleets[fl]['BoatList'].append(bt)
         sailNumberChoice['values'] = BoatList(fl)

      gizmo.set(hn)
      unassignedGizmos.remove(hn)
      sailNumberChoice.set(bt)
      fleetChoice.set(fl)
      statusSet()

def rmBoat(bt, fl, t=None):
   """
   Remove bt, update files and unassign gizmo.
   Removing a boat without the gizmo responding causes complications in contacting 
   the gizmo. While it may be tempting to allow this, it is being prevented.
   """
   global fleets, sailNumberChoice, fleetChoice, gizmo, unassignedGizmos
   if t is not None: t.destroy()

   if bt not in BoatList(fl) :
      tkinter.messagebox.showinfo("Wrong fleet", "%s was not in fleet %s." % (bt, fl))
      return None

   r = callForBoat(bt, fl)

   if r['hn'] is None :  # no response
      tkWarning(bt + " gizmo is not responding.\nBoat is not being removed.")
      return None  
   else:
      unassignedGizmos.append(r['hn'])
      cf = {'BT_ID':'unassigned', 'FLEET':''}
      CallOut(r['hn'], "requestBTconfig", conf=cf, timeout=10)
      fleets[fl]['BoatList'].remove(bt)
      sailNumberChoice['values'] = BoatList(fl)
      sailNumberChoice.set('')
      fleetChoice.set('')
      gizmo.set('') 


def chgSail(bt, t=None):
   """Change a boats sail number."""
   # arg bt comes from change sail# dialog not main GUI
   global fleets, sailNumberChoice
   if t is not None: t.destroy()
   
   fl = fleetChoice.get()
   oldbt = sailNumberChoice.get() # use old for callout

   if bt in BoatList(fl): 
      tkWarning("%s is already in fleet %s\nNumber change not allowed." % (bt, fl))
      return None
   else:
      # important to change BT first. 
      # If it fails then do not changes 'BoatList' or gizmo cannot be contacted
      cf = {'BT_ID': bt, 'FLEET': fl, 'RC_IP': fleets[fl]['RC_IP'], 'RC_PORT': fleets[fl]['RC_PORT'] }
         
      logging.debug('in chgSail cf '+ str(cf))
      conf = CallOut(oldbt+','+fl, "requestBTconfig", conf=cf, timeout=10)
      logging.debug('conf '+ str(conf))

      if conf['hn'] is  None :    # no response
         tkWarning("gizmo not responding.\n %s number not changed." % (oldbt))
         return None
      else:
         fleets[fl]['BoatList'].remove(oldbt)    
         fleets[fl]['BoatList'].append(bt)
         sailNumberChoice['values'] = BoatList(fl)
         sailNumberChoice.set(bt)

   
def chgFleet(fl, t=None):
   """Change a boat's fleet."""
   # arg fl comes from change fleet dialog not main GUI
   global fleets, fleetChoice, sailNumberChoice
   if t is not None: t.destroy()
   
   bt = sailNumberChoice.get()
   oldfl = fleetChoice.get()
   #logging.debug('fl '+ fl)
   #logging.debug('oldfl '+ oldfl)

   if bt in BoatList(fl): 
      tkWarning("%s is already in fleet %s\nFleet change not allowed." % (bt, fl))
      return None
   else:
      # important to change BT first. 
      # If it fails then do not changes 'BoatList' or gizmo cannot be contacted
      cf = {'BT_ID': bt, 'FLEET': fl, 'RC_IP': fleets[fl]['RC_IP'], 'RC_PORT': fleets[fl]['RC_PORT'] }
         
      conf = CallOut(bt+','+oldfl, "requestBTconfig", conf=cf, timeout=10)
    
      if conf['hn'] is not None :    # not no response
         fleets[oldfl]['BoatList'].remove(bt)    
         fleets[fl]['BoatList'].append(bt)

         fleetChoice.set(fl)
         sailNumberChoice['values'] = BoatList(fl)



def callForGizmo(callout, t=None):
   global fleetChoice, sailNumberChoice, gizmo, status
   if t is not None: t.destroy()
   
   #unset sail# and fleet for case nothing is returned
   sailNumberChoice.set('')
   fleetChoice.set('unknown')
   gizmo.set('unknown')
   status.set('')

   conf = CallOut(callout, "report config")
   logging.debug(conf)

   # don't message here. Instead give more detail in the function returned to.
   if conf['hn'] is None :  return conf   # no response

   # hn is not a standard part of BTconfig, it was added by CallOutRespond()
   gizmo.set(           conf['hn']) 
   fleetChoice.set(     conf['FLEET'])
   sailNumberChoice.set(conf['BT_ID'])
   return conf

def callForBoat(bt, fl):
   global fleetChoice, sailNumberChoice, gizmo, status
   #unset gizmo for case nothing is returned
   gizmo.set('unknown')
   status.set('')

   callout =bt + ',' + fl
   conf = CallOut(callout, "report config")
   logging.debug(conf)

   # don't message here. Instead give more detail in the function returned to.
   if conf['hn'] is None :  return conf   # no response

   fl = conf['FLEET']
   fleetChoice.set(fl)

   bt = conf['BT_ID']
   sailNumberChoice.set(bt)
       
   # ensure correct RC settings
   fIP = fleets[fl]['RC_IP']
   fPT = fleets[fl]['RC_PORT']
   bIP = conf['RC_IP']
   bPT = conf['RC_PORT']

   if fIP != bIP  or  fPT != bPT :
      tkWarning("Boat's IP/PORT was not set to fleet values!\n" +
                "boat:  " + bIP + ":" + bPT + "\n" +
                "fleet: " + fIP + ":" + fPT + "\n" +
                "It is being reset. If the boat values were correct\n" +
                "then reset the fleet values and propogate.", width=45)
      # reset this boat's RC settings
      btfl = bt + ',' + fl
      rc =  btfl + "::" + str({x: fleets[fl][x] for x in ('RC_IP', 'RC_PORT')})
      conf =  CallOut(btfl, 'setRC', conf=rc, timeout=20)
 
   # hn is not a standard part of BTconfig, it was added by CallOutRespond()
   gizmo.set(conf['hn']) 
   statusSet()
   return conf

def checkOut(): 
   global fleets
   bt = sailNumberChoice.get()
   fl = fleetChoice.get()

   # This callForBoat is used to discover gizmo hn, which also gets set in the GUI.
   # When callForBoat used only bt and not fl, it could also discover fl, but that 
   # assumed bt was unique across fleets.

   r = callForBoat(bt, fl)
   hn = r['hn']
   if hn is None :       
      tkinter.messagebox.showinfo("No Response", "%s in fleet %s not responding." % (bt, fl))
      return None

   CallOut(hn, "checkout")

   fleets[fl]['checkedOut'].append(bt)    
   updateBoatHostMap(bt,hn)
   statusSet()
   logging.debug('status ' +  status.get())

def checkIn(): 
   global fleets
   bt = sailNumberChoice.get()
   fl = fleetChoice.get()

   # This callForBoat is used to discover gizmo hn, which also gets set in the GUI.
   r = callForBoat(bt, fl)
   if r['hn'] is None :       
      tkinter.messagebox.showinfo("No Response", "%s in fleet %s not responding." % (bt, fl))
      return None

   if bt not in checkedOut(fl):
      tkWarning("%s was not checkedOut in fleet %s" % (bt,fl))
   fleets[fl]['checkedOut'].remove(bt)

   CallOut(gizmo.get(), "checkin")
   statusSet()
   logging.debug('checkIn status ' +  status.get())


##########  GUI utilities  ########### 

def abortHandler(signum, frame):
    logging.info('main thread exit via abortHandler.')
    sys.exit("RC process killed.")

def showRC(t=None): 
   if t is not None: t.destroy()

   w = tkinter.Toplevel()
   w.wm_title("Fleet Names & RC settings")
   for d in fleetList:
      rc = str({x: fleets[d][x] for x in ('RC_IP', 'RC_PORT')})
      ROW(w, text='%s   %s' % (d, rc), pad=2, width=40)


def showBoatList(w=None):
   if w is not None: w.destroy() 
   
   fl     = fleetChoice.get()
   BtLst  = BoatList(fl)
   chO    = checkedOut(fl)
   BHMap  = fleets['BoatHostMap']
   
   t = tkinter.Toplevel()
   t.wm_title(fl)
   
   if  0 == len(BtLst) : 
       ROW(t, text='boat list not available for ' + fl, pad=2)
   else : 
      for f in sorted(BtLst) :
         if f  in  chO : out = ' out '
         else          : out = '     '
         gz = str([h for h,b in BHMap.items() if b == f])
         ROW(t, text='%s   %s      %s' % (f, out, gz), pad=2)


def statusSet():
   global status
   OutLst = checkedOut(fleetChoice.get())
   if sailNumberChoice.get() in OutLst :
          status.set('Out')
   else : status.set('In ')

def changeFleet():
   # This changes the drop down sail number menu when GUI changes
   # from one fleet to another. It does not change the fleet of a boat.
   global sailNumberChoice, gizmo, status
   sailNumberChoice['values'] = BoatList(fleetChoice.get())
   sailNumberChoice.set('')
   gizmo.set('')
   status.set('')

def changeBoat():
   # This changes the gizmo ID and status in the GUI when the sail# is changed
   global gizmo, status
   gizmo.set('')
   statusSet()

##########   Change a Boat's Fleet  Window   ########### 

def chgFleetWindow(w=None):
   if w is not None: w.destroy() 
   t = tkinter.Toplevel()
   t.wm_title("New Fleet")

   bt    = sailNumberChoice.get()
   oldfl = fleetChoice.get()

   row = tkinter.Frame(t)
   tkinter.Label(row, text='For Boat %s change Fleet from %s to: ' % (bt,oldfl), anchor='w').pack(side=tkinter.LEFT)

   e = ttk.Combobox(row, values=fleetList, state="readonly" , width=10 )
   e.pack(side=tkinter.LEFT)
   e.set(oldfl) 

   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(t)
   But(row, text="Commit", command=(lambda : chgFleet(e.get(), t)))
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

##########   Change Sail #  Window   ########### 

def chgSailWindow(w=None):
   if w is not None: w.destroy() 

   t = tkinter.Toplevel()
   t.wm_title("New Sail #")

   oldbt = sailNumberChoice.get()

   row = tkinter.Frame(t)
   tkinter.Label(row, text='Change Sail ' + oldbt + ' to: ',   anchor='w').pack(side=tkinter.LEFT)
   e = tkinter.Entry(row, bg = "white", width=10)
   e.pack(side=tkinter.LEFT)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(t)
   But(row, text="Commit", command=(lambda : chgSail(e.get(), t)))
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

##########   New Boat  Window   ########### 

def newBoatWindow(w=None):
   if w is not None: w.destroy() 
   t = tkinter.Toplevel()
   t.wm_title("New Boat")

   row = tkinter.Frame(t)
   f = ttk.Combobox(row, values=fleetList, state="readonly" , width=10 )
   f.bind("<<ComboboxSelected>>", (lambda event : changeFleet()))
   f.pack(side=tkinter.LEFT)
   f.set(fleetList[0]) 

   tkinter.Label(row, text='New Boat Sail #',   anchor='w').pack(side=tkinter.LEFT)
   b = tkinter.Entry(row, bg = "white", width=10)
   b.pack(side=tkinter.LEFT)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(t)
   tkinter.Label(row, text='Assign gizmo:',   anchor='w').pack(side=tkinter.LEFT)
   g = ttk.Combobox(row, values=sorted(unassignedGizmos.values), state="readonly" , width=10)
   g.pack(side=tkinter.LEFT)
   g.set(unassignedGizmos.values[0]) 

   But(row, text="Commit",  
                  command=(lambda : newBoatSetup(b.get(), f.get(), g.get(), t)))
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)


##########   Remove Boat  Window   ########### 

def removeBoatWindow(w=None):
   if w is not None: w.destroy() 
   t = tkinter.Toplevel()
   t.wm_title("Remove Boat")

   fl = fleetChoice.get()
   bt = sailNumberChoice.get()

   row = tkinter.Frame(t)
   txt = 'Remove  Boat Sail # %s   from Fleet  %s !!'  % (bt, fl)
   tkinter.Label(row, text= txt, anchor='w').pack(side=tkinter.LEFT)

   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(t)
   But(row, text="Commit", command=(lambda : rmBoat(bt, fl, t)))
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

##########    More  Window   ########### 

def moreWindow():
   t = tkinter.Toplevel()
   t.wm_title("More Options")

   row = tkinter.Frame(t)
   But(row, text="Change\nBoat's Fleet", command=(lambda : chgFleetWindow(t)))
   But(row, text="Change\nBoat's Sail#", command=(lambda : chgSailWindow(t)))
   But(row, text='New Boat',             command=(lambda : newBoatWindow(t)))
   But(row, text='Remove Boat',          command=(lambda : removeBoatWindow(t)))
   But(row, text='extra',                command=(lambda : extraWindow(t)))
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

##########    Extra  Window   ########### 

def extraWindow(w=None):
   if w is not None: w.destroy() 
   t = tkinter.Toplevel()
   t.wm_title("Extra Options")

   row = tkinter.Frame(t)
   But(row,  text="Propogate\nRegist. IP",       command=(lambda : setREG(t)) )
   But(row,  text="Show fleets'\nRC settings",   command=(lambda : showRC(t)) )
   But(row,  text="Propogate\nfleet's RC",       command=(lambda : setAllRC(t)) )

   tkinter.Label(row, text= 'Call Out Gizmo:',   anchor='w').pack(side=tkinter.LEFT)
   gz = tkinter.StringVar()
   gzC = ttk.Combobox(row, values=gizmoList.values, textvariable=gz, state="readonly", width=10)
   gzC.bind("<<ComboboxSelected>>", lambda _ : callForGizmo(gz.get(), t)  )
   gzC.pack(side=tkinter.LEFT)

   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
   

##################  Gcheckout  Main  GUI     ################

def GcheckoutGUI(w):
   global fleetChoice, sailNumberChoice, gizmo, status
   #w = ttk.Style()
   #w.configure("BW.TLabel", foreground="black", background="white")

   w.wm_title("Gizmo check out / check in")
   
   row = tkinter.Frame(w)
   fleetChoice = ttk.Combobox(row,
                     values=fleetList, state="readonly" , width=10 )
   fleetChoice.bind("<<ComboboxSelected>>", (lambda event : changeFleet()))
   fleetChoice.pack(side=tkinter.LEFT)
   fleetChoice.set(fleetList[0]) 

   tkinter.Label(row, text= 'Sail #:',   anchor='w').pack(side=tkinter.LEFT)
   sailNumberChoice = ttk.Combobox(row,
                    values=BoatList(fleetList[0]), state="readonly" , width=10)
   sailNumberChoice.bind("<<ComboboxSelected>>", (lambda event : changeBoat()))
   sailNumberChoice.pack(side=tkinter.LEFT)

   But(row, text='Call Out\nBoat', command =
          (lambda : callForBoat(sailNumberChoice.get(), fleetChoice.get())))

   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(w)
   tkinter.Label(row, text= 'Gizmo ID:',      anchor='w').pack(side=tkinter.LEFT)
   gizmo = tkinter.StringVar()
   tkinter.Label(row, textvariable = gizmo,   anchor='w').pack(side=tkinter.LEFT)

   tkinter.Label(row, text= '     Status:',   anchor='w').pack(side=tkinter.LEFT)
   status = tkinter.StringVar()
   tkinter.Label(row, textvariable = status,   anchor='w').pack(side=tkinter.LEFT)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
   status.set('')

   row = tkinter.Frame(w)
   But(row,  text='Check Out\nGizmo',       command=checkOut)
   But(row,  text='Check In\nGizmo',        command=checkIn)
   But(row,  text='fleet check-\nOut status', command=showBoatList)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

   row = tkinter.Frame(w)
   But(row, text='more',                command=moreWindow)
   row.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)
   
   # return used for unit testing
   return {'fleetChoice': fleetChoice,
           'sailNumberChoice' : sailNumberChoice,
           'status' : status }

###############  end  Gcheckout  Main  GUI     ###############

##################  initiate from files    ################

def initiate(path=os.getcwd()+'/'):
   global fleets, fleetList, gizmoList, unassignedGizmos

   gizmoList        = syncdList(path + 'gizmoList.txt') 
   unassignedGizmos = syncdList(path + 'unassignedGizmos.txt')   

   try :
      # This also has RC_IP and port info
      with open(path + 'FleetListRC.json','r') as f: fleets =  json.load(f)
   except :
      fleets = {'No fleet': None}
   
   fleetList = sorted(fleets.keys())  
   
   for d in fleetList:
      if not os.path.exists(path + 'FLEETS/' + d):  os.makedirs(path + 'FLEETS/'+d)
   
   for d in fleetList:
      fleets[d]['BoatList']   = syncdList(path + 'FLEETS/' +d+ '/BoatList.txt')
   
   for d in fleetList:
      fleets[d]['checkedOut'] = syncdList(path + 'FLEETS/' +d+ '/checkedOut.txt')
   
   
   try :
      with open(path + 'BoatHostMap.json') as f:  fleets['BoatHostMap'] = json.load(f)
   except :
      fleets['BoatHostMap'] = {}
   
   # currently these are globals, returning is only for unit testing.
   # It might be better if this was a class object
   return {    'fleets': fleets, 
            'fleetList': fleetList, 
            'gizmoList': gizmoList, 
     'unassignedGizmos': unassignedGizmos,
     
     }
