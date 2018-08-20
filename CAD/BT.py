# Copyright 2018 Paul Gilbert
#CC BY-SA 4.0

#This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. 
#To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/ or send a 
#letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

#import FreeCAD, FreeCADGui
import Part, PartDesignGui
import Mesh, MeshPart, MeshPartGui
import math

####### define utilities ###################

def makeSTL(part, body = "Box") :
   ''' 
   Generate an STL mesh file. part is string used to generate stl file name.
   body is a string indicating an object in doc that has a .Shape attribute
   ''' 
   
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


def hexHole(width = 6.3, depth = 20.0, face_norm = FreeCAD.Vector(1.0, 0, 0),
        center = FreeCAD.Vector(0, 0, 0)):
   ''' 
   Generate a hex hole suitable for bolt nut.
   width is face to face across hex nut hole (not vertexes circle diameter).
   face_norm is normal vector to one of the hex faces, as if center were at zero, 
   used to orient the hex hole.
   depth is positive in the positive z direction.
   dr is rotation axis = direction of hole. This could be an argument with default z-axis
   but nothing other than z-axis has been tested.
   
   Hex nuts are supposed to be 1.6 D across faces and 1.8 D across vertexes, 
   so M3 nut is 4.8mm face to face and 5.4mm vertex to vertex. (The M3 nuts used measure
   5.3mm face to face.) Width 6.3 for holes gives clearance. Previously tried smaller but
   they were too tight, possibly because of print material swelling into the hole. 
   This could change with better printer calibration.
   
   Printing without support material (for were hex hole becomes bore) seems to work better.
   The hole is cleaner. Set width = 6.3 without support. Needed 6.5 in testing when support
   material was used. The problem was that the vertexes of the holes were not clean.
   ''' 
   
   dr = FreeCAD.Vector(0, 0, 1)
  
   # 60 deg between vertices, 30 between normal to face and vertex at end of that face.
   r = (width/2) / math.cos(math.pi/6) # radius of vertexes, math.pi/6 = 30 deg
   v1 = App.Rotation(dr,  30).multVec(face_norm) # direction but not yet right length
   v1.Length = r
   v2 = App.Rotation(dr,  60).multVec(v1)
   v3 = App.Rotation(dr,  60).multVec(v2)
   v4 = App.Rotation(dr,  60).multVec(v3)
   v5 = App.Rotation(dr,  60).multVec(v4)
   v6 = App.Rotation(dr,  60).multVec(v5)
   
   e1 = Part.LineSegment(v6, v1).toShape()
   e2 = Part.LineSegment(v1, v2).toShape()
   e3 = Part.LineSegment(v2, v3).toShape()
   e4 = Part.LineSegment(v3, v4).toShape()
   e5 = Part.LineSegment(v4, v5).toShape()
   e6 = Part.LineSegment(v5, v6).toShape()
   
   head = Part.Face(Part.Wire([e1, e2, e3, e4, e5, e6]))
   if depth < 0 : dr = -1 * dr
   dr.Length = abs(depth)
   hex_hole = head.extrude(dr)
   hex_hole.Placement.Base = center
   return hex_hole

# ex = hexHole(center = FreeCAD.Vector(10, 10, 0))
# ex.Placement
# Part.show(ex)

FreeCAD.Console.PrintMessage('finished utilities definition.\n')

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
height = 45  # front to back of box, not including cover and back

wall = 13.0
backwall = 5.0
indent = 5.0  # amount that box interior is bigger than box opening
coverThickness = 3.0 # 2.0 might work here, but solar opening needs fine adjustment
backThickness  = 3.0

GPSwallHeight = 28

# GPSwallHeight is highest  part of solarBack, and the battery must fit between it and
# inside back of the Box, so
#  height - backwall > GPSwallHeight + 9  (9mm thick battery)
#   45    - 5        >    28        + 9

sp = 3.7 # previously 3.5 distance from box edge to bolt hole centers
bolt_length = 25 # used to calculate recess for nut, effectively shortest possible bolt.
bolt_hole_dia  = 3.8 # 3.8mm for M3 with clearance

#  hex holes for bolts are oriented differently on the sides and on top-bottom, 
#  so they don't go though.
bolts_holes_sides = ((20, sp),         (length/2, sp),         (length -20, sp),
                     (20, width - sp), (length/2, width - sp), (length -20, width - sp))

bolts_holes_tb = ((   sp,       20),    (     sp,     width/2),    (     sp,     width - 20),
                  (length - sp, 20),    (length - sp, width/2),    (length - sp, width - 20) )


bolts_holes = bolts_holes_sides + bolts_holes_tb

# pongs bolts for charging go tight through base (sealed) and heads protrude through cover.
# space enough to fasten diode bridge.
pong_holes = ((18, 23),  (29,23))
pong_hole_dia  = 3.6 # 3.6mm for M3 no clearance
pong_head_dia  = 6.2 # for M3

glandTongue = 2    # depth into gland, width needs clearance
glandWidth  = 3.6  # 20% larger than 3.0 seal dia.
glandDepth  = 4.4  # glandTongue + 75% of 3.0 seal dia.
glandCornerRadius_inside  = 5.0   # previously 1.5
glandCornerRadius_outside = 8.5   # previously 1.5


#  LEDs  vertical at top
LEDcenters = (FreeCAD.Vector( 16, 35, 0),
              FreeCAD.Vector( 24, 35, 0),
              FreeCAD.Vector( 32, 35, 0))
LEDholeDia   = 5.6
LEDbaseDia   = 6.2
LEDholeDepth = 4.0    #should not go all the wy through cover and back
LEDwireSlotWidth   = 3.0
LEDwireSlotLength  = LEDholeDia - 0.2

strapSlotWidth  = 40.0  # previusly 25.0
strapSlotHeight = 5.0
strapSlotPos    = (28, 93.5)# previusly (28, 108.5)

FreeCAD.Console.PrintMessage('finished common variables definition.\n')

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

Gui.ActiveDocument=Gui.getDocument(docName)  # this adds origin to MainBox
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

# type(box_out.makeFillet(6, edges)) is <type 'Part.Shape'>
# type(box_outside.Shape)            is <type 'Part.Compound'>

doc.recompute() 

# Part.makeBox ( length,width,height,[pnt,dir] )
# pnt,dir are used in next and they do make a difference, but they 
# do not seem to be recorded in .Placement.Base 

# indent below gland to make lip
lipDepth =  5 # previously 10 
lip = height -  backwall - lipDepth

opening = Part.makeBox(          
   length - 2 * wall,
   width  - 2 * wall,
   lipDepth,               
   originBox + FreeCAD.Vector(wall, wall, height -  lipDepth),
   FreeCAD.Vector(0,0,1) ) 

#Part.show(opening)
 
holes = []  # these will be fused to opening and removed

interiorBox =Part.makeBox(          
   length - 2 * (wall - indent),
   width  - 2 * (wall - indent),
   lip ) 

#  chamfer bottom so it does not cut into strap holes
edges = []
for e in interiorBox.Edges :
   if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == 0 :
       edges.append(e)

edges = list(set(edges)) # unique elements

# Size 11.0 adjusted to not cut into strap holes and leave some material.
# This has to print on chamfer ange (45 deg) and may be difficult over holes.
interior = interiorBox.makeChamfer(11.0, edges) # 0 placement Base

#  chamfer top so support material is not needed
edges = []
for e in interiorBox.Edges :
   if e.Vertexes[0].Point[2] == lip and e.Vertexes[1].Point[2] == lip :
       edges.append(e)

edges = list(set(edges)) # unique elements

# chamfer size indent makes it coincide with lip inside edge
interior = interior.makeChamfer(indent, edges) # 0 placement Base

interior.Placement.Base = originBox + FreeCAD.Vector(wall - indent, wall - indent, backwall) 

#type(interiorBox)       is <type 'Part.Solid'>
#type(interior) is <type 'Part.Shape'>

doc.recompute() 

#Part.show(interiorBox)
#Part.show(interior)

holes.append(interior)

doc.recompute() 



# bolt holes 
for pos in bolts_holes :
   p = originBox + FreeCAD.Vector(pos[0],  pos[1],  0)
   holes.append(Part.makeCylinder( bolt_hole_dia /2, height, p, dr, 360 ) )

# recess for nuts, oriented differently on sides and on top-bottom
recess = height + coverThickness + backThickness  - (bolt_length -5)  # about 31
for pos in bolts_holes_tb :
   p = originBox + FreeCAD.Vector(pos[0],  pos[1],  0)
   z = hexHole(width = 5.5, depth = recess, face_norm = FreeCAD.Vector(1.0, 0, 0), center = p)
   holes.append(z)

for pos in bolts_holes_sides :
   p = originBox + FreeCAD.Vector(pos[0],  pos[1],  0)
   z = hexHole(width = 5.5, depth = recess, face_norm = FreeCAD.Vector(0, 1.0, 0), center = p)
   holes.append(z)

# Part.show(z)

# slots for straps through back edges
# angled at 55° (previously 45° but changed to improve overhang printing)
# 50mm is long enough to go all the way through
# starting 10mm out is enough ensure removed rectangle does not start inside the wall.
# starting 30mm from edge is enough to leave edge and not to pierce inside.
# slot positioning point is below slot on the left and above slot on the right.
# 27 on left is about 10+strapSlotHeight (angled) on the right

for pos in strapSlotPos :
   # left slots: remove rectangles positioned on the side and extending downward at 55° 
   z = Part.makeBox(strapSlotWidth, 50, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, -10, 27), 
                              FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -55))   # -55° about X) 
   holes.append(z ) 

   # this is a bit crude, identify edge and round would be better
   # flatten edge at slot side opening to distribute strap tension load
   z = Part.makeBox(strapSlotWidth, 3, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, 0, 9),
                              FreeCAD.Rotation(dr, 0)) 
   holes.append(z ) 

   # right slots: remove rectangles positioned on the bottom and extending upward at 55°
   z = Part.makeBox(strapSlotWidth, 50, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, width-10-strapSlotHeight, -10), 
                              FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 55))   # 55° about X) 
   holes.append(z ) 

   # flatten edge at slot side opening to distribute strap tension load
   z = Part.makeBox(strapSlotWidth, 3, strapSlotHeight)
   z.Placement = FreeCAD.Placement(originBox + FreeCAD.Vector( pos, width-3, 9),
                              FreeCAD.Rotation(dr, 0)) 
   holes.append(z ) 


# slot for extra attachment line (saftey)
# bottom edge: remove 5x5 rectangle positioned on the bottom and extending upward at 45°

pos = 35 # cannot be center because of bolt hole
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

# For some reason this works doing the corners first then the botton, but not the other way.

gland3 = gland_outside.cut(gland_inside)
# fillet all gland corners (verticle edges so x and y coordinates of 
#    end points are equal)
edgesCi=[]
edgesCo=[]
for e in gland3.Edges :
   if e.Vertexes[0].Point[0] ==  e.Vertexes[1].Point[0] and \
      e.Vertexes[0].Point[1] ==  e.Vertexes[1].Point[1] :
         if e.Vertexes[0].Point[0] in ( w, length - w ) :
                edgesCi.append(e)
         else : edgesCo.append(e)

gland3i =  gland3.makeFillet(glandCornerRadius_inside,  list(set(edgesCi))) 
gland2  = gland3i.makeFillet(glandCornerRadius_outside, list(set(edgesCo))) 

# fillet gland bottom edges (both ends at height h)
h = height - glandDepth
edgesB=[]
for e in gland2.Edges :
   if (e.Vertexes[0].Point[2] == h ) and \
      (e.Vertexes[1].Point[2] == h ) : edgesB.append(e)

edgesB = list(set(edgesB)) # unique elements

gland = gland2.makeFillet(1.5, edgesB) # radius = seal  dia/2 =3/2 

holes.append(gland )

doc.recompute() 

FreeCAD.Console.PrintMessage('finished slot definition.\n')
FreeCAD.Console.PrintMessage('starting compound holes object.\n')

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

remove = doc.addObject("Part::Feature","Remove")
remove.Shape = opening.fuse(holes)
#or something like remove = Part.makeCompound(holes)


# or something like 
# MainBox = box_outside.cut(remove)
# see https://www.freecadweb.org/wiki/Topological_data_scripting


   # slot
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
# (This 3mm is arbitrary, not related to 3mm o-ring cord)
# tongue is narrower by clr on both sides

clr = 0.4  #clearance
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

# fillet all gland corners (verticle edges so x and y coordinates of 
#    end points are equal)

gland_inside = Part.makeBox( length - 2 * (w - clr), 
                              width - 2 * (w - clr),  glandTongue, 
               originBack + FreeCAD.Vector(w - clr, w - clr, backThickness), dr )

edgesCi=[]
for e in gland_inside.Edges :
   if e.Vertexes[0].Point[0] ==  e.Vertexes[1].Point[0] and \
      e.Vertexes[0].Point[1] ==  e.Vertexes[1].Point[1] : edgesCi.append(e)

gland_inside  =  gland_inside.makeFillet(glandCornerRadius_inside,  list(set(edgesCi)))



gland_outside = Part.makeBox( length - 2 * (w + clr - glandWidth), 
                               width - 2 * (w + clr - glandWidth),  glandTongue, 
            originBack + FreeCAD.Vector(w + clr - glandWidth, w + clr - glandWidth, 
                                        backThickness), dr )
edgesCo=[]
for e in gland_outside.Edges :
   if e.Vertexes[0].Point[0] ==  e.Vertexes[1].Point[0] and \
      e.Vertexes[0].Point[1] ==  e.Vertexes[1].Point[1] : edgesCo.append(e)

gland_outside  =  gland_outside.makeFillet(glandCornerRadius_outside,  list(set(edgesCo)))



glandBack = gland_outside.cut(gland_inside)
#Part.show(inside)
#Part.show(glandBack)

doc.addObject("Part::Feature","Gland").Shape = glandBack
doc.recompute() 


# add wall for GPS. top right beside LEDs.  Add 2.0 for clearance

# vertical
doc.addObject("Part::Feature","GPSv").Shape =  Part.makeBox( 
     15, 2, GPSwallHeight, originBack + FreeCAD.Vector(wall + 2.0, 49, backThickness), dr)

#horizontal
doc.addObject("Part::Feature","GPSh").Shape =  Part.makeBox( 
     2, 30, GPSwallHeight, originBack + FreeCAD.Vector(wall + 15, 49, backThickness),dr)

# small ledge to prevent lifting
doc.addObject("Part::Feature","GPSl").Shape =  Part.makeBox( 
     2, 6, 10, originBack + FreeCAD.Vector(wall + 8, 49, backThickness),dr)


# add walls to support battery during assembly. Midway along length, both sides.
# After assembly they just push the battery to the back of the box.

# battery edges - these form a shallow cradle to help center the battery.
#  There is not enough room in the box opening to have walls for the battery.
# 102=width   102 - 2 * (14 +2) = 70 = near battery width

doc.addObject("Part::Feature","BatL").Shape =  Part.makeBox( 
     20, 1.5, GPSwallHeight+ 2, originBack + FreeCAD.Vector(75,        12.5, backThickness), dr)

doc.addObject("Part::Feature","BatR").Shape =  Part.makeBox( 
     20, 1.5, GPSwallHeight+ 2, originBack + FreeCAD.Vector(87, width - 14.5, backThickness), dr)


#supports (under battery during assembly).
doc.addObject("Part::Feature","BatSupL1").Shape =  Part.makeBox( 
     2, 9, GPSwallHeight, originBack + FreeCAD.Vector(75, 12.5, backThickness),dr)

doc.addObject("Part::Feature","BatSupL2").Shape =  Part.makeBox( 
     2, 9, GPSwallHeight, originBack + FreeCAD.Vector(85, 12.5, backThickness),dr)

doc.addObject("Part::Feature","BatSupL3").Shape =  Part.makeBox( 
     10, 2, GPSwallHeight, originBack + FreeCAD.Vector(75, 19.5, backThickness),dr)


doc.addObject("Part::Feature","BatSupR1").Shape =  Part.makeBox( 
     2, 10, GPSwallHeight, originBack + FreeCAD.Vector(87, width - (14+10), backThickness),dr)

doc.addObject("Part::Feature","BatSupR2").Shape =  Part.makeBox( 
     2, 10, GPSwallHeight, originBack + FreeCAD.Vector(97, width - (14+10), backThickness),dr)

doc.addObject("Part::Feature","BatSupR3").Shape =  Part.makeBox( 
     10, 2, GPSwallHeight, originBack + FreeCAD.Vector(87, width - (14+10), backThickness),dr)


# add stud pins for boards

def makePin(num, x, y, bsRad, bsHt, hdRad, hdHt, part, 
       p = originBack + FreeCAD.Vector(0,  0,  backThickness)) :
   ''' 
   num is string appended to name or body object in doc
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

makePin("1", 106, 17, 3.0/2, 4.0,  1.5/2, 5.0,  "SolarBack") 
makePin("2", 106, 84, 3.0/2, 4.0,  1.5/2, 5.0,  "SolarBack") 
makePin("3", 125, 17, 3.0/2, 4.0,  1.5/2, 5.0,  "SolarBack") 
makePin("4", 125, 84, 3.0/2, 4.0,  1.5/2, 5.0,  "SolarBack") 

# R Pi zero board pins 23x58

makePin("5", 35, 19, 5.0/2, 2.0,  2.2/2, 4.0,  "SolarBack") 
makePin("6", 35, 77, 5.0/2, 2.0,  2.2/2, 4.0,  "SolarBack") 
makePin("7", 58, 19, 5.0/2, 2.0,  2.2/2, 4.0,  "SolarBack") 
makePin("8", 58, 77, 5.0/2, 2.0,  2.2/2, 4.0,  "SolarBack") 

# O Pi zero plus board  pins 42x40

makePin("9",   25, 33, 5.0/2, 2.0,  2.5/2, 4.0,  "SolarBack") 
makePin("10",  25, 73, 5.0/2, 2.0,  2.5/2, 4.0,  "SolarBack") 
makePin("11",  67, 33, 5.0/2, 2.0,  2.5/2, 4.0,  "SolarBack") 
makePin("12",  67, 73, 5.0/2, 2.0,  2.5/2, 4.0,  "SolarBack") 


#  Fuse the body objects 
#  note that edges at fused joint cannot be selected, at least not in GUI view

doc.addObject("Part::MultiFuse","Fusion")
# next causes view to disappear until doc.recompute() 
#in model view this adds  BT>Fusion with [..] bodies but only seen after doc.recompute() 
doc.Fusion.Shapes = [doc.BackOutside, doc.Gland, doc.GPSv, doc.GPSh, doc.GPSl,
    doc.BatL, doc.BatR, doc.BatSupL1, doc.BatSupL2, doc.BatSupL3, doc.BatSupR1, doc.BatSupR2, doc.BatSupR3,
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

# bolt holes 
for pos in bolts_holes :
   p = originBack + FreeCAD.Vector(pos[0],  pos[1],  0)
   holes.append(Part.makeCylinder( bolt_hole_dia /2, height, p, dr, 360 ) )

# pong bolt holes 
for pos in pong_holes :
   p = originBack + FreeCAD.Vector(pos[0],  pos[1],  0)
   holes.append(Part.makeCylinder( pong_hole_dia /2, height, p, dr, 360 ) )


# Solar panel wire hole
holes.append( 
  Part.makeCylinder( 2.0, 5, originBack + FreeCAD.Vector(105, 10.0 + width/2, 0), dr, 360 ) )


#  LED wire slots

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

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarBack object construction complete.\n')


makeSTL("SolarBack", "Back")

#######################################
################ Cover ################
#######################################

# bolt holes 
# see l. 191 in ProjectEnclosure.py re countersink holes 

doc.Tip = doc.addObject('App::Part','SolarCover')

cover_out = Part.makeBox ( length,width,coverThickness)  #,[pnt,dir] )


# bolt holes 
bolt_hole_dia = 3.5 ## redefined from above, less clearance
r1 = bolt_hole_dia / 2.0
boreDepth = coverThickness
for p in bolts_holes :
    bore = Part.makeCylinder( r1, boreDepth)   #, p, dr, 360 ) )
    bore.translate(FreeCAD.Vector(p[0], p[1], 0))  # +originCover +  #, point[2])
    cover_out = cover_out.cut(bore)

# bolt hole countersink 
r2 = 2 * bolt_hole_dia / 2.0  
h = 1.5

for p in bolts_holes:
    sink = Part.makeCone(r2, r1, h)
    sink.translate(FreeCAD.Vector(p[0], p[1], 0))  # +originCover +  #, point[2])
    cover_out = cover_out.cut(sink)

# pong bolt head holes 
for p in pong_holes :
    pong = Part.makeCylinder( pong_head_dia /2, coverThickness) 
    pong.translate(FreeCAD.Vector(p[0], p[1], 0))  
    cover_out = cover_out.cut(pong)


#  round corners
edges = []
for e in cover_out.Edges :
   # holes have edges but only one vertex (I think)
   if len(e.Vertexes) == 2: 
      if e.Vertexes[0].Point[2] == 0 and e.Vertexes[1].Point[2] == coverThickness : edges.append(e)
      if e.Vertexes[1].Point[2] == 0 and e.Vertexes[0].Point[2] == coverThickness : edges.append(e)

edges = list(set(edges)) # unique elements

doc.recompute() 

cover_outside = doc.addObject("Part::Feature","CoverOutside")
cover_outside.Shape = cover_out
cover_outside.Shape = cover_out.makeFillet(6, edges)
cover_outside.Placement.Base = originCover # sensitive to Placement after Shape!

doc.recompute() 

holeLength = 112   # solar panel is 110 x 69. Add 2mm so it sits in better.
holeWidth  =  71   # chamfer will be used to reduce outside edge of hole


solarHole = Part.makeBox(          
   holeLength,
   holeWidth,
   coverThickness,
   originCover + FreeCAD.Vector(40, (width - holeWidth)/2, 0), # 
   dr ) 

doc.recompute() 

# Fillet edges of *part being removed* to hold solar panel.
# These are the edge with ends all at zero height. The result will be that
# the outside of the cover (bottom in layout) is smaller since the fillet
# makes the part removed smaller at the bottom.
edges=[]
for e in solarHole.Edges :
   if (e.Vertexes[0].Point[2] == 0.0 ) and \
      (e.Vertexes[1].Point[2] == 0.0 ) : edges.append(e)

solarHole = solarHole.makeChamfer(1.99, edges)

doc.recompute() 


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


# 1mm larger part of LED holes for LED base
# position
h =  1.0    
p = originCover + FreeCAD.Vector(0, 0, coverThickness - 1  )

holes.append( 
  Part.makeCylinder( LEDbaseDia/2, h, p + LEDcenters[0], dr, 360 ) ) #LED 1

holes.append( 
  Part.makeCylinder( LEDbaseDia/2, h, p + LEDcenters[1], dr, 360 ) ) #LED 2

holes.append( 
  Part.makeCylinder( LEDbaseDia/2, h, p + LEDcenters[2], dr, 360 ) ) #LED 3


#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

CoverRemove = doc.addObject("Part::Feature","CoverRemove")
CoverRemove.Shape = solarHole.fuse(holes)

cover=doc.addObject("Part::Cut","CoverWithHoles")
cover.Base = cover_outside
# not sure why next two have opposite effect on what is left.
cover.Tool = CoverRemove
#cover.Tool = solarHole.fuse(holes)


doc.SolarCover.addObject(doc.CoverWithHoles) #mv CoverWithHoles (body) into part SolarCover

doc.recompute() 

# Fillet cover outside edges
edges=[]
for e in doc.CoverWithHoles.Shape.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == 0 :
         if p.Point[0] == originCover[0]          : edges.append(e)
         if p.Point[0] == originCover[0] + length : edges.append(e)

edges = list(set(edges)) # unique elements

coverFinished = doc.addObject("Part::Feature","CoverFinished")
# this fillet does not seem to be working
coverFinished.Shape = doc.CoverWithHoles.Shape.makeFillet(1.5, edges)
doc.SolarCover.addObject(doc.CoverFinished) #mv CoverFinished into part SolarCover

doc.recompute() 

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarCover object construction complete.\n')


makeSTL("SolarCover", "CoverFinished")
