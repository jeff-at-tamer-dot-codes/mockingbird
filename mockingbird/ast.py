from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Var:
  index: int

  def __str__(self) -> str:
    return str(self.index)
  ##
##

@dataclass(frozen=True, slots=True)
class Func:
  body: Expr

  def __str__(self) -> str:
    return f"λ {self.body}"
  ##
##

@dataclass(frozen=True, slots=True)
class Appl:
  func: Expr
  arg: Expr

  def __str__(self) -> str:
    left = f"({self.func})" if isinstance(self.func, Func) else self.func
    right = f"({self.arg})" if isinstance(self.arg, (Func, Appl)) else self.arg
    return f"{left} {right}"
  ##
##

type Expr = Var | Func | Appl
