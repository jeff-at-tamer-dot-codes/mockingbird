from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
from mockingbird.ast import Expr, Var, Func

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
class Layout:
  width: float
  height: float
  boxes: tuple[LBox, ...]
  pipes: tuple[LPipe, ...]
##

_SVG_NS = "http://www.w3.org/2000/svg"

def layout(expr: Expr, style: Style | None = None) -> Layout:
  if not isinstance(expr, Func) or not isinstance(expr.body, Var) or expr.body.index != 0:
    raise NotImplementedError(f"layout() currently only supports Func(Var(0)), got: {expr}")
  ##
  s = style or Style()
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
  return tostring(svg, encoding="unicode")
##

def render(expr: Expr, style: Style | None = None) -> str:
  s = style or Style()
  lo = layout(expr, s)
  return render_layout(lo, s)
##
