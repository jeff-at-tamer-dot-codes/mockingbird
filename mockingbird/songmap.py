from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
from mockingbird.ast import Expr, Var, Func, Appl

@dataclass(frozen=True, slots=True)
class Point:
  x: float
  y: float
  def offset(self, dx: float, dy: float) -> 'Point':
    return Point(self.x + dx, self.y + dy)
  ##
  def scale(self, factor: float) -> 'Point':
    return Point(self.x * factor, self.y * factor)
  ##
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
  grid: float = 10.0
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
  def offset(self, dx: float, dy: float) -> 'LBox':
    return LBox(
      rect=Rect(self.rect.x + dx, self.rect.y + dy, self.rect.width, self.rect.height),
      ear=self.ear.offset(dx, dy),
      throat=self.throat.offset(dx, dy),
    )
  ##
  def scale(self, factor: float) -> 'LBox':
    return LBox(
      rect=Rect(self.rect.x * factor, self.rect.y * factor, self.rect.width * factor, self.rect.height * factor),
      ear=self.ear.scale(factor),
      throat=self.throat.scale(factor),
    )
  ##
##

@dataclass(frozen=True, slots=True)
class LPipe:
  points: tuple[Point, ...]
  def offset(self, dx: float, dy: float) -> 'LPipe':
    return LPipe(points=tuple(p.offset(dx, dy) for p in self.points))
  ##
  def scale(self, factor: float) -> 'LPipe':
    return LPipe(points=tuple(p.scale(factor) for p in self.points))
  ##
##

@dataclass(frozen=True, slots=True)
class LApplicator:
  center: Point
  func_port: Point
  arg_port: Point
  out_port: Point
  @classmethod
  def from_center(cls, x: float, y: float, r: float) -> 'LApplicator':
    return cls(
      center=Point(x, y),
      func_port=Point(x, y - r),
      arg_port=Point(x - r, y),
      out_port=Point(x + r, y),
    )
  ##
  def offset(self, dx: float, dy: float) -> 'LApplicator':
    return LApplicator(
      center=self.center.offset(dx, dy),
      func_port=self.func_port.offset(dx, dy),
      arg_port=self.arg_port.offset(dx, dy),
      out_port=self.out_port.offset(dx, dy),
    )
  ##
  def scale(self, factor: float) -> 'LApplicator':
    return LApplicator(
      center=self.center.scale(factor),
      func_port=self.func_port.scale(factor),
      arg_port=self.arg_port.scale(factor),
      out_port=self.out_port.scale(factor),
    )
  ##
##

@dataclass(frozen=True, slots=True)
class Layout:
  width: float
  height: float
  boxes: tuple[LBox, ...]
  pipes: tuple[LPipe, ...]
  applicators: tuple[LApplicator, ...] = ()
  output: Point | None = None
  def offset(self, dx: float, dy: float) -> 'Layout':
    return Layout(
      width=self.width, height=self.height,
      boxes=tuple(b.offset(dx, dy) for b in self.boxes),
      pipes=tuple(p.offset(dx, dy) for p in self.pipes),
      applicators=tuple(a.offset(dx, dy) for a in self.applicators),
      output=self.output.offset(dx, dy) if self.output is not None else None,
    )
  ##
  def scale(self, factor: float) -> 'Layout':
    return Layout(
      width=self.width * factor, height=self.height * factor,
      boxes=tuple(b.scale(factor) for b in self.boxes),
      pipes=tuple(p.scale(factor) for p in self.pipes),
      applicators=tuple(a.scale(factor) for a in self.applicators),
      output=self.output.scale(factor) if self.output is not None else None,
    )
  ##
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

class _BodyBuilder:
  def __init__(
      self, body: Expr, boxes: list[LBox], throat: Point,
      box_x: float, box_y: float, box_w: float, box_h: float,
  ) -> None:
    self._body = body
    self._boxes = boxes
    self._throat = throat
    self._box_x = box_x
    self._r = 1
    num_vars, depth = _body_stats(body)
    self._num_cols = depth + 2
    self._box_w = box_w
    self._box_h = box_h
    self._box_y = box_y
    self._num_vars = num_vars
    self._num_rows = int(box_h / 2)
    self._row_offset = self._num_rows - num_vars - 1
    self._fan_x = self._col_x(1)
    self.pipes: list[LPipe] = []
    self.applicators: list[LApplicator] = []
    self._leaf_counter = 0
    self._var_indices: list[int] = []
  ##
  def _col_x(self, i: int) -> float:
    return self._box_x + i * self._box_w / self._num_cols
  ##
  def _row_y(self, i: int) -> float:
    return self._box_y + (i + 1 + self._row_offset) * self._box_h / self._num_rows
  ##
  def _var_entry(self, var_ear: Point) -> tuple[Point, ...]:
    if var_ear.x < self._box_x: return (var_ear, Point(self._box_x, var_ear.y))
    return (var_ear,)
  ##
  def _build(self, expr: Expr, depth_from_root: int) -> tuple[int | LApplicator, int]:
    if isinstance(expr, Var):
      idx = self._leaf_counter
      self._leaf_counter += 1
      self._var_indices.append(expr.index)
      return (idx, idx)
    ##
    assert isinstance(expr, Appl)
    func_result, _ = self._build(expr.func, depth_from_root + 1)
    arg_result, arg_last = self._build(expr.arg, depth_from_root + 1)
    appl_col = self._num_cols - 1 - depth_from_root
    ax = self._col_x(appl_col)
    ay = self._row_y(arg_last)
    appl = LApplicator.from_center(ax, ay, self._r)
    self.applicators.append(appl)
    if isinstance(func_result, int):
      leaf_y = self._row_y(func_result)
      var_ear = self._boxes[len(self._boxes) - 1 - self._var_indices[func_result]].ear
      self.pipes.append(LPipe(points=(
        *self._var_entry(var_ear), Point(self._fan_x, leaf_y), Point(ax, leaf_y), appl.func_port,
      )))
    else:
      child_y = func_result.center.y
      self.pipes.append(LPipe(points=(func_result.out_port, Point(ax, child_y), appl.func_port)))
    ##
    if isinstance(arg_result, int):
      leaf_y = self._row_y(arg_result)
      var_ear = self._boxes[len(self._boxes) - 1 - self._var_indices[arg_result]].ear
      self.pipes.append(LPipe(points=(*self._var_entry(var_ear), Point(self._fan_x, leaf_y), appl.arg_port)))
    else:
      self.pipes.append(LPipe(points=(arg_result.out_port, appl.arg_port)))
    ##
    return (appl, arg_last)
  ##
  def run(self) -> tuple[list[LPipe], list[LApplicator]]:
    result, _ = self._build(self._body, 0)
    if isinstance(result, int):
      var_ear = self._boxes[len(self._boxes) - 1 - self._var_indices[result]].ear
      if var_ear.x < self._box_x:
        self.pipes.append(LPipe(points=(
          var_ear, Point(self._box_x, var_ear.y), Point(self._fan_x, self._throat.y), self._throat,
        )))
      else:
        self.pipes.append(LPipe(points=(var_ear, self._throat)))
      ##
    else:
      self.pipes.append(LPipe(points=(result.out_port, self._throat)))
    ##
    return (self.pipes, self.applicators)
  ##
##

def _layout_body_in_box(
    body: Expr, boxes: list[LBox], throat: Point,
    box_x: float, box_y: float, box_w: float, box_h: float,
) -> tuple[list[LPipe], list[LApplicator]]:
  return _BodyBuilder(body, boxes, throat, box_x, box_y, box_w, box_h).run()
##

def _layout_nested_body(depth: int, body: Expr) -> Layout:
  num_vars, body_depth = _body_stats(body)
  num_cols = body_depth + 2
  inner_w = 4 * num_cols
  max_k = _max_var_index(body)
  inner_h = 2 * max(num_vars + 1, max_k + 2)
  N = depth
  gap_w = 4
  outer_w = inner_w + 2 * (N - 1) * gap_w
  outer_h = inner_h + 4 * (N - 1)
  bx = 1
  by = 1
  total_w = outer_w + 2 * bx
  total_h = outer_h + 2 * by
  inner_top = 1 + 2 * (N - 1)
  inner_ear_y = inner_top + inner_h - 2
  boxes: list[LBox] = []
  for i in range(N):
    w_i = inner_w + 2 * (N - 1 - i) * gap_w
    x_i = bx + i * gap_w
    top_i = 1 + i * 2
    h_i = inner_h + 4 * (N - 1 - i)
    ety = inner_ear_y - 2 * (N - 1 - i)
    ear = Point(x_i, ety)
    throat = Point(x_i + w_i, ety)
    boxes.append(LBox(rect=Rect(x_i, top_i, w_i, h_i), ear=ear, throat=throat))
  ##
  innermost = boxes[N - 1]
  body_pipes, applicators = _layout_body_in_box(
    body, boxes, innermost.throat,
    innermost.rect.x, innermost.rect.y, innermost.rect.width, innermost.rect.height,
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
  return lo.offset(dx, dy)
##

def _output_point(lo: Layout) -> Point:
  if lo.output is not None: return lo.output
  return max(lo.boxes, key=lambda b: b.throat.x).throat
##

def _collect_element_rects(lo: Layout, dx: float, dy: float) -> list[Rect]:
  rects: list[Rect] = []
  for box in lo.boxes:
    rects.append(Rect(box.rect.x + dx, box.rect.y + dy, box.rect.width, box.rect.height))
    rects.append(Rect(box.ear.x - 1 + dx, box.ear.y - 1 + dy, 1, 2))
    rects.append(Rect(box.throat.x + dx, box.throat.y - 1 + dy, 1, 2))
  ##
  for appl in lo.applicators:
    rects.append(Rect(appl.center.x - 1 + dx, appl.center.y - 1 + dy, 2, 2))
  ##
  return rects
##

def _find_min_vertical_gap(lo_top: Layout, dx_top: float, lo_bot: Layout, dx_bot: float) -> float:
  top_rects = _collect_element_rects(lo_top, dx_top, 0.0)
  bot_rects = _collect_element_rects(lo_bot, dx_bot, 0.0)
  min_dy = 0.0
  for tr in top_rects:
    for br in bot_rects:
      if tr.x < br.x + br.width and br.x < tr.x + tr.width:
        needed = tr.y + tr.height + 2 - br.y
        if needed > min_dy: min_dy = needed
      ##
    ##
  ##
  return min_dy
##

def _layout_func_wrapping(depth: int, inner_lo: Layout) -> Layout:
  N = depth
  margin_x = 1
  margin_y = 1
  gap_w = 4
  inner_out = _output_point(inner_lo)
  is_throat_output = inner_lo.output is None
  right_pad = 4 if is_throat_output else 1
  innermost_w = 3 + max(inner_out.x + right_pad, inner_lo.width)
  innermost_h = inner_lo.height + 2
  inner_dx = N * 4
  inner_dy = N * 2
  case_offset = -2 if is_throat_output else 0
  innermost_throat_y = inner_out.y + inner_dy + case_offset
  boxes: list[LBox] = []
  for i in range(N):
    box_w = innermost_w + 2 * (N - 1 - i) * gap_w
    box_h = innermost_h + 4 * (N - 1 - i)
    box_x = margin_x + i * gap_w
    box_y = 1 + i * 2
    throat_y = innermost_throat_y - (N - 1 - i) * 2
    ear = Point(box_x, throat_y)
    throat = Point(box_x + box_w, throat_y)
    boxes.append(LBox(rect=Rect(box_x, box_y, box_w, box_h), ear=ear, throat=throat))
  ##
  shifted_inner = inner_lo.offset(inner_dx, inner_dy)
  inner_out_shifted = Point(inner_out.x + inner_dx, inner_out.y + inner_dy)
  innermost_throat = boxes[N - 1].throat
  pipes: list[LPipe] = list(shifted_inner.pipes)
  if is_throat_output:
    mid_x = (inner_out_shifted.x + innermost_throat.x) / 2
    pipes.append(LPipe(points=(
      inner_out_shifted,
      Point(mid_x, inner_out_shifted.y),
      Point(mid_x, innermost_throat.y),
      innermost_throat,
    )))
  else:
    pipes.append(LPipe(points=(inner_out_shifted, innermost_throat)))
  ##
  for i in reversed(range(N - 1)):
    mid_x = (boxes[i + 1].throat.x + boxes[i].throat.x) / 2
    pipes.append(LPipe(points=(
      boxes[i + 1].throat,
      Point(mid_x, boxes[i + 1].throat.y),
      Point(mid_x, boxes[i].throat.y),
      boxes[i].throat,
    )))
  ##
  outermost_w = innermost_w + 2 * (N - 1) * gap_w
  outermost_h = innermost_h + 4 * (N - 1)
  total_w = 2 * margin_x + outermost_w
  total_h = 2 * margin_y + outermost_h
  return Layout(
    width=total_w, height=total_h,
    boxes=tuple(boxes) + shifted_inner.boxes,
    pipes=tuple(pipes),
    applicators=shifted_inner.applicators,
  )
##

def _layout_left_appl(expr: Appl) -> Layout:
  lo_top = _layout(expr.func)
  lo_bot = _layout(expr.arg)
  top_out = _output_point(lo_top)
  bot_out = _output_point(lo_bot)
  max_out_x = max(top_out.x, bot_out.x)
  dx_top = max_out_x - top_out.x
  dx_bot = max_out_x - bot_out.x
  dy_bot = _find_min_vertical_gap(lo_top, dx_top, lo_bot, dx_bot)
  sh_top = _offset_layout(lo_top, dx_top, 0.0)
  sh_bot = _offset_layout(lo_bot, dx_bot, dy_bot)
  top_out_shifted = Point(top_out.x + dx_top, top_out.y)
  bot_out_shifted = Point(bot_out.x + dx_bot, bot_out.y + dy_bot)
  appl_cx = max_out_x + 2
  appl_cy = bot_out_shifted.y
  appl = LApplicator.from_center(appl_cx, appl_cy, 1)
  func_wire = LPipe(points=(top_out_shifted, Point(appl_cx, top_out_shifted.y), appl.func_port))
  arg_wire = LPipe(points=(bot_out_shifted, appl.arg_port))
  width = max(dx_top + lo_top.width, dx_bot + lo_bot.width, appl_cx + 1)
  height = max(lo_top.height, dy_bot + lo_bot.height)
  return Layout(
    width=width, height=height,
    boxes=sh_top.boxes + sh_bot.boxes,
    pipes=sh_top.pipes + sh_bot.pipes + (func_wire, arg_wire),
    applicators=sh_top.applicators + sh_bot.applicators + (appl,),
    output=appl.out_port,
  )
##

def _layout_right_appl_chain(expr: Appl) -> Layout:
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
  layouts = [_layout(term) for term in terms]
  conn_ys = [lo.boxes[0].ear.y for lo in layouts]
  max_y = max(conn_ys)
  dys = [max_y - cy for cy in conn_ys]
  dxs: list[float] = [0.0]
  for i in range(1, len(layouts)):
    prev_throat_x = dxs[i - 1] + layouts[i - 1].boxes[0].throat.x
    dxs.append(prev_throat_x + 2 - layouts[i].boxes[0].ear.x)
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

def _layout_appl(expr: Appl) -> Layout:
  if isinstance(expr.func, Appl):
    return _layout_left_appl(expr)
  ##
  return _layout_right_appl_chain(expr)
##

def _layout(expr: Expr) -> Layout:
  if isinstance(expr, Appl):
    return _layout_appl(expr)
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
    return _layout_nested_body(depth, inner)
  ##
  if isinstance(inner, Appl) and not any(inner.is_free(i) for i in range(depth)):
    inner_lo = _layout(inner)
    return _layout_func_wrapping(depth, inner_lo)
  ##
  raise NotImplementedError(f"layout() does not yet support: {expr}")
##

def layout(expr: Expr, style: Style | None = None) -> Layout:
  s = style or Style()
  return _layout(expr).scale(s.grid)
##

def _render_boxes(parent: Element, boxes: tuple[LBox, ...], s: Style) -> None:
  g = SubElement(parent, "g")
  g.set("class", "boxes")
  for box in boxes:
    rect = box.rect
    rect_el = SubElement(g, "rect")
    rect_el.set("x", str(rect.x))
    rect_el.set("y", str(rect.y))
    rect_el.set("width", str(rect.width))
    rect_el.set("height", str(rect.height))
    rect_el.set("stroke", s.box_stroke)
    rect_el.set("stroke-dasharray", "4 3")
    rect_el.set("fill", "none")
    rect_el.set("stroke-width", "1")
  ##
##

def _render_pipes(parent: Element, pipes: tuple[LPipe, ...], s: Style) -> None:
  g = SubElement(parent, "g")
  g.set("class", "pipes")
  for pipe in pipes:
    poly = SubElement(g, "polyline")
    pts = " ".join(f"{p.x},{p.y}" for p in pipe.points)
    poly.set("points", pts)
    poly.set("stroke", s.pipe_stroke)
    poly.set("stroke-width", str(s.pipe_width))
    poly.set("fill", "none")
  ##
##

def _render_ears(parent: Element, boxes: tuple[LBox, ...], s: Style) -> None:
  g = SubElement(parent, "g")
  g.set("class", "ears")
  w = s.pipe_width
  for box in boxes:
    ear = box.ear
    r = s.grid
    ri = r - w
    r2 = r - 2 * w
    ring = SubElement(g, "path")
    ring.set("d", (
      f"M {ear.x},{ear.y - r} A {r},{r} 0 0 0 {ear.x},{ear.y + r}"
      f" L {ear.x},{ear.y + ri} A {ri},{ri} 0 0 1 {ear.x},{ear.y - ri} Z"
    ))
    ring.set("fill", s.fill)
    dot = SubElement(g, "path")
    dot.set("d", f"M {ear.x},{ear.y - r2} A {r2},{r2} 0 0 0 {ear.x},{ear.y + r2} Z")
    dot.set("fill", s.fill)
  ##
##

def _render_throats(parent: Element, boxes: tuple[LBox, ...], s: Style) -> None:
  g = SubElement(parent, "g")
  g.set("class", "throats")
  w = s.pipe_width
  for box in boxes:
    throat = box.throat
    r = s.grid
    ri = r - w
    r2 = r - 2 * w
    ring = SubElement(g, "path")
    ring.set("d", (
      f"M {throat.x},{throat.y - r} A {r},{r} 0 0 1 {throat.x},{throat.y + r}"
      f" L {throat.x},{throat.y + ri} A {ri},{ri} 0 0 0 {throat.x},{throat.y - ri} Z"
    ))
    ring.set("fill", s.fill)
    dot = SubElement(g, "path")
    dot.set("d", f"M {throat.x},{throat.y - r2} A {r2},{r2} 0 0 1 {throat.x},{throat.y + r2} Z")
    dot.set("fill", s.fill)
  ##
##

def _render_applicators(parent: Element, applicators: tuple[LApplicator, ...], s: Style) -> None:
  g = SubElement(parent, "g")
  g.set("class", "applicators")
  w = s.pipe_width
  r = s.grid
  for appl in applicators:
    ring = SubElement(g, "circle")
    ring.set("cx", str(appl.center.x))
    ring.set("cy", str(appl.center.y))
    ring.set("r", str(r - w / 2))
    ring.set("stroke", s.fill)
    ring.set("stroke-width", str(w))
    ring.set("fill", "none")
    dot = SubElement(g, "circle")
    dot.set("cx", str(appl.center.x))
    dot.set("cy", str(appl.center.y))
    dot.set("r", str(r - 2 * w))
    dot.set("fill", s.fill)
  ##
##

def render_layout(lo: Layout, style: Style | None = None) -> str:
  s = style or Style()
  svg = Element("svg", xmlns=_SVG_NS)
  svg.set("viewBox", f"0 0 {lo.width} {lo.height}")
  svg.set("width", str(lo.width))
  svg.set("height", str(lo.height))
  _render_boxes(svg, lo.boxes, s)
  _render_pipes(svg, lo.pipes, s)
  _render_ears(svg, lo.boxes, s)
  _render_throats(svg, lo.boxes, s)
  _render_applicators(svg, lo.applicators, s)
  return tostring(svg, encoding="unicode")
##

def render(expr: Expr, style: Style | None = None) -> str:
  s = style or Style()
  lo = layout(expr, s)
  return render_layout(lo, s)
##
