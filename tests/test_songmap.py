import xml.etree.ElementTree as ET
import pytest
from mockingbird.ast import Var, Func, Appl
from mockingbird.songmap import layout, render

IDENTITY = Func(Var(0))
MOCKINGBIRD = Func(Appl(Var(0), Var(0)))
DOUBLE_MOCKINGBIRD = Func(Appl(Appl(Var(0), Var(0)), Appl(Var(0), Var(0))))
SELF_APPLY_LEFT = Func(Appl(Appl(Var(0), Var(0)), Var(0)))
SELF_APPLY_RIGHT = Func(Appl(Var(0), Appl(Var(0), Var(0))))
KITE = Func(Func(Var(0)))
KESTREL = Func(Func(Var(1)))
TRIPLE_VAR0 = Func(Func(Func(Var(0))))
TRIPLE_VAR1 = Func(Func(Func(Var(1))))
TRIPLE_VAR2 = Func(Func(Func(Var(2))))

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

def test_nested_func_appl_body_raises():
  with pytest.raises(NotImplementedError):
    layout(Func(Func(Appl(Var(0), Var(1)))))
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

# --- Kite layout tests ---

def test_kite_layout_structure():
  lo = layout(KITE)
  assert len(lo.boxes) == 2
  assert len(lo.pipes) == 2
  assert len(lo.applicators) == 0
##

def test_kite_outer_box_dimensions():
  lo = layout(KITE)
  box = lo.boxes[0]
  assert box.rect.width == 8 * 20
  assert box.rect.height == 5 * 20
##

def test_kite_inner_box_dimensions():
  lo = layout(KITE)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  assert inner.rect.width == outer.rect.width / 2
  assert inner.rect.height == 3 * outer.rect.height / 5
##

def test_kite_inner_box_position():
  lo = layout(KITE)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  assert inner.rect.x == outer.rect.x + outer.rect.width / 4
  assert inner.rect.y == outer.rect.y + outer.rect.height / 5
##

def test_kite_outer_ear_on_left_edge():
  lo = layout(KITE)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_kite_outer_throat_on_right_edge():
  lo = layout(KITE)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_kite_outer_ear_throat_at_two_fifths():
  lo = layout(KITE)
  box = lo.boxes[0]
  y = box.rect.y + 2 * box.rect.height / 5
  assert box.ear.y == y
  assert box.throat.y == y
##

def test_kite_inner_ear_on_inner_left_edge():
  lo = layout(KITE)
  inner = lo.boxes[1]
  assert inner.ear.x == inner.rect.x
##

def test_kite_inner_throat_on_inner_right_edge():
  lo = layout(KITE)
  inner = lo.boxes[1]
  assert inner.throat.x == inner.rect.x + inner.rect.width
##

def test_kite_inner_ear_throat_at_three_fifths():
  lo = layout(KITE)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  y = outer.rect.y + 3 * outer.rect.height / 5
  assert inner.ear.y == y
  assert inner.throat.y == y
##

def test_kite_pipe_counts():
  lo = layout(KITE)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [2, 4]
##

def test_kite_throat_pipe():
  lo = layout(KITE)
  pipe = lo.pipes[1]
  inner = lo.boxes[1]
  outer = lo.boxes[0]
  assert pipe.points[0] == inner.throat
  assert pipe.points[-1] == outer.throat
##

def test_kite_body_pipe():
  lo = layout(KITE)
  pipe = lo.pipes[0]
  inner = lo.boxes[1]
  assert pipe.points[0] == inner.ear
  assert pipe.points[-1] == inner.throat
##

def test_kite_svg_valid_xml():
  svg = render(KITE)
  ET.fromstring(svg)
##

def test_kite_svg_elements():
  svg = render(KITE)
  root = ET.fromstring(svg)
  ns = "{http://www.w3.org/2000/svg}"
  rects = root.findall(f".//{ns}rect")
  polylines = root.findall(f".//{ns}polyline")
  circles = root.findall(f".//{ns}circle")
  paths = root.findall(f".//{ns}path")
  assert len(rects) == 2
  assert len(polylines) == 2
  assert len(circles) == 0
  assert len(paths) == 4
##

# --- Kestrel layout tests ---

def test_kestrel_layout_structure():
  lo = layout(KESTREL)
  assert len(lo.boxes) == 2
  assert len(lo.pipes) == 2
  assert len(lo.applicators) == 0
##

def test_kestrel_outer_box_dimensions():
  lo = layout(KESTREL)
  box = lo.boxes[0]
  assert box.rect.width == 8 * 20
  assert box.rect.height == 5 * 20
##

def test_kestrel_inner_box_dimensions():
  lo = layout(KESTREL)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  assert inner.rect.width == outer.rect.width / 2
  assert inner.rect.height == 3 * outer.rect.height / 5
##

def test_kestrel_inner_box_position():
  lo = layout(KESTREL)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  assert inner.rect.x == outer.rect.x + outer.rect.width / 4
  assert inner.rect.y == outer.rect.y + outer.rect.height / 5
##

def test_kestrel_outer_ear_on_left_edge():
  lo = layout(KESTREL)
  box = lo.boxes[0]
  assert box.ear.x == box.rect.x
##

def test_kestrel_outer_throat_on_right_edge():
  lo = layout(KESTREL)
  box = lo.boxes[0]
  assert box.throat.x == box.rect.x + box.rect.width
##

def test_kestrel_outer_ear_throat_at_two_fifths():
  lo = layout(KESTREL)
  box = lo.boxes[0]
  y = box.rect.y + 2 * box.rect.height / 5
  assert box.ear.y == y
  assert box.throat.y == y
##

def test_kestrel_inner_ear_on_inner_left_edge():
  lo = layout(KESTREL)
  inner = lo.boxes[1]
  assert inner.ear.x == inner.rect.x
##

def test_kestrel_inner_throat_on_inner_right_edge():
  lo = layout(KESTREL)
  inner = lo.boxes[1]
  assert inner.throat.x == inner.rect.x + inner.rect.width
##

def test_kestrel_inner_ear_throat_at_three_fifths():
  lo = layout(KESTREL)
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  y = outer.rect.y + 3 * outer.rect.height / 5
  assert inner.ear.y == y
  assert inner.throat.y == y
##

def test_kestrel_pipe_counts():
  lo = layout(KESTREL)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [4, 4]
##

def test_kestrel_throat_pipe():
  lo = layout(KESTREL)
  pipe = lo.pipes[1]
  inner = lo.boxes[1]
  outer = lo.boxes[0]
  assert pipe.points[0] == inner.throat
  assert pipe.points[-1] == outer.throat
##

def test_kestrel_body_pipe():
  lo = layout(KESTREL)
  pipe = lo.pipes[0]
  outer = lo.boxes[0]
  inner = lo.boxes[1]
  assert pipe.points[0] == outer.ear
  assert pipe.points[-1] == inner.throat
##

def test_kestrel_svg_valid_xml():
  svg = render(KESTREL)
  ET.fromstring(svg)
##

def test_kestrel_svg_elements():
  svg = render(KESTREL)
  root = ET.fromstring(svg)
  ns = "{http://www.w3.org/2000/svg}"
  rects = root.findall(f".//{ns}rect")
  polylines = root.findall(f".//{ns}polyline")
  circles = root.findall(f".//{ns}circle")
  paths = root.findall(f".//{ns}path")
  assert len(rects) == 2
  assert len(polylines) == 2
  assert len(circles) == 0
  assert len(paths) == 4
##

# --- Triple Var0 (λλλ0) layout tests ---

def test_triple_var0_layout_structure():
  lo = layout(TRIPLE_VAR0)
  assert len(lo.boxes) == 3
  assert len(lo.pipes) == 3
  assert len(lo.applicators) == 0
##

def test_triple_var0_outer_box_dimensions():
  lo = layout(TRIPLE_VAR0)
  box = lo.boxes[0]
  assert box.rect.width == 10 * 20
  assert box.rect.height == 8 * 20
##

def test_triple_var0_box_widths():
  lo = layout(TRIPLE_VAR0)
  outer = lo.boxes[0]
  assert lo.boxes[0].rect.width == outer.rect.width
  assert lo.boxes[1].rect.width == 2 * outer.rect.width / 3
  assert lo.boxes[2].rect.width == outer.rect.width / 3
##

def test_triple_var0_box_heights():
  lo = layout(TRIPLE_VAR0)
  outer = lo.boxes[0]
  assert lo.boxes[0].rect.height == outer.rect.height
  assert lo.boxes[1].rect.height == 3 * outer.rect.height / 4
  assert lo.boxes[2].rect.height == outer.rect.height / 2
##

def test_triple_var0_box_positions():
  lo = layout(TRIPLE_VAR0)
  outer = lo.boxes[0]
  assert lo.boxes[1].rect.x == outer.rect.x + outer.rect.width / 6
  assert lo.boxes[1].rect.y == outer.rect.y + outer.rect.height / 8
  assert lo.boxes[2].rect.x == outer.rect.x + outer.rect.width / 3
  assert lo.boxes[2].rect.y == outer.rect.y + outer.rect.height / 4
##

def test_triple_var0_ear_throat_y_positions():
  lo = layout(TRIPLE_VAR0)
  outer = lo.boxes[0]
  assert lo.boxes[0].ear.y == outer.rect.y + 3 * outer.rect.height / 8
  assert lo.boxes[1].ear.y == outer.rect.y + outer.rect.height / 2
  assert lo.boxes[2].ear.y == outer.rect.y + 5 * outer.rect.height / 8
##

def test_triple_var0_pipe_counts():
  lo = layout(TRIPLE_VAR0)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [2, 4, 4]
##

def test_triple_var0_body_pipe():
  lo = layout(TRIPLE_VAR0)
  pipe = lo.pipes[0]
  innermost = lo.boxes[2]
  assert pipe.points[0] == innermost.ear
  assert pipe.points[-1] == innermost.throat
##

def test_triple_var0_throat_pipes():
  lo = layout(TRIPLE_VAR0)
  inner_throat_pipe = lo.pipes[1]
  assert inner_throat_pipe.points[0] == lo.boxes[2].throat
  assert inner_throat_pipe.points[-1] == lo.boxes[1].throat
  outer_throat_pipe = lo.pipes[2]
  assert outer_throat_pipe.points[0] == lo.boxes[1].throat
  assert outer_throat_pipe.points[-1] == lo.boxes[0].throat
##

def test_triple_var0_svg():
  svg = render(TRIPLE_VAR0)
  root = ET.fromstring(svg)
  ns = "{http://www.w3.org/2000/svg}"
  rects = root.findall(f".//{ns}rect")
  polylines = root.findall(f".//{ns}polyline")
  circles = root.findall(f".//{ns}circle")
  paths = root.findall(f".//{ns}path")
  assert len(rects) == 3
  assert len(polylines) == 3
  assert len(circles) == 0
  assert len(paths) == 6
##

# --- Triple Var1 (λλλ1) layout tests ---

def test_triple_var1_layout_structure():
  lo = layout(TRIPLE_VAR1)
  assert len(lo.boxes) == 3
  assert len(lo.pipes) == 3
  assert len(lo.applicators) == 0
##

def test_triple_var1_pipe_counts():
  lo = layout(TRIPLE_VAR1)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [4, 4, 4]
##

def test_triple_var1_body_pipe():
  lo = layout(TRIPLE_VAR1)
  pipe = lo.pipes[0]
  middle = lo.boxes[1]
  innermost = lo.boxes[2]
  assert pipe.points[0] == middle.ear
  assert pipe.points[-1] == innermost.throat
##

# --- Triple Var2 (λλλ2) layout tests ---

def test_triple_var2_layout_structure():
  lo = layout(TRIPLE_VAR2)
  assert len(lo.boxes) == 3
  assert len(lo.pipes) == 3
  assert len(lo.applicators) == 0
##

def test_triple_var2_pipe_counts():
  lo = layout(TRIPLE_VAR2)
  counts = [len(p.points) for p in lo.pipes]
  assert counts == [4, 4, 4]
##

def test_triple_var2_body_pipe():
  lo = layout(TRIPLE_VAR2)
  pipe = lo.pipes[0]
  outer = lo.boxes[0]
  innermost = lo.boxes[2]
  assert pipe.points[0] == outer.ear
  assert pipe.points[-1] == innermost.throat
##
