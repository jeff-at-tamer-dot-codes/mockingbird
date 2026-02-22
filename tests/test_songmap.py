import xml.etree.ElementTree as ET
import pytest
from mockingbird.ast import Var, Func, Appl
from mockingbird.songmap import layout, render

IDENTITY = Func(Var(0))
MOCKINGBIRD = Func(Appl(Var(0), Var(0)))
DOUBLE_MOCKINGBIRD = Func(Appl(Appl(Var(0), Var(0)), Appl(Var(0), Var(0))))
SELF_APPLY_LEFT = Func(Appl(Appl(Var(0), Var(0)), Var(0)))
SELF_APPLY_RIGHT = Func(Appl(Var(0), Appl(Var(0), Var(0))))

# --- Identity layout tests ---

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

# --- Mockingbird layout tests ---

def test_mockingbird_layout_structure():
  lo = layout(MOCKINGBIRD)
  assert len(lo.boxes) == 1
  assert len(lo.pipes) == 3
  assert len(lo.applicators) == 1
##

def test_mockingbird_box_dimensions():
  lo = layout(MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.rect.width > 0
  assert box.rect.height > 0
##

def test_mockingbird_ear_on_left_edge():
  lo = layout(MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_mockingbird_throat_on_right_edge():
  lo = layout(MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_mockingbird_ear_throat_at_two_thirds():
  lo = layout(MOCKINGBIRD)
  box = lo.boxes[0]
  y_2_3 = box.rect.y + 2 * box.rect.height / 3
  assert box.ear.y == y_2_3
  assert box.throat.y == y_2_3
##

def test_mockingbird_applicator_inside_box():
  lo = layout(MOCKINGBIRD)
  box = lo.boxes[0]
  appl = lo.applicators[0]
  assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
  assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
##

def test_mockingbird_applicator_ports():
  lo = layout(MOCKINGBIRD)
  appl = lo.applicators[0]
  assert appl.func_port.y < appl.center.y
  assert appl.arg_port.x < appl.center.x
  assert appl.out_port.x > appl.center.x
##

def test_mockingbird_pipe_func():
  lo = layout(MOCKINGBIRD)
  pipe = lo.pipes[0]
  assert len(pipe.points) == 4
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[0].func_port
##

def test_mockingbird_pipe_arg():
  lo = layout(MOCKINGBIRD)
  pipe = lo.pipes[1]
  assert len(pipe.points) == 3
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[0].arg_port
##

def test_mockingbird_pipe_out_to_throat():
  lo = layout(MOCKINGBIRD)
  pipe = lo.pipes[2]
  assert len(pipe.points) == 2
  assert pipe.points[0] == lo.applicators[0].out_port
  assert pipe.points[-1] == lo.boxes[0].throat
##

# --- Identity SVG tests ---

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

# --- Mockingbird SVG tests ---

def test_mockingbird_svg_valid_xml():
  svg = render(MOCKINGBIRD)
  ET.fromstring(svg)
##

def test_mockingbird_svg_has_rect():
  svg = render(MOCKINGBIRD)
  root = ET.fromstring(svg)
  rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
  assert len(rects) == 1
##

def test_mockingbird_svg_has_polylines():
  svg = render(MOCKINGBIRD)
  root = ET.fromstring(svg)
  polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
  assert len(polylines) == 3
##

def test_mockingbird_svg_has_ear_and_throat():
  svg = render(MOCKINGBIRD)
  root = ET.fromstring(svg)
  paths = root.findall(".//{http://www.w3.org/2000/svg}path")
  assert len(paths) == 2
##

def test_mockingbird_svg_has_circles():
  svg = render(MOCKINGBIRD)
  root = ET.fromstring(svg)
  circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
  assert len(circles) == 1
##

# --- Double Mockingbird layout tests ---

def test_double_mockingbird_layout_structure():
  lo = layout(DOUBLE_MOCKINGBIRD)
  assert len(lo.boxes) == 1
  assert len(lo.pipes) == 7
  assert len(lo.applicators) == 3
##

def test_double_mockingbird_box_dimensions():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.rect.width > 0
  assert box.rect.height > 0
##

def test_double_mockingbird_ear_on_left_edge():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_double_mockingbird_throat_on_right_edge():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_double_mockingbird_ear_throat_at_four_fifths():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  y_4_5 = box.rect.y + 4 * box.rect.height / 5
  assert box.ear.y == y_4_5
  assert box.throat.y == y_4_5
##

def test_double_mockingbird_applicators_inside_box():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  for appl in lo.applicators:
    assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
    assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
  ##
##

def test_double_mockingbird_applicator_columns():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  inner1, inner2, outer = lo.applicators
  mid_x = box.rect.x + box.rect.width / 2
  three_quarter_x = box.rect.x + 3 * box.rect.width / 4
  assert inner1.center.x == mid_x
  assert inner2.center.x == mid_x
  assert outer.center.x == three_quarter_x
##

def test_double_mockingbird_applicator_rows():
  lo = layout(DOUBLE_MOCKINGBIRD)
  box = lo.boxes[0]
  inner1, inner2, outer = lo.applicators
  y_2_5 = box.rect.y + 2 * box.rect.height / 5
  y_4_5 = box.rect.y + 4 * box.rect.height / 5
  assert inner1.center.y == y_2_5
  assert inner2.center.y == y_4_5
  assert outer.center.y == y_4_5
##

def test_double_mockingbird_pipe_inner1_func():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[0]
  assert len(pipe.points) == 4
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[0].func_port
##

def test_double_mockingbird_pipe_inner1_arg():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[1]
  assert len(pipe.points) == 3
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[0].arg_port
##

def test_double_mockingbird_pipe_inner2_func():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[2]
  assert len(pipe.points) == 4
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[1].func_port
##

def test_double_mockingbird_pipe_inner2_arg():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[3]
  assert len(pipe.points) == 3
  assert pipe.points[0] == lo.boxes[0].ear
  assert pipe.points[-1] == lo.applicators[1].arg_port
##

def test_double_mockingbird_pipe_inner1_to_outer():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[4]
  assert len(pipe.points) == 3
  assert pipe.points[0] == lo.applicators[0].out_port
  assert pipe.points[-1] == lo.applicators[2].func_port
##

def test_double_mockingbird_pipe_inner2_to_outer():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[5]
  assert len(pipe.points) == 2
  assert pipe.points[0] == lo.applicators[1].out_port
  assert pipe.points[-1] == lo.applicators[2].arg_port
##

def test_double_mockingbird_pipe_out_to_throat():
  lo = layout(DOUBLE_MOCKINGBIRD)
  pipe = lo.pipes[6]
  assert len(pipe.points) == 2
  assert pipe.points[0] == lo.applicators[2].out_port
  assert pipe.points[-1] == lo.boxes[0].throat
##

# --- Double Mockingbird SVG tests ---

def test_double_mockingbird_svg_valid_xml():
  svg = render(DOUBLE_MOCKINGBIRD)
  ET.fromstring(svg)
##

def test_double_mockingbird_svg_has_polylines():
  svg = render(DOUBLE_MOCKINGBIRD)
  root = ET.fromstring(svg)
  polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
  assert len(polylines) == 7
##

def test_double_mockingbird_svg_has_circles():
  svg = render(DOUBLE_MOCKINGBIRD)
  root = ET.fromstring(svg)
  circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
  assert len(circles) == 3
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

# --- Self-apply-left layout tests ---

def test_self_apply_left_layout_structure():
  lo = layout(SELF_APPLY_LEFT)
  assert len(lo.boxes) == 1
  assert len(lo.pipes) == 5
  assert len(lo.applicators) == 2
##

def test_self_apply_left_box_dimensions():
  lo = layout(SELF_APPLY_LEFT)
  box = lo.boxes[0]
  assert box.rect.width > 0
  assert box.rect.height > 0
##

def test_self_apply_left_ear_on_left_edge():
  lo = layout(SELF_APPLY_LEFT)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_self_apply_left_throat_on_right_edge():
  lo = layout(SELF_APPLY_LEFT)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_self_apply_left_ear_throat_at_three_quarters():
  lo = layout(SELF_APPLY_LEFT)
  box = lo.boxes[0]
  y_3_4 = box.rect.y + 3 * box.rect.height / 4
  assert box.ear.y == y_3_4
  assert box.throat.y == y_3_4
##

def test_self_apply_left_applicators_inside_box():
  lo = layout(SELF_APPLY_LEFT)
  box = lo.boxes[0]
  for appl in lo.applicators:
    assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
    assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
  ##
##

def test_self_apply_left_pipe_counts():
  lo = layout(SELF_APPLY_LEFT)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [4, 3, 3, 3, 2]
##

def test_self_apply_left_svg_valid_xml():
  svg = render(SELF_APPLY_LEFT)
  ET.fromstring(svg)
##

def test_self_apply_left_svg_has_polylines():
  svg = render(SELF_APPLY_LEFT)
  root = ET.fromstring(svg)
  polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
  assert len(polylines) == 5
##

def test_self_apply_left_svg_has_circles():
  svg = render(SELF_APPLY_LEFT)
  root = ET.fromstring(svg)
  circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
  assert len(circles) == 2
##

# --- Self-apply-right layout tests ---

def test_self_apply_right_layout_structure():
  lo = layout(SELF_APPLY_RIGHT)
  assert len(lo.boxes) == 1
  assert len(lo.pipes) == 5
  assert len(lo.applicators) == 2
##

def test_self_apply_right_box_dimensions():
  lo = layout(SELF_APPLY_RIGHT)
  box = lo.boxes[0]
  assert box.rect.width > 0
  assert box.rect.height > 0
##

def test_self_apply_right_ear_on_left_edge():
  lo = layout(SELF_APPLY_RIGHT)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_self_apply_right_throat_on_right_edge():
  lo = layout(SELF_APPLY_RIGHT)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_self_apply_right_ear_throat_at_three_quarters():
  lo = layout(SELF_APPLY_RIGHT)
  box = lo.boxes[0]
  y_3_4 = box.rect.y + 3 * box.rect.height / 4
  assert box.ear.y == y_3_4
  assert box.throat.y == y_3_4
##

def test_self_apply_right_applicators_inside_box():
  lo = layout(SELF_APPLY_RIGHT)
  box = lo.boxes[0]
  for appl in lo.applicators:
    assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
    assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
  ##
##

def test_self_apply_right_pipe_counts():
  lo = layout(SELF_APPLY_RIGHT)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [4, 3, 4, 2, 2]
##

def test_self_apply_right_svg_valid_xml():
  svg = render(SELF_APPLY_RIGHT)
  ET.fromstring(svg)
##

def test_self_apply_right_svg_has_polylines():
  svg = render(SELF_APPLY_RIGHT)
  root = ET.fromstring(svg)
  polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
  assert len(polylines) == 5
##

def test_self_apply_right_svg_has_circles():
  svg = render(SELF_APPLY_RIGHT)
  root = ET.fromstring(svg)
  circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
  assert len(circles) == 2
##
