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

def _is_single_lambda_body(expr: Expr) -> bool:
  if isinstance(expr, Var): return expr.index == 0
  if isinstance(expr, Appl): return _is_single_lambda_body(expr.func) and _is_single_lambda_body(expr.arg)
  return False
##

def _body_stats(expr: Expr) -> tuple[int, int]:
  if isinstance(expr, Var): return (1, 0)
  assert isinstance(expr, Appl)
  fv, fd = _body_stats(expr.func)
  av, ad = _body_stats(expr.arg)
  return (fv + av, max(fd, ad) + 1)
##

def _layout_general(body: Expr, s: Style) -> Layout:
  num_vars, depth = _body_stats(body)
  num_cols = depth + 2
  r = s.ear_radius
  margin = r
  box_w = 2 * num_cols * s.grid
  box_h = (num_vars + 1) * s.grid
  total_w = box_w + 2 * margin
  total_h = box_h + 2 * margin
  box_x = margin
  box_y = margin
  ear_y = box_y + num_vars * box_h / (num_vars + 1)
  ear = Point(box_x, ear_y)
  throat = Point(box_x + box_w, ear_y)
  box = LBox(rect=Rect(box_x, box_y, box_w, box_h), ear=ear, throat=throat)
  def col_x(i: int) -> float:
    return box_x + i * box_w / num_cols
  ##
  def row_y(i: int) -> float:
    return box_y + (i + 1) * box_h / (num_vars + 1)
  ##
  fan_x = col_x(1)
  applicators: list[LApplicator] = []
  pipes: list[LPipe] = []
  leaf_counter = [0]
  def build(expr: Expr, depth_from_root: int) -> tuple[int | LApplicator, int]:
    if isinstance(expr, Var):
      idx = leaf_counter[0]
      leaf_counter[0] += 1
      return (idx, idx)
    ##
    assert isinstance(expr, Appl)
    func_result, _ = build(expr.func, depth_from_root + 1)
    arg_result, arg_last = build(expr.arg, depth_from_root + 1)
    appl_col = num_cols - 1 - depth_from_root
    ax = col_x(appl_col)
    ay = row_y(arg_last)
    appl = LApplicator(
      center=Point(ax, ay),
      func_port=Point(ax, ay - r),
      arg_port=Point(ax - r, ay),
      out_port=Point(ax + r, ay),
    )
    applicators.append(appl)
    if isinstance(func_result, int):
      leaf_y = row_y(func_result)
      pipes.append(LPipe(points=(ear, Point(fan_x, leaf_y), Point(ax, leaf_y), appl.func_port)))
    else:
      child_y = func_result.center.y
      pipes.append(LPipe(points=(func_result.out_port, Point(ax, child_y), appl.func_port)))
    ##
    if isinstance(arg_result, int):
      leaf_y = row_y(arg_result)
      pipes.append(LPipe(points=(ear, Point(fan_x, leaf_y), appl.arg_port)))
    else:
      pipes.append(LPipe(points=(arg_result.out_port, appl.arg_port)))
    ##
    return (appl, arg_last)
  ##
  result, _ = build(body, 0)
  if isinstance(result, int):
    pipes.append(LPipe(points=(ear, throat)))
  else:
    pipes.append(LPipe(points=(result.out_port, throat)))
  ##
  return Layout(
    width=total_w, height=total_h, boxes=(box,),
    pipes=tuple(pipes), applicators=tuple(applicators),
  )
##

def _layout_nested_var(var_index: int, s: Style) -> Layout:
  g = s.grid
  r = s.ear_radius
  margin = r
  box_w = 8 * g
  box_h = 5 * g
  total_w = box_w + 2 * margin
  total_h = box_h + 2 * margin
  bx = margin
  by = margin
  outer_ear = Point(bx, by + 2 * box_h / 5)
  outer_throat = Point(bx + box_w, by + 2 * box_h / 5)
  outer_box = LBox(rect=Rect(bx, by, box_w, box_h), ear=outer_ear, throat=outer_throat)
  inner_w = box_w / 2
  inner_h = 3 * box_h / 5
  inner_x = bx + box_w / 4
  inner_y = by + box_h / 5
  inner_ear = Point(inner_x, by + 3 * box_h / 5)
  inner_throat = Point(inner_x + inner_w, by + 3 * box_h / 5)
  inner_box = LBox(rect=Rect(inner_x, inner_y, inner_w, inner_h), ear=inner_ear, throat=inner_throat)
  throat_pipe = LPipe(points=(
    inner_throat,
    Point(bx + 7 * box_w / 8, by + 3 * box_h / 5),
    Point(bx + 7 * box_w / 8, by + 2 * box_h / 5),
    outer_throat,
  ))
  if var_index == 0:
    body_pipe = LPipe(points=(inner_ear, inner_throat))
  else:
    body_pipe = LPipe(points=(
      outer_ear,
      Point(inner_x, by + 2 * box_h / 5),
      Point(bx + box_w / 2, by + 3 * box_h / 5),
      inner_throat,
    ))
  ##
  return Layout(
    width=total_w, height=total_h,
    boxes=(outer_box, inner_box),
    pipes=(body_pipe, throat_pipe),
  )
##

def layout(expr: Expr, style: Style | None = None) -> Layout:
  if not isinstance(expr, Func):
    raise NotImplementedError(f"layout() only supports Func expressions, got: {expr}")
  ##
  s = style or Style()
  body = expr.body
  if isinstance(body, Func) and isinstance(body.body, Var) and body.body.index in (0, 1):
    return _layout_nested_var(body.body.index, s)
  ##
  if _is_single_lambda_body(body):
    return _layout_general(body, s)
  ##
  raise NotImplementedError(f"layout() does not yet support: {expr}")
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
