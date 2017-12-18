import pya

'''
Get Technology functions:
 - get_technology_by_name(tech_name)
 - get_technology()
 - get_layout_variables(), also returns layout, cell.

return:
TECHNOLOGY['dbu'] is the database unit
TECHNOLOGY['layer name'] is a LayerInfo object. 

'''
# Read the layer table for a given technology.
def get_technology_by_name(tech_name):
    technology = {}
    if int(pya.Application.instance().version().split('.')[1]) > 24:
      technology['dbu'] = pya.Technology.technology_by_name(tech_name).dbu
    else:
      technology['dbu'] = 0.001
    lyp_file = pya.Technology.technology_by_name(tech_name).eff_layer_properties_file()	
    file = open(lyp_file, 'r') 
    layer_dict = xml_to_dict(file.read())['layer-properties']['properties']
    file.close()
     
    for k in layer_dict:
      layerInfo = k['source'].split('@')[0]
      if 'group-members' in k:
        # encoutered a layer group, look inside:
        j = k['group-members']
        if 'name' in j:
          layerInfo = j['source'].split('@')[0]
          technology[j['name']] = pya.LayerInfo(int(layerInfo.split('/')[0]), int(layerInfo.split('/')[1]))
        else:
          for j in k['group-members']:
            print(j['source'])
            layerInfo = j['source'].split('@')[0]
            technology[j['name']] = pya.LayerInfo(int(layerInfo.split('/')[0]), int(layerInfo.split('/')[1]))
      else:
        technology[k['name']] = pya.LayerInfo(int(layerInfo.split('/')[0]), int(layerInfo.split('/')[1]))
    return technology
# end of get_technology_by_name(tech_name)
# test example: give it a name of a technology, e.g., GSiP
# print(get_technology_by_name('EBeam'))
# print(get_technology_by_name('GSiP'))

#Keeps SiEPIC global variables and libraries consistent with technology of current layout
def get_technology():
    technology = {}
    technology['Waveguide'] = pya.LayerInfo(1, 0)
    lv = pya.Application.instance().main_window().current_view()
    if lv == None:
      # no layout open; return an default technology
      print ("No view selected")
      technology['dbu']=0.001
      return technology
#      raise Exception("No view selected")
    
    if int(pya.Application.instance().version().split('.')[1]) > 24:
      pass
      technology['dbu'] = pya.Technology.technology_by_name(lv.active_cellview().technology).dbu
    else:
      technology['dbu'] = 0.001
    itr = lv.begin_layers()
    while True:
      if itr == lv.end_layers():
        break
      else:
        layerInfo = itr.current().source.split('@')[0]
        if layerInfo == '*/*':
          # likely encoutered a layer group, skip it
          pass
        else:
          technology[itr.current().name] = pya.LayerInfo(int(layerInfo.split('/')[0]), int(layerInfo.split('/')[1]))
        itr.next()
    return technology

def get_layout_variables():
  from .utils import get_technology
  TECHNOLOGY = get_technology()

  # Configure variables to find in the presently selected cell:
  lv = pya.Application.instance().main_window().current_view()
  if lv == None:
    print("No view selected")
    raise UserWarning("No view selected. Make sure you have an open layout.")
  # Find the currently selected layout.
  ly = pya.Application.instance().main_window().current_view().active_cellview().layout() 
  if ly == None:
    raise UserWarning("No layout. Make sure you have an open layout.")
  # find the currently selected cell:
  cv = pya.Application.instance().main_window().current_view().active_cellview()
  cell = pya.Application.instance().main_window().current_view().active_cellview().cell
  if cell == None:
    raise UserWarning("No cell. Make sure you have an open layout.")


  return TECHNOLOGY, lv, ly, cell
   
  

#Define an Enumeration type for Python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

#Return all selected paths. If nothing is selected, select paths automatically
def select_paths(lyr, cell = None):
  lv = pya.Application.instance().main_window().current_view()
  if lv == None:
    raise Exception("No view selected")

  if cell is None:
    ly = lv.active_cellview().layout() 
    if ly == None:
      raise Exception("No active layout")
    cell = lv.active_cellview().cell
    if cell == None:
      raise Exception("No active cell")
  else:
    ly = cell.layout()
    
  selection = lv.object_selection
  if selection == []:
    itr = cell.begin_shapes_rec(ly.layer(lyr))
    while not(itr.at_end()):
      if itr.shape().is_path():
        selection.append(pya.ObjectInstPath())
        selection[-1].layer = ly.layer(lyr)
        selection[-1].shape = itr.shape()
        selection[-1].top = cell.cell_index()
        selection[-1].cv_index = 0
      itr.next()
    lv.object_selection = selection
  else:
    lv.object_selection = [o for o in selection if (not o.is_cell_inst()) and o.shape.is_path()]
    
  return lv.object_selection
  
#Return all selected waveguides. If nothing is selected, select waveguides automatically
def select_waveguides(cell = None):
  lv = pya.Application.instance().main_window().current_view()
  if lv == None:
    raise Exception("No view selected")

  if cell is None:
    ly = lv.active_cellview().layout() 
    if ly == None:
      raise Exception("No active layout")
    cell = lv.active_cellview().cell
    if cell == None:
      raise Exception("No active cell")
  else:
    ly = cell.layout()

  selection = lv.object_selection
  if selection == []:
    for instance in cell.each_inst():
      if instance.cell.basic_name() == "Waveguide":
        selection.append(pya.ObjectInstPath())
        selection[-1].top = cell.cell_index()
        selection[-1].append_path(pya.InstElement.new(instance))
    lv.object_selection = selection
  else:
    lv.object_selection = [o for o in selection if o.is_cell_inst() and o.inst().cell.basic_name() == "Waveguide"]
    
  return lv.object_selection
  
#Find the angle between two vectors (not necessarily the smaller angle)
def angle_b_vectors(u, v):
  from math import atan2, pi
  return (atan2(v.y, v.x)-atan2(u.y, u.x))/pi*180

#Find the angle between two vectors (will always be the smaller angle)
def inner_angle_b_vectors(u, v):
  from math import acos, pi
  return acos((u.x*v.x+u.y*v.y)/(u.abs()*v.abs()))/pi*180

#Find the angle of a vector
def angle_vector(u):
  from math import atan2, pi
  return (atan2(u.y,u.x))/pi*180

#Truncate the angle
def angle_trunc(a, trunc):
  return ((a%trunc)+trunc)%trunc


# Calculate the recommended number of points in a circle, based on 
# http://stackoverflow.com/questions/11774038/how-to-render-a-circle-with-as-few-vertices-as-possible
def points_per_circle(radius):
  from math import acos, pi, ceil
  from .utils import get_technology
  TECHNOLOGY = get_technology()
  err = 1e3*TECHNOLOGY['dbu']/2
  return int(ceil(2*pi/acos(2 * (1 - err / radius)**2 - 1))) if radius > 0.1 else 100

#Create an arc spanning from start to stop in degrees
def arc(radius, start, stop):
  from math import pi, cos, sin
  from .utils import points_per_circle
  circle_fraction = abs(start-stop) / 360.0
  n = int(points_per_circle(radius) * circle_fraction)
  if n == 0: n = 1
  # need to make sure that the increment exactly matches the start & stop
  da = 2 * pi / n * circle_fraction # increment, in radians
  start = start*pi/180.0
  stop = stop*pi/180.0
  
  return [pya.Point.from_dpoint(pya.DPoint(radius*cos(start+i*da), radius*sin(start+i*da))) for i in range(0, n+1) ]


#Create a bezier curve. While there are parameters for start and stop in degrees, this is currently only implemented for 90 degree bends
def arc_bezier(radius, start, stop, bezier):
  from math import sin, cos, pi
  N=100
  L = radius  # effective bend radius / Length of the bend
  diff = 1/(N-1)
  xp=[0, (1-bezier)*L, L, L]
  yp=[0, 0, bezier*L, L]
  xA = xp[3] - 3*xp[2] + 3*xp[1] - xp[0]
  xB = 3*xp[2] - 6*xp[1] + 3*xp[0]
  xC = 3*xp[1] - 3*xp[0]
  xD = xp[0]
  yA = yp[3] - 3*yp[2] + 3*yp[1] - yp[0]
  yB = 3*yp[2] - 6*yp[1] + 3*yp[0]
  yC = 3*yp[1] - 3*yp[0]
  yD = yp[0]
  
  pts = [pya.Point(-L,0) + pya.Point(xD, yD)]
  for i in range(1, N):
    t = i*diff
    pts.append(pya.Point(-L,0) + pya.Point(t**3*xA + t**2*xB + t*xC + xD, t**3*yA + t**2*yB + t*yC + yD))
  return [pt + pya.Point(L, -L) for pt in pts]

#Take a list of points and create a polygon of width 'width' 
def arc_to_waveguide(pts, width):
  return pya.Polygon(translate_from_normal(pts, -width/2.) + translate_from_normal(pts, width/2.)[::-1])

#Translate each point by its normal a distance 'trans'
def translate_from_normal(pts, trans):
  from math import cos, sin, pi
  d = 1/(len(pts)-1)
  
  a = angle_vector(pts[1]-pts[0])*pi/180 + (pi/2 if trans > 0 else -pi/2)
  tpts = [pts[0] + pya.Point(abs(trans)*cos(a), abs(trans)*sin(a))]
  
  for i in range(1, len(pts)-1):
    dpt = (pts[i+1]-pts[i-1])*(2/d)
    tpts.append(pts[i] + pya.Point(-dpt.y, dpt.x)*(trans/1/dpt.abs()))
    
  a = angle_vector(pts[-1]-pts[-2])*pi/180 + (pi/2 if trans > 0 else -pi/2)
  tpts.append(pts[-1] + pya.Point(abs(trans)*cos(a), abs(trans)*sin(a)))
  
  return tpts

#Check if point c intersects the segment defined by pts a and b
def pt_intersects_segment(a, b, c):
  """ How can you determine a point is between two other points on a line segment?
  http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
  by Cyrille Ka.  Check if c is between a and b? """
  cross = abs((c.y - a.y) * (b.x - a.x) - (c.x - a.x) * (b.y - a.y))
  if round(cross, 5) != 0 : return False

  dot = (c.x - a.x) * (b.x - a.x) + (c.y - a.y)*(b.y - a.y)
  if dot < 0 : return False
  return False if dot > (b.x - a.x)*(b.x - a.x) + (b.y - a.y)*(b.y - a.y) else True

#Add bubble to a cell
# Example
# cell = pya.Application.instance().main_window().current_view().active_cellview().cell
# layout_pgtext(cell, LayerInfo(10, 0), 0, 0, "test", 1)
def layout_pgtext(cell, layer, x, y, text, mag, inv = False):
  pcell = cell.layout().create_cell("TEXT", "Basic", {"text": text, 
                                                      "layer": layer, 
                                                      "mag": mag,
                                                      "inverse": inv })
  dbu = cell.layout().dbu
  cell.insert(pya.CellInstArray(pcell.cell_index(), pya.Trans(pya.Trans.R0, x/dbu, y/dbu)))

def find_automated_measurement_labels(cell, LayerTextN):
  # example usage:
  # topcell = pya.Application.instance().main_window().current_view().active_cellview().cell
  # LayerText = pya.LayerInfo(10, 0)
  # LayerTextN = topcell.layout().layer(LayerText)
  # find_automated_measurement_labels(topcell, LayerTextN)
  t = ''
  dbu = cell.layout().dbu
  iter = cell.begin_shapes_rec(LayerTextN)
  i=0
  while not(iter.at_end()):
    if iter.shape().is_text():
      text = iter.shape().text
      if text.string.find("opt_in") > -1:
        i+=1
        text2 = iter.shape().text.transformed(iter.itrans())
        t += "label: %s, location: (%s, %s) <br>" %(text.string, text2.x*dbu, text2.y*dbu )
    iter.next()
  t += "<br>*** Number of automated measurement labels: %s.<br>" % i
  return t

try:
  advance_iterator = next
except NameError:
  def advance_iterator(it):
    return it.next()
    

# XML to Dict parser, from:
# https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary-in-python/10077069
def etree_to_dict(t):
  from collections import defaultdict
  d = {t.tag: {} if t.attrib else None}
  children = list(t)
  if children:
    dd = defaultdict(list)
    for dc in map(etree_to_dict, children):
      for k, v in dc.items():
        dd[k].append(v)
    d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
  if t.attrib:
    d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
  if t.text:
    text = t.text.strip()
    if children or t.attrib:
      if text:
        d[t.tag]['#text'] = text
    else:
      d[t.tag] = text
  return d

def xml_to_dict(t):
  from xml.etree import cElementTree as ET
  e = ET.XML(t)
  return etree_to_dict(e)
  