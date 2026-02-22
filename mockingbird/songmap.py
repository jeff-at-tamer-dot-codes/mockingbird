from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
from mockingbird.ast import Expr, Var, Func, Appl

@dataclass(frozen=True, slots=True)
class Point:
  x: float
  y: float
##

@dataclass(frozen=True, slots=True)
class Rect:
  x: float
  y: float
  width: float
  height: float
##

@dataclass(frozen=True, slots=True)
class Style:
  grid: float = 20.0
  box_padding: float = 1.0
  ear_radius: float = 8.0
  pipe_width: float = 2.0
  box_stroke: str = "#000"
  pipe_stroke: str = "#000"
  fill: str = "#000"
##

@dataclass(frozen=True, slots=True)
class LBox:
  rect: Rect
  ear: Point
  throat: Point
##

@dataclass(frozen=True, slots=True)
class LPipe:
  points: tuple[Point, ...]
##

@dataclass(frozen=True, slots=True)
class LApplicator:
  center: Point
  func_port: Point
  arg_port: Point
  out_port: Point
##

@dataclass(frozen=True, slots=True)
class Layout:
  width: float
  height: float
  boxes: tuple[LBox, ...]
  pipes: tuple[LPipe, ...]
  applicators: tuple[LApplicator, ...] = ()
##

_SVG_NS = "http://www.w3.org/2000/svg"

def layout(expr: Expr, style: Style | None = None) -> Layout:
  if not isinstance(expr, Func):
    raise NotImplementedError(f"layout() only supports Func expressions, got: {expr}")
  ##
  s = style or Style()
  body = expr.body
  if isinstance(body, Var) and body.index == 0:
    return _layout_identity(s)
  ##
  if (isinstance(body, Appl) and isinstance(body.func, Var) and body.func.index == 0
      and isinstance(body.arg, Var) and body.arg.index == 0):
    return _layout_mockingbird(s)
  ##
  if (isinstance(body, Appl) and isinstance(body.func, Appl) and isinstance(body.arg, Appl)
      and isinstance(body.func.func, Var) and body.func.func.index == 0
      and isinstance(body.func.arg, Var) and body.func.arg.index == 0
      and isinstance(body.arg.func, Var) and body.arg.func.index == 0
      and isinstance(body.arg.arg, Var) and body.arg.arg.index == 0):
    return _layout_double_mockingbird(s)
  ##
  raise NotImplementedError(f"layout() does not yet support: {expr}")
##

def _layout_identity(s: Style) -> Layout:
  box_w = 4 * s.grid
  box_h = 2 * s.grid
  margin = s.ear_radius
  total_w = box_w + 2 * margin
  total_h = box_h + 2 * margin
  box_x = margin
  box_y = margin
  mid_y = box_y + box_h / 2
  ear = Point(box_x, mid_y)
  throat = Point(box_x + box_w, mid_y)
  box = LBox(rect=Rect(box_x, box_y, box_w, box_h), ear=ear, throat=throat)
  pipe = LPipe(points=(ear, throat))
  return Layout(width=total_w, height=total_h, boxes=(box,), pipes=(pipe,))
##

def _layout_mockingbird(s: Style) -> Layout:
  box_w = 6 * s.grid
  box_h = 3 * s.grid
  margin = s.ear_radius
  total_w = box_w + 2 * margin
  total_h = box_h + 2 * margin
  box_x = margin
  box_y = margin
  y_2_3 = box_y + 2 * box_h / 3
  ear = Point(box_x, y_2_3)
  throat = Point(box_x + box_w, y_2_3)
  box = LBox(rect=Rect(box_x, box_y, box_w, box_h), ear=ear, throat=throat)
  ar = s.ear_radius
  ax = box_x + 2 * box_w / 3
  appl = LApplicator(
    center=Point(ax, y_2_3),
    func_port=Point(ax, y_2_3 - ar),
    arg_port=Point(ax - ar, y_2_3),
    out_port=Point(ax + ar, y_2_3),
  )
  wp1 = Point(box_x + box_w / 3, box_y + box_h / 3)
  wp2 = Point(ax, box_y + box_h / 3)
  pipes = (
    LPipe(points=(ear, wp1, wp2, appl.func_port)),
    LPipe(points=(ear, appl.arg_port)),
    LPipe(points=(appl.out_port, throat)),
  )
  return Layout(
    width=total_w, height=total_h, boxes=(box,), pipes=pipes,
    applicators=(appl,),
  )
##

def _layout_double_mockingbird(s: Style) -> Layout:
  box_w = 8 * s.grid
  box_h = 5 * s.grid
  margin = s.ear_radius
  total_w = box_w + 2 * margin
  total_h = box_h + 2 * margin
  box_x = margin
  box_y = margin
  r = s.ear_radius
  y_ear = box_y + 4 * box_h / 5
  ear = Point(box_x, y_ear)
  throat = Point(box_x + box_w, y_ear)
  box = LBox(rect=Rect(box_x, box_y, box_w, box_h), ear=ear, throat=throat)
  inner1_x = box_x + box_w / 2
  inner1_y = box_y + 2 * box_h / 5
  inner1 = LApplicator(
    center=Point(inner1_x, inner1_y),
    func_port=Point(inner1_x, inner1_y - r),
    arg_port=Point(inner1_x - r, inner1_y),
    out_port=Point(inner1_x + r, inner1_y),
  )
  inner2_x = box_x + box_w / 2
  inner2_y = box_y + 4 * box_h / 5
  inner2 = LApplicator(
    center=Point(inner2_x, inner2_y),
    func_port=Point(inner2_x, inner2_y - r),
    arg_port=Point(inner2_x - r, inner2_y),
    out_port=Point(inner2_x + r, inner2_y),
  )
  outer_x = box_x + 3 * box_w / 4
  outer_y = box_y + 4 * box_h / 5
  outer = LApplicator(
    center=Point(outer_x, outer_y),
    func_port=Point(outer_x, outer_y - r),
    arg_port=Point(outer_x - r, outer_y),
    out_port=Point(outer_x + r, outer_y),
  )
  fan_x = box_x + box_w / 4
  pipes = (
    LPipe(points=(ear, Point(fan_x, box_y + box_h / 5), Point(inner1_x, box_y + box_h / 5), inner1.func_port)),
    LPipe(points=(ear, Point(fan_x, inner1_y), inner1.arg_port)),
    LPipe(points=(ear, Point(fan_x, box_y + 3 * box_h / 5), Point(inner2_x, box_y + 3 * box_h / 5),
                  inner2.func_port)),
    LPipe(points=(ear, Point(fan_x, inner2_y), inner2.arg_port)),
    LPipe(points=(inner1.out_port, Point(outer_x, inner1_y), outer.func_port)),
    LPipe(points=(inner2.out_port, outer.arg_port)),
    LPipe(points=(outer.out_port, throat)),
  )
  return Layout(
    width=total_w, height=total_h, boxes=(box,), pipes=pipes,
    applicators=(inner1, inner2, outer),
  )
##

def render_layout(lo: Layout, style: Style | None = None) -> str:
  s = style or Style()
  svg = Element("svg", xmlns=_SVG_NS)
  svg.set("viewBox", f"0 0 {lo.width} {lo.height}")
  svg.set("width", str(lo.width))
  svg.set("height", str(lo.height))
  g_boxes = SubElement(svg, "g")
  g_boxes.set("class", "boxes")
  for box in lo.boxes:
    rect = box.rect
    rect_el = SubElement(g_boxes, "rect")
    rect_el.set("x", str(rect.x))
    rect_el.set("y", str(rect.y))
    rect_el.set("width", str(rect.width))
    rect_el.set("height", str(rect.height))
    rect_el.set("stroke", s.box_stroke)
    rect_el.set("stroke-dasharray", "4 3")
    rect_el.set("fill", "none")
    rect_el.set("stroke-width", "1")
  ##
  g_pipes = SubElement(svg, "g")
  g_pipes.set("class", "pipes")
  for pipe in lo.pipes:
    poly = SubElement(g_pipes, "polyline")
    pts = " ".join(f"{p.x},{p.y}" for p in pipe.points)
    poly.set("points", pts)
    poly.set("stroke", s.pipe_stroke)
    poly.set("stroke-width", str(s.pipe_width))
    poly.set("fill", "none")
  ##
  g_ears = SubElement(svg, "g")
  g_ears.set("class", "ears")
  for box in lo.boxes:
    ear = box.ear
    r = s.ear_radius
    path = SubElement(g_ears, "path")
    path.set("d", f"M {ear.x},{ear.y - r} A {r},{r} 0 0 0 {ear.x},{ear.y + r} Z")
    path.set("fill", s.fill)
  ##
  g_throats = SubElement(svg, "g")
  g_throats.set("class", "throats")
  for box in lo.boxes:
    throat = box.throat
    r = s.ear_radius
    path = SubElement(g_throats, "path")
    path.set("d", f"M {throat.x},{throat.y - r} A {r},{r} 0 0 1 {throat.x},{throat.y + r} Z")
    path.set("fill", s.fill)
  ##
  g_applicators = SubElement(svg, "g")
  g_applicators.set("class", "applicators")
  for appl in lo.applicators:
    circle = SubElement(g_applicators, "circle")
    circle.set("cx", str(appl.center.x))
    circle.set("cy", str(appl.center.y))
    circle.set("r", str(s.ear_radius))
    circle.set("fill", s.fill)
  ##
  return tostring(svg, encoding="unicode")
##

def render(expr: Expr, style: Style | None = None) -> str:
  s = style or Style()
  lo = layout(expr, s)
  return render_layout(lo, s)
##
