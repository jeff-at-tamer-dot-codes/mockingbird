from mockingbird.ast import Appl, Func, Var

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
