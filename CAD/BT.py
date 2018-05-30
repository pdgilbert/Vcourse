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

#  LEDs
LEDcenter = FreeCAD.Vector( length - 20, width/2, 0)
LEDspacing =FreeCAD.Vector(0, 8, 0)
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
#outside = doc.addObject("Part::Box","Outside") 
#outside.Placement.Base = originBox 
#outside.Length = length
#outside.Width  = width
#outside.Height = height
##outside.Label = 'Outside'
#for e in outside.Shape.Edges :
#   for p in e.Vertexes : 
#      if p.Point[2] == 0 : edges.append(e)
#edges = list(set(edges)) # unique elements
# outside.Shape = outside.Shape.makeFillet(6, edges) 
#doc.recompute() 


out = Part.makeBox ( length,width,height)  #,[pnt,dir] )

for e in out.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == 0 : edges.append(e)

edges = list(set(edges)) # unique elements

outside = doc.addObject("Part::Feature","Outside")
outside.Shape = out.makeFillet(6, edges)

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
# MainBox = outside.cut(remove)
# see https://www.freecadweb.org/wiki/Topological_data_scripting

box=doc.addObject("Part::Cut","Box")
box.Base = outside
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

outside = doc.addObject("Part::Box","BackOutside") 
outside.Placement.Base = originBack 
outside.Length = length
outside.Width  = width
outside.Height = backThickness
#outside.Label = 'Outside'

#makeBox ( length,width,height,[pnt,dir] )

# add Gland
# groove inside is 3mm from inside wall edge, outside is glandWidth more.
# (3mm is arbitrary, not related to 3mm o-ring cord)
# tongue is narrower by clr on both sides

clr = 0.2  #clearance
w = wall - 3  # outside edge of box to inside edge of gland groove
 
gland_inside = Part.makeBox( length - 2 * (w - clr), 
               width - 2 * (w- clr),  glandTongue, 
               originBack + FreeCAD.Vector(w, w, backThickness), dr )


gland_outside = Part.makeBox( length - 2 * (w - clr - glandWidth), 
            width - 2 * (w - clr - glandWidth),  glandTongue, 
            originBack + FreeCAD.Vector(w - clr - glandWidth, 
                                        w - clr - glandWidth, 
                                        backThickness), dr )


glandBack = gland_outside.cut(gland_inside)
#Part.show(inside)

# fillet all gland corners (verticle edges so x and y coordinates of 
#    end points are equal

edges=[]

for e in glandBack.Edges :
   if e.Vertexes[0].Point[0] ==  e.Vertexes[1].Point[0] and \
      e.Vertexes[0].Point[1] ==  e.Vertexes[1].Point[1] :  edges.append(e)

glandBack = glandBack.makeFillet(1.5, edges) # radius = seal  dia/2 =3/2 


#add = [glandBack ]  no need, glandBack is only addition

plus = doc.addObject("Part::Feature","Gland")
plus.Shape = glandBack   # glandBack.fuse(add) glandBack is the only addition

doc.addObject("Part::MultiFuse","Fusion")
doc.Fusion.Shapes = [doc.BackOutside, doc.Gland,]

doc.SolarBack.addObject(doc.Fusion) #mv Fusion into part SolarBack

doc.recompute() 

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
h =  coverThickness + backThickness - LEDholeDepth
p = originBack + LEDcenter + FreeCAD.Vector(0, 0, h)    # main box


# these holes need to be slightly bigger than in cover as the LED base needs to
# go into them, but cover can go on after base is already in.
holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, backThickness,  p,  dr, 360 ) ) #LED center

holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, backThickness,  p -
                                LEDspacing, dr, 360 ) ) #LED left

holes.append( 
  Part.makeCylinder( (LEDholeDia + 1.0) / 2, backThickness,  p +
                                LEDspacing, dr, 360 ) ) #LED right

#  wire slots

p = originBack + LEDcenter - \
           FreeCAD.Vector(LEDwireSlotWidth/2, LEDwireSlotLength/2, 0)

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, 
               backThickness, p, dr ) )#LED center

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, 
               backThickness, p + LEDspacing, dr ) )#LED left

holes.append(Part.makeBox( LEDwireSlotWidth, LEDwireSlotLength, 
               backThickness, p - LEDspacing, dr ) )#LED right

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

doc.recompute() 

# Gui.activeDocument().Outside.Visibility=False
# Gui.activeDocument().Add.Visibility=False
# Gui.ActiveDocument.Fusion.ShapeColor=Gui.ActiveDocument.Outside.ShapeColor
# Gui.ActiveDocument.Fusion.DisplayMode=Gui.ActiveDocument.Outside.DisplayMode

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

edges = list(set(edges)) # unique elements

BackFinished = doc.addObject("Part::Feature","BackFinished")
BackFinished.Shape = doc.Back.Shape.makeFillet(0.5, edges)
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

outside = doc.addObject("Part::Box","CoverOutside") 
outside.Placement.Base = originCover 
outside.Length = length
outside.Width  = width
outside.Height = coverThickness


#makeBox ( length,width,height,[pnt,dir] )

holeLength = 110   # solar panel is 110 x 69
holeWidth  =  69   # chamfer will be used to reduce outside edge of hole

# an option here would be to do this with something like
# solarHole = doc.addObject("Part::Cut","SolarHole") 
# but other holes need to be removed too.

#solarHole =  doc.addObject("Part::Box","SolarHole")          
#solarHole.Placement.Base = originCover + FreeCAD.Vector(20, (width - holeWidth)/2, 0)
#solarHole.Length = holeLength
#solarHole.Width  = holeWidth
#solarHole.Height = coverThickness

solarHole = Part.makeBox(          
   holeLength,
   holeWidth,
   coverThickness,
   originCover + FreeCAD.Vector(20, (width - holeWidth)/2, 0),
   dr ) 

doc.recompute() 

# fillet outside edges of part being removed to hold solar panel
edges=[]

# both edge ends at coverThickness
# edge ends all at zero height 
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
p = originCover + LEDcenter


holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness,  p,  dr, 360 ) ) #LED center

holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness,  p -
                                LEDspacing, dr, 360 ) ) #LED left

holes.append( 
  Part.makeCylinder( LEDholeDia / 2, coverThickness,  p +
                                LEDspacing, dr, 360 ) ) #LED right

#Gui.activeDocument().resetEdit()
#Gui.SendMsgToActiveView("ViewFit")

CoverRemove = doc.addObject("Part::Feature","CoverRemove")
CoverRemove.Shape = inside.fuse(holes)

cover=doc.addObject("Part::Cut","CoverWithHoles")
cover.Base = outside
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

# Fillet cover outside edges
edges=[]
for e in doc.CoverFusion.Shape.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == 0 :
         if p.Point[0] == originCover[0]          : edges.append(e)
         if p.Point[0] == originCover[0] + length : edges.append(e)

edges = list(set(edges)) # unique elements

# z = doc.CoverFusion.Shape.makeChamfer(3.0, edges) 
coverFinished = doc.addObject("Part::Feature","CoverFinished")
coverFinished.Shape = doc.CoverFusion.Shape.makeFillet(2.5, edges)
doc.SolarCover.addObject(doc.CoverFinished) #mv Finished into part SolarCover

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

coverFinished = doc.addObject("Part::Feature","CoverFinished")
coverFinished.Shape = doc.CoverFusion.Shape.makeFillet(0.5, edges)

doc.SolarCover.addObject(doc.CoverFinished) #mv Finished into part SolarCover

doc.recompute() 

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarCover object construction complete.\n')


makeSTL("SolarCover", "CoverFinished")
