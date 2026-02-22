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

def _layout_body_in_box(
    body: Expr, ear: Point, throat: Point,
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
  return (pipes, applicators)
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
  pipes, applicators = _layout_body_in_box(body, ear, throat, box_x, box_y, box_w, box_h, s)
  return Layout(
    width=total_w, height=total_h, boxes=(box,),
    pipes=tuple(pipes), applicators=tuple(applicators),
  )
##

def _layout_nested_var(depth: int, var_index: int, s: Style) -> Layout:
  g = s.grid
  bx = s.ear_radius
  by = s.ear_radius
  N = depth
  outer_w = 2 * (N + 2) * g
  outer_h = (3 * N - 1) * g
  total_w = outer_w + 2 * bx
  total_h = outer_h + 2 * by
  boxes: list[LBox] = []
  for i in range(N):
    w_i = outer_w * (N - i) / N
    x_i = bx + outer_w * i / (2 * N)
    top_i = by + outer_h * i / (3 * N - 1)
    h_i = outer_h * (3 * N - 1 - 2 * i) / (3 * N - 1)
    ety = by + outer_h * (N + i) / (3 * N - 1)
    ear = Point(x_i, ety)
    throat = Point(x_i + w_i, ety)
    boxes.append(LBox(rect=Rect(x_i, top_i, w_i, h_i), ear=ear, throat=throat))
  ##
  innermost = boxes[N - 1]
  if var_index == 0:
    body_pipe = LPipe(points=(innermost.ear, innermost.throat))
  else:
    source = boxes[N - 1 - var_index]
    body_pipe = LPipe(points=(
      source.ear,
      Point(innermost.rect.x, source.ear.y),
      Point(innermost.rect.x + innermost.rect.width / 2, innermost.throat.y),
      innermost.throat,
    ))
  ##
  pipes: list[LPipe] = [body_pipe]
  for i in reversed(range(N - 1)):
    mid_x = bx + outer_w * (4 * N - 2 * i - 1) / (4 * N)
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
  )
##

def _layout_nested_body(depth: int, body: Expr, s: Style) -> Layout:
  g = s.grid
  r = s.ear_radius
  num_vars, body_depth = _body_stats(body)
  num_cols = body_depth + 2
  inner_w = 2 * num_cols * g
  inner_h = (num_vars + 1) * g
  N = depth
  gap_w = 2 * g
  outer_w = inner_w + 2 * (N - 1) * gap_w
  outer_h = inner_h * (3 * N - 1) / (N + 1)
  bx = r
  by = r
  total_w = outer_w + 2 * bx
  total_h = outer_h + 2 * by
  inner_top = by + outer_h * (N - 1) / (3 * N - 1)
  inner_ear_y = inner_top + inner_h - g
  boxes: list[LBox] = []
  for i in range(N):
    w_i = inner_w + 2 * (N - 1 - i) * gap_w
    x_i = bx + i * gap_w
    top_i = by + outer_h * i / (3 * N - 1)
    h_i = outer_h * (3 * N - 1 - 2 * i) / (3 * N - 1)
    ety = inner_ear_y - (N - 1 - i) * g
    ear = Point(x_i, ety)
    throat = Point(x_i + w_i, ety)
    boxes.append(LBox(rect=Rect(x_i, top_i, w_i, h_i), ear=ear, throat=throat))
  ##
  innermost = boxes[N - 1]
  body_pipes, applicators = _layout_body_in_box(
    body, innermost.ear, innermost.throat,
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

def layout(expr: Expr, style: Style | None = None) -> Layout:
  if not isinstance(expr, Func):
    raise NotImplementedError(f"layout() only supports Func expressions, got: {expr}")
  ##
  s = style or Style()
  body = expr.body
  depth, inner = 1, body
  while isinstance(inner, Func):
    depth += 1
    inner = inner.body
  ##
  if depth >= 2 and isinstance(inner, Var) and 0 <= inner.index < depth:
    return _layout_nested_var(depth, inner.index, s)
  ##
  if depth >= 2 and _is_single_lambda_body(inner):
    return _layout_nested_body(depth, inner, s)
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
