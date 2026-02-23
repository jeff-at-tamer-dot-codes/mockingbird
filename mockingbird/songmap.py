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
  output: Point | None = None
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
  output = pt(lo.output) if lo.output is not None else None
  return Layout(width=lo.width, height=lo.height, boxes=boxes, pipes=pipes, applicators=applicators, output=output)
##

def _output_point(lo: Layout) -> Point:
  if lo.output is not None: return lo.output
  return max(lo.boxes, key=lambda b: b.throat.x).throat
##

def _collect_element_rects(lo: Layout, dx: float, dy: float, r: float) -> list[Rect]:
  rects: list[Rect] = []
  for box in lo.boxes:
    rects.append(Rect(box.rect.x + dx, box.rect.y + dy, box.rect.width, box.rect.height))
    rects.append(Rect(box.ear.x - r + dx, box.ear.y - r + dy, r, 2 * r))
    rects.append(Rect(box.throat.x + dx, box.throat.y - r + dy, r, 2 * r))
  ##
  for appl in lo.applicators:
    rects.append(Rect(appl.center.x - r + dx, appl.center.y - r + dy, 2 * r, 2 * r))
  ##
  return rects
##

def _find_min_vertical_gap(lo_top: Layout, dx_top: float, lo_bot: Layout, dx_bot: float, s: Style) -> float:
  r = s.ear_radius
  g = s.grid
  top_rects = _collect_element_rects(lo_top, dx_top, 0.0, r)
  bot_rects = _collect_element_rects(lo_bot, dx_bot, 0.0, r)
  min_dy = 0.0
  for tr in top_rects:
    for br in bot_rects:
      if tr.x < br.x + br.width and br.x < tr.x + tr.width:
        needed = tr.y + tr.height + g - br.y
        if needed > min_dy: min_dy = needed
      ##
    ##
  ##
  return min_dy
##

def _layout_left_appl(expr: Appl, s: Style) -> Layout:
  g = s.grid
  r = s.ear_radius
  lo_top = layout(expr.func, s)
  lo_bot = layout(expr.arg, s)
  top_out = _output_point(lo_top)
  bot_out = _output_point(lo_bot)
  max_out_x = max(top_out.x, bot_out.x)
  dx_top = max_out_x - top_out.x
  dx_bot = max_out_x - bot_out.x
  dy_bot = _find_min_vertical_gap(lo_top, dx_top, lo_bot, dx_bot, s)
  sh_top = _offset_layout(lo_top, dx_top, 0.0)
  sh_bot = _offset_layout(lo_bot, dx_bot, dy_bot)
  top_out_shifted = Point(top_out.x + dx_top, top_out.y)
  bot_out_shifted = Point(bot_out.x + dx_bot, bot_out.y + dy_bot)
  appl_cx = max_out_x + g
  appl_cy = bot_out_shifted.y
  appl = LApplicator(
    center=Point(appl_cx, appl_cy),
    func_port=Point(appl_cx, appl_cy - r),
    arg_port=Point(appl_cx - r, appl_cy),
    out_port=Point(appl_cx + r, appl_cy),
  )
  func_wire = LPipe(points=(top_out_shifted, Point(appl_cx, top_out_shifted.y), appl.func_port))
  arg_wire = LPipe(points=(bot_out_shifted, appl.arg_port))
  width = max(dx_top + lo_top.width, dx_bot + lo_bot.width, appl_cx + r)
  height = max(lo_top.height, dy_bot + lo_bot.height)
  return Layout(
    width=width, height=height,
    boxes=sh_top.boxes + sh_bot.boxes,
    pipes=sh_top.pipes + sh_bot.pipes + (func_wire, arg_wire),
    applicators=sh_top.applicators + sh_bot.applicators + (appl,),
    output=appl.out_port,
  )
##

def _layout_appl(expr: Appl, s: Style) -> Layout:
  if isinstance(expr.func, Appl):
    return _layout_left_appl(expr, s)
  ##
  terms: list[Func] = []
  current: Expr = expr
  while isinstance(current, Appl):
    if not isinstance(current.func, Func):
      raise NotImplementedError(f"layout() only supports right-nested Appl of Func terms, got: {expr}")
    ##
    terms.append(current.func)
    current = current.arg
  ##
  if not isinstance(current, Func):
    raise NotImplementedError(f"layout() only supports right-nested Appl of Func terms, got: {expr}")
  ##
  terms.append(current)
  terms.reverse()
  layouts = [layout(term, s) for term in terms]
  conn_ys = [lo.boxes[0].ear.y for lo in layouts]
  max_y = max(conn_ys)
  dys = [max_y - cy for cy in conn_ys]
  dxs: list[float] = [0.0]
  for i in range(1, len(layouts)):
    prev_throat_x = dxs[i - 1] + layouts[i - 1].boxes[0].throat.x
    dxs.append(prev_throat_x + s.grid - layouts[i].boxes[0].ear.x)
  ##
  shifted = [_offset_layout(layouts[i], dxs[i], dys[i]) for i in range(len(layouts))]
  all_boxes: tuple[LBox, ...] = ()
  all_pipes: tuple[LPipe, ...] = ()
  all_applicators: tuple[LApplicator, ...] = ()
  for i, sh in enumerate(shifted):
    all_boxes += sh.boxes
    all_pipes += sh.pipes
    if i < len(shifted) - 1:
      all_pipes += (LPipe(points=(sh.boxes[0].throat, shifted[i + 1].boxes[0].ear)),)
    ##
    all_applicators += sh.applicators
  ##
  total_width = dxs[-1] + layouts[-1].width
  total_height = max(dys[i] + layouts[i].height for i in range(len(layouts)))
  return Layout(
    width=total_width, height=total_height,
    boxes=all_boxes, pipes=all_pipes,
    applicators=all_applicators,
  )
##

def layout(expr: Expr, style: Style | None = None) -> Layout:
  s = style or Style()
  if isinstance(expr, Appl):
    return _layout_appl(expr, s)
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
