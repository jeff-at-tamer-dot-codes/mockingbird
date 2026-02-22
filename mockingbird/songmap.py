from dataclasses import dataclass

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
