# Copyright 2018 Paul Gilbert
#CC BY-SA 4.0

#This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. 
#To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/ or send a 
#letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

#import FreeCAD, FreeCADGui
import Part, PartDesignGui
import Mesh, MeshPart, MeshPartGui

####### define utility ###################

def makeSTL(part, body = "Box") :
   FreeCAD.Console.PrintMessage('generating stl file.\n')

   Gui.activateWorkbench("MeshWorkbench")
   App.setActiveDocument(docName)
   #doc = FreeCAD.getDocument("LEDMainBox")

   mesh = doc.addObject("Mesh::Feature","Mesh")
   mesh.Mesh = MeshPart.meshFromShape(Shape=doc.getObject(body).Shape, 
              LinearDeflection=0.1, AngularDeflection=0.523599, Relative=False)
   mesh.Label= body + " (Meshed)"
   mesh.ViewObject.CreaseAngle=25.0

   #Gui.getDocument("LEDMainBox").getObject(body).Visibility=False
   #Gui.getDocument("LEDMainBox").getObject(body + " (Meshed)").Visibility=True

   Mesh.export([mesh], "./BT-" + part + ".stl")
   return None

#######################################

docName = 'BT'

#  first setup the document (Parts and Bodys) and GUI

doc = FreeCAD.newDocument(docName)

App.setActiveDocument(docName)

# NB App.ActiveDocument is an object = doc = FreeCAD.ActiveDocument, 
#    App.activeDocument is a method
#   and  App.activeDocument() evaluates to an object = doc
#   so  this       App.ActiveDocument=App.getDocument(docName)
#   is the same as App.ActiveDocument=doc

################ common variables ################

originBox   = FreeCAD.Vector(0, 0, 0)    # main box
originBack  = FreeCAD.Vector(0, 150, 0)  # behind solar panel
originCover = FreeCAD.Vector(0, 300, 0)  # over solar panel

dr = FreeCAD.Vector(0,0,1)

# Outside dimensions
length = 161 # top to bottom
width  = 102 # side to side
height = 55  # front to back of box, not including cover and back

wall = 13.0
backwall = 10.0
coverThickness = 3.0
backThickness  = 3.0

# prongs
# reference locations (center, outside edge of slot holes)
# on X-Y plane these are 2mm from outside edges
# These will be displaced by origin.

# left  and right as in axiometric view. If back and cover are folded over onto
# the box with LEDs at bottom. left on box will be port and right on prongs
# will be port.
prongs_left =   ((20.5, 2),         (60.5, 2),         (100.5, 2),         (141.5, 2))
prongs_right =  ((20.5, width - 2), (60.5, width - 2), (100.5, width - 2), (141.5, width - 2))
prongs_bottom = ((length - 2, 20), (length - 2, width/2), (length - 2, width - 20) )
prongs_top =    ((   2,       20), (      2,    width/2), (      2,    width - 20) )

prongWidth = 6.0
prongThickness =  1.5  #2.0
prongBump = 1.5
prongCutoutDepth = 5.0 # cutout for catch
prongCatchDepth = height - prongCutoutDepth # from top of box, not through back to cover

prongSlotDepth  = height  #20.0
prongSlotLength = prongWidth + 4.0 # lots of clearance
prongSlotWidth  = 3.8  # 2 + 1.5 + clearance

glandTongue = 2    # depth into gland, width needs clearance
glandWidth  = 3.6  # 20% larger than 3.0 seal dia.
glandDepth  = 4.4  # glandTongue + 75% of 3.0 seal dia.

#  LEDs  vertical at top
LEDcenters = (FreeCAD.Vector( 16, width/2, 0),
              FreeCAD.Vector( 24, width/2, 0),
              FreeCAD.Vector( 32, width/2, 0))
LEDholeDia   = 5.2
LEDholeDepth = 4.0    #should not go alll the wy through cover and back
LEDwireSlotWidth   = 3.6
LEDwireSlotLength  = LEDholeDia - 0.2

strapSlotWidth  = 25.0
strapSlotHeight = 5.0
strapSlotPos    = (28, 108.5)

#######################################
################ MainBox ################
#######################################

doc.Tip = doc.addObject('App::Part','MainBox')
#  is the same as
#App.activeDocument().Tip = App.ActiveDocument.addObject('App::Part','MainBox')
#  is the same as
# App.activeDocument().Tip = App.activeDocument().addObject('App::Part','MainBox')

#doc.MainBox.Label = 'newPartLabel'

#doc.addObject('PartDesign::Body','Box')
#doc.MainBox.addObject(doc.Box) #mv box into part

doc.recompute()

Gui.ActiveDocument=Gui.getDocument(docName)
Gui.activateWorkbench("PartDesignWorkbench")
Gui.activeView().setActiveObject('pdbody', App.activeDocument().MainBox)
Gui.activeView().setActiveObject('part', App.activeDocument().MainBox)
Gui.Selection.clearSelection()
Gui.Selection.addSelection(App.ActiveDocument.MainBox)

# Fillet all edges that touch zero height, so corners and bottom edges
edges=[]

# next works and does Fillet but then the Fillet is lost on recompute ??
#box_outside = doc.addObject("Part::Box","Outside") 
#box_outside.Placement.Base = originBox 
#box_outside.Length = length
#box_outside.Width  = width
#box_outside.Height = height
##box_outside.Label = 'Outside'
#for e in box_outside.Shape.Edges :
#   for p in e.Vertexes : 
#      if p.Point[2] == 0 : edges.append(e)
#edges = list(set(edges)) # unique elements
# outside.Shape = outside.Shape.makeFillet(6, edges) 
#doc.recompute() 


box_out = Part.makeBox ( length,width,height)  #,[pnt,dir] )

#  round back edges (bottom outside of box)
for e in box_out.Edges :
   if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == 0 : edges.append(e)

#  round corners
for e in box_out.Edges :
   if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == height : edges.append(e)
   if e.Vertexes[1].Point[2] == 0 and e.Vertexes[0].Point[2] == height : edges.append(e)

edges = list(set(edges)) # unique elements

box_outside = doc.addObject("Part::Feature","Outside")
box_outside.Placement.Base = originBox 
box_outside.Shape = box_out.makeFillet(6, edges)

doc.recompute() 

inside = Part.makeBox(          
   length - 2 * wall,
   width  - 2 * wall,
   height -  backwall,
   originBox + FreeCAD.Vector(wall, wall, backwall),
   FreeCAD.Vector(0,0,1) ) 

#Part.show(inside)
 
holes = []  # these will be fused to inside

#  prong slots

w = prongSlotLength / 2
h = height - prongSlotDepth

for pos in prongs_left :
   p = originBox + FreeCAD.Vector(pos[0] -w,  pos[1],  h)

   # slot
   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth, 
            prongSlotDepth, p, dr ) )

   #catch cutout
   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth + 2, 
            prongCutoutDepth, p, dr ) )


for pos in prongs_right :
   p = originBox + FreeCAD.Vector(pos[0] -w,  pos[1] - prongSlotWidth,  h)

   # slot
   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth, 
               prongSlotDepth, p, dr ) )

   #catch cutout
   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth + 2, 
               prongCutoutDepth, p + FreeCAD.Vector(0, -2, 0), dr ) )


for pos in prongs_bottom :
   p = originBox + FreeCAD.Vector(pos[0] - prongSlotWidth,  pos[1] - w,  h)

   holes.append(Part.makeBox( prongSlotWidth,  prongSlotLength, 
               prongSlotDepth, p, dr ) )

   #catch cutout
   holes.append(Part.makeBox( prongSlotWidth + 2, prongSlotLength, 
               prongCutoutDepth, p + FreeCAD.Vector(-2, 0, 0), dr ) )


for pos in prongs_top :
   p = originBox + FreeCAD.Vector(pos[0],  pos[1] - w,  h)

   holes.append(Part.makeBox( prongSlotWidth, prongSlotLength, 
               prongSlotDepth, p, dr ) )

   #catch cutout
   holes.append(Part.makeBox( prongSlotWidth + 2, prongSlotLength, 
               prongCutoutDepth, p, dr ) )


# slots for straps through back edges
# 50mm is long enough to go all the way through
# starting 10mm out is enough ensure removed rectangle does not start inside the wall.
# starting 23mm from edge is enough to leave edge and not to pierce inside.
# slot positioning point is below slot on the left and above slot on the right.
# 23 on left is about 18+strapSlotHeight (angled) on the right

for pos in strapSlotPos :
   # left slots: remove rectangles positioned on the side and extending downward at 45° 
   z = Part.makeBox(strapSlotWidth, 50, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, -10, 23), 
                              FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -45))   # -45° about X) 
   holes.append(z ) 

   # flatten 45° edge at slot side opening
   z = Part.makeBox(strapSlotWidth, 5, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, 0, 9),
                              FreeCAD.Rotation(dr, 0)) 
   holes.append(z ) 

   # right slots: remove rectangles positioned on the bottom and extending upward at 45°
   z = Part.makeBox(strapSlotWidth, 50, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, width-18-strapSlotHeight, -10), 
                              FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 45))   # 45° about X) 
   holes.append(z ) 

   # flatten 45° edge at slot side opening
   z = Part.makeBox(strapSlotWidth, 5, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, width-5, 9),
                              FreeCAD.Rotation(dr, 0)) 
   holes.append(z ) 


# slot for extra attachment line (saftey)
# bottom edge: remove 5x5 rectangle positioned on the bottom and extending upward at 45°

pos = 35 # cannot be center because of prong hole
z = Part.makeBox(50, 5, 5)
z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( length-5-15, pos,  -10), 
                           FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -45))   # -45° about Y) 
holes.append(z ) 

# Gland
# inside is 3mm from inside wall edge, outside is glandWidth more.

w = wall - 3

gland_inside = Part.makeBox( length - 2 * w, 
               width - 2 * w,  glandDepth, 
               originBox + FreeCAD.Vector(w, w, height - glandDepth), dr )


gland_outside = Part.makeBox( length - 2 * (w-glandWidth), 
            width -2 * (w-glandWidth),  glandDepth, 
            originBox + FreeCAD.Vector(w-glandWidth, w-glandWidth, height - glandDepth), dr )


gland2 = gland_outside.cut(gland_inside)

# fillet all gland edges that touch the bottom, so corners and bottom edges
h = height - glandDepth
edges=[]

for e in gland2.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == h : edges.append(e)

edges = list(set(edges)) # unique elements
gland = gland2.makeFillet(1.5, edges) # radius = seal  dia/2 =3/2 

#   NEED TO WORK ON THE GLAND CORNERS

holes.append(gland )

doc.recompute() 

FreeCAD.Console.PrintMessage('finished slot definition.\n')
FreeCAD.Console.PrintMessage('starting compound holes object.\n')

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

remove = doc.addObject("Part::Feature","Remove")
remove.Shape = inside.fuse(holes)
#or something like remove = Part.makeCompound(holes)


# or something like 
# MainBox = box_outside.cut(remove)
# see https://www.freecadweb.org/wiki/Topological_data_scripting

box=doc.addObject("Part::Cut","Box")
box.Base = box_outside
box.Tool = remove

doc.MainBox.addObject(doc.Box) #mv Box (body) into part MainBox

doc.recompute() 
Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('MainBox object construction complete.\n')

####### about fuse see
# https://forum.freecadweb.org/viewtopic.php?f=10&t=18179&start=30#p143867

makeSTL("MainBox", "Box")


##################################################
############# Back (of solar panel) ##############
##################################################

doc.Tip = doc.addObject('App::Part','SolarBack')

back_out = Part.makeBox ( length,width,backThickness)  #,[pnt,dir] )

# MIGHT BE CLEANER, DON'T NEED back_out AND back_outside

#  round corners
edges = []
for e in back_out.Edges :
   if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == backThickness : edges.append(e)
   if e.Vertexes[1].Point[2] == 0 and e.Vertexes[0].Point[2] == backThickness : edges.append(e)

edges = list(set(edges)) # unique elements

back_outside = doc.addObject("Part::Feature","BackOutside")
back_outside.Shape = back_out.makeFillet(6, edges)
back_outside.Placement.Base = originBack # sensitive to Placement after Shape!

doc.recompute() 

# add Gland
# groove inside is 3mm from inside wall edge, outside is glandWidth more.
# (3mm is arbitrary, not related to 3mm o-ring cord)
# tongue is narrower by clr on both sides

clr = 0.2  #clearance
w = wall - 3  # outside edge of box to inside edge of gland groove

# relative to originBack
# pos for inside box is wall - (3 + clr) = w -clr
# which is outside edge of box to inside edge of gland tongue
# pos for outside box is wall - (3 + glandWidth - clr) = w - glandWidth + clr
# which is outside edge of box to outside edge of gland tongue
# len   of inside  box is length - 2 * (wall - 3 - clr) =  length - 2 * (w -clr)
# width of inside  box is  width - 2 * (wall - 3 - clr) =  width  - 2 * (w -clr)
# len   of outside box is length - 2 * (wall - 3 - glandWidth + clr)  
# width of outside box is  width - 2 * (wall - 3 - glandWidth + clr) =  width  - 2 * (w -glandWidth + clr)

gland_inside = Part.makeBox( length - 2 * (w - clr), 
                              width - 2 * (w - clr),  glandTongue, 
               originBack + FreeCAD.Vector(w - clr, w - clr, backThickness), dr )


gland_outside = Part.makeBox( length - 2 * (w + clr - glandWidth), 
                               width - 2 * (w + clr - glandWidth),  glandTongue, 
            originBack + FreeCAD.Vector(w + clr - glandWidth, w + clr - glandWidth, 
                                        backThickness), dr )


glandBack = gland_outside.cut(gland_inside)
#Part.show(inside)

# fillet all gland corners (verticle edges so x and y coordinates of 
#    end points are equal)

edges=[]

for e in glandBack.Edges :
   if e.Vertexes[0].Point[0] ==  e.Vertexes[1].Point[0] and \
      e.Vertexes[0].Point[1] ==  e.Vertexes[1].Point[1] :  edges.append(e)

# radius = seal  dia/2 =3/2   
doc.addObject("Part::Feature","Gland").Shape = glandBack.makeFillet(1.5, edges) 
doc.recompute() 


# add wall for GPS. top right beside LEDs.  Add 2.0 for clearance
doc.addObject("Part::Feature","GPSv").Shape =  Part.makeBox( 
     15, 2, 25, originBack + FreeCAD.Vector(wall+2.0, 3 + width/2, backThickness), dr)

doc.addObject("Part::Feature","GPSh").Shape =  Part.makeBox( 
     2, 30, 25, originBack + FreeCAD.Vector(wall + 15, 3 + width/2, backThickness),dr)


# add stud pins for boards

def makePin(num, x, y, bsRad, bsHt, hdRad, hdHt, part, 
       p = originBack + FreeCAD.Vector(0,  0,  backThickness)) :
   ''' 
   num is string appended to name or boy object in doc
   x, y  center wall and originBack + backThickness
   bsRad, hdRad base and pin radius
   bsHt,  hdHt  base and pin height
   '''
   base = doc.addObject("Part::Cylinder", "PinBase"+num)
   # Note that Shape and Placement from Part.makeCylinder get lost on recompute() so this
   #   base.Shape =  Part.makeCylinder(3.0/2, 4.0)  # looses values and returns to defaults
   # and
   #   base.Shape =  Part.makeCylinder(3.0/2, 4.0, 
   #      p + FreeCAD.Vector(wall+26,  17,   0 ), dr, 360 ) # loose placement on recompute()
   
   base.Radius = bsRad
   base.Height = bsHt
   base.Placement = FreeCAD.Placement(p + FreeCAD.Vector(wall+x,  y,   0 ), dr, 360 )
   
   head = doc.addObject("Part::Cylinder", "PinHead"+num)
   head.Radius =  hdRad
   head.Height = hdHt
   head.Placement = FreeCAD.Placement(p + FreeCAD.Vector(wall+x,  y,  bsHt), dr, 360 )
   
   doc.SolarBack.addObject(base) #mv  into part SolarBack
   doc.SolarBack.addObject(head) #mv  into part SolarBack
   
   doc.recompute() 
   
   return None

#p = originBack + FreeCAD.Vector(0,  0,  backThickness)

# power management board pins 19x67

# doc.SolarBack" still hardcoded in function
makePin("1", 26, 17, 3.0/2, 4.0,  1.2/2, 5.0,  "SolarBack") 
makePin("2", 26, 84, 3.0/2, 4.0,  1.2/2, 5.0,  "SolarBack") 
makePin("3", 45, 17, 3.0/2, 4.0,  1.2/2, 5.0,  "SolarBack") 
makePin("4", 45, 84, 3.0/2, 4.0,  1.2/2, 5.0,  "SolarBack") 

# power R Pi zero board pins 23x58

makePin("5", 55, 22, 5.0/2, 7.0,  2.5/2, 5.0,  "SolarBack") 
makePin("6", 55, 80, 5.0/2, 7.0,  2.5/2, 5.0,  "SolarBack") 
makePin("7", 78, 22, 5.0/2, 7.0,  2.5/2, 5.0,  "SolarBack") 
makePin("8", 78, 80, 5.0/2, 7.0,  2.5/2, 5.0,  "SolarBack") 

# power O Pi zero plus board  pins 42x40

makePin("9",  55, 31, 5.0/2, 2.0,  2.5/2, 5.0,  "SolarBack") 
makePin("10", 55, 71, 5.0/2, 2.0,  2.5/2, 5.0,  "SolarBack") 
makePin("11", 97, 31, 5.0/2, 2.0,  2.5/2, 5.0,  "SolarBack") 
makePin("12", 97, 71, 5.0/2, 2.0,  2.5/2, 5.0,  "SolarBack") 


#  Fuse the body objects 
#  note that edges at fused joint cannot be selected, at least not in GUI view

doc.addObject("Part::MultiFuse","Fusion")
# next causes view to disappear until doc.recompute() 
#in model view this adds  BT>Fusion with [..] bodies but only seen after doc.recompute() 
doc.Fusion.Shapes = [doc.BackOutside, doc.Gland, doc.GPSv, doc.GPSh,
    doc.PinBase1,  doc.PinHead1,  doc.PinBase2,  doc.PinHead2, 
    doc.PinBase3,  doc.PinHead3,  doc.PinBase4,  doc.PinHead4,
    doc.PinBase5,  doc.PinHead5,  doc.PinBase6,  doc.PinHead6, 
    doc.PinBase7,  doc.PinHead7,  doc.PinBase8,  doc.PinHead8,
    doc.PinBase9,  doc.PinHead9,  doc.PinBase10, doc.PinHead10, 
    doc.PinBase11, doc.PinHead11, doc.PinBase12, doc.PinHead12, ]

doc.SolarBack.addObject(doc.Fusion) #mv Fusion into part SolarBack
doc.recompute() 

#  Above fuse can also be done by the following but view does not appear until fusion and
#  only Plus is indicated in the model tree view, so understanding and debugging are harder.
#  However, for writing functions this might be preferred, since in the above the part name
# becomes an object atribute, and ."Fusion". syntax doe not work.
# add = [glandBack ]  
# gps_wall_vert = Part.makeBox( 15, 2, 25, 
#               originBack + FreeCAD.Vector(wall, 3 + width/2, backThickness), dr )
# add.append(gps_wall_vert)
# add.append(gps_wall_horiz)
# plus = doc.addObject("Part::Feature","Plus")
# plus.Shape = add[0].fuse(add) # or glandBack.fuse(add)  
# doc.addObject("Part::MultiFuse","Fusion")
# doc.Fusion.Shapes = [doc.BackOutside, doc.Plus,] 
# doc.recompute() 


holes = []

#  prong slots

w = prongSlotLength / 2

for pos in prongs_left :
   p = originBack + FreeCAD.Vector(pos[0] -w,  pos[1],  0)

   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth,
                backThickness, p, dr ) )

for pos in prongs_right :
   p = originBack + FreeCAD.Vector(pos[0] -w,  pos[1] - prongSlotWidth, 0)

   holes.append(Part.makeBox( prongSlotLength, prongSlotWidth, 
                backThickness, p, dr ) )

for pos in prongs_bottom :
   p = originBack + FreeCAD.Vector(pos[0] - prongSlotWidth,  pos[1] - w, 0)

   holes.append(Part.makeBox( prongSlotWidth,  prongSlotLength, 
               backThickness, p, dr ) )

for pos in prongs_top :
   p = originBack + FreeCAD.Vector(pos[0],  pos[1] - w,  0)

   holes.append(Part.makeBox( prongSlotWidth, prongSlotLength, 
               backThickness, p, dr ) )


#LED holes
#makeCylinder ( radius,height,[pnt,dir,angle] )

# position
h =  LEDholeDepth - coverThickness #should not go all the way through
p = originBack   


# these holes need to be slightly bigger than in cover as the LED base needs to
# go into them, but cover can go on after base is already in.
holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, h, p + LEDcenters[0], dr, 360 ) ) #LED 1

holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, h, p + LEDcenters[1], dr, 360 ) ) #LED 2

holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, h, p + LEDcenters[2], dr, 360 ) ) #LED 3

#  wire slots

p = originBack -  FreeCAD.Vector(LEDwireSlotWidth/2, LEDwireSlotLength/2, 0)

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, backThickness, 
               p + LEDcenters[0], dr ) )#LED 1

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, backThickness, 
               p + LEDcenters[1], dr ) )#LED 2

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, backThickness, 
               p + LEDcenters[2], dr ) )#LED right3

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

doc.recompute() 

# Gui.activeDocument().Outside.Visibility=False
# Gui.activeDocument().Add.Visibility=False
# Gui.ActiveDocument.Fusion.ShapeColor=Gui.ActiveDocument.Outside.ShapeColor
# Gui.ActiveDocument.Fusion.DisplayMode=Gui.ActiveDocument.Outside.DisplayMode

# note that 
#  less = doc.addObject("Part::Feature","Less").Shape = holes[0].fuse(holes)
# does not seem to work. It leave the holes and removes the good part
less = doc.addObject("Part::Feature","Less")
less.Shape = holes[0].fuse(holes)   

back=doc.addObject("Part::Cut","Back")
back.Base = doc.Fusion
back.Tool = less
doc.SolarBack.addObject(doc.Back) #mv Back (body) into part SolarBack

doc.recompute() 

# fillet holes to accommodate fillet on prongs
edges=[]
for e in doc.Back.Shape.Edges :
   for p in e.Vertexes : 
       p0 =  p.Point[0] - originBack[0]
       p1 =  p.Point[1] - originBack[1]
       if p.Point[2] == 0.0 :
          if       0.5      < p1  <     10.0      : edges.append(e)  # left
          if  width  - 10.0 < p1  < width  - 0.5  : edges.append(e)  # right
          if  length - 10.0 < p0  < length - 0.5  : edges.append(e)  # bottom
          if       0.5      < p0  <     10.0      : edges.append(e)  # top


doc.addObject("Part::Feature","BackFinished").Shape = doc.Back.Shape.makeFillet(
   0.5, list(set(edges))) # unique edge elements

doc.SolarBack.addObject(doc.BackFinished) #mv BackFinished (body) into part SolarBack

doc.recompute() 

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarBack object construction complete.\n')


makeSTL("SolarBack", "BackFinished")

#######################################
################ Cover ################
#######################################

doc.Tip = doc.addObject('App::Part','SolarCover')

cover_out = Part.makeBox ( length,width,backThickness)  #,[pnt,dir] )

#  round corners
edges = []
for e in cover_out.Edges :
   if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == coverThickness : edges.append(e)
   if e.Vertexes[1].Point[2] == 0 and e.Vertexes[0].Point[2] == coverThickness : edges.append(e)

edges = list(set(edges)) # unique elements

doc.recompute() 

cover_outside = doc.addObject("Part::Feature","CoverOutside")
cover_outside.Shape = cover_out.makeFillet(6, edges)
cover_outside.Placement.Base = originCover # sensitive to Placement after Shape!

doc.recompute() 

holeLength = 110   # solar panel is 110 x 69
holeWidth  =  69   # chamfer will be used to reduce outside edge of hole


solarHole = Part.makeBox(          
   holeLength,
   holeWidth,
   coverThickness,
   originCover + FreeCAD.Vector(35, (width - holeWidth)/2, 0), # 
   dr ) 

doc.recompute() 

# fillet outside edges of part being removed to hold solar panel
# both edge ends at coverThickness
# edge ends all at zero height 
edges=[]
for e in solarHole.Edges :
   if (e.Vertexes[0].Point[2] == 0.0 ) and \
      (e.Vertexes[1].Point[2] == 0.0 ) : edges.append(e)

solarHole = solarHole.makeChamfer(2.5, edges)


#Part.show(outside)
#Part.show(solarHole)
 
holes = [solarHole ]

#LED holes
#makeCylinder ( radius,height,[pnt,dir,angle] )

# position
p = originCover


holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness,  
                   p + LEDcenters[0],  dr, 360 ) ) #LED 1

holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness,  
                   p + LEDcenters[1],  dr, 360 ) ) #LED 2

holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness, 
                   p + LEDcenters[2],  dr, 360 ) ) #LED 3

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

CoverRemove = doc.addObject("Part::Feature","CoverRemove")
CoverRemove.Shape = inside.fuse(holes)

cover=doc.addObject("Part::Cut","CoverWithHoles")
cover.Base = cover_outside
# not sure why next two have opposite effect on what is left.
cover.Tool = CoverRemove
#cover.Tool = inside.fuse(holes)


doc.SolarCover.addObject(doc.CoverWithHoles) #mv CoverWithHoles (body) into part SolarCover

doc.recompute() 


# add prongs

prongs = []

w = prongWidth / 2

# 0.2 is for clearance for catch to click into place

h = backThickness + prongCatchDepth + 0.2 
# add 2 * prongBump to length to make the prong long enough for taper

prongLength = h + 2 * prongBump

for pos in prongs_left :
   p = originCover + FreeCAD.Vector(pos[0] -w,  pos[1],  coverThickness)

   prongs.append(
       Part.makeBox( prongWidth, prongThickness, prongLength, p, dr ) )

   #catch 
   z = Part.makeBox( prongWidth,   prongBump,        2 * prongBump, 
            p + FreeCAD.Vector(0, prongThickness, h), dr )

   # fillet edges to get catch taper
   edges=[]

   # both edge ends at prong ends and
   # both edge ends at inside (not at outside)
   for e in z.Edges :
      if (e.Vertexes[0].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[1].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[0].Point[1] == p[1] + prongThickness + prongBump ) and \
         (e.Vertexes[1].Point[1] == p[1] + prongThickness + prongBump ): edges.append(e)

   z = z.makeChamfer(prongBump - 0.2, edges) 

   prongs.append(z)

for pos in prongs_right :
   p = originCover + FreeCAD.Vector(pos[0] -w,  pos[1] - prongThickness, coverThickness)

   prongs.append(
       Part.makeBox( prongWidth, prongThickness, prongLength, p, dr ) )

   #catch
   z = Part.makeBox( prongWidth,   prongBump,        2 * prongBump,
            p + FreeCAD.Vector(0, -prongBump, h), dr )

   edges=[]
   for e in z.Edges :
      if (e.Vertexes[0].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[1].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[0].Point[1] == p[1]  - prongBump    ) and \
         (e.Vertexes[1].Point[1] == p[1]  - prongBump    ): edges.append(e)

   z = z.makeChamfer(prongBump - 0.2, edges) 

   prongs.append(z)

for pos in prongs_bottom :
   p = originCover + FreeCAD.Vector(pos[0] - prongThickness,  pos[1] - w, coverThickness)

   prongs.append(
       Part.makeBox( prongThickness, prongWidth,  prongLength, p, dr ) )

   #catch
   z = Part.makeBox(  prongBump,     prongWidth,      2 * prongBump,
            p + FreeCAD.Vector( - prongBump, 0, h), dr )

   edges=[]
   for e in z.Edges :
      if (e.Vertexes[0].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[1].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[0].Point[0] == p[0] - prongBump   ) and \
         (e.Vertexes[1].Point[0] == p[0] - prongBump   ): edges.append(e)

   z = z.makeChamfer(prongBump - 0.2, edges) 

   prongs.append(z)

for pos in prongs_top :
   p = originCover + FreeCAD.Vector(pos[0],  pos[1] - w, coverThickness)

   prongs.append(
       Part.makeBox( prongThickness, prongWidth, prongLength, p, dr ) )

   #catch
   z = Part.makeBox(  prongBump,     prongWidth,     2 * prongBump, 
                p + FreeCAD.Vector(prongThickness, 0, h), dr )

   edges=[]
   for e in z.Edges :
      if (e.Vertexes[0].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[1].Point[2] == coverThickness + prongLength) and \
         (e.Vertexes[0].Point[0] == p[0] + prongThickness + prongBump  ) and \
         (e.Vertexes[1].Point[0] == p[0] + prongThickness + prongBump  ): edges.append(e)

   z = z.makeChamfer(prongBump - 0.2, edges) 

   prongs.append(z)

#def fuseIntoAndAddTo(lst, fuseName, AddToName) : 
#    fuse = doc.addObject("Part::Feature", fuseName)
#    fuse.Shape = lst[0].fuse(lst)   
#    #doc.addObject("Part::MultiFuse","fuseName")
#    #doc.fuseName.Shapes = lst
#    doc.recompute() 
#fuseIntoAndAddTo(prongs, "Prongs", "CoverWithHoles")

CoverAdd = doc.addObject("Part::Feature","Prongs")
CoverAdd.Shape = prongs[0].fuse(prongs)
#CoverAdd = doc.addObject("Part::Feature","Prongs").Shape = prongs[0].fuse(prongs)

doc.addObject("Part::MultiFuse","CoverFusion").Shapes = [doc.CoverWithHoles, doc.Prongs,]

doc.SolarCover.addObject(doc.CoverFusion) #mv Fusion into part SolarCover

doc.recompute() 

# fillet prong connection to cover
edges=[]
for e in doc.CoverFusion.Shape.Edges :
   for p in e.Vertexes : 
       p0 =  p.Point[0] - originCover[0]
       p1 =  p.Point[1] - originCover[1]
       if p.Point[2] == coverThickness :
          if       0.5      < p1  <     10.0      : edges.append(e)  # left
          if  width  - 10.0 < p1  < width  - 0.5  : edges.append(e)  # right
          if  length - 10.0 < p0  < length - 0.5  : edges.append(e)  # bottom
          if       0.5      < p0  <     10.0      : edges.append(e)  # top

edges = list(set(edges)) # unique elements

coverPreFinished = doc.addObject("Part::Feature","CoverPreFinished")
coverPreFinished.Shape = doc.CoverFusion.Shape.makeFillet(0.5, edges)

doc.SolarCover.addObject(doc.CoverPreFinished) #mv PreFinished into part SolarCover

doc.recompute() 

makeSTL("SolarCover", "CoverPreFinished")

#NEXT SOMEHOW MANGLES STL GENERATION
# Fillet cover outside edges
edges=[]
for e in doc.CoverPreFinished.Shape.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == 0 :
         if p.Point[0] == originCover[0]          : edges.append(e)
         if p.Point[0] == originCover[0] + length : edges.append(e)

edges = list(set(edges)) # unique elements

# z = doc.CoverCoverPreFinished.Shape.makeChamfer(3.0, edges) 
coverFinished = doc.addObject("Part::Feature","CoverFinished")
coverFinished.Shape = doc.CoverPreFinished.Shape.makeFillet(2.5, edges)
doc.SolarCover.addObject(doc.CoverFinished) #mv Finished into part SolarCover

doc.recompute() 

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarCover object construction complete.\n')


makeSTL("SolarCover", "CoverFinished")
