import pytest
from mockingbird.ast import Appl, Func, Var
from mockingbird.parser import parse

def test_single_variable():
  result = parse("0")
  assert isinstance(result, Var)
  assert result.index == 0
##

def test_multi_digit_variable():
  result = parse("42")
  assert isinstance(result, Var)
  assert result.index == 42
##

def test_identity():
  result = parse("λ 0")
  assert isinstance(result, Func)
  assert isinstance(result.body, Var)
  assert result.body.index == 0
##

def test_backslash_variant():
  assert str(parse("\\ 0")) == "λ 0"
##

def test_simple_application():
  result = parse("0 1")
  assert isinstance(result, Appl)
  assert str(result) == "0 1"
##

def test_left_associative_application():
  result = parse("0 1 2")
  assert isinstance(result, Appl)
  assert isinstance(result.func, Appl)
  assert str(result) == "0 1 2"
##

def test_right_grouped_application():
  result = parse("0 (1 2)")
  assert isinstance(result, Appl)
  assert isinstance(result.arg, Appl)
  assert str(result) == "0 (1 2)"
##

def test_nested_abstraction():
  result = parse("λ λ 1")
  assert isinstance(result, Func)
  assert isinstance(result.body, Func)
  assert str(result) == "λ λ 1"
##

def test_func_in_func_position():
  result = parse("(λ 0) 1")
  assert isinstance(result, Appl)
  assert isinstance(result.func, Func)
  assert str(result) == "(λ 0) 1"
##

def test_func_in_arg_position_with_parens():
  result = parse("0 (λ 1)")
  assert isinstance(result, Appl)
  assert isinstance(result.arg, Func)
  assert str(result) == "0 (λ 1)"
##

def test_func_in_arg_position_without_parens():
  result = parse("0 λ 1")
  assert isinstance(result, Appl)
  assert isinstance(result.arg, Func)
  assert str(result) == "0 (λ 1)"
##

def test_y_combinator_round_trip():
  s = "λ (λ 1 (0 0)) (λ 1 (0 0))"
  assert str(parse(s)) == s
##

def test_empty_string():
  with pytest.raises(ValueError):
    parse("")
  ##
##

def test_whitespace_only():
  with pytest.raises(ValueError):
    parse("   ")
  ##
##

def test_unmatched_open_paren():
  with pytest.raises(ValueError):
    parse("(0")
  ##
##

def test_unmatched_close_paren():
  with pytest.raises(ValueError):
    parse("0)")
  ##
##

def test_empty_parens():
  with pytest.raises(ValueError, match="expected expression after '\\('"):
    parse("()")
  ##
##

def test_bare_lambda():
  with pytest.raises(ValueError, match="expected expression after lambda"):
    parse("λ")
  ##
##

def test_trailing_lambda_in_application():
  with pytest.raises(ValueError, match="expected expression after lambda"):
    parse("0 λ")
  ##
##

def test_unexpected_character():
  with pytest.raises(ValueError):
    parse("abc")
  ##
##

def test_round_trip_complex():
  exprs = [
    "0",
    "λ 0",
    "0 1",
    "0 1 2",
    "0 (1 2)",
    "λ λ 1",
    "(λ 0) 1",
    "0 (λ 1)",
    "λ (λ 1 (0 0)) (λ 1 (0 0))",
  ]
  for s in exprs:
    assert str(parse(s)) == s, f"round-trip failed for: {s}"
  ##
##
