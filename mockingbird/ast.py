class Var:
  def __init__(self, index: int) -> None:
    self.index = index
  ##

  def __str__(self) -> str:
    return str(self.index)
  ##
##


class Func:
  def __init__(self, body: Expr) -> None:
    self.body = body
  ##

  def __str__(self) -> str:
    return f"λ {self.body}"
  ##
##


class Appl:
  def __init__(self, func: Expr, arg: Expr) -> None:
    self.func = func
    self.arg = arg
  ##

  def __str__(self) -> str:
    left = f"({self.func})" if isinstance(self.func, Func) else self.func
    right = f"({self.arg})" if isinstance(self.arg, (Func, Appl)) else self.arg
    return f"{left} {right}"
  ##
##


type Expr = Var | Func | Appl
