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

def _is_closed_appl_body(expr: Expr, depth: int) -> bool:
  if isinstance(expr, Var): return 0 <= expr.index < depth
  if isinstance(expr, Appl): return _is_closed_appl_body(expr.func, depth) and _is_closed_appl_body(expr.arg, depth)
  return False
##

def _body_stats(expr: Expr) -> tuple[int, int]:
  if isinstance(expr, Var): return (1, 0)
  assert isinstance(expr, Appl)
  fv, fd = _body_stats(expr.func)
  av, ad = _body_stats(expr.arg)
  return (fv + av, max(fd, ad) + 1)
##

def _max_var_index(expr: Expr) -> int:
  if isinstance(expr, Var): return expr.index
  assert isinstance(expr, Appl)
  return max(_max_var_index(expr.func), _max_var_index(expr.arg))
##

def _layout_body_in_box(
    body: Expr, boxes: list[LBox], throat: Point,
    box_x: float, box_y: float, box_w: float, box_h: float,
    s: Style,
) -> tuple[list[LPipe], list[LApplicator]]:
  num_vars, depth = _body_stats(body)
  num_cols = depth + 2
  r = s.ear_radius
  def col_x(i: int) -> float:
    return box_x + i * box_w / num_cols
  ##
  def row_y(i: int) -> float:
    return box_y + (i + 1) * box_h / (num_vars + 1)
  ##
  fan_x = col_x(1)
  def _var_entry(var_ear: Point) -> tuple[Point, ...]:
    if var_ear.x < box_x: return (var_ear, Point(box_x, var_ear.y))
    return (var_ear,)
  ##
  applicators: list[LApplicator] = []
  pipes: list[LPipe] = []
  leaf_counter = [0]
  var_indices: list[int] = []
  def build(expr: Expr, depth_from_root: int) -> tuple[int | LApplicator, int]:
    if isinstance(expr, Var):
      idx = leaf_counter[0]
      leaf_counter[0] += 1
      var_indices.append(expr.index)
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
      var_ear = boxes[len(boxes) - 1 - var_indices[func_result]].ear
      pipes.append(LPipe(points=(*_var_entry(var_ear), Point(fan_x, leaf_y), Point(ax, leaf_y), appl.func_port)))
    else:
      child_y = func_result.center.y
      pipes.append(LPipe(points=(func_result.out_port, Point(ax, child_y), appl.func_port)))
    ##
    if isinstance(arg_result, int):
      leaf_y = row_y(arg_result)
      var_ear = boxes[len(boxes) - 1 - var_indices[arg_result]].ear
      pipes.append(LPipe(points=(*_var_entry(var_ear), Point(fan_x, leaf_y), appl.arg_port)))
    else:
      pipes.append(LPipe(points=(arg_result.out_port, appl.arg_port)))
    ##
    return (appl, arg_last)
  ##
  result, _ = build(body, 0)
  if isinstance(result, int):
    var_ear = boxes[len(boxes) - 1 - var_indices[result]].ear
    if var_ear.x < box_x:
      pipes.append(LPipe(points=(var_ear, Point(box_x, var_ear.y), Point(fan_x, throat.y), throat)))
    else:
      pipes.append(LPipe(points=(var_ear, throat)))
    ##
  else:
    pipes.append(LPipe(points=(result.out_port, throat)))
  ##
  return (pipes, applicators)
##

def _layout_nested_body(depth: int, body: Expr, s: Style) -> Layout:
  g = s.grid
  r = s.ear_radius
  num_vars, body_depth = _body_stats(body)
  num_cols = body_depth + 2
  inner_w = 2 * num_cols * g
  max_k = _max_var_index(body)
  inner_h = max(num_vars + 1, max_k + 2) * g
  N = depth
  gap_w = 2 * g
  outer_w = inner_w + 2 * (N - 1) * gap_w
  outer_h = inner_h + 2 * (N - 1) * g
  bx = r
  by = r
  total_w = outer_w + 2 * bx
  total_h = outer_h + 2 * by
  inner_top = by + (N - 1) * g
  inner_ear_y = inner_top + inner_h - g
  boxes: list[LBox] = []
  for i in range(N):
    w_i = inner_w + 2 * (N - 1 - i) * gap_w
    x_i = bx + i * gap_w
    top_i = by + i * g
    h_i = inner_h + 2 * (N - 1 - i) * g
    ety = inner_ear_y - (N - 1 - i) * g
    ear = Point(x_i, ety)
    throat = Point(x_i + w_i, ety)
    boxes.append(LBox(rect=Rect(x_i, top_i, w_i, h_i), ear=ear, throat=throat))
  ##
  innermost = boxes[N - 1]
  body_pipes, applicators = _layout_body_in_box(
    body, boxes, innermost.throat,
    innermost.rect.x, innermost.rect.y, innermost.rect.width, innermost.rect.height, s,
  )
  pipes: list[LPipe] = list(body_pipes)
  for i in reversed(range(N - 1)):
    mid_x = (boxes[i + 1].throat.x + boxes[i].throat.x) / 2
    pipes.append(LPipe(points=(
      boxes[i + 1].throat,
      Point(mid_x, boxes[i + 1].throat.y),
      Point(mid_x, boxes[i].throat.y),
      boxes[i].throat,
    )))
  ##
  return Layout(
    width=total_w, height=total_h,
    boxes=tuple(boxes), pipes=tuple(pipes),
    applicators=tuple(applicators),
  )
##

def _offset_layout(lo: Layout, dx: float, dy: float) -> Layout:
  if dx == 0 and dy == 0: return lo
  def pt(p: Point) -> Point:
    return Point(p.x + dx, p.y + dy)
  ##
  boxes = tuple(
    LBox(rect=Rect(b.rect.x + dx, b.rect.y + dy, b.rect.width, b.rect.height),
         ear=pt(b.ear), throat=pt(b.throat))
    for b in lo.boxes
  )
  pipes = tuple(
    LPipe(points=tuple(pt(p) for p in pipe.points))
    for pipe in lo.pipes
  )
  applicators = tuple(
    LApplicator(center=pt(a.center), func_port=pt(a.func_port), arg_port=pt(a.arg_port), out_port=pt(a.out_port))
    for a in lo.applicators
  )
  return Layout(width=lo.width, height=lo.height, boxes=boxes, pipes=pipes, applicators=applicators)
##

def layout(expr: Expr, style: Style | None = None) -> Layout:
  s = style or Style()
  if isinstance(expr, Appl) and isinstance(expr.func, Func) and isinstance(expr.arg, Func):
    lo_func = layout(expr.func, s)
    lo_arg = layout(expr.arg, s)
    arg_throat = lo_arg.boxes[0].throat
    func_ear = lo_func.boxes[0].ear
    dy_arg = max(0.0, func_ear.y - arg_throat.y)
    dy_func = max(0.0, arg_throat.y - func_ear.y)
    dx_func = arg_throat.x + s.grid - func_ear.x
    shifted_arg = _offset_layout(lo_arg, 0.0, dy_arg)
    shifted_func = _offset_layout(lo_func, dx_func, dy_func)
    wire = LPipe(points=(shifted_arg.boxes[0].throat, shifted_func.boxes[0].ear))
    return Layout(
      width=dx_func + lo_func.width,
      height=max(dy_arg + lo_arg.height, dy_func + lo_func.height),
      boxes=shifted_arg.boxes + shifted_func.boxes,
      pipes=shifted_arg.pipes + (wire,) + shifted_func.pipes,
      applicators=shifted_arg.applicators + shifted_func.applicators,
    )
  ##
  if not isinstance(expr, Func):
    raise NotImplementedError(f"layout() only supports Func expressions, got: {expr}")
  ##
  body = expr.body
  depth, inner = 1, body
  while isinstance(inner, Func):
    depth += 1
    inner = inner.body
  ##
  if _is_closed_appl_body(inner, depth):
    return _layout_nested_body(depth, inner, s)
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
