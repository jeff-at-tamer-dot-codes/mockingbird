# Mockingbird

A Python 3.14 project for manipulating untyped lambda calculus expressions.

## Code Style

- Wrap long lines at 120 characters.
- Use **two spaces** for indentation (not four).
- Use **one blank line** between module-level definitions, never two.
- Close every indented block with a line containing only `##`.

```python
if foo:
  bar()
##
```

- If an indented block consists solely of a single line, e.g. `break`, `continue`, `pass`, `return`, etc., then it should be moved to the end of the previous line. In these cases, the trailing `##` is omitted. This rule does not apply for `class` & `def` statements, which should always be multi-line.

```python
if foo: return None
```

- Always use **type hints**.
- Keep things simple. Avoid over-engineering.

## Architecture

- `mockingbird/` — main package
- `tests/` — test suite
- Lambda calculus AST uses **de Bruijn indices** (zero-based) instead of named variables.
  - `Var(index)` — variable reference by de Bruijn index
  - `Func(body)` — lambda abstraction (no parameter name needed)
  - `Appl(func, arg)` — application of one expression to another
- `__str__` format: `λ` for abstraction, bare integers for variables.
  - Example: Y combinator = `λ (λ 1 (0 0)) (λ 1 (0 0))`

## Environment

- Always use the `.venv` virtual environment (activate before running anything).
- Run tests: `source .venv/bin/activate && python -m pytest tests/ -v`

## Workflow

- Create plan `.md` files before diving into large tasks.
- Ask clarifying questions when requirements are ambiguous.

## Owner

Jeff
