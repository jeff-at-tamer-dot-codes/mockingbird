from mockingbird.ast import Appl, Expr, Func, Var

class _Parser:

  def __init__(self, text: str) -> None:
    self.text = text
    self.pos = 0
  ##

  def _skip_spaces(self) -> None:
    while self.pos < len(self.text) and self.text[self.pos] == ' ':
      self.pos += 1
    ##
  ##

  def _peek(self) -> str | None:
    self._skip_spaces()
    if self.pos >= len(self.text): return None
    return self.text[self.pos]
  ##

  def _parse_atom(self) -> Expr | None:
    ch = self._peek()
    if ch is None: return None
    if ch.isdigit():
      start = self.pos
      while self.pos < len(self.text) and self.text[self.pos].isdigit():
        self.pos += 1
      ##
      return Var(int(self.text[start:self.pos]))
    ##
    if ch == '(':
      self.pos += 1
      expr = self._parse_expr()
      if expr is None:
        raise ValueError("expected expression after '('")
      ##
      self._skip_spaces()
      if self.pos >= len(self.text) or self.text[self.pos] != ')':
        raise ValueError("expected ')'")
      ##
      self.pos += 1
      return expr
    ##
    return None
  ##

  def _parse_expr(self) -> Expr | None:
    ch = self._peek()
    if ch in ('λ', '\\'):
      self.pos += 1
      body = self._parse_expr()
      if body is None:
        raise ValueError("expected expression after lambda")
      ##
      return Func(body)
    ##
    first = self._parse_atom()
    if first is None: return None
    result = first
    while True:
      ch = self._peek()
      if ch in ('λ', '\\'):
        self.pos += 1
        body = self._parse_expr()
        if body is None:
          raise ValueError("expected expression after lambda")
        ##
        result = Appl(result, Func(body))
        break
      ##
      atom = self._parse_atom()
      if atom is None: break
      result = Appl(result, atom)
    ##
    return result
  ##

  def parse(self) -> Expr:
    if not self.text.strip():
      raise ValueError("empty input")
    ##
    result = self._parse_expr()
    if result is None:
      raise ValueError("expected expression")
    ##
    self._skip_spaces()
    if self.pos < len(self.text):
      raise ValueError(f"unexpected character '{self.text[self.pos]}' at position {self.pos}")
    ##
    return result
  ##
##

def parse(text: str) -> Expr:
  return _Parser(text).parse()
##
