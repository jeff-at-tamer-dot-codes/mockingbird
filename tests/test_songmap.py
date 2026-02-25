import xml.etree.ElementTree as ET
import pytest
from mockingbird.parser import parse
from mockingbird.songmap import layout, render, Point

IDENTITY = parse(r'λ 0')
MOCKINGBIRD = parse(r'λ 0 0')
DOUBLE_MOCKINGBIRD = parse(r'λ 0 0 (0 0)')
SELF_APPLY_LEFT = parse(r'λ 0 0 0')
SELF_APPLY_RIGHT = parse(r'λ 0 (0 0)')
KITE = parse(r'λ λ 0')
KESTREL = parse(r'λ λ 1')
NESTED_01 = parse(r'λ λ 0 1')
NESTED_10 = parse(r'λ λ 1 0')
NESTED_11 = parse(r'λ λ 1 1')
NESTED_MOCKINGBIRD = parse(r'λ λ 0 0')
NESTED_DOUBLE_MOCKINGBIRD = parse(r'λ λ 0 0 (0 0)')
TRIPLE_VAR0 = parse(r'λ λ λ 0')
TRIPLE_VAR1 = parse(r'λ λ λ 1')
TRIPLE_VAR2 = parse(r'λ λ λ 2')
APPL_II = parse(r'(λ 0) (λ 0)')
APPL_MI = parse(r'(λ 0 0) (λ 0)')
APPL_III = parse(r'(λ 0) ((λ 0) (λ 0))')
APPL_LEFT_III = parse(r'(λ 0) (λ 0) (λ 0)')
APPL_LEFT_MI_I = parse(r'(λ 0 0) (λ 0) (λ 0)')
APPL_LEFT_IIII = parse(r'(λ 0) (λ 0) (λ 0) (λ 0)')
FUNC_APPL_II = parse(r'λ (λ 0) (λ 0)')
FUNC_APPL_LEFT_III = parse(r'λ (λ 0) (λ 0) (λ 0)')
FUNC2_APPL_II = parse(r'λ λ (λ 0) (λ 0)')
TRIPLE_APPL_02 = parse(r'λ λ λ 0 2')

class TestIdentity:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(IDENTITY)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 1
    assert len(self.lo.pipes) == 1
  ##
  def test_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width > 0
    assert box.rect.height > 0
  ##
  def test_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_ear_throat_vertically_centered(self):
    box = self.lo.boxes[0]
    mid_y = box.rect.y + box.rect.height / 2
    assert box.ear.y == mid_y
    assert box.throat.y == mid_y
  ##
  def test_pipe_connects_ear_to_throat(self):
    box = self.lo.boxes[0]
    pipe = self.lo.pipes[0]
    assert pipe.points[0] == box.ear
    assert pipe.points[-1] == box.throat
  ##
  def test_svg_valid_xml(self):
    svg = render(IDENTITY)
    ET.fromstring(svg)
  ##
  def test_svg_has_rect(self):
    svg = render(IDENTITY)
    root = ET.fromstring(svg)
    rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
    assert len(rects) == 1
  ##
  def test_svg_has_dashed_rect(self):
    svg = render(IDENTITY)
    root = ET.fromstring(svg)
    rect = root.find(".//{http://www.w3.org/2000/svg}rect")
    assert rect is not None
    assert rect.get("stroke-dasharray") is not None
  ##
  def test_svg_has_polyline(self):
    svg = render(IDENTITY)
    root = ET.fromstring(svg)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    assert len(polylines) == 1
  ##
  def test_svg_has_ear_and_throat(self):
    svg = render(IDENTITY)
    root = ET.fromstring(svg)
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")
    assert len(paths) == 2
  ##
##

class TestMockingbird:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(MOCKINGBIRD)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 1
    assert len(self.lo.pipes) == 3
    assert len(self.lo.applicators) == 1
  ##
  def test_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width > 0
    assert box.rect.height > 0
  ##
  def test_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_ear_throat_at_two_thirds(self):
    box = self.lo.boxes[0]
    y_2_3 = box.rect.y + 2 * box.rect.height / 3
    assert box.ear.y == y_2_3
    assert box.throat.y == y_2_3
  ##
  def test_applicator_inside_box(self):
    box = self.lo.boxes[0]
    appl = self.lo.applicators[0]
    assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
    assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
  ##
  def test_applicator_ports(self):
    appl = self.lo.applicators[0]
    assert appl.func_port.y < appl.center.y
    assert appl.arg_port.x < appl.center.x
    assert appl.out_port.x > appl.center.x
  ##
  def test_pipe_func(self):
    pipe = self.lo.pipes[0]
    assert len(pipe.points) == 4
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[0].func_port
  ##
  def test_pipe_arg(self):
    pipe = self.lo.pipes[1]
    assert len(pipe.points) == 3
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
  ##
  def test_pipe_out_to_throat(self):
    pipe = self.lo.pipes[2]
    assert len(pipe.points) == 2
    assert pipe.points[0] == self.lo.applicators[0].out_port
    assert pipe.points[-1] == self.lo.boxes[0].throat
  ##
  def test_svg_valid_xml(self):
    svg = render(MOCKINGBIRD)
    ET.fromstring(svg)
  ##
  def test_svg_has_rect(self):
    svg = render(MOCKINGBIRD)
    root = ET.fromstring(svg)
    rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
    assert len(rects) == 1
  ##
  def test_svg_has_polylines(self):
    svg = render(MOCKINGBIRD)
    root = ET.fromstring(svg)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    assert len(polylines) == 3
  ##
  def test_svg_has_ear_and_throat(self):
    svg = render(MOCKINGBIRD)
    root = ET.fromstring(svg)
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")
    assert len(paths) == 2
  ##
  def test_svg_has_circles(self):
    svg = render(MOCKINGBIRD)
    root = ET.fromstring(svg)
    circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
    assert len(circles) == 1
  ##
##

class TestDoubleMockingbird:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(DOUBLE_MOCKINGBIRD)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 1
    assert len(self.lo.pipes) == 7
    assert len(self.lo.applicators) == 3
  ##
  def test_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width > 0
    assert box.rect.height > 0
  ##
  def test_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_ear_throat_at_four_fifths(self):
    box = self.lo.boxes[0]
    y_4_5 = box.rect.y + 4 * box.rect.height / 5
    assert box.ear.y == y_4_5
    assert box.throat.y == y_4_5
  ##
  def test_applicators_inside_box(self):
    box = self.lo.boxes[0]
    for appl in self.lo.applicators:
      assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
      assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
    ##
  ##
  def test_applicator_columns(self):
    box = self.lo.boxes[0]
    inner1, inner2, outer = self.lo.applicators
    mid_x = box.rect.x + box.rect.width / 2
    three_quarter_x = box.rect.x + 3 * box.rect.width / 4
    assert inner1.center.x == mid_x
    assert inner2.center.x == mid_x
    assert outer.center.x == three_quarter_x
  ##
  def test_applicator_rows(self):
    box = self.lo.boxes[0]
    inner1, inner2, outer = self.lo.applicators
    y_2_5 = box.rect.y + 2 * box.rect.height / 5
    y_4_5 = box.rect.y + 4 * box.rect.height / 5
    assert inner1.center.y == y_2_5
    assert inner2.center.y == y_4_5
    assert outer.center.y == y_4_5
  ##
  def test_pipe_inner1_func(self):
    pipe = self.lo.pipes[0]
    assert len(pipe.points) == 4
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[0].func_port
  ##
  def test_pipe_inner1_arg(self):
    pipe = self.lo.pipes[1]
    assert len(pipe.points) == 3
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
  ##
  def test_pipe_inner2_func(self):
    pipe = self.lo.pipes[2]
    assert len(pipe.points) == 4
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[1].func_port
  ##
  def test_pipe_inner2_arg(self):
    pipe = self.lo.pipes[3]
    assert len(pipe.points) == 3
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[-1] == self.lo.applicators[1].arg_port
  ##
  def test_pipe_inner1_to_outer(self):
    pipe = self.lo.pipes[4]
    assert len(pipe.points) == 3
    assert pipe.points[0] == self.lo.applicators[0].out_port
    assert pipe.points[-1] == self.lo.applicators[2].func_port
  ##
  def test_pipe_inner2_to_outer(self):
    pipe = self.lo.pipes[5]
    assert len(pipe.points) == 2
    assert pipe.points[0] == self.lo.applicators[1].out_port
    assert pipe.points[-1] == self.lo.applicators[2].arg_port
  ##
  def test_pipe_out_to_throat(self):
    pipe = self.lo.pipes[6]
    assert len(pipe.points) == 2
    assert pipe.points[0] == self.lo.applicators[2].out_port
    assert pipe.points[-1] == self.lo.boxes[0].throat
  ##
  def test_svg_valid_xml(self):
    svg = render(DOUBLE_MOCKINGBIRD)
    ET.fromstring(svg)
  ##
  def test_svg_has_polylines(self):
    svg = render(DOUBLE_MOCKINGBIRD)
    root = ET.fromstring(svg)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    assert len(polylines) == 7
  ##
  def test_svg_has_circles(self):
    svg = render(DOUBLE_MOCKINGBIRD)
    root = ET.fromstring(svg)
    circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
    assert len(circles) == 3
  ##
##

class TestSelfApplyLeft:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(SELF_APPLY_LEFT)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 1
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 2
  ##
  def test_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width > 0
    assert box.rect.height > 0
  ##
  def test_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_ear_throat_at_three_quarters(self):
    box = self.lo.boxes[0]
    y_3_4 = box.rect.y + 3 * box.rect.height / 4
    assert box.ear.y == y_3_4
    assert box.throat.y == y_3_4
  ##
  def test_applicators_inside_box(self):
    box = self.lo.boxes[0]
    for appl in self.lo.applicators:
      assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
      assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
    ##
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [4, 3, 3, 3, 2]
  ##
  def test_svg_valid_xml(self):
    svg = render(SELF_APPLY_LEFT)
    ET.fromstring(svg)
  ##
  def test_svg_has_polylines(self):
    svg = render(SELF_APPLY_LEFT)
    root = ET.fromstring(svg)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    assert len(polylines) == 5
  ##
  def test_svg_has_circles(self):
    svg = render(SELF_APPLY_LEFT)
    root = ET.fromstring(svg)
    circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
    assert len(circles) == 2
  ##
##

class TestSelfApplyRight:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(SELF_APPLY_RIGHT)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 1
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 2
  ##
  def test_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width > 0
    assert box.rect.height > 0
  ##
  def test_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_ear_throat_at_three_quarters(self):
    box = self.lo.boxes[0]
    y_3_4 = box.rect.y + 3 * box.rect.height / 4
    assert box.ear.y == y_3_4
    assert box.throat.y == y_3_4
  ##
  def test_applicators_inside_box(self):
    box = self.lo.boxes[0]
    for appl in self.lo.applicators:
      assert box.rect.x < appl.center.x < box.rect.x + box.rect.width
      assert box.rect.y < appl.center.y < box.rect.y + box.rect.height
    ##
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [4, 3, 4, 2, 2]
  ##
  def test_svg_valid_xml(self):
    svg = render(SELF_APPLY_RIGHT)
    ET.fromstring(svg)
  ##
  def test_svg_has_polylines(self):
    svg = render(SELF_APPLY_RIGHT)
    root = ET.fromstring(svg)
    polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
    assert len(polylines) == 5
  ##
  def test_svg_has_circles(self):
    svg = render(SELF_APPLY_RIGHT)
    root = ET.fromstring(svg)
    circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
    assert len(circles) == 2
  ##
##

class TestKite:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(KITE)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 2
    assert len(self.lo.applicators) == 0
  ##
  def test_outer_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width == 8 * 20
    assert box.rect.height == 4 * 20
  ##
  def test_inner_box_dimensions(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert inner.rect.width == outer.rect.width / 2
    assert inner.rect.height == outer.rect.height / 2
  ##
  def test_inner_box_position(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert inner.rect.x == outer.rect.x + outer.rect.width / 4
    assert inner.rect.y == outer.rect.y + outer.rect.height / 4
  ##
  def test_outer_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_outer_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_outer_ear_throat_at_one_quarter(self):
    box = self.lo.boxes[0]
    y = box.rect.y + box.rect.height / 4
    assert box.ear.y == y
    assert box.throat.y == y
  ##
  def test_inner_ear_on_inner_left_edge(self):
    inner = self.lo.boxes[1]
    assert inner.ear.x == inner.rect.x
  ##
  def test_inner_throat_on_inner_right_edge(self):
    inner = self.lo.boxes[1]
    assert inner.throat.x == inner.rect.x + inner.rect.width
  ##
  def test_inner_ear_throat_at_one_half(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    y = outer.rect.y + outer.rect.height / 2
    assert inner.ear.y == y
    assert inner.throat.y == y
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [2, 4]
  ##
  def test_throat_pipe(self):
    pipe = self.lo.pipes[1]
    inner = self.lo.boxes[1]
    outer = self.lo.boxes[0]
    assert pipe.points[0] == inner.throat
    assert pipe.points[-1] == outer.throat
  ##
  def test_body_pipe(self):
    pipe = self.lo.pipes[0]
    inner = self.lo.boxes[1]
    assert pipe.points[0] == inner.ear
    assert pipe.points[-1] == inner.throat
  ##
  def test_svg_valid_xml(self):
    svg = render(KITE)
    ET.fromstring(svg)
  ##
  def test_svg_elements(self):
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
##

class TestKestrel:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(KESTREL)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 2
    assert len(self.lo.applicators) == 0
  ##
  def test_outer_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width == 8 * 20
    assert box.rect.height == 5 * 20
  ##
  def test_inner_box_dimensions(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert inner.rect.width == outer.rect.width / 2
    assert inner.rect.height == 3 * outer.rect.height / 5
  ##
  def test_inner_box_position(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert inner.rect.x == outer.rect.x + outer.rect.width / 4
    assert inner.rect.y == outer.rect.y + outer.rect.height / 5
  ##
  def test_outer_ear_on_left_edge(self):
    box = self.lo.boxes[0]
    assert box.ear.x == box.rect.x
  ##
  def test_outer_throat_on_right_edge(self):
    box = self.lo.boxes[0]
    assert box.throat.x == box.rect.x + box.rect.width
  ##
  def test_outer_ear_throat_at_two_fifths(self):
    box = self.lo.boxes[0]
    y = box.rect.y + 2 * box.rect.height / 5
    assert box.ear.y == y
    assert box.throat.y == y
  ##
  def test_inner_ear_on_inner_left_edge(self):
    inner = self.lo.boxes[1]
    assert inner.ear.x == inner.rect.x
  ##
  def test_inner_throat_on_inner_right_edge(self):
    inner = self.lo.boxes[1]
    assert inner.throat.x == inner.rect.x + inner.rect.width
  ##
  def test_inner_ear_throat_at_three_fifths(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    y = outer.rect.y + 3 * outer.rect.height / 5
    assert inner.ear.y == y
    assert inner.throat.y == y
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [4, 4]
  ##
  def test_throat_pipe(self):
    pipe = self.lo.pipes[1]
    inner = self.lo.boxes[1]
    outer = self.lo.boxes[0]
    assert pipe.points[0] == inner.throat
    assert pipe.points[-1] == outer.throat
  ##
  def test_body_pipe(self):
    pipe = self.lo.pipes[0]
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert pipe.points[0] == outer.ear
    assert pipe.points[-1] == inner.throat
  ##
  def test_svg_valid_xml(self):
    svg = render(KESTREL)
    ET.fromstring(svg)
  ##
  def test_svg_elements(self):
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
##

class TestNestedMockingbird:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(NESTED_MOCKINGBIRD)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 4
    assert len(self.lo.applicators) == 1
  ##
  def test_canvas_dimensions(self):
    assert self.lo.width == 216
    assert self.lo.height == 116
  ##
  def test_outer_box(self):
    box = self.lo.boxes[0]
    assert box.rect.x == 8
    assert box.rect.y == 8
    assert box.rect.width == 200
    assert box.rect.height == 100
  ##
  def test_inner_box(self):
    inner = self.lo.boxes[1]
    assert inner.rect.x == 48
    assert inner.rect.y == 28
    assert inner.rect.width == 120
    assert inner.rect.height == 60
  ##
  def test_inner_nested_in_outer(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    assert inner.rect.x > outer.rect.x
    assert inner.rect.y > outer.rect.y
    assert inner.rect.x + inner.rect.width < outer.rect.x + outer.rect.width
    assert inner.rect.y + inner.rect.height < outer.rect.y + outer.rect.height
  ##
  def test_outer_ear_throat(self):
    box = self.lo.boxes[0]
    assert box.ear == Point(8, 48)
    assert box.throat == Point(208, 48)
  ##
  def test_inner_ear_throat(self):
    inner = self.lo.boxes[1]
    assert inner.ear == Point(48, 68)
    assert inner.throat == Point(168, 68)
  ##
  def test_applicator(self):
    appl = self.lo.applicators[0]
    assert appl.center == Point(128, 68)
    assert appl.func_port == Point(128, 60)
    assert appl.arg_port == Point(120, 68)
    assert appl.out_port == Point(136, 68)
  ##
  def test_func_pipe(self):
    pipe = self.lo.pipes[0]
    assert pipe.points[0] == self.lo.boxes[1].ear
    assert pipe.points[-1] == self.lo.applicators[0].func_port
    assert len(pipe.points) == 4
  ##
  def test_arg_pipe(self):
    pipe = self.lo.pipes[1]
    assert pipe.points[0] == self.lo.boxes[1].ear
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
    assert len(pipe.points) == 3
  ##
  def test_out_pipe(self):
    pipe = self.lo.pipes[2]
    assert pipe.points[0] == self.lo.applicators[0].out_port
    assert pipe.points[-1] == self.lo.boxes[1].throat
    assert len(pipe.points) == 2
  ##
  def test_throat_pipe(self):
    pipe = self.lo.pipes[3]
    assert pipe.points[0] == self.lo.boxes[1].throat
    assert pipe.points[-1] == self.lo.boxes[0].throat
    assert len(pipe.points) == 4
  ##
  def test_svg_valid_xml(self):
    svg = render(NESTED_MOCKINGBIRD)
    ET.fromstring(svg)
  ##
  def test_svg_elements(self):
    svg = render(NESTED_MOCKINGBIRD)
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    rects = root.findall(f".//{ns}rect")
    polylines = root.findall(f".//{ns}polyline")
    paths = root.findall(f".//{ns}path")
    circles = root.findall(f".//{ns}circle")
    assert len(rects) == 2
    assert len(polylines) == 4
    assert len(paths) == 4
    assert len(circles) == 1
  ##
##

class TestNestedDoubleMockingbird:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(NESTED_DOUBLE_MOCKINGBIRD)
  ##
  def test_inner_ear_one_row_above_bottom(self):
    inner = self.lo.boxes[1]
    g = 20.0
    assert inner.ear.y == inner.rect.y + inner.rect.height - g
  ##
  def test_outer_ear_one_row_above_inner(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    g = 20.0
    assert outer.ear.y == inner.ear.y - g
  ##
  def test_vertical_gap_is_one_row(self):
    outer = self.lo.boxes[0]
    inner = self.lo.boxes[1]
    g = 20.0
    assert inner.rect.y - outer.rect.y == g
    assert (outer.rect.y + outer.rect.height) - (inner.rect.y + inner.rect.height) == g
  ##
##

class TestTripleVar0:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(TRIPLE_VAR0)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 3
    assert len(self.lo.applicators) == 0
  ##
  def test_outer_box_dimensions(self):
    box = self.lo.boxes[0]
    assert box.rect.width == 12 * 20
    assert box.rect.height == 6 * 20
  ##
  def test_box_widths(self):
    outer = self.lo.boxes[0]
    assert self.lo.boxes[0].rect.width == outer.rect.width
    assert self.lo.boxes[1].rect.width == 2 * outer.rect.width / 3
    assert self.lo.boxes[2].rect.width == outer.rect.width / 3
  ##
  def test_box_heights(self):
    outer = self.lo.boxes[0]
    assert self.lo.boxes[0].rect.height == outer.rect.height
    assert self.lo.boxes[1].rect.height == 2 * outer.rect.height / 3
    assert self.lo.boxes[2].rect.height == outer.rect.height / 3
  ##
  def test_box_positions(self):
    outer = self.lo.boxes[0]
    assert self.lo.boxes[1].rect.x == outer.rect.x + outer.rect.width / 6
    assert self.lo.boxes[1].rect.y == outer.rect.y + outer.rect.height / 6
    assert self.lo.boxes[2].rect.x == outer.rect.x + outer.rect.width / 3
    assert self.lo.boxes[2].rect.y == outer.rect.y + outer.rect.height / 3
  ##
  def test_ear_throat_y_positions(self):
    outer = self.lo.boxes[0]
    assert self.lo.boxes[0].ear.y == outer.rect.y + outer.rect.height / 6
    assert self.lo.boxes[1].ear.y == outer.rect.y + outer.rect.height / 3
    assert self.lo.boxes[2].ear.y == outer.rect.y + outer.rect.height / 2
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [2, 4, 4]
  ##
  def test_body_pipe(self):
    pipe = self.lo.pipes[0]
    innermost = self.lo.boxes[2]
    assert pipe.points[0] == innermost.ear
    assert pipe.points[-1] == innermost.throat
  ##
  def test_throat_pipes(self):
    inner_throat_pipe = self.lo.pipes[1]
    assert inner_throat_pipe.points[0] == self.lo.boxes[2].throat
    assert inner_throat_pipe.points[-1] == self.lo.boxes[1].throat
    outer_throat_pipe = self.lo.pipes[2]
    assert outer_throat_pipe.points[0] == self.lo.boxes[1].throat
    assert outer_throat_pipe.points[-1] == self.lo.boxes[0].throat
  ##
  def test_svg(self):
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
##

class TestTripleVar1:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(TRIPLE_VAR1)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 3
    assert len(self.lo.applicators) == 0
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [4, 4, 4]
  ##
  def test_body_pipe(self):
    pipe = self.lo.pipes[0]
    middle = self.lo.boxes[1]
    innermost = self.lo.boxes[2]
    assert pipe.points[0] == middle.ear
    assert pipe.points[-1] == innermost.throat
  ##
##

class TestTripleVar2:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(TRIPLE_VAR2)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 3
    assert len(self.lo.applicators) == 0
  ##
  def test_pipe_counts(self):
    counts = [len(p.points) for p in self.lo.pipes]
    assert counts == [4, 4, 4]
  ##
  def test_body_pipe(self):
    pipe = self.lo.pipes[0]
    outer = self.lo.boxes[0]
    innermost = self.lo.boxes[2]
    assert pipe.points[0] == outer.ear
    assert pipe.points[-1] == innermost.throat
  ##
##

class TestNested01:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(NESTED_01)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 4
    assert len(self.lo.applicators) == 1
  ##
  def test_func_pipe_from_inner_ear(self):
    pipe = self.lo.pipes[0]
    assert pipe.points[0] == self.lo.boxes[1].ear
    assert pipe.points[-1] == self.lo.applicators[0].func_port
  ##
  def test_arg_pipe_from_outer_ear(self):
    pipe = self.lo.pipes[1]
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[1] == Point(self.lo.boxes[1].rect.x, self.lo.boxes[0].ear.y)
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
    assert len(pipe.points) == 4
  ##
  def test_svg_valid_xml(self):
    svg = render(NESTED_01)
    ET.fromstring(svg)
  ##
##

class TestNested10:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(NESTED_10)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 4
    assert len(self.lo.applicators) == 1
  ##
  def test_func_pipe_from_outer_ear(self):
    pipe = self.lo.pipes[0]
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[1] == Point(self.lo.boxes[1].rect.x, self.lo.boxes[0].ear.y)
    assert pipe.points[-1] == self.lo.applicators[0].func_port
    assert len(pipe.points) == 5
  ##
  def test_arg_pipe_from_inner_ear(self):
    pipe = self.lo.pipes[1]
    assert pipe.points[0] == self.lo.boxes[1].ear
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
  ##
  def test_svg_valid_xml(self):
    svg = render(NESTED_10)
    ET.fromstring(svg)
  ##
##

class TestNested11:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(NESTED_11)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 4
    assert len(self.lo.applicators) == 1
  ##
  def test_func_pipe_from_outer_ear(self):
    pipe = self.lo.pipes[0]
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[1] == Point(self.lo.boxes[1].rect.x, self.lo.boxes[0].ear.y)
    assert pipe.points[-1] == self.lo.applicators[0].func_port
    assert len(pipe.points) == 5
  ##
  def test_arg_pipe_from_outer_ear(self):
    pipe = self.lo.pipes[1]
    assert pipe.points[0] == self.lo.boxes[0].ear
    assert pipe.points[1] == Point(self.lo.boxes[1].rect.x, self.lo.boxes[0].ear.y)
    assert pipe.points[-1] == self.lo.applicators[0].arg_port
    assert len(pipe.points) == 4
  ##
  def test_svg_valid_xml(self):
    svg = render(NESTED_11)
    ET.fromstring(svg)
  ##
##

class TestErrors:
  def test_appl_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'0 1'))
    ##
  ##
  def test_nested_func_free_var_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'λ λ 0 2'))
    ##
  ##
  def test_bare_var_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'0'))
    ##
  ##
  def test_func_in_body_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'λ 0 (λ 0)'))
    ##
  ##
  def test_appl_var_func_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'0 (λ 0)'))
    ##
  ##
  def test_appl_func_var_raises(self):
    with pytest.raises(NotImplementedError):
      layout(parse(r'(λ 0) 0'))
    ##
  ##
##

class TestApplII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_II)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 3
    assert len(self.lo.applicators) == 0
  ##
  def test_arg_left_func_right(self):
    arg_box = self.lo.boxes[0]
    func_box = self.lo.boxes[1]
    assert arg_box.throat.x < func_box.ear.x
  ##
  def test_wire_connects_throat_to_ear(self):
    wire = self.lo.pipes[1]
    assert len(wire.points) == 2
    assert wire.points[0] == self.lo.boxes[0].throat
    assert wire.points[1] == self.lo.boxes[1].ear
  ##
  def test_wire_horizontal(self):
    wire = self.lo.pipes[1]
    assert wire.points[0].y == wire.points[1].y
  ##
  def test_wire_length(self):
    wire = self.lo.pipes[1]
    assert wire.points[1].x - wire.points[0].x == 20.0
  ##
  def test_no_vertical_shift(self):
    arg_box = self.lo.boxes[0]
    func_box = self.lo.boxes[1]
    assert arg_box.rect.y == func_box.rect.y
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_II)
    ET.fromstring(svg)
  ##
##

class TestApplMI:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_MI)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 2
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 1
  ##
  def test_arg_left_func_right(self):
    arg_box = self.lo.boxes[0]
    func_box = self.lo.boxes[1]
    assert arg_box.throat.x < func_box.ear.x
  ##
  def test_wire_horizontal(self):
    wire = self.lo.pipes[1]
    assert len(wire.points) == 2
    assert wire.points[0].y == wire.points[1].y
  ##
  def test_wire_length(self):
    wire = self.lo.pipes[1]
    assert wire.points[1].x - wire.points[0].x == 20.0
  ##
  def test_vertical_alignment(self):
    arg_box = self.lo.boxes[0]
    func_box = self.lo.boxes[1]
    assert arg_box.throat.y == func_box.ear.y
  ##
  def test_identity_shifted_down(self):
    arg_box = self.lo.boxes[0]
    func_box = self.lo.boxes[1]
    assert arg_box.rect.y > func_box.rect.y
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_MI)
    ET.fromstring(svg)
  ##
##

class TestApplIII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_III)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 0
  ##
  def test_left_to_right(self):
    for i in range(len(self.lo.boxes) - 1):
      assert self.lo.boxes[i].throat.x < self.lo.boxes[i + 1].ear.x
    ##
  ##
  def test_wires_connect_adjacent(self):
    wire0 = self.lo.pipes[1]
    assert wire0.points[0] == self.lo.boxes[0].throat
    assert wire0.points[1] == self.lo.boxes[1].ear
    wire1 = self.lo.pipes[3]
    assert wire1.points[0] == self.lo.boxes[1].throat
    assert wire1.points[1] == self.lo.boxes[2].ear
  ##
  def test_wires_horizontal(self):
    wire0 = self.lo.pipes[1]
    assert wire0.points[0].y == wire0.points[1].y
    wire1 = self.lo.pipes[3]
    assert wire1.points[0].y == wire1.points[1].y
  ##
  def test_wire_lengths(self):
    wire0 = self.lo.pipes[1]
    assert wire0.points[1].x - wire0.points[0].x == 20.0
    wire1 = self.lo.pipes[3]
    assert wire1.points[1].x - wire1.points[0].x == 20.0
  ##
  def test_no_vertical_shift(self):
    y0 = self.lo.boxes[0].rect.y
    for box in self.lo.boxes[1:]:
      assert box.rect.y == y0
    ##
  ##
  def test_total_width(self):
    single = layout(IDENTITY)
    spacing = single.boxes[0].throat.x + 20.0 - single.boxes[0].ear.x
    assert self.lo.width == single.width + 2 * spacing
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_III)
    ET.fromstring(svg)
  ##
##

class TestApplLeftIII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_LEFT_III)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 6
    assert len(self.lo.applicators) == 1
  ##
  def test_has_output(self):
    assert self.lo.output is not None
    assert self.lo.output == self.lo.applicators[0].out_port
  ##
  def test_func_wire_l_shaped(self):
    func_wire = self.lo.pipes[-2]
    assert len(func_wire.points) == 3
    assert func_wire.points[0].y == func_wire.points[1].y
    assert func_wire.points[1].x == func_wire.points[2].x
    assert func_wire.points[-1] == self.lo.applicators[0].func_port
  ##
  def test_arg_wire_horizontal(self):
    arg_wire = self.lo.pipes[-1]
    assert len(arg_wire.points) == 2
    assert arg_wire.points[0].y == arg_wire.points[1].y
    assert arg_wire.points[-1] == self.lo.applicators[0].arg_port
  ##
  def test_right_alignment(self):
    func_wire = self.lo.pipes[-2]
    arg_wire = self.lo.pipes[-1]
    assert func_wire.points[0].x == arg_wire.points[0].x
  ##
  def test_applicator_position(self):
    appl = self.lo.applicators[0]
    g = 20.0
    r = 8.0
    func_wire = self.lo.pipes[-2]
    aligned_x = func_wire.points[0].x
    assert appl.center.x == aligned_x + g
    arg_wire = self.lo.pipes[-1]
    assert appl.center.y == arg_wire.points[0].y
    assert appl.func_port == Point(appl.center.x, appl.center.y - r)
    assert appl.arg_port == Point(appl.center.x - r, appl.center.y)
    assert appl.out_port == Point(appl.center.x + r, appl.center.y)
  ##
  def test_top_above_bottom(self):
    func_wire = self.lo.pipes[-2]
    arg_wire = self.lo.pipes[-1]
    assert func_wire.points[0].y < arg_wire.points[0].y
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_LEFT_III)
    ET.fromstring(svg)
  ##
##

class TestApplLeftMII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_LEFT_MI_I)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 8
    assert len(self.lo.applicators) == 2
  ##
  def test_has_output(self):
    assert self.lo.output is not None
    assert self.lo.output == self.lo.applicators[-1].out_port
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_LEFT_MI_I)
    ET.fromstring(svg)
  ##
##

class TestApplLeftIIII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(APPL_LEFT_IIII)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 4
    assert len(self.lo.pipes) == 9
    assert len(self.lo.applicators) == 2
  ##
  def test_has_output(self):
    assert self.lo.output is not None
    assert self.lo.output == self.lo.applicators[-1].out_port
  ##
  def test_recursive_func_wire(self):
    func_wire = self.lo.pipes[-2]
    assert len(func_wire.points) == 3
    assert func_wire.points[0].y == func_wire.points[1].y
    assert func_wire.points[1].x == func_wire.points[2].x
    assert func_wire.points[-1] == self.lo.applicators[-1].func_port
  ##
  def test_recursive_arg_wire(self):
    arg_wire = self.lo.pipes[-1]
    assert len(arg_wire.points) == 2
    assert arg_wire.points[0].y == arg_wire.points[1].y
    assert arg_wire.points[-1] == self.lo.applicators[-1].arg_port
  ##
  def test_svg_valid_xml(self):
    svg = render(APPL_LEFT_IIII)
    ET.fromstring(svg)
  ##
##

class TestFuncApplII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(FUNC_APPL_II)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 4
    assert len(self.lo.applicators) == 0
  ##
  def test_wrapping_box_surrounds_inner(self):
    wrap = self.lo.boxes[0]
    for inner in self.lo.boxes[1:]:
      assert wrap.rect.x < inner.rect.x
      assert wrap.rect.y <= inner.rect.y
      assert wrap.rect.x + wrap.rect.width > inner.rect.x + inner.rect.width
      assert wrap.rect.y + wrap.rect.height > inner.rect.y + inner.rect.height
    ##
  ##
  def test_wrapping_box_ear_throat_same_y(self):
    wrap = self.lo.boxes[0]
    assert wrap.ear.y == wrap.throat.y
  ##
  def test_throat_pipe_s_curve(self):
    pipe = self.lo.pipes[3]
    assert len(pipe.points) == 4
    inner_rightmost = self.lo.boxes[2]
    wrap = self.lo.boxes[0]
    assert pipe.points[0] == inner_rightmost.throat
    assert pipe.points[-1] == wrap.throat
  ##
  def test_vertical_padding_one_grid_unit(self):
    g = 20.0
    wrap = self.lo.boxes[0]
    inner_tops = [b.rect.y for b in self.lo.boxes[1:]]
    inner_bottoms = [b.rect.y + b.rect.height for b in self.lo.boxes[1:]]
    assert min(inner_tops) - wrap.rect.y == g
    assert wrap.rect.y + wrap.rect.height - max(inner_bottoms) == g
  ##
  def test_ear_unconnected(self):
    wrap = self.lo.boxes[0]
    for pipe in self.lo.pipes:
      for pt in pipe.points:
        assert pt != wrap.ear
      ##
    ##
  ##
  def test_svg_valid_xml(self):
    svg = render(FUNC_APPL_II)
    ET.fromstring(svg)
  ##
##

class TestFuncApplLeftIII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(FUNC_APPL_LEFT_III)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 4
    assert len(self.lo.pipes) == 7
    assert len(self.lo.applicators) == 1
  ##
  def test_vertical_padding_one_grid_unit(self):
    g = 20.0
    wrap = self.lo.boxes[0]
    inner_tops = [b.rect.y for b in self.lo.boxes[1:]]
    inner_bottoms = [b.rect.y + b.rect.height for b in self.lo.boxes[1:]]
    assert min(inner_tops) - wrap.rect.y == g
    assert wrap.rect.y + wrap.rect.height - max(inner_bottoms) == g
  ##
  def test_wrapping_throat_horizontal_wire(self):
    wrap = self.lo.boxes[0]
    appl = self.lo.applicators[0]
    assert wrap.throat.y == appl.out_port.y
    wire = self.lo.pipes[6]
    assert len(wire.points) == 2
    assert wire.points[0].y == wire.points[1].y
    assert wire.points[-1] == wrap.throat
  ##
  def test_horizontal_padding_one_grid_unit(self):
    g = 20.0
    wrap = self.lo.boxes[0]
    appl = self.lo.applicators[0]
    assert wrap.throat.x - appl.center.x == g
  ##
  def test_svg_valid_xml(self):
    svg = render(FUNC_APPL_LEFT_III)
    ET.fromstring(svg)
  ##
##

class TestFunc2ApplII:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.lo = layout(FUNC2_APPL_II)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 4
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 0
  ##
  def test_two_wrapping_boxes_surround_inner(self):
    outer = self.lo.boxes[0]
    middle = self.lo.boxes[1]
    for inner in self.lo.boxes[2:]:
      assert outer.rect.x < middle.rect.x < inner.rect.x
      assert outer.rect.y < middle.rect.y <= inner.rect.y
      assert inner.rect.x + inner.rect.width < middle.rect.x + middle.rect.width
      assert middle.rect.x + middle.rect.width < outer.rect.x + outer.rect.width
    ##
  ##
  def test_throat_pipe_inner_to_middle(self):
    pipe = self.lo.pipes[3]
    assert len(pipe.points) == 4
    assert pipe.points[-1] == self.lo.boxes[1].throat
  ##
  def test_throat_pipe_middle_to_outer(self):
    pipe = self.lo.pipes[4]
    assert len(pipe.points) == 4
    assert pipe.points[0] == self.lo.boxes[1].throat
    assert pipe.points[-1] == self.lo.boxes[0].throat
  ##
  def test_svg_valid_xml(self):
    svg = render(FUNC2_APPL_II)
    ET.fromstring(svg)
  ##
##

class TestTripleAppl02:
  @pytest.fixture(autouse=True)
  def _layout(self):
    self.g = 20.0
    self.lo = layout(TRIPLE_APPL_02)
  ##
  def test_layout_structure(self):
    assert len(self.lo.boxes) == 3
    assert len(self.lo.pipes) == 5
    assert len(self.lo.applicators) == 1
  ##
  def test_applicator_y_equals_innermost_throat_y(self):
    innermost = self.lo.boxes[2]
    appl = self.lo.applicators[0]
    assert appl.center.y == innermost.throat.y
  ##
  def test_applicator_grid_aligned(self):
    innermost = self.lo.boxes[2]
    appl = self.lo.applicators[0]
    offset = appl.center.y - innermost.rect.y
    assert offset % self.g == 0
  ##
  def test_svg_valid_xml(self):
    svg = render(TRIPLE_APPL_02)
    ET.fromstring(svg)
  ##
##
