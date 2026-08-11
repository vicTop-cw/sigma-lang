#!/usr/bin/env python3
"""
sigma-ai-bench.py — ΣLang AI Verifier Benchmark toolchain (整改项 4.2).

Benchmarks an AI's ability to: read a ΣLang spec JSON -> generate an
implementation -> match the reference behavior test-by-test (both output
values and error names).

Pipeline per round:
  1. Prompt   : spec JSON (+ previous-round failure list as feedback context)
  2. Generate : candidate implementation (Python snippet defining IMPL: {op: fn})
  3. Verify   : run every spec test against the candidate; compare value/error
                with the declared expectation. Reference results are derived
                from the JSON `definition`s (lambda bodies / table transitions)
                and cross-checked against the declared tests (spec consistency).
  4. Feedback : failure list (op + expected/actual) -> next round's prompt.

Run modes:
  --mock : built-in pseudo-model. Round 1 ships an implementation with 2 seeded
           bugs, round 2 fixes one of them (driven by the feedback list),
           round 3 is fully correct. No API credentials needed.
  real   : llm_generate(model, prompt) -> code via an OpenAI-compatible
           endpoint (stdlib urllib only). Requires SIGMA_LLM_API_KEY; without
           it a clear error is printed with a --mock hint.

Outputs:
  bench/results.json     — full run report (per-round pass rates, failure lists,
                           attempts, final status)
  bench/leaderboard.json — append-mode cumulative leaderboard across runs/models

stdlib-only. Windows-friendly UTF-8 output.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# Force UTF-8 on stdout/stderr so the report survives PowerShell pipes where
# the locale codec is GBK/cp936 (would otherwise raise UnicodeEncodeError).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BENCH_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "bench"))

PY_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
}
RESERVED_NAMES = {"SigmaError", "_idx", "IMPL", "True", "False", "None"}

# ============================================================
# Errors
# ============================================================

class SigmaError(Exception):
    """Runtime error raised by an implementation under test."""

    def __init__(self, name):
        super().__init__(name)
        self.name = name


class LLMNotConfigured(Exception):
    """Raised when the real-mode LLM layer lacks credentials."""


# ============================================================
# Spec-expression language: tokenizer / parser / evaluator
# (a small, self-contained evaluator for `preconditions` expressions
#  and `definition` bodies, per spec/json-schema.md v1.0)
# ============================================================

TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<num>-?\d+\.\d+|-?\d+)
      | (?P<str>'[^']*'|"[^"]*")
      | (?P<op>>=|<=|==|!=|//|[<>+\-*/%])
      | (?P<kw>and|or|not|true|false|unit)
      | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<punct>[(),\[\]])
    )""",
    re.VERBOSE,
)


class ExprSyntaxError(ValueError):
    pass


def tokenize_expr(s):
    toks = []
    pos = 0
    while pos < len(s):
        m = TOKEN_RE.match(s, pos)
        if not m:
            raise ExprSyntaxError(f"unexpected char {s[pos]!r} at {pos} in {s!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "num":
            txt = m.group("num")
            toks.append(("num", float(txt) if "." in txt else int(txt)))
        elif kind == "str":
            toks.append(("str", m.group("str")[1:-1]))
        elif kind == "op":
            toks.append(("op", m.group("op")))
        elif kind == "kw":
            toks.append(("kw", m.group("kw")))
        elif kind == "ident":
            toks.append(("ident", m.group("ident")))
        else:
            toks.append(("punct", m.group("punct")))
    toks.append(("eof", ""))
    return toks


class ExprParser:
    """Recursive-descent parser for the spec expression language.

    Grammar:
        expr   := or_expr
        or_expr := and_expr ('or' and_expr)*
        and_expr := not_expr ('and' not_expr)*
        not_expr := 'not' not_expr | cmp_expr
        cmp_expr := arith (('>='|'<='|'=='|'!='|'>'|'<') arith)?
        arith := term (('+'|'-') term)*
        term := factor (('*'|'//'|'/'|'%') factor)*
        factor := num | str | 'true'|'false'|'unit' | ident | list | '(' expr ')' | call
        list := '[' (expr (',' expr)*)? ']'
        call := ident '(' (expr (',' expr)*)? ')'
    AST nodes: ('num', v) ('str', s) ('bool', b) ('ident', n) ('list', [...])
               ('binop', op, l, r) ('cmp', op, l, r) ('boolop', op, l, r)
               ('not', e) ('call', name, [args])
    """

    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i]

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, kind, val=None):
        t = self.next()
        if t[0] != kind or (val is not None and t[1] != val):
            raise ExprSyntaxError(f"expected {kind}:{val}, got {t}")
        return t

    def parse(self):
        e = self.or_expr()
        if self.peek()[0] != "eof":
            raise ExprSyntaxError(f"trailing tokens after {e!r}")
        return e

    def or_expr(self):
        left = self.and_expr()
        while self.peek() == ("kw", "or"):
            self.next()
            left = ("boolop", "or", left, self.and_expr())
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.peek() == ("kw", "and"):
            self.next()
            left = ("boolop", "and", left, self.not_expr())
        return left

    def not_expr(self):
        if self.peek() == ("kw", "not"):
            self.next()
            return ("not", self.not_expr())
        return self.cmp_expr()

    def cmp_expr(self):
        left = self.arith()
        if self.peek()[0] == "op" and self.peek()[1] in (">=", "<=", "==", "!=", ">", "<"):
            op = self.next()[1]
            left = ("cmp", op, left, self.arith())
        return left

    def arith(self):
        left = self.term()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            left = ("binop", op, left, self.term())
        return left

    def term(self):
        left = self.factor()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "//", "/", "%"):
            op = self.next()[1]
            left = ("binop", op, left, self.factor())
        return left

    def factor(self):
        t = self.peek()
        if t[0] == "num":
            self.next()
            return ("num", t[1])
        if t[0] == "str":
            self.next()
            return ("str", t[1])
        if t[0] == "kw":
            self.next()
            if t[1] == "true":
                return ("bool", True)
            if t[1] == "false":
                return ("bool", False)
            if t[1] == "unit":
                return ("unit", None)
            raise ExprSyntaxError(f"unexpected keyword {t[1]}")
        if t[0] == "ident":
            self.next()
            if self.peek() == ("punct", "("):
                self.next()
                args = []
                if self.peek() != ("punct", ")"):
                    args.append(self.or_expr())
                    while self.peek() == ("punct", ","):
                        self.next()
                        args.append(self.or_expr())
                self.expect("punct", ")")
                return ("call", t[1], args)
            return ("ident", t[1])
        if t == ("punct", "["):
            self.next()
            items = []
            if self.peek() != ("punct", "]"):
                items.append(self.or_expr())
                while self.peek() == ("punct", ","):
                    self.next()
                    items.append(self.or_expr())
            self.expect("punct", "]")
            return ("list", items)
        if t == ("punct", "("):
            self.next()
            e = self.or_expr()
            self.expect("punct", ")")
            return e
        raise ExprSyntaxError(f"unexpected token {t}")


def parse_expr(s):
    return ExprParser(tokenize_expr(s)).parse()


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SigmaError("TypeError")
    return v


def eval_ast(node, env):
    """Evaluate a spec-expression AST. env maps identifiers to values."""
    tag = node[0]
    if tag == "num":
        return node[1]
    if tag == "str":
        return node[1]
    if tag == "bool":
        return node[1]
    if tag == "unit":
        return None
    if tag == "ident":
        if node[1] not in env:
            raise SigmaError("TypeError")
        return env[node[1]]
    if tag == "list":
        return [eval_ast(x, env) for x in node[1]]
    if tag == "binop":
        l, r = eval_ast(node[2], env), eval_ast(node[3], env)
        op = node[1]
        if op == "+":
            return _num(l) + _num(r)
        if op == "-":
            return _num(l) - _num(r)
        if op == "*":
            return _num(l) * _num(r)
        if op == "/":
            if _num(r) == 0:
                raise SigmaError("DivByZero")
            return _num(l) / _num(r)
        if op == "//":
            if _num(r) == 0:
                raise SigmaError("DivByZero")
            return _num(l) // _num(r)
        if op == "%":
            if _num(r) == 0:
                raise SigmaError("DivByZero")
            return _num(l) % _num(r)
        raise SigmaError("TypeError")
    if tag == "cmp":
        l, r = eval_ast(node[2], env), eval_ast(node[3], env)
        op = node[1]
        if op == "==":
            return val_equal(l, r)
        if op == "!=":
            return not val_equal(l, r)
        return {"<": l < r, ">": l > r, "<=": l <= r, ">=": l >= r}[op]
    if tag == "boolop":
        l = eval_ast(node[2], env)
        if node[1] == "and":
            return bool(l) and bool(eval_ast(node[3], env))
        return bool(l) or bool(eval_ast(node[3], env))
    if tag == "not":
        return not bool(eval_ast(node[1], env))
    if tag == "call":
        return eval_call(node[1], [eval_ast(a, env) for a in node[2]])
    raise SigmaError("TypeError")


def eval_call(name, args):
    if name == "index":
        if len(args) != 2 or not isinstance(args[0], (list, tuple)):
            raise SigmaError("TypeError")
        if not isinstance(args[1], int) or isinstance(args[1], bool):
            raise SigmaError("TypeError")
        if args[1] < 0 or args[1] >= len(args[0]):
            raise SigmaError("ShapeError")
        return args[0][args[1]]
    if name in ("min", "max"):
        if not args:
            raise SigmaError("TypeError")
        return (min if name == "min" else max)(args)
    if name in ("sum", "fold_add"):
        if len(args) != 1 or not isinstance(args[0], (list, tuple)):
            raise SigmaError("TypeError")
        xs = args[0]
        if name == "fold_add" and xs and all(isinstance(x, (list, tuple)) for x in xs):
            return sum(x[-1] for x in xs)
        return sum(_num(x) for x in xs)
    if name == "sum_contribs":
        if len(args) != 1 or not isinstance(args[0], (list, tuple)):
            raise SigmaError("TypeError")
        return sum(x[1] for x in args[0])
    if name == "min_source_id":
        if len(args) != 1 or not isinstance(args[0], (list, tuple)):
            raise SigmaError("TypeError")
        return min((x[2] for x in args[0]), default=10 ** 9)
    if name == "len":
        if len(args) != 1 or not isinstance(args[0], (list, tuple)):
            raise SigmaError("TypeError")
        return len(args[0])
    if name == "abs":
        if len(args) != 1:
            raise SigmaError("TypeError")
        return abs(_num(args[0]))
    raise SigmaError("TypeError")


def eval_expr_str(s, env):
    """Evaluate a precondition/guard expression string in env."""
    try:
        return eval_ast(parse_expr(s), env)
    except SigmaError:
        raise
    except Exception as e:  # parse or evaluation failures -> TypeError
        raise SigmaError("TypeError") from e


def val_equal(a, b):
    """Type-aware structural equality (bools are NOT numbers)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(val_equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def ast_to_py(node, name_map):
    """Compile a spec-expression AST to a self-contained Python expression.
    name_map: original identifier -> sanitized Python parameter name."""
    tag = node[0]
    if tag == "num":
        return repr(node[1])
    if tag == "str":
        return repr(node[1])
    if tag == "bool":
        return "True" if node[1] else "False"
    if tag == "unit":
        return "None"
    if tag == "ident":
        return name_map.get(node[1], node[1])
    if tag == "list":
        return "[" + ", ".join(ast_to_py(x, name_map) for x in node[1]) + "]"
    if tag == "binop":
        return f"({ast_to_py(node[2], name_map)} {node[1]} {ast_to_py(node[3], name_map)})"
    if tag == "cmp":
        return f"({ast_to_py(node[2], name_map)} {node[1]} {ast_to_py(node[3], name_map)})"
    if tag == "boolop":
        return f"({ast_to_py(node[2], name_map)} {node[1]} {ast_to_py(node[3], name_map)})"
    if tag == "not":
        return f"(not {ast_to_py(node[1], name_map)})"
    if tag == "call":
        name, args = node[1], node[2]
        py_args = [ast_to_py(a, name_map) for a in args]
        if name == "index" and len(py_args) == 2:
            return f"_idx({py_args[0]}, {py_args[1]})"
        return f"{name}({', '.join(py_args)})"
    raise ExprSyntaxError(f"cannot compile node {node!r}")


# ============================================================
# Spec loading & reference evaluation (from JSON `definition`s)
# ============================================================

BUILTIN_SPEC = {
    "spec": "§SK-bench",
    "version": "0.7.0",
    "fingerprint_prefix": "0xF000",
    "types": [
        {"name": "Task", "kind": "alias", "target": "List<nat>"},
        {"name": "Bounty", "kind": "alias", "target": "nat"},
        {"name": "Vote", "kind": "alias", "target": "List<nat>"},
    ],
    "operations": [
        {
            "name": "task_create",
            "fingerprint": "0xF001",
            "signature": {"params": ["nat", "nat"], "returns": "Task"},
            "definition": {
                "kind": "lambda", "params": ["a", "b"],
                "body": {"list": ["a", "b", 0, 0]},
            },
            "preconditions": [
                {"expr": "b >= 0", "error": "BountyErr",
                 "description": "bounty must be non-negative"}
            ],
            "laws": [
                {"forall": ["a", "b"], "predicate": "index(task_create(a,b), 2) == 0",
                 "description": "freshly created task is open"}
            ],
            "tests": [
                {"input": [7, 100], "output": [7, 100, 0, 0], "description": "basic create"},
                {"input": [1, 0], "output": [1, 0, 0, 0], "description": "zero bounty"},
                {"input": [1, -5], "output": None, "error": "BountyErr",
                 "description": "negative bounty rejected"},
            ],
        },
        {
            "name": "accept_task",
            "fingerprint": "0xF002",
            "signature": {"params": ["Task", "nat"], "returns": "Task"},
            "definition": {
                "kind": "lambda", "params": ["t", "h"],
                "body": {"list": [
                    {"fn": "index", "args": ["t", 0]},
                    {"fn": "index", "args": ["t", 1]},
                    1,
                    "h",
                ]},
            },
            "preconditions": [
                {"expr": "index(t, 2) == 0", "error": "StateError",
                 "description": "only open tasks can be accepted"}
            ],
            "laws": [
                {"forall": ["t", "h"], "predicate": "index(accept_task(t,h), 2) == 1",
                 "description": "accepted task is in progress"}
            ],
            "tests": [
                {"input": [[7, 100, 0, 0], 5], "output": [7, 100, 1, 5],
                 "description": "accept open task"},
                {"input": [[7, 100, 1, 3], 5], "output": None, "error": "StateError",
                 "description": "in-progress task cannot be accepted"},
                {"input": [[7, 100, 0, 0], 0], "output": [7, 100, 1, 0],
                 "description": "zero handler id"},
            ],
        },
        {
            "name": "task_submit",
            "fingerprint": "0xF003",
            "signature": {"params": ["Task"], "returns": "Task"},
            "definition": {
                "kind": "lambda", "params": ["t"],
                "body": {"list": [
                    {"fn": "index", "args": ["t", 0]},
                    {"fn": "index", "args": ["t", 1]},
                    2,
                    {"fn": "index", "args": ["t", 3]},
                ]},
            },
            "preconditions": [
                {"expr": "index(t, 2) == 1", "error": "StateError",
                 "description": "only in-progress tasks can be submitted"}
            ],
            "laws": [
                {"forall": ["t"], "predicate": "index(task_submit(t), 2) == 2",
                 "description": "submitted task is pending review"}
            ],
            "tests": [
                {"input": [[7, 100, 1, 5]], "output": [7, 100, 2, 5],
                 "description": "submit in-progress task"},
                {"input": [[7, 100, 0, 0]], "output": None, "error": "StateError",
                 "description": "open task cannot be submitted"},
            ],
        },
        {
            "name": "task_accept",
            "fingerprint": "0xF004",
            "signature": {"params": ["Task", "nat"], "returns": "Task"},
            "definition": {
                "kind": "lambda", "params": ["t", "c"],
                "body": {"list": [
                    {"fn": "index", "args": ["t", 0]},
                    {"fn": "index", "args": ["t", 1]},
                    3,
                    {"fn": "index", "args": ["t", 3]},
                ]},
            },
            "preconditions": [
                {"expr": "index(t, 2) == 2", "error": "StateError",
                 "description": "only pending-review tasks can be accepted"},
                {"expr": "c == index(t, 0)", "error": "AuthError",
                 "description": "only the author may accept the merge"},
            ],
            "laws": [
                {"forall": ["t", "c"], "predicate": "index(task_accept(t,c), 2) == 3",
                 "description": "accepted merge is final"}
            ],
            "tests": [
                {"input": [[7, 100, 2, 5], 7], "output": [7, 100, 3, 5],
                 "description": "author accepts pending review"},
                {"input": [[7, 100, 2, 5], 99], "output": None, "error": "AuthError",
                 "description": "non-author rejected"},
                {"input": [[7, 100, 0, 0], 7], "output": None, "error": "StateError",
                 "description": "open task cannot be accepted"},
            ],
        },
    ],
}


def load_spec(path):
    """Load a spec JSON from path. Returns (spec_dict, label)."""
    if path:
        if not os.path.isfile(path):
            print(f"[warn] spec file not found: {path} — falling back to builtin example spec")
            return BUILTIN_SPEC, f"builtin:{BUILTIN_SPEC['spec']}"
        with open(path, encoding="utf-8-sig") as f:
            spec = json.load(f)
        for op in spec.get("operations", []):
            if "tests" not in op:
                op["tests"] = []
        return spec, os.path.abspath(path)
    return BUILTIN_SPEC, f"builtin:{BUILTIN_SPEC['spec']}"


def index_spec(spec):
    """Index operations by name; validate minimal shape."""
    ops = {}
    for op in spec.get("operations", []):
        name = op.get("name")
        if not name:
            raise ValueError(f"operation missing name in {spec.get('spec')!r}")
        ops[name] = op
    return ops


def reference_run(spec, ops, opname, args, depth=0):
    """Evaluate an operation against its JSON `definition` (reference impl).

    Preconditions are checked first (raise the declared error name on
    violation); then kind=lambda body or kind=table transitions produce the
    result. Returns a plain value or raises SigmaError."""
    if depth > 8:
        raise SigmaError("TypeError")  # nested-call guard
    op = ops.get(opname)
    if op is None:
        raise SigmaError("TypeError")
    definition = op.get("definition") or {}
    params = definition.get("params", [])
    env = dict(zip(params, args))
    for pre in op.get("preconditions", []):
        if not bool(eval_expr_str(pre["expr"], env)):
            raise SigmaError(pre["error"])
    kind = definition.get("kind", "lambda")
    if kind == "table":
        return eval_table(definition, env, spec, ops, depth)
    return eval_body(definition.get("body"), env, spec, ops, depth)


def resolve_input(spec, ops, node, depth=0):
    """Resolve nested {"op": ...} expression nodes in a test input to plain
    values, using the reference evaluator (LeetCode-style test env: the test
    harness builds valid inputs, the candidate implements atomic ops)."""
    if depth > 8:
        raise SigmaError("TypeError")
    if isinstance(node, list):
        return [resolve_input(spec, ops, x, depth + 1) for x in node]
    if isinstance(node, dict) and "op" in node:
        fargs = [resolve_input(spec, ops, a, depth + 1) for a in node.get("args", [])]
        return reference_run(spec, ops, node["op"], fargs, depth + 1)
    return node


def eval_body(node, env, spec, ops, depth):
    """Evaluate a definition-body node (schema §definition 表达式语法)."""
    if isinstance(node, bool) or node is None:
        return node
    if isinstance(node, (int, float)):
        return node
    if isinstance(node, str):
        if node == "$_":
            return env.get("$_")
        if node in env:
            return env[node]
        return node  # bare string literal
    if isinstance(node, list):
        return [eval_body(x, env, spec, ops, depth) for x in node]
    if isinstance(node, dict):
        if "list" in node:
            return [eval_body(x, env, spec, ops, depth) for x in node["list"]]
        if "fn" in node:
            fname = node["fn"]
            fargs = [eval_body(a, env, spec, ops, depth) for a in node.get("args", [])]
            if fname == "index":
                if len(fargs) != 2 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                if not isinstance(fargs[1], int) or isinstance(fargs[1], bool):
                    raise SigmaError("TypeError")
                if fargs[1] < 0 or fargs[1] >= len(fargs[0]):
                    raise SigmaError("ShapeError")
                return fargs[0][fargs[1]]
            if fname in ("min", "max"):
                if not fargs:
                    raise SigmaError("TypeError")
                return (min if fname == "min" else max)(fargs)
            if fname in ("sum", "fold_add"):
                if len(fargs) != 1 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                xs = fargs[0]
                if xs and all(isinstance(x, list) for x in xs):
                    return sum(x[-1] for x in xs)  # fold over last column (deltas/shares)
                return sum(_num(x) for x in xs)
            if fname == "len":
                if len(fargs) != 1 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                return len(fargs[0])
            if fname == "abs":
                if len(fargs) != 1:
                    raise SigmaError("TypeError")
                return abs(_num(fargs[0]))
            if fname in ("add", "sum_multi"):
                if len(fargs) < 2:
                    raise SigmaError("TypeError")
                return sum(_num(x) for x in fargs)
            if fname == "sub":
                if len(fargs) < 2:
                    raise SigmaError("TypeError")
                acc = _num(fargs[0])
                for x in fargs[1:]:
                    acc -= _num(x)
                return acc
            if fname == "mul":
                if len(fargs) != 2:
                    raise SigmaError("TypeError")
                return _num(fargs[0]) * _num(fargs[1])
            if fname == "floordiv":
                if len(fargs) != 2 or _num(fargs[1]) == 0:
                    raise SigmaError("TypeError" if len(fargs) != 2 else "DivByZero")
                return _num(fargs[0]) // _num(fargs[1])
            if fname == "mod":
                if len(fargs) != 2 or _num(fargs[1]) == 0:
                    raise SigmaError("TypeError" if len(fargs) != 2 else "DivByZero")
                return _num(fargs[0]) % _num(fargs[1])
            cmp_fns = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
                       "lt": lambda a, b: a < b, "le": lambda a, b: a <= b,
                       "gt": lambda a, b: a > b, "ge": lambda a, b: a >= b}
            if fname in cmp_fns:
                if len(fargs) != 2:
                    raise SigmaError("TypeError")
                return cmp_fns[fname](fargs[0], fargs[1])
            if fname in ("weighted_accept", "weighted_support"):
                if len(fargs) != 1 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                return sum(row[2] for row in fargs[0] if row[1] == 1)
            if fname == "weighted_reject":
                if len(fargs) != 1 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                return sum(row[2] for row in fargs[0] if row[1] == 0)
            if fname == "fold_credit":
                if len(fargs) != 2 or not isinstance(fargs[1], list):
                    raise SigmaError("TypeError")
                credit = _num(fargs[0])
                for event in fargs[1]:
                    kind, count = event[0], event[1]
                    if kind == 0:
                        credit += 5 * count
                    elif kind == 1:
                        for _ in range(count):
                            credit = (credit * 7) // 10
                return max(0, credit)
            if fname == "split_floor":
                if len(fargs) != 2 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                contribs, reward = fargs[0], _num(fargs[1])
                total = sum(c for _, c in contribs)
                if total == 0:
                    raise SigmaError("DivByZero")
                return [[m, (reward * c) // total] for m, c in contribs]
            if fname == "enumerate_ledger":
                if len(fargs) != 1 or not isinstance(fargs[0], list):
                    raise SigmaError("TypeError")
                ledger = []
                for i, entry in enumerate(fargs[0], 1):
                    amount, source_id = entry[1], entry[2]
                    if source_id < 1:
                        raise SigmaError("NotTraceable")
                    if amount < 0:
                        raise SigmaError("TypeError")
                    ledger.append([i, source_id, amount])
                return ledger
            raise SigmaError("TypeError")
        if "if" in node:
            cond = node["if"]
            then_node = node.get("then")
            else_node = node.get("else")
            return eval_body(then_node, env, spec, ops, depth) if \
                eval_cond(cond, env) else eval_body(else_node, env, spec, ops, depth)
        if "op" in node:
            fargs = [eval_body(a, env, spec, ops, depth) for a in node.get("args", [])]
            return reference_run(spec, ops, node["op"], fargs, depth + 1)
        raise SigmaError("TypeError")
    raise SigmaError("TypeError")


def eval_cond(cond, env):
    """Evaluate an `if` condition node: {"field": i, "eq"/"neq"/"lt"/"gt"/"le"/"ge": v}
    (field indexes into the first list-typed argument), {"expr": "..."} string,
    or a generic body node."""
    if isinstance(cond, dict):
        if "field" in cond:
            target = None
            for v in env.values():
                if isinstance(v, (list, tuple)):
                    target = v
                    break
            if target is None:
                raise SigmaError("TypeError")
            f = cond["field"]
            if f < 0 or f >= len(target):
                raise SigmaError("ShapeError")
            ops_map = {"eq": "==", "neq": "!=", "lt": "<", "gt": ">", "le": "<=", "ge": ">="}
            for op, sym in ops_map.items():
                if op in cond:
                    return val_equal(target[f], cond[op]) if sym == "==" else \
                        (not val_equal(target[f], cond[op]) if sym == "!=" else
                         eval(f"{target[f]!r} {sym} {cond[op]!r}"))
            raise SigmaError("TypeError")
        if "expr" in cond:
            return bool(eval_expr_str(cond["expr"], env))
    return bool(eval_body(cond, env, {}, {}, 0))


def matches_when(state, when):
    ops_map = {"eq": "==", "neq": "!=", "lt": "<", "gt": ">", "le": "<=", "ge": ">="}
    for key, sym in ops_map.items():
        if key in when:
            f = when["field"]
            if f < 0 or f >= len(state):
                return False
            if sym == "==":
                if not val_equal(state[f], when[key]):
                    return False
            elif sym == "!=":
                if val_equal(state[f], when[key]):
                    return False
            else:
                try:
                    if not eval(f"{state[f]!r} {sym} {when[key]!r}"):
                        return False
                except Exception:
                    return False
    return True


def eval_table(definition, env, spec, ops, depth):
    """Best-effort state-machine evaluation (kind=table, schema v1.0).

    State starts as the list of parameters; the first matching transition is
    applied repeatedly until no transition matches (bounded)."""
    state = [env.get(p) for p in definition.get("params", [])]
    transitions = definition.get("table", [])
    for _ in range(1000):
        applied = False
        for tr in transitions:
            when = tr.get("when", {})
            if not matches_when(state, when):
                continue
            guard = tr.get("guard") or {}
            if "expr" in guard and not bool(eval_expr_str(guard["expr"], env)):
                continue
            set_spec = tr.get("set", {})
            f = set_spec.get("field", 0)
            val = set_spec.get("value", 0)
            if isinstance(val, dict):
                val = eval_body(val, env, spec, ops, depth)
            if f < 0 or f >= len(state):
                raise SigmaError("ShapeError")
            state[f] = val
            applied = True
            break
        if not applied:
            break
    return state


# ============================================================
# Candidate-code generation (mock model) — JSON definition -> Python source
# ============================================================

MODULE_HEADER = '''\
def _idx(coll, i):
    if not isinstance(coll, list):
        raise SigmaError("TypeError")
    if not isinstance(i, int) or isinstance(i, bool):
        raise SigmaError("TypeError")
    if i < 0 or i >= len(coll):
        raise SigmaError("TypeError")
    return coll[i]


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SigmaError("TypeError")
    return v


def _fold_add(xs):
    """sum of last column if list-of-lists, else plain sum."""
    if not isinstance(xs, list):
        raise SigmaError("TypeError")
    if xs and all(isinstance(x, list) for x in xs):
        return sum(x[-1] for x in xs)
    return sum(_num(x) for x in xs)


def _weighted(xs, v):
    """sum of weights where row[1] == v (weighted_accept/reject/support)."""
    if not isinstance(xs, list):
        raise SigmaError("TypeError")
    total = 0
    for row in xs:
        if not isinstance(row, list) or len(row) < 3:
            raise SigmaError("TypeError")
        if row[1] == v:
            total += row[2]
    return total


def _fold_credit(init, events):
    """credit fold: kind 0 +5*count, kind 1 x7//10 per count, floor 0."""
    _num(init)
    if not isinstance(events, list):
        raise SigmaError("TypeError")
    credit = init
    for event in events:
        if not isinstance(event, list) or len(event) < 2:
            raise SigmaError("TypeError")
        kind, count = event[0], event[1]
        if kind == 0:
            credit += 5 * count
        elif kind == 1:
            for _ in range(count):
                credit = (credit * 7) // 10
        else:
            raise SigmaError("TypeError")
    return max(0, credit)


def _split_floor(contribs, reward):
    """share = floor(reward * c / total); total == 0 -> DivByZero."""
    if not isinstance(contribs, list):
        raise SigmaError("TypeError")
    _num(reward)
    rows = []
    total = 0
    for row in contribs:
        if not isinstance(row, list) or len(row) < 2:
            raise SigmaError("TypeError")
        rows.append(row)
        total += row[1]
    if total == 0:
        raise SigmaError("DivByZero")
    return [[m, (reward * c) // total] for m, c in rows]


def _enumerate_ledger(entries):
    """number entries 1..n; source < 1 -> NotTraceable."""
    if not isinstance(entries, list):
        raise SigmaError("TypeError")
    ledger = []
    for i, entry in enumerate(entries, 1):
        if not isinstance(entry, list) or len(entry) < 3:
            raise SigmaError("TypeError")
        amount, source_id = entry[1], entry[2]
        if source_id < 1:
            raise SigmaError("NotTraceable")
        if amount < 0:
            raise SigmaError("TypeError")
        ledger.append([i, source_id, amount])
    return ledger


def sum_contribs(c):
    if not isinstance(c, list):
        raise SigmaError("TypeError")
    return sum(x[1] for x in c)


def min_source_id(e):
    if not isinstance(e, list):
        raise SigmaError("TypeError")
    return min((x[2] for x in e), default=10 ** 9)

'''


def sanitize_params(params):
    """Map spec param names to safe Python identifiers (p0, p1, ...)."""
    name_map = {}
    for i, p in enumerate(params):
        safe = f"p{i}"
        name_map[p] = safe
    return name_map


def node_to_py(node, name_map):
    """Compile a definition-body node to a Python expression string.
    Parameter references are resolved through name_map (sanitized names)."""
    if isinstance(node, bool):
        return "True" if node else "False"
    if node is None:
        return "None"
    if isinstance(node, (int, float)):
        return repr(node)
    if isinstance(node, str):
        if node == "$_":
            return "None"  # corpus sequences not supported in mock codegen
        if node in name_map:
            return name_map[node]
        return repr(node)
    if isinstance(node, list):
        return "[" + ", ".join(node_to_py(x, name_map) for x in node) + "]"
    if isinstance(node, dict):
        if "list" in node:
            return "[" + ", ".join(node_to_py(x, name_map) for x in node["list"]) + "]"
        if "fn" in node:
            fname = node["fn"]
            fargs = [node_to_py(a, name_map) for a in node.get("args", [])]
            if fname == "index" and len(fargs) == 2:
                return f"_idx({fargs[0]}, {fargs[1]})"
            if fname in ("min", "max") and len(fargs) == 2:
                return f"{fname}({fargs[0]}, {fargs[1]})"
            if fname in ("sum", "fold_add") and len(fargs) == 1:
                return f"_fold_add({fargs[0]})"
            if fname == "len" and len(fargs) == 1:
                return f"len({fargs[0]})"
            if fname == "abs" and len(fargs) == 1:
                return f"abs({fargs[0]})"
            if fname in ("add", "sum") and len(fargs) >= 2:
                return "(" + " + ".join(fargs) + ")"
            if fname == "sub" and len(fargs) >= 2:
                return "(" + " - ".join(fargs) + ")"
            if fname == "mul" and len(fargs) == 2:
                return f"({fargs[0]} * {fargs[1]})"
            if fname == "floordiv" and len(fargs) == 2:
                return f"({fargs[0]} // {fargs[1]})"
            if fname == "mod" and len(fargs) == 2:
                return f"({fargs[0]} % {fargs[1]})"
            cmp_ops = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
            if fname in cmp_ops and len(fargs) == 2:
                return f"({fargs[0]} {cmp_ops[fname]} {fargs[1]})"
            if fname in ("weighted_accept", "weighted_support") and len(fargs) == 1:
                return f"_weighted({fargs[0]}, 1)"
            if fname == "weighted_reject" and len(fargs) == 1:
                return f"_weighted({fargs[0]}, 0)"
            if fname == "fold_credit" and len(fargs) == 2:
                return f"_fold_credit({fargs[0]}, {fargs[1]})"
            if fname == "split_floor" and len(fargs) == 2:
                return f"_split_floor({fargs[0]}, {fargs[1]})"
            if fname == "enumerate_ledger" and len(fargs) == 1:
                return f"_enumerate_ledger({fargs[0]})"
            raise ValueError(f"cannot codegen fn {fname!r}")
        if "if" in node:
            cond = node["if"]
            if isinstance(cond, dict) and "expr" in cond:
                cond_py = ast_to_py(parse_expr(cond["expr"]), name_map)
            elif isinstance(cond, dict) and "field" in cond:
                field_ops = {"eq": "==", "neq": "!=", "lt": "<", "gt": ">", "le": "<=", "ge": ">="}
                target = next((v for v in name_map.values() if v.startswith("p")), "p0")
                for op, sym in field_ops.items():
                    if op in cond:
                        cond_py = f"({target}[{cond['field']}] {sym} {cond[op]!r})"
                        break
                else:
                    raise ValueError(f"cannot codegen if-cond {cond!r}")
            else:
                cond_py = f"bool({node_to_py(cond, name_map)})"
            then_py = node_to_py(node.get("then"), name_map)
            else_py = node_to_py(node.get("else"), name_map)
            return f"({then_py} if {cond_py} else {else_py})"
        if "op" in node:
            fargs = [node_to_py(a, name_map) for a in node.get("args", [])]
            return f"{node['op']}({', '.join(fargs)})"
        raise ValueError(f"cannot codegen node {node!r}")
    raise ValueError(f"cannot codegen node {node!r}")


def op_src_correct(spec, ops, opname):
    """Generate the correct implementation source for one operation."""
    op = ops[opname]
    definition = op.get("definition") or {}
    params = definition.get("params", [])
    name_map = sanitize_params(params)
    py_params = [name_map[p] for p in params]
    lines = [f"def {opname}({', '.join(py_params)}):"]
    for pre in op.get("preconditions", []):
        try:
            cond_py = ast_to_py(parse_expr(pre["expr"]), name_map)
        except ExprSyntaxError as e:
            raise ValueError(f"op {opname}: cannot compile precondition {pre['expr']!r}: {e}")
        lines.append(f"    if not ({cond_py}):")
        lines.append(f"        raise SigmaError({pre['error']!r})")
    body = definition.get("body")
    if definition.get("kind") == "table":
        raise ValueError(f"op {opname}: table-kind codegen not supported in mock mode")
    body_py = node_to_py(body, name_map)
    lines.append(f"    return {body_py}")
    return "\n".join(lines)


def op_src_buggy(spec, ops, opname, kind):
    """Generate a buggy implementation: correct body wrapped by a mutation.

    kind="invert"   : error -> returns 0; value -> raises StateError
                      (every test of the op fails).
    kind="offbyone" : error -> returns 0; value -> first element (or scalar)
                      incremented by 1 (every test of the op fails)."""
    inner = op_src_correct(spec, ops, opname)
    inner = inner.replace(f"def {opname}(", f"def _correct_{opname}(", 1)
    op = ops[opname]
    params = (op.get("definition") or {}).get("params", [])
    name_map = sanitize_params(params)
    py_params = [name_map[p] for p in params]
    call_args = ", ".join(py_params)
    if kind == "invert":
        wrapper = (
            f"\ndef {opname}({call_args}):\n"
            f"    try:\n"
            f"        _r = _correct_{opname}({call_args})\n"
            f"    except SigmaError:\n"
            f"        return 0\n"
            f"    raise SigmaError(\"StateError\")\n"
        )
    else:  # offbyone
        wrapper = (
            f"\ndef {opname}({call_args}):\n"
            f"    try:\n"
            f"        _r = _correct_{opname}({call_args})\n"
            f"    except SigmaError:\n"
            f"        return 0\n"
            f"    if isinstance(_r, list):\n"
            f"        _r = list(_r)\n"
            f"        if _r:\n"
            f"            _r[0] = _r[0] + 1\n"
            f"        return _r\n"
            f"    return _r + 1\n"
        )
    return inner + wrapper


def build_mock_module(spec, ops, bug_ops):
    """Assemble the full candidate module source for the mock model."""
    parts = [MODULE_HEADER]
    for opname in ops:
        bug_kind = bug_ops.get(opname)
        if bug_kind:
            parts.append(op_src_buggy(spec, ops, opname, bug_kind))
        else:
            parts.append(op_src_correct(spec, ops, opname))
    impl_lines = ["IMPL = {"]
    for opname in ops:
        impl_lines.append(f"    {opname!r}: {opname},")
    impl_lines.append("}")
    parts.append("\n".join(impl_lines))
    return "\n".join(parts) + "\n"


class MockModel:
    """Pseudo-model for --mock: reads the prompt (spec + feedback) and emits
    candidate code. Round 1 carries 2 seeded bugs; each later round fixes the
    ops listed in the previous failure feedback (round 2 fixes one, later
    rounds fix all remaining), demonstrating the feedback loop."""

    def __init__(self, spec, ops):
        self.spec = spec
        self.ops = ops
        self.bug_ops = {}  # opname -> bug kind, persists across rounds

    def _choose_targets(self):
        candidates = [name for name, op in self.ops.items() if op.get("tests")]
        targets = []
        if candidates:
            targets.append((candidates[0], "invert"))
        if len(candidates) > 1:
            targets.append((candidates[1], "invert"))
        elif candidates:
            targets.append((candidates[0], "offbyone"))
        return targets

    def generate(self, prompt, round_idx, failures_prev):
        if round_idx == 1:
            self.bug_ops = {}
            for opname, kind in self._choose_targets():
                self.bug_ops[opname] = kind
        elif failures_prev:
            failing = []
            seen = set()
            for f in failures_prev:
                if f["op"] not in seen:
                    seen.add(f["op"])
                    failing.append(f["op"])
            if round_idx == 2:
                # fix exactly one op (the first in the failure list)
                for opname in failing:
                    if opname in self.bug_ops:
                        del self.bug_ops[opname]
                        break
            else:
                for opname in failing:
                    self.bug_ops.pop(opname, None)
        return build_mock_module(self.spec, self.ops, self.bug_ops)


# ============================================================
# Real-mode LLM layer (interface placeholder — stdlib urllib only)
# ============================================================

def llm_generate(model, prompt):
    """llm_generate(model, prompt) -> code.

    Interface placeholder for the real-mode LLM layer. Without
    SIGMA_LLM_API_KEY this raises LLMNotConfigured with a --mock hint.
    With the key set, calls an OpenAI-compatible chat/completions endpoint
    (SIGMA_LLM_BASE_URL, default https://api.openai.com/v1) using stdlib
    urllib only — no third-party dependencies."""
    api_key = os.environ.get("SIGMA_LLM_API_KEY")
    if not api_key:
        raise LLMNotConfigured(
            "LLM layer not configured: set SIGMA_LLM_API_KEY "
            "(optional: SIGMA_LLM_BASE_URL, SIGMA_LLM_MODEL) "
            "or run with --mock for a credential-free pipeline demo"
        )
    base = os.environ.get("SIGMA_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    llm_model = os.environ.get("SIGMA_LLM_MODEL", model)
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system",
             "content": "You are a ΣLang implementation generator. "
                        "Emit ONLY a Python code block defining IMPL."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM endpoint returned HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"LLM endpoint unreachable: {e.reason}")
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"unexpected LLM response shape: {str(body)[:300]}")


def extract_code(text):
    """Extract the Python code block from a model response."""
    m = re.search(r"```(?:python|py)?\s*(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    return text.strip()


# ============================================================
# Verification layer
# ============================================================

RESTRICTED_BUILTINS = {
    "len": len, "range": range, "min": min, "max": max, "sum": sum,
    "abs": abs, "int": int, "float": float, "str": str, "list": list,
    "tuple": tuple, "dict": dict, "bool": bool, "isinstance": isinstance,
    "enumerate": enumerate, "zip": zip, "sorted": sorted, "reversed": reversed,
    "repr": repr, "Exception": Exception, "ValueError": ValueError,
    "TypeError": TypeError, "SigmaError": SigmaError, "True": True, "False": False,
    "None": None, "all": all, "any": any,
    "__build_class__": __build_class__, "__name__": "<sigma-candidate>",
}


def exec_candidate(code):
    """Dynamically exec candidate code; returns the IMPL dict."""
    ns = {"__builtins__": RESTRICTED_BUILTINS}
    try:
        exec(compile(code, "<sigma-candidate>", "exec"), ns)
    except Exception as e:
        raise RuntimeError(f"candidate code failed to compile/exec: {type(e).__name__}: {e}") from e
    impl = ns.get("IMPL")
    if not isinstance(impl, dict):
        raise RuntimeError("candidate code did not define IMPL: {op_name: fn}")
    return impl


def run_candidate(impl, opname, args):
    try:
        fn = impl.get(opname)
        if fn is None:
            return ("missing", f"no implementation for {opname!r}")
        v = fn(*args)
        return ("value", v)
    except SigmaError as e:
        return ("error", e.name)
    except Exception as e:
        return ("crash", f"{type(e).__name__}: {e}")


def fmt_value(v):
    try:
        return json.dumps(v, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(v)


def fmt_result(result):
    kind = result[0]
    if kind == "value":
        return fmt_value(result[1])
    if kind == "error":
        return f"error {result[1]}"
    if kind == "crash":
        return f"crash: {result[1]}"
    if kind == "missing":
        return f"missing: {result[1]}"
    return repr(result)


def run_reference(spec, ops, opname, args):
    try:
        return ("value", reference_run(spec, ops, opname, args))
    except SigmaError as e:
        return ("error", e.name)
    except Exception as e:
        return ("crash", f"{type(e).__name__}: {e}")


def check_test(expected, result):
    """Compare a candidate result against the test's declared expectation.
    Returns (passed, detail)."""
    exp_error = expected.get("error")
    exp_output = expected.get("output")
    has_output = "output" in expected
    if exp_error:
        if result[0] == "error":
            return (result[1] == exp_error, None)
        return (False, f"expected error {exp_error}, got {fmt_result(result)}")
    if has_output:
        if result[0] == "value":
            return (val_equal(result[1], exp_output), None)
        return (False, f"expected {fmt_value(exp_output)}, got {fmt_result(result)}")
    return (False, "test declares neither output nor error")


def verify_round(spec, ops, impl, spec_warnings):
    """Run every test of every op against the candidate. Returns
    (passed, total, failures, attempts)."""
    passed = 0
    total = 0
    failures = []
    attempts = 0
    for opname, op in ops.items():
        for t in op.get("tests", []):
            total += 1
            attempts += 1
            try:
                args = resolve_input(spec, ops, t.get("input", []))
            except SigmaError as e:
                failures.append({
                    "op": opname,
                    "test": t.get("description", ""),
                    "input": fmt_value(t.get("input", [])),
                    "expected": t.get("error") or fmt_value(t.get("output")),
                    "actual": f"input resolution failed: {e.name}",
                    "detail": "nested op input could not be resolved by the reference evaluator",
                })
                continue
            result = run_candidate(impl, opname, args)
            ok, detail = check_test(t, result)
            if ok:
                passed += 1
            else:
                failures.append({
                    "op": opname,
                    "test": t.get("description", ""),
                    "input": fmt_value(args),
                    "expected": t.get("error") or fmt_value(t.get("output")),
                    "actual": fmt_result(result),
                    "detail": detail or "",
                })
            # reference cross-check (spec consistency, not candidate score)
            ref = run_reference(spec, ops, opname, args)
            ref_ok, _ = check_test(t, ref)
            if not ref_ok:
                spec_warnings.append({
                    "op": opname,
                    "test": t.get("description", ""),
                    "input": fmt_value(args),
                    "expected": t.get("error") or fmt_value(t.get("output")),
                    "reference": fmt_result(ref),
                    "detail": "reference (definition-derived) disagrees with declared test",
                })
    return passed, total, failures, attempts


# ============================================================
# Prompts & feedback
# ============================================================

def build_prompt(spec, spec_label, round_idx, failures_prev):
    spec_text = json.dumps(spec, ensure_ascii=False, indent=2)
    lines = [
        "You are implementing a ΣLang specification. Read the spec JSON below",
        "and produce a Python implementation that passes every declared test.",
        "",
        "CONTRACT:",
        "  - Emit a single ```python code block.",
        "  - Define IMPL = { 'op_name': fn, ... } — one entry per operation.",
        "  - Each fn takes the operation's parameters positionally and returns",
        "    the result value (lists for structured types).",
        "  - On an error case, raise SigmaError('ErrorName') using exactly the",
        "    declared error name (the harness provides SigmaError).",
        "",
        f"SPEC: {spec_label}",
        spec_text,
    ]
    if round_idx > 1 and failures_prev:
        lines.append("")
        lines.append(f"PREVIOUS ROUND {round_idx - 1} FAILURES (fix these):")
        for f in failures_prev[:20]:
            lines.append(f"  - {f['op']}: {f['test']} — expected {f['expected']}, got {f['actual']}")
        lines.append("")
        lines.append("Fix ALL listed failures while keeping the passing tests green.")
    return "\n".join(lines)


# ============================================================
# Reporting
# ============================================================

def round_summary_line(r):
    return (f"[Round {r['round']}] passed {r['passed']}/{r['tests_total']} "
            f"({r['pass_rate'] * 100:.1f}%) — {len(r['failures'])} failures")


def write_results(results, bench_dir):
    os.makedirs(bench_dir, exist_ok=True)
    path = os.path.join(bench_dir, "results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return path


def write_leaderboard(entry, bench_dir):
    os.makedirs(bench_dir, exist_ok=True)
    path = os.path.join(bench_dir, "leaderboard.json")
    entries = []
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                entries = json.load(f)
            if not isinstance(entries, list):
                entries = []
        except (ValueError, OSError):
            entries = []
    entries.append(entry)
    entries.sort(key=lambda e: (e.get("final_pass_rate", 0.0), e.get("timestamp", "")),
                 reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return path


# ============================================================
# Main pipeline
# ============================================================

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sigma-ai-bench.py",
        description="ΣLang AI Verifier Benchmark — spec->implementation conformance pipeline",
    )
    ap.add_argument("--model", default=None, help="model name (default: mock-fixer in --mock mode)")
    ap.add_argument("--spec", default=None, help="path to a spec JSON (default: builtin example spec)")
    ap.add_argument("--rounds", type=int, default=3, help="number of generation/verification rounds (default 3)")
    ap.add_argument("--mock", action="store_true", help="use the built-in pseudo-model (no API credentials needed)")
    ap.add_argument("--bench-dir", default=DEFAULT_BENCH_DIR, help=f"output directory (default: {DEFAULT_BENCH_DIR})")
    args = ap.parse_args(argv)

    if args.rounds < 1:
        ap.error("--rounds must be >= 1")

    spec, spec_label = load_spec(args.spec)
    ops = index_spec(spec)
    n_tests = sum(len(op.get("tests", [])) for op in ops.values())

    mode = "mock" if args.mock else "real"
    model = args.model or ("mock-fixer" if args.mock else None)
    if model is None:
        ap.error("--model NAME is required in real mode (or pass --mock)")

    if not args.mock and not os.environ.get("SIGMA_LLM_API_KEY"):
        print("error: real mode requires the LLM layer to be configured.")
        print("  set SIGMA_LLM_API_KEY (optional: SIGMA_LLM_BASE_URL, SIGMA_LLM_MODEL),")
        print("  or run with --mock to demo the full pipeline without API credentials.")
        return 2

    print("=" * 72)
    print("ΣLang AI Verifier Benchmark (整改项 4.2)")
    print("=" * 72)
    print(f"spec : {spec_label} v{spec.get('version', '?')} "
          f"({spec.get('fingerprint_prefix', '?')}) — {len(ops)} ops, {n_tests} tests")
    print(f"model: {model} ({mode}) | rounds: {args.rounds}")
    print()

    rounds_out = []
    spec_warnings = []
    failures_prev = []
    final_status = "FAIL"

    for r in range(1, args.rounds + 1):
        prompt = build_prompt(spec, spec_label, r, failures_prev)
        if args.mock:
            mock = MockModel(spec, ops) if r == 1 else mock
            code = mock.generate(prompt, r, failures_prev)
        else:
            print(f"[round {r}] calling llm_generate({model!r}, prompt[{len(prompt)} chars]) ...")
            text = llm_generate(model, prompt)
            code = extract_code(text)
        try:
            impl = exec_candidate(code)
        except RuntimeError as e:
            print(f"[round {r}] candidate rejected: {e}")
            passed, total, failures = 0, n_tests, []
            for opname, op in ops.items():
                for t in op.get("tests", []):
                    failures.append({
                        "op": opname,
                        "test": t.get("description", ""),
                        "input": fmt_value(t.get("input", [])),
                        "expected": t.get("error") or fmt_value(t.get("output")),
                        "actual": "candidate rejected",
                        "detail": str(e),
                    })
            attempts = n_tests
        else:
            passed, total, failures, attempts = verify_round(spec, ops, impl, spec_warnings)
        rate = round(passed / total, 4) if total else 0.0
        rounds_out.append({
            "round": r,
            "tests_total": total,
            "passed": passed,
            "pass_rate": rate,
            "failures": failures,
            "attempts": attempts,
        })
        failures_prev = failures
        print(round_summary_line(rounds_out[-1]))
        for f in failures[:5]:
            print(f"    - {f['op']}: {f['test']} — expected {f['expected']}, got {f['actual']}")
        if len(failures) > 5:
            print(f"    ... and {len(failures) - 5} more (see bench/results.json)")

    rates = [r_["pass_rate"] for r_ in rounds_out]
    final_status = "PASS" if rates[-1] == 1.0 else "FAIL"
    total_attempts = sum(r_["attempts"] for r_ in rounds_out)
    best = max(rates) if rates else 0.0

    results = {
        "model": model,
        "mode": mode,
        "spec": spec_label,
        "spec_version": spec.get("version", "?"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "rounds_requested": args.rounds,
        "rounds": rounds_out,
        "total_attempts": total_attempts,
        "best_pass_rate": best,
        "final_pass_rate": rates[-1] if rates else 0.0,
        "final_status": final_status,
        "spec_consistency_warnings": spec_warnings,
    }

    print()
    print(f"final status: {final_status} | total attempts: {total_attempts} "
          f"| best pass rate: {best * 100:.1f}%")
    if spec_warnings:
        print(f"[warn] {len(spec_warnings)} spec-consistency warning(s) "
              "(reference derived from definitions disagrees with declared tests)")

    results_path = write_results(results, args.bench_dir)
    leaderboard_entry = {
        "model": model,
        "mode": mode,
        "spec": spec_label,
        "timestamp": results["timestamp"],
        "rounds": args.rounds,
        "total_attempts": total_attempts,
        "best_pass_rate": best,
        "final_pass_rate": rates[-1] if rates else 0.0,
        "final_status": final_status,
        "results_file": os.path.relpath(results_path, args.bench_dir),
    }
    lb_path = write_leaderboard(leaderboard_entry, args.bench_dir)
    print(f"wrote {results_path}")
    print(f"wrote {lb_path}")

    # leaderboard top-5 preview
    try:
        with open(lb_path, encoding="utf-8") as f:
            entries = json.load(f)
        print(f"leaderboard entries: {len(entries)}")
        for e in entries[:5]:
            print(f"    {e['final_pass_rate'] * 100:6.1f}%  {e['model']:<16} "
                  f"{e['spec']:<14} {e['final_status']:<4} {e['timestamp']}")
    except (OSError, ValueError):
        pass

    # mock self-check: canonical 3-round behavior — strictly increasing pass
    # rates up to the first perfect round, then stable at 100%.
    if args.mock:
        first_100 = next((i for i, v in enumerate(rates) if v == 1.0), None)
        monotonic = first_100 is not None and all(
            (rates[i] < rates[i + 1]) for i in range(first_100)
        ) and all(v == 1.0 for v in rates[first_100:])
        if monotonic and final_status == "PASS":
            print()
            print(f"AGENT_BENCH COMPLETE: mock pipeline {args.rounds} rounds ok")
            return 0
        print()
        print(f"AGENT_BENCH COMPLETE: mock pipeline {args.rounds} rounds — "
              "UNEXPECTED: pass rates did not converge monotonically to 100%")
        return 1
    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
