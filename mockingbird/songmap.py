from __future__ import annotations
from dataclasses import dataclass, field
from mockingbird.ast import Appl, Expr, Func, Var

# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Layout elements
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LBox:
  rect: Rect
  ear: Point
  throat: Point
  depth: int
##

@dataclass(frozen=True, slots=True)
class LApplicator:
  center: Point
  operator_input: Point
  operand_input: Point
  output: Point
##

@dataclass(frozen=True, slots=True)
class LPipe:
  points: tuple[Point, ...]
##

@dataclass(frozen=True, slots=True)
class LFanout:
  source: Point
  targets: tuple[Point, ...]
##

@dataclass(frozen=True, slots=True)
class LCrossing:
  pipe_a: LPipe
  pipe_b: LPipe
  intersection: Point
##

@dataclass(frozen=True, slots=True)
class LFreeVar:
  entry: Point
  index: int
##

@dataclass(frozen=True, slots=True)
class Layout:
  width: float
  height: float
  boxes: tuple[LBox, ...]
  applicators: tuple[LApplicator, ...]
  pipes: tuple[LPipe, ...]
  fanouts: tuple[LFanout, ...]
  crossings: tuple[LCrossing, ...]
  free_vars: tuple[LFreeVar, ...]
##

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Style:
  grid: float = 30.0
  ear_radius: float = 6.0
  throat_radius: float = 6.0
  applicator_radius: float = 6.0
  pipe_width: float = 2.0
  box_padding: float = 12.0
  font_size: float = 12.0
  color_pipe: str = "#222"
  color_box: str = "#222"
  color_fill: str = "#222"
  color_bg: str = "white"
##

_DEFAULT_STYLE = Style()

# ---------------------------------------------------------------------------
# Analysis pass — collect variable usage info
# ---------------------------------------------------------------------------

@dataclass
class _VarUsage:
  uses: int = 0
  positions: list[Point] = field(default_factory=list)
##

@dataclass
class _Analysis:
  """Per-Func usage counts and free variable detection."""
  # Map from (depth, ear_index) → usage info; populated during layout
  bound_uses: dict[int, int] = field(default_factory=dict)
  free_indices: set[int] = field(default_factory=set)
##

def _analyze(expr: Expr, depth: int = 0) -> _Analysis:
  """Walk AST and collect variable usage info."""
  a = _Analysis()
  _analyze_walk(expr, depth, a)
  return a
##

def _analyze_walk(expr: Expr, depth: int, a: _Analysis) -> None:
  if isinstance(expr, Var):
    if expr.index < depth:
      # Bound variable — key is the binder depth
      binder = depth - 1 - expr.index
      a.bound_uses[binder] = a.bound_uses.get(binder, 0) + 1
    else:
      a.free_indices.add(expr.index - depth)
    ##
  elif isinstance(expr, Func):
    _analyze_walk(expr.body, depth + 1, a)
  elif isinstance(expr, Appl):
    _analyze_walk(expr.func, depth, a)
    _analyze_walk(expr.arg, depth, a)
  ##
##

# ---------------------------------------------------------------------------
# Measure pass — compute bounding sizes bottom-up
# ---------------------------------------------------------------------------

@dataclass
class _Size:
  width: float
  height: float
##

def _measure(expr: Expr, style: Style) -> _Size:
  g = style.grid
  pad = style.box_padding
  if isinstance(expr, Var):
    return _Size(0, g)
  ##
  if isinstance(expr, Func):
    body = _measure(expr.body, style)
    ear_row = g if body.height > g else 0
    w = g + pad + body.width + pad + g
    h = pad + ear_row + body.height + pad
    return _Size(w, h)
  ##
  if isinstance(expr, Appl):
    func_size = _measure(expr.func, style)
    arg_size = _measure(expr.arg, style)
    # Operator above, operand below; applicator column on right
    w = max(func_size.width, arg_size.width) + g
    h = func_size.height + arg_size.height
    return _Size(w, h)
  ##
  return _Size(g, g)  # fallback
##

# ---------------------------------------------------------------------------
# Place pass — assign absolute coordinates top-down
# ---------------------------------------------------------------------------

@dataclass
class _LayoutBuilder:
  boxes: list[LBox] = field(default_factory=list)
  applicators: list[LApplicator] = field(default_factory=list)
  pipes: list[LPipe] = field(default_factory=list)
  fanouts: list[LFanout] = field(default_factory=list)
  crossings: list[LCrossing] = field(default_factory=list)
  free_vars: list[LFreeVar] = field(default_factory=list)
  # Map binder_depth → ear position
  ear_positions: dict[int, Point] = field(default_factory=dict)
  # Collect var usage positions keyed by binder_depth
  var_positions: dict[int, list[Point]] = field(default_factory=dict)
  # Free var positions keyed by free index
  free_var_positions: dict[int, list[Point]] = field(default_factory=dict)
##

def _place(
  expr: Expr, x: float, y: float, style: Style, depth: int, builder: _LayoutBuilder,
) -> Point:
  """Place expr at (x, y). Returns the output point for wiring."""
  g = style.grid
  pad = style.box_padding
  if isinstance(expr, Var):
    # A variable reference — just a connection point, zero width
    pt = Point(x, y + g / 2)
    if expr.index < depth:
      binder = depth - 1 - expr.index
      builder.var_positions.setdefault(binder, []).append(pt)
    else:
      free_idx = expr.index - depth
      builder.free_var_positions.setdefault(free_idx, []).append(pt)
    ##
    return pt
  ##
  if isinstance(expr, Func):
    size = _measure(expr, style)
    body_size = _measure(expr.body, style)
    ear_row = g if body_size.height > g else 0
    rect = Rect(x, y, size.width, size.height)
    ear_y = y + pad + g / 2
    ear = Point(x, ear_y)
    throat = Point(x + size.width, ear_y)
    builder.boxes.append(LBox(rect, ear, throat, depth))
    builder.ear_positions[depth] = ear
    # Place body below the ear row
    body_x = x + g + pad
    body_y = y + pad + ear_row
    body_out = _place(expr.body, body_x, body_y, style, depth + 1, builder)
    # Pipe from body output to throat
    builder.pipes.append(LPipe((body_out, throat)))
    return throat
  ##
  if isinstance(expr, Appl):
    func_size = _measure(expr.func, style)
    arg_size = _measure(expr.arg, style)
    content_w = max(func_size.width, arg_size.width)
    total_h = func_size.height + arg_size.height
    # Applicator dot on the right edge
    app_x = x + content_w + g / 2
    app_y = y + total_h / 2
    app_center = Point(app_x, app_y)
    operator_input = Point(app_x, y + func_size.height / 2)
    operand_input = Point(x + content_w, y + func_size.height + arg_size.height / 2)
    output = Point(app_x + g / 2, app_y)
    builder.applicators.append(LApplicator(app_center, operator_input, operand_input, output))
    # Place operator (func) in upper region
    func_out = _place(expr.func, x, y, style, depth, builder)
    # Place operand (arg) in lower region
    arg_out = _place(expr.arg, x, y + func_size.height, style, depth, builder)
    # Pipe from func output → operator input
    builder.pipes.append(LPipe((func_out, operator_input)))
    # Pipe from arg output → operand input
    builder.pipes.append(LPipe((arg_out, operand_input)))
    return output
  ##
  return Point(x + g, y + g / 2)  # fallback
##

# ---------------------------------------------------------------------------
# Pipe routing — connect ears to usage points
# ---------------------------------------------------------------------------

def _route_pipes(builder: _LayoutBuilder, style: Style) -> None:
  """Connect ears to their variable usage points and handle free vars."""
  # Bound variables
  for binder_depth, ear_pos in builder.ear_positions.items():
    targets = builder.var_positions.get(binder_depth, [])
    if not targets:
      # Unused variable — short stub
      stub_end = Point(ear_pos.x + style.grid / 2, ear_pos.y)
      builder.pipes.append(LPipe((ear_pos, stub_end)))
    elif len(targets) == 1:
      builder.pipes.append(LPipe((ear_pos, targets[0])))
    else:
      # Fan-out: ear → fan point → each target
      fan_x = ear_pos.x + style.grid / 2
      fan_point = Point(fan_x, ear_pos.y)
      builder.pipes.append(LPipe((ear_pos, fan_point)))
      builder.fanouts.append(LFanout(fan_point, tuple(targets)))
      for t in targets:
        builder.pipes.append(LPipe((fan_point, t)))
      ##
    ##
  ##
  # Free variables
  for free_idx, targets in builder.free_var_positions.items():
    entry = Point(0, targets[0].y)
    builder.free_vars.append(LFreeVar(entry, free_idx))
    if len(targets) == 1:
      builder.pipes.append(LPipe((entry, targets[0])))
    else:
      fan_point = Point(style.grid / 2, entry.y)
      builder.pipes.append(LPipe((entry, fan_point)))
      builder.fanouts.append(LFanout(fan_point, tuple(targets)))
      for t in targets:
        builder.pipes.append(LPipe((fan_point, t)))
      ##
    ##
  ##
##

# ---------------------------------------------------------------------------
# Crossing detection
# ---------------------------------------------------------------------------

def _segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> Point | None:
  """Test if two line segments intersect. Returns intersection point or None."""
  dx_a = a2.x - a1.x
  dy_a = a2.y - a1.y
  dx_b = b2.x - b1.x
  dy_b = b2.y - b1.y
  denom = dx_a * dy_b - dy_a * dx_b
  if abs(denom) < 1e-10: return None
  t = ((b1.x - a1.x) * dy_b - (b1.y - a1.y) * dx_b) / denom
  u = ((b1.x - a1.x) * dy_a - (b1.y - a1.y) * dx_a) / denom
  if 0 < t < 1 and 0 < u < 1:
    return Point(a1.x + t * dx_a, a1.y + t * dy_a)
  ##
  return None
##

def _detect_crossings(builder: _LayoutBuilder) -> None:
  """Find pipe crossings and record them."""
  pipes = builder.pipes
  for i in range(len(pipes)):
    for j in range(i + 1, len(pipes)):
      pa, pb = pipes[i], pipes[j]
      for ai in range(len(pa.points) - 1):
        for bi in range(len(pb.points) - 1):
          pt = _segments_intersect(pa.points[ai], pa.points[ai + 1], pb.points[bi], pb.points[bi + 1])
          if pt is not None:
            builder.crossings.append(LCrossing(pa, pb, pt))
          ##
        ##
      ##
    ##
  ##
##

# ---------------------------------------------------------------------------
# Public API: layout
# ---------------------------------------------------------------------------

def layout(expr: Expr, style: Style | None = None) -> Layout:
  """Compute spatial layout for a lambda expression."""
  s = style or _DEFAULT_STYLE
  size = _measure(expr, s)
  margin = s.grid
  builder = _LayoutBuilder()
  _place(expr, margin, margin, s, 0, builder)
  _route_pipes(builder, s)
  _detect_crossings(builder)
  return Layout(
    width=size.width + 2 * margin,
    height=size.height + 2 * margin,
    boxes=tuple(builder.boxes),
    applicators=tuple(builder.applicators),
    pipes=tuple(builder.pipes),
    fanouts=tuple(builder.fanouts),
    crossings=tuple(builder.crossings),
    free_vars=tuple(builder.free_vars),
  )
##

# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

import xml.etree.ElementTree as ET

def _svg_root(lo: Layout, s: Style) -> ET.Element:
  svg = ET.Element("svg", {
    "xmlns": "http://www.w3.org/2000/svg",
    "viewBox": f"0 0 {lo.width} {lo.height}",
    "width": str(lo.width),
    "height": str(lo.height),
  })
  # Background
  ET.SubElement(svg, "rect", {
    "width": str(lo.width), "height": str(lo.height),
    "fill": s.color_bg,
  })
  return svg
##

def _render_boxes(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "boxes"})
  for box in lo.boxes:
    ET.SubElement(g, "rect", {
      "x": str(box.rect.x), "y": str(box.rect.y),
      "width": str(box.rect.width), "height": str(box.rect.height),
      "fill": "none", "stroke": s.color_box,
      "stroke-width": str(s.pipe_width), "stroke-dasharray": "6,3",
    })
    # Ear (left half-circle)
    r = s.ear_radius
    ex, ey = box.ear.x, box.ear.y
    ear_path = f"M {ex},{ey - r} A {r},{r} 0 0 0 {ex},{ey + r}"
    ET.SubElement(g, "path", {
      "d": ear_path, "fill": s.color_fill, "stroke": "none",
    })
    # Throat (right half-circle)
    r = s.throat_radius
    tx, ty = box.throat.x, box.throat.y
    throat_path = f"M {tx},{ty - r} A {r},{r} 0 0 1 {tx},{ty + r}"
    ET.SubElement(g, "path", {
      "d": throat_path, "fill": s.color_fill, "stroke": "none",
    })
  ##
##

def _render_applicators(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "applicators"})
  for app in lo.applicators:
    ET.SubElement(g, "circle", {
      "cx": str(app.center.x), "cy": str(app.center.y),
      "r": str(s.applicator_radius), "fill": s.color_fill,
    })
  ##
##

def _render_pipes(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "pipes"})
  for pipe in lo.pipes:
    if len(pipe.points) < 2: continue
    pts = " ".join(f"{p.x},{p.y}" for p in pipe.points)
    ET.SubElement(g, "polyline", {
      "points": pts, "fill": "none",
      "stroke": s.color_pipe, "stroke-width": str(s.pipe_width),
    })
  ##
##

def _render_fanouts(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "fanouts"})
  for fan in lo.fanouts:
    ET.SubElement(g, "circle", {
      "cx": str(fan.source.x), "cy": str(fan.source.y),
      "r": str(s.pipe_width * 1.5), "fill": s.color_fill,
    })
  ##
##

def _render_crossings(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "crossings"})
  r = s.pipe_width * 3
  for cx in lo.crossings:
    ET.SubElement(g, "circle", {
      "cx": str(cx.intersection.x), "cy": str(cx.intersection.y),
      "r": str(r), "fill": s.color_bg, "stroke": "none",
    })
  ##
##

def _render_free_vars(parent: ET.Element, lo: Layout, s: Style) -> None:
  g = ET.SubElement(parent, "g", {"class": "free-vars"})
  for fv in lo.free_vars:
    ET.SubElement(g, "text", {
      "x": str(fv.entry.x + 2), "y": str(fv.entry.y - 4),
      "font-size": str(s.font_size), "fill": s.color_fill,
    }).text = str(fv.index)
  ##
##

def render_layout(lo: Layout, style: Style | None = None) -> str:
  """Render a pre-computed Layout as SVG string."""
  s = style or _DEFAULT_STYLE
  svg = _svg_root(lo, s)
  _render_pipes(svg, lo, s)
  _render_crossings(svg, lo, s)
  _render_boxes(svg, lo, s)
  _render_applicators(svg, lo, s)
  _render_fanouts(svg, lo, s)
  _render_free_vars(svg, lo, s)
  return ET.tostring(svg, encoding="unicode")
##

def render(expr: Expr, style: Style | None = None) -> str:
  """Render a lambda expression as an SVG string."""
  s = style or _DEFAULT_STYLE
  lo = layout(expr, s)
  return render_layout(lo, s)
##
