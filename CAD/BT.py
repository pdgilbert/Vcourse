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

#######################################
################ MainBox ################
#######################################

doc.Tip = doc.addObject('App::Part','MainBox')
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

outside = doc.addObject("Part::Box","Outside") 
outside.Placement.Base = originBox 
outside.Length = length
outside.Width  = width
outside.Height = height
#outside.Label = 'Outside'

#makeBox ( length,width,height,[pnt,dir] )

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

# NEXT IS NOT WORKING
# fillet all edges that touch zero height, so corners and bottom edges
edges=[]

for e in box.Edges :
   for p in e.Vertexes : 
      if p.Point[2] == 0 : edges.append(e)

edges = list(set(edges)) # unique elements
outside = outside.makeFillet(1.5, edges) # radius = seal  dia/2 =3/2 


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

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarBack object construction complete.\n')


makeSTL("SolarBack", "Back")

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

holeLength = 110 - 4    # solar panel is 110 x 69
holeWidth  =  69 - 4

# an option here would be to do this with something like
# solarHole = doc.addObject("Part::Cut","SolarHole") 
# but other holes need to be removed too.

solarHole = Part.makeBox(          
   holeLength,
   holeWidth,
   coverThickness,
   originCover + FreeCAD.Vector(20, (width - holeWidth)/2, 0),
   dr ) 

doc.recompute() 

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

# REATTEMPT HERE SO CHAMFER CAN BE CUT

CoverRemove = doc.addObject("Part::Feature","CoverRemove")
CoverRemove.Shape = inside.fuse(holes)

cover=doc.addObject("Part::Cut","CoverWithHoles")
cover.Base = outside
# not sure why next two have opposite effect on what is left.
cover.Tool = CoverRemove
#cover.Tool = inside.fuse(holes)

# fillet inside edges to hold solar panel
edges=[]

# both edge ends at coverThickness
# edge ends not at outside 
for e in solarHole.Edges :
   if (e.Vertexes[0].Point[2] == coverThickness ) and \
      (e.Vertexes[1].Point[2] == coverThickness ) : edges.append(e)

xcover = doc.CoverWithHoles.makeChamfer(2.0, edges) 

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

doc.addObject("Part::MultiFuse","CoverFusion")
doc.CoverFusion.Shapes = [doc.CoverWithHoles, doc.Prongs,]

doc.SolarCover.addObject(doc.CoverFusion) #mv Fusion into part SolarCover

doc.recompute() 

Gui.activeDocument().resetEdit()
Gui.SendMsgToActiveView("ViewFit")
Gui.activeDocument().activeView().viewAxonometric()

FreeCAD.Console.PrintMessage('SolarCover object construction complete.\n')


makeSTL("SolarCover", "CoverFusion")
