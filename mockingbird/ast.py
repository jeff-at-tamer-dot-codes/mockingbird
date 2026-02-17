from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Var:
  index: int

  def __str__(self) -> str:
    return str(self.index)
  ##

  def shift(self, d: int, cutoff: int = 0) -> Expr:
    if self.index >= cutoff: return Var(self.index + d)
    return self
  ##

  def substitute(self, index: int, replacement: Expr) -> Expr:
    if self.index == index: return replacement
    return self
  ##

  def is_free(self, index: int) -> bool:
    return self.index == index
  ##

  def beta_step(self) -> Expr | None:
    return None
  ##

  def eta_step(self) -> Expr | None:
    return None
  ##
##

@dataclass(frozen=True, slots=True)
class Func:
  body: Expr

  def __str__(self) -> str:
    return f"λ {self.body}"
  ##

  def shift(self, d: int, cutoff: int = 0) -> Expr:
    return Func(self.body.shift(d, cutoff + 1))
  ##

  def substitute(self, index: int, replacement: Expr) -> Expr:
    return Func(self.body.substitute(index + 1, replacement.shift(1)))
  ##

  def is_free(self, index: int) -> bool:
    return self.body.is_free(index + 1)
  ##

  def beta_step(self) -> Expr | None:
    result = self.body.beta_step()
    if result is not None: return Func(result)
    return None
  ##

  def eta_step(self) -> Expr | None:
    if isinstance(self.body, Appl) and self.body.arg == Var(0) and not self.body.func.is_free(0):
      return self.body.func.shift(-1)
    ##
    result = self.body.eta_step()
    if result is not None: return Func(result)
    return None
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

  def shift(self, d: int, cutoff: int = 0) -> Expr:
    return Appl(self.func.shift(d, cutoff), self.arg.shift(d, cutoff))
  ##

  def substitute(self, index: int, replacement: Expr) -> Expr:
    return Appl(self.func.substitute(index, replacement), self.arg.substitute(index, replacement))
  ##

  def is_free(self, index: int) -> bool:
    return self.func.is_free(index) or self.arg.is_free(index)
  ##

  def beta_step(self) -> Expr | None:
    if isinstance(self.func, Func):
      return _beta_reduce(self.func.body, self.arg)
    ##
    result = self.func.beta_step()
    if result is not None: return Appl(result, self.arg)
    result = self.arg.beta_step()
    if result is not None: return Appl(self.func, result)
    return None
  ##

  def eta_step(self) -> Expr | None:
    result = self.func.eta_step()
    if result is not None: return Appl(result, self.arg)
    result = self.arg.eta_step()
    if result is not None: return Appl(self.func, result)
    return None
  ##
##

type Expr = Var | Func | Appl

def _beta_reduce(body: Expr, arg: Expr) -> Expr:
  return body.substitute(0, arg.shift(1)).shift(-1)
##

def step(expr: Expr) -> Expr | None:
  return expr.beta_step() or expr.eta_step()
##
