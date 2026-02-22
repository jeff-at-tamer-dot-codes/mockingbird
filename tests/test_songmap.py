import xml.etree.ElementTree as ET
import pytest
from mockingbird.ast import Var, Func, Appl
from mockingbird.songmap import layout, render

IDENTITY = Func(Var(0))

# --- Layout tests ---

def test_identity_layout_structure():
  lo = layout(IDENTITY)
  assert len(lo.boxes) == 1
  assert len(lo.pipes) == 1
##

def test_identity_box_dimensions():
  lo = layout(IDENTITY)
  box = lo.boxes[0]
  assert box.rect.width > 0
  assert box.rect.height > 0
##

def test_identity_ear_on_left_edge():
  lo = layout(IDENTITY)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_identity_throat_on_right_edge():
  lo = layout(IDENTITY)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_identity_ear_throat_vertically_centered():
  lo = layout(IDENTITY)
  box = lo.boxes[0]
  mid_y = box.rect.y + box.rect.height / 2
  assert box.ear.y == mid_y
  assert box.throat.y == mid_y
##

def test_identity_pipe_connects_ear_to_throat():
  lo = layout(IDENTITY)
  box = lo.boxes[0]
  pipe = lo.pipes[0]
  assert pipe.points[0] == box.ear
  assert pipe.points[-1] == box.throat
##

# --- SVG tests ---

def test_identity_svg_valid_xml():
  svg = render(IDENTITY)
  ET.fromstring(svg)
##

def test_identity_svg_has_rect():
  svg = render(IDENTITY)
  root = ET.fromstring(svg)
  rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
  assert len(rects) == 1
##

def test_identity_svg_has_dashed_rect():
  svg = render(IDENTITY)
  root = ET.fromstring(svg)
  rect = root.find(".//{http://www.w3.org/2000/svg}rect")
  assert rect is not None
  assert rect.get("stroke-dasharray") is not None
##

def test_identity_svg_has_polyline():
  svg = render(IDENTITY)
  root = ET.fromstring(svg)
  polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
  assert len(polylines) == 1
##

def test_identity_svg_has_ear_and_throat():
  svg = render(IDENTITY)
  root = ET.fromstring(svg)
  paths = root.findall(".//{http://www.w3.org/2000/svg}path")
  assert len(paths) == 2
##

# --- Error tests ---

def test_appl_raises():
  with pytest.raises(NotImplementedError):
    layout(Appl(Var(0), Var(1)))
  ##
##

def test_nested_func_raises():
  with pytest.raises(NotImplementedError):
    layout(Func(Func(Var(0))))
  ##
##

def test_bare_var_raises():
  with pytest.raises(NotImplementedError):
    layout(Var(0))
  ##
##
