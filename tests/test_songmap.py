import xml.etree.ElementTree as ET
from mockingbird.ast import Appl, Func, Var
from mockingbird.songmap import (
  Layout, LBox, LApplicator, LPipe, LFanout, LCrossing, LFreeVar,
  Point, Rect, Style, layout, render, render_layout,
)

# ---------------------------------------------------------------------------
# Helper combinators
# ---------------------------------------------------------------------------

I = Func(Var(0))                                          # λ 0
OMEGA_INNER = Func(Appl(Var(0), Var(0)))                  # λ 0 0
OMEGA = Appl(OMEGA_INNER, OMEGA_INNER)                    # (λ 0 0) (λ 0 0)
K = Func(Func(Var(1)))                                    # λ λ 1
KI = Appl(K, I)                                           # (λ λ 1) (λ 0)
T = Func(Func(Appl(Appl(Var(0), Var(1)), Var(0))))        # λ λ 0 1 0  (Thrush-like)
S = Func(Func(Func(Appl(Appl(Var(2), Var(0)), Appl(Var(1), Var(0))))))
Y_INNER = Func(Appl(Var(1), Appl(Var(0), Var(0))))
Y = Func(Appl(Y_INNER, Y_INNER))

# ---------------------------------------------------------------------------
# Layout element count tests
# ---------------------------------------------------------------------------

def test_identity_layout():
  lo = layout(I)
  assert len(lo.boxes) == 1
  assert len(lo.applicators) == 0
##

def test_omega_layout():
  lo = layout(OMEGA)
  assert len(lo.boxes) == 2
  assert len(lo.applicators) == 3  # inner self-apps + outer app
##

def test_k_layout():
  lo = layout(K)
  assert len(lo.boxes) == 2
  assert len(lo.applicators) == 0
##

def test_application_layout():
  expr = Appl(Var(0), Var(1))
  lo = layout(expr)
  assert len(lo.applicators) == 1
  assert len(lo.boxes) == 0
##

def test_y_combinator_layout():
  lo = layout(Y)
  assert len(lo.boxes) == 3  # outer + two inner λ
##

def test_s_combinator_layout():
  lo = layout(S)
  assert len(lo.boxes) == 3
  assert len(lo.applicators) == 3
##

# ---------------------------------------------------------------------------
# Box nesting — inner boxes spatially contained within outer boxes
# ---------------------------------------------------------------------------

def _rect_contains(outer: Rect, inner: Rect) -> bool:
  return (
    inner.x >= outer.x and inner.y >= outer.y
    and inner.x + inner.width <= outer.x + outer.width
    and inner.y + inner.height <= outer.y + outer.height
  )
##

def test_k_inner_box_nested():
  lo = layout(K)
  assert len(lo.boxes) == 2
  outer = min(lo.boxes, key=lambda b: b.depth)
  inner = max(lo.boxes, key=lambda b: b.depth)
  assert outer.depth < inner.depth
  assert _rect_contains(outer.rect, inner.rect)
##

def test_s_boxes_nested():
  lo = layout(S)
  boxes_by_depth = sorted(lo.boxes, key=lambda b: b.depth)
  for i in range(len(boxes_by_depth) - 1):
    assert _rect_contains(boxes_by_depth[i].rect, boxes_by_depth[i + 1].rect)
  ##
##

# ---------------------------------------------------------------------------
# Pipe bounds — all pipe points within layout dimensions
# ---------------------------------------------------------------------------

def test_pipe_bounds_identity():
  lo = layout(I)
  for pipe in lo.pipes:
    for pt in pipe.points:
      assert 0 <= pt.x <= lo.width
      assert 0 <= pt.y <= lo.height
    ##
  ##
##

def test_pipe_bounds_y():
  lo = layout(Y)
  for pipe in lo.pipes:
    for pt in pipe.points:
      assert 0 <= pt.x <= lo.width
      assert 0 <= pt.y <= lo.height
    ##
  ##
##

# ---------------------------------------------------------------------------
# Fan-out tests
# ---------------------------------------------------------------------------

def test_omega_inner_fanout():
  # λ 0 0 — var 0 used twice, should produce a fanout
  lo = layout(OMEGA_INNER)
  assert len(lo.fanouts) >= 1
##

def test_identity_no_fanout():
  lo = layout(I)
  assert len(lo.fanouts) == 0
##

def test_k_no_fanout():
  # K = λ λ 1 — var 0 of outer used once, var 0 of inner unused
  lo = layout(K)
  assert len(lo.fanouts) == 0
##

# ---------------------------------------------------------------------------
# Free variable tests
# ---------------------------------------------------------------------------

def test_free_var_single():
  expr = Var(0)
  lo = layout(expr)
  assert len(lo.free_vars) == 1
  assert lo.free_vars[0].index == 0
##

def test_free_var_in_application():
  # 0 1 — two free variables
  expr = Appl(Var(0), Var(1))
  lo = layout(expr)
  assert len(lo.free_vars) == 2
  indices = {fv.index for fv in lo.free_vars}
  assert indices == {0, 1}
##

def test_no_free_vars_in_identity():
  lo = layout(I)
  assert len(lo.free_vars) == 0
##

# ---------------------------------------------------------------------------
# SVG well-formedness tests
# ---------------------------------------------------------------------------

def test_svg_valid_xml_identity():
  svg = render(I)
  root = ET.fromstring(svg)
  assert root.tag == "{http://www.w3.org/2000/svg}svg" or root.tag == "svg"
##

def test_svg_valid_xml_omega():
  svg = render(OMEGA)
  root = ET.fromstring(svg)
  assert root is not None
##

def test_svg_valid_xml_k():
  svg = render(K)
  root = ET.fromstring(svg)
  assert root is not None
##

def test_svg_valid_xml_y():
  svg = render(Y)
  root = ET.fromstring(svg)
  assert root is not None
##

def test_svg_valid_xml_s():
  svg = render(S)
  root = ET.fromstring(svg)
  assert root is not None
##

def test_svg_box_count_matches():
  svg = render(K)
  root = ET.fromstring(svg)
  ns = {"svg": "http://www.w3.org/2000/svg"}
  # Find rects with stroke-dasharray (boxes, not background)
  rects = root.findall(".//{http://www.w3.org/2000/svg}rect[@stroke-dasharray]")
  if not rects:
    rects = root.findall(".//rect[@stroke-dasharray]")
  ##
  assert len(rects) == 2  # K has 2 boxes
##

def test_svg_applicator_count_matches():
  expr = Appl(Var(0), Var(1))
  svg = render(expr)
  root = ET.fromstring(svg)
  # Find circles in applicators group
  circles = root.findall(".//{http://www.w3.org/2000/svg}circle")
  if not circles:
    circles = root.findall(".//circle")
  ##
  # At least 1 applicator circle
  assert len(circles) >= 1
##

# ---------------------------------------------------------------------------
# Round-trip: render several combinators
# ---------------------------------------------------------------------------

def test_render_all_combinators():
  for expr in [I, OMEGA_INNER, OMEGA, K, KI, S, Y, Var(0), Appl(Var(0), Var(1))]:
    svg = render(expr)
    root = ET.fromstring(svg)
    assert root is not None
  ##
##

# ---------------------------------------------------------------------------
# render_layout separate from render
# ---------------------------------------------------------------------------

def test_render_layout_roundtrip():
  lo = layout(I)
  svg = render_layout(lo)
  root = ET.fromstring(svg)
  assert root is not None
##

# ---------------------------------------------------------------------------
# Layout dimensions positive
# ---------------------------------------------------------------------------

def test_layout_dimensions_positive():
  for expr in [I, K, S, Y, OMEGA, Var(0)]:
    lo = layout(expr)
    assert lo.width > 0
    assert lo.height > 0
  ##
##

# ---------------------------------------------------------------------------
# Custom style
# ---------------------------------------------------------------------------

def test_custom_style():
  s = Style(grid=50.0, pipe_width=3.0)
  svg = render(I, style=s)
  root = ET.fromstring(svg)
  assert root is not None
##
