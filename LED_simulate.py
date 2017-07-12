# License GPL 2. Copyright Paul D. Gilbert, 2017

# simulate LED signal hardware by simple print statements


""" simulate LED signal hardware by simple print statements.
    Optional argument is appended to print, mainly used for debugging.
    eg
       LEDsignal.bound(x ='LtoR boundL') 
"""

def  bound(x ='')  : print('zone  red '   + str(x))
def  warn(x ='')   : print('flash red '   + str(x))
def  center(x ='') : print('flash green ' + str(x))
def  off(x ='')    : print('no light '    + str(x))

