from mockingbird.ast import Appl, Func, Var, step

def test_var():
  assert str(Var(0)) == "0"
  assert str(Var(42)) == "42"
##

def test_identity():
  assert str(Func(Var(0))) == "λ 0"
##

def test_simple_application():
  assert str(Appl(Var(0), Var(1))) == "0 1"
##

def test_left_associative_application():
  # (0 1) 2 — no extra parens needed
  assert str(Appl(Appl(Var(0), Var(1)), Var(2))) == "0 1 2"
##

def test_right_associative_application():
  # 0 (1 2) — parens needed on the right
  assert str(Appl(Var(0), Appl(Var(1), Var(2)))) == "0 (1 2)"
##

def test_nested_abstraction():
  # λ λ 1 — two nested lambdas
  assert str(Func(Func(Var(1)))) == "λ λ 1"
##

def test_func_in_func_position():
  # (λ 0) 1
  assert str(Appl(Func(Var(0)), Var(1))) == "(λ 0) 1"
##

def test_func_in_arg_position():
  # 0 (λ 1)
  assert str(Appl(Var(0), Func(Var(1)))) == "0 (λ 1)"
##

def test_y_combinator():
  # λ (λ 1 (0 0)) (λ 1 (0 0))
  inner = Func(Appl(Var(1), Appl(Var(0), Var(0))))
  y = Func(Appl(inner, inner))
  assert str(y) == "λ (λ 1 (0 0)) (λ 1 (0 0))"
##

def test_var_equality():
  assert Var(0) == Var(0)
  assert Var(1) != Var(2)
##

def test_func_equality():
  assert Func(Var(0)) == Func(Var(0))
  assert Func(Var(0)) != Func(Var(1))
##

def test_appl_equality():
  assert Appl(Var(0), Var(1)) == Appl(Var(0), Var(1))
  assert Appl(Var(0), Var(1)) != Appl(Var(0), Var(2))
##

def test_nested_equality():
  a = Func(Appl(Var(1), Appl(Var(0), Var(0))))
  b = Func(Appl(Var(1), Appl(Var(0), Var(0))))
  assert a == b
  assert Appl(a, a) == Appl(b, b)
##

# --- shift tests ---

def test_shift_free_var():
  assert Var(0).shift(1) == Var(1)
  assert Var(2).shift(3) == Var(5)
##

def test_shift_below_cutoff():
  assert Var(0).shift(1, cutoff=1) == Var(0)
  assert Var(1).shift(2, cutoff=2) == Var(1)
##

def test_shift_at_cutoff():
  assert Var(1).shift(1, cutoff=1) == Var(2)
##

def test_shift_negative():
  assert Var(3).shift(-1) == Var(2)
##

def test_shift_func():
  # λ 0 — bound var stays, cutoff increments
  assert Func(Var(0)).shift(1) == Func(Var(0))
  # λ 1 — free var gets shifted
  assert Func(Var(1)).shift(1) == Func(Var(2))
##

def test_shift_appl():
  assert Appl(Var(0), Var(1)).shift(2) == Appl(Var(2), Var(3))
##

def test_shift_nested_func():
  # λ λ 2 → shift by 1 → λ λ 3
  assert Func(Func(Var(2))).shift(1) == Func(Func(Var(3)))
  # λ λ 1 → shift by 1 → λ λ 1 (bound, not shifted)
  assert Func(Func(Var(1))).shift(1) == Func(Func(Var(1)))
##

def test_shift_zero():
  expr = Appl(Func(Var(0)), Var(1))
  assert expr.shift(0) == expr
##

# --- substitute tests ---

def test_substitute_matching_var():
  assert Var(0).substitute(0, Var(5)) == Var(5)
##

def test_substitute_non_matching_var():
  assert Var(1).substitute(0, Var(5)) == Var(1)
##

def test_substitute_into_func():
  # λ 0 — 0 is bound, substituting index 0 becomes index 1 inside
  assert Func(Var(0)).substitute(0, Var(99)) == Func(Var(0))
  # λ 1 — 1 inside = 0 outside, should be replaced
  assert Func(Var(1)).substitute(0, Var(0)) == Func(Var(1))
##

def test_substitute_into_appl():
  expr = Appl(Var(0), Var(1))
  assert expr.substitute(0, Var(5)) == Appl(Var(5), Var(1))
##

# --- is_free tests ---

def test_is_free_var():
  assert Var(0).is_free(0) is True
  assert Var(0).is_free(1) is False
##

def test_is_free_func_bound():
  # λ 0 — variable 0 is bound
  assert Func(Var(0)).is_free(0) is False
##

def test_is_free_func_free():
  # λ 1 — variable 0 (outside) appears as 1 inside the binder
  assert Func(Var(1)).is_free(0) is True
##

def test_is_free_appl():
  assert Appl(Var(0), Var(1)).is_free(0) is True
  assert Appl(Var(0), Var(1)).is_free(2) is False
##

def test_is_free_nested():
  # λ λ 2 — free var 0 appears as 2 under two binders
  assert Func(Func(Var(2))).is_free(0) is True
  assert Func(Func(Var(1))).is_free(0) is False
##

# --- beta_step tests ---

def test_beta_identity():
  # (λ 0) x → x
  expr = Appl(Func(Var(0)), Var(0))
  assert expr.beta_step() == Var(0)
##

def test_beta_constant():
  # (λ λ 1) x → λ x  (constant function applied)
  expr = Appl(Func(Func(Var(1))), Var(0))
  assert expr.beta_step() == Func(Var(1))
##

def test_beta_discard():
  # (λ λ 0) x → λ 0  (argument discarded)
  expr = Appl(Func(Func(Var(0))), Var(42))
  assert expr.beta_step() == Func(Var(0))
##

def test_beta_irreducible_var():
  assert Var(0).beta_step() is None
##

def test_beta_irreducible_appl():
  # 0 1 — no redex
  assert Appl(Var(0), Var(1)).beta_step() is None
##

def test_beta_normal_order_outermost():
  # (λ 0) ((λ 0) x) — should reduce outermost first
  inner = Appl(Func(Var(0)), Var(0))
  expr = Appl(Func(Var(0)), inner)
  assert expr.beta_step() == inner
##

def test_beta_under_lambda():
  # λ (λ 0) 1 → λ 1
  expr = Func(Appl(Func(Var(0)), Var(1)))
  assert expr.beta_step() == Func(Var(1))
##

def test_beta_left_before_right():
  # ((λ 0) a) ((λ 0) b) — left redex first
  expr = Appl(Appl(Func(Var(0)), Var(0)), Appl(Func(Var(0)), Var(1)))
  assert expr.beta_step() == Appl(Var(0), Appl(Func(Var(0)), Var(1)))
##

def test_beta_right_when_left_normal():
  # x ((λ 0) y) — left is normal, reduce right
  expr = Appl(Var(0), Appl(Func(Var(0)), Var(1)))
  assert expr.beta_step() == Appl(Var(0), Var(1))
##

def test_beta_self_application():
  # (λ 0 0) (λ 0) → (λ 0) (λ 0)
  expr = Appl(Func(Appl(Var(0), Var(0))), Func(Var(0)))
  result = expr.beta_step()
  assert result == Appl(Func(Var(0)), Func(Var(0)))
##

def test_beta_free_vars_through_binder():
  # (λ λ 1 0) x → λ x 0
  expr = Appl(Func(Func(Appl(Var(1), Var(0)))), Var(0))
  result = expr.beta_step()
  assert result == Func(Appl(Var(1), Var(0)))
##

# --- eta_step tests ---

def test_eta_simple():
  # λ f 0 where f has no free 0 → just f (shifted down)
  # λ (1 0) → 0
  expr = Func(Appl(Var(1), Var(0)))
  assert expr.eta_step() == Var(0)
##

def test_eta_not_applicable_free():
  # λ (0 0) — 0 is free in func part, not η-reducible
  expr = Func(Appl(Var(0), Var(0)))
  assert expr.eta_step() is None
##

def test_eta_not_applicable_not_var0():
  # λ (1 1) — arg is not Var(0)
  expr = Func(Appl(Var(1), Var(1)))
  assert expr.eta_step() is None
##

def test_eta_not_applicable_not_appl():
  # λ 0 — body is not application
  expr = Func(Var(0))
  assert expr.eta_step() is None
##

def test_eta_nested():
  # λ (λ 2 0) — inner λ is η-reducible: λ 2 0 → 1
  inner = Func(Appl(Var(2), Var(0)))
  expr = Func(inner)
  # First eta step reduces the inner λ
  result = expr.eta_step()
  assert result == Func(Var(1))
  # λ 1 is NOT η-reducible (body is Var, not Appl)
  assert result and result.eta_step() is None
##

def test_eta_outermost_first():
  # λ (λ 2 0) 0 — outer is η-reducible (func = λ 2 0, arg = Var(0))
  # but is 0 free in (λ 2 0)? No (0 inside binder refers to bound var).
  # So η applies: result = (λ 2 0).shift(-1) = λ 1 0
  expr = Func(Appl(Func(Appl(Var(2), Var(0))), Var(0)))
  result = expr.eta_step()
  assert result == Func(Appl(Var(1), Var(0)))
##

def test_eta_in_appl():
  # (λ 1 0) x — eta in func position
  expr = Appl(Func(Appl(Var(1), Var(0))), Var(5))
  assert expr.eta_step() == Appl(Var(0), Var(5))
##

# --- step tests ---

def test_step_prefers_beta():
  # λ (λ 0) 0 — has both a β-redex and is η-reducible
  expr = Func(Appl(Func(Var(0)), Var(0)))
  # β-step: reduce the inner application
  assert step(expr) == Func(Var(0))
##

def test_step_falls_back_to_eta():
  # λ 1 0 — no β-redex, but η-reducible
  expr = Func(Appl(Var(1), Var(0)))
  assert step(expr) == Var(0)
##

def test_step_irreducible():
  assert step(Var(0)) is None
  assert step(Appl(Var(0), Var(1))) is None
##

# --- integration tests ---

def test_omega_reduces_to_itself():
  # Ω = (λ 0 0) (λ 0 0) → (λ 0 0) (λ 0 0)
  omega_inner = Func(Appl(Var(0), Var(0)))
  omega = Appl(omega_inner, omega_inner)
  assert omega.beta_step() == omega
##

def test_skk_reduces_to_identity():
  # S = λ λ λ 2 0 (1 0)
  # K = λ λ 1
  # SKK x should reduce to x
  s = Func(Func(Func(Appl(Appl(Var(2), Var(0)), Appl(Var(1), Var(0))))))
  k = Func(Func(Var(1)))
  # SKK = ((S K) K)
  skk = Appl(Appl(s, k), k)
  # Reduce until stable (should reach λ 0)
  expr = skk
  for _ in range(20):
    result = step(expr)
    if result is None: break
    expr = result
  ##
  assert expr == Func(Var(0))
##

def test_church_numeral_application():
  # 2 f x = f (f x) where 2 = λ λ 1 (1 0)
  two = Func(Func(Appl(Var(1), Appl(Var(1), Var(0)))))
  # Apply 2 to f (free var 0)
  expr = Appl(Appl(two, Var(0)), Var(1))
  # Reduce until stable
  for _ in range(20):
    result = step(expr)
    if result is None: break
    expr = result
  ##
  # Should be f (f x) = 0 (0 1)
  assert expr == Appl(Var(0), Appl(Var(0), Var(1)))
##
