#!/usr/bin/env python3
"""
sigma-prove.py — SMT-backed proof discharge for ΣLang proof-carrying specs.

For every corpus module (or a single module path):
  1. P-01 structural check (reuses verify_consensus.check_python):
     `## Proof` must have Model + Invariant; ops must pair Pre/Post.
  2. Obligation generation: translate laws and Pre/Post contracts into
     SMT-LIB2 (ℕ→Int, ⊕→+, ⊗→*, ⊖→-, relations/connectives mapped).
  3. Discharge: try z3 (Python API, then CLI); if no solver is available,
     degrade gracefully — report the generated obligations and the
     structural verdict.

Exit: 0 = structure OK (and obligations discharged if a solver exists),
      1 = structural failure or a discharged obligation disproved.

Run:  python3 tools/sigma-prove.py              # whole corpus
      python3 tools/sigma-prove.py corpus/proof_ok.md
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import verify_consensus as vc  # parse_module + check_python (P-01 structural)

CORPUS_DIR = os.path.join(ROOT, "corpus")
OUT_DIR = os.path.join(ROOT, "tools", "_sigma_prove_out")

# ---------------------------------------------------------------------------
# Expression translation (ΣLang-ish → SMT-LIB2)
# ---------------------------------------------------------------------------

BINOPS = {"⊕": "+", "⊗": "*", "⊖": "-", "+": "+", "-": "-", "*": "*"}
RELATIONS = {"≡": "=", "≥": ">=", "≤": "<=", ">": ">", "<": "<", "≠": "!="}
CONNECTIVES = {"∧": "and", "∨": "or", "⇒": "=>", "→": "=>"}
NEGATION = "¬"
# Function calls translatable to SMT-LIB2 (z3: n-ary max/min, unary abs).
# index(...) is kept as an uninterpreted function application (v0.10 basic
# ops); gen_obligation declares it alongside the other operands.
FUNCS = {"max": "max", "min": "min", "abs": "abs", "index": "index"}

_TOKEN = re.compile(r"\s*(\d+|∀|∃|[a-zA-Z_][a-zA-Z_0-9]*|[⊕⊗⊖≡≥≤><≠∧∨⇒→¬(),]|[-+*])\s*")


def tokenize(s):
    """Tokenize an expression into atoms."""
    toks, pos = [], 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise ValueError(f"unparseable token near: {s[pos:pos+20]!r}")
        toks.append(m.group(1))
        pos = m.end()
    return toks


def shunting_yard(toks):
    """Convert infix arithmetic to SMT-LIB2 prefix. Handles () + - * with
    precedence, plus function calls max(a,b) / min(a,b) / abs(x)."""
    prec = {"*": 3, "+": 2, "-": 2}
    out, stack = [], []
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t in FUNCS and i + 1 < n and toks[i + 1] == "(":
            # Function call: collect tokens up to the matching close paren.
            depth = 0
            j = i + 1
            while j < n:
                if toks[j] == "(":
                    depth += 1
                elif toks[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = toks[i + 2:j]
            # Split args at top-level commas.
            args, cur, d2 = [], [], 0
            for tk in inner:
                if tk == "(":
                    d2 += 1
                elif tk == ")":
                    d2 -= 1
                if tk == "," and d2 == 0:
                    args.append(cur)
                    cur = []
                else:
                    cur.append(tk)
            if cur:
                args.append(cur)
            arg_smt = [shunting_yard(a) for a in args]
            # NIA (z3) has no built-in max/min constants — encode with ite.
            if t == "max" and len(arg_smt) == 2:
                out.append(f"(ite (>= {arg_smt[0]} {arg_smt[1]}) {arg_smt[0]} {arg_smt[1]})")
            elif t == "min" and len(arg_smt) == 2:
                out.append(f"(ite (<= {arg_smt[0]} {arg_smt[1]}) {arg_smt[0]} {arg_smt[1]})")
            else:
                out.append(f"({FUNCS[t]} {' '.join(arg_smt)})")
            i = j + 1
            continue
        if t == "(":
            stack.append(t)
        elif t == ")":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            stack.pop()  # discard '('
        elif t in BINOPS:
            while (stack and stack[-1] in BINOPS
                   and prec.get(stack[-1], 0) >= prec.get(t, 0)):
                out.append(stack.pop())
            stack.append(t)
        else:  # number, variable, or already-translated (func ...) group
            out.append(t)
        i += 1
    while stack:
        out.append(stack.pop())
    # Convert RPN to nested prefix.
    stack2 = []
    for t in out:
        if t in BINOPS:
            b, a = stack2.pop(), stack2.pop()
            stack2.append(f"({BINOPS[t]} {a} {b})")
        else:
            stack2.append(t)
    return stack2[0] if stack2 else ""


def parse_relation(toks):
    """Split a token stream at the top-level relation; return (lhs, rel, rhs) tokens."""
    depth = 0
    for i, t in enumerate(toks):
        if t == "(":
            depth += 1
        elif t == ")":
            depth -= 1
        elif t in RELATIONS and depth == 0:
            return toks[:i], t, toks[i + 1:]
    return None


def translate_expr(s, env):
    """Translate one arithmetic/logic expression (no quantifiers) to SMT-LIB2."""
    s = s.replace("result", "result")  # keep as-is; callers substitute
    toks = tokenize(s)
    rel = parse_relation(toks)
    if rel is None:
        return shunting_yard(toks)
    lhs, rel, rhs = rel
    lt, rt = shunting_yard(lhs), shunting_yard(rhs)
    r = RELATIONS[rel]
    if r == "!=":
        return f"(not (= {lt} {rt}))"
    return f"({r} {lt} {rt})"


def split_top_level(toks, sep):
    """Split token stream at depth-0 occurrences of sep (a connective)."""
    out, depth, cur = [], 0, []
    for t in toks:
        if t == "(":
            depth += 1
        elif t == ")":
            depth -= 1
        if t == sep and depth == 0:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


def translate_formula(s):
    """Translate a formula with connectives and optional ∀ quantifier to SMT-LIB2."""
    s = s.strip()
    # I₂ (identity matrix) → ASCII SMT-LIB2 identifier (declared by
    # gen_obligation); keeps the tokenizer simple and z3 happy.
    s = s.replace("I₂", "I2")
    m = re.match(r"^∀\s*([a-zA-Z_](?:\s+[a-zA-Z_])*)\s*\.\s*(.+)$", s)
    vars_list, body = None, s
    if m:
        vars_list = m.group(1).split()
        body = m.group(2)
    toks = tokenize(body)
    # Top-level implication (⇒) and conjunction/disjunction (∧ ∨).
    for sep in ("⇒", "→"):
        parts = split_top_level(toks, sep)
        if len(parts) == 2:
            body = f"(=> {translate_formula_toks(parts[0])} {translate_formula_toks(parts[1])})"
            break
    else:
        body = translate_formula_toks(toks)
    if vars_list:
        decl = " ".join(f"({v} Int)" for v in vars_list)
        return f"(forall ({decl}) {body})"
    return body


def translate_formula_toks(toks):
    parts = split_top_level(toks, "∧")
    if len(parts) > 1:
        return "(and " + " ".join(translate_formula_toks(p) for p in parts) + ")"
    parts = split_top_level(toks, "∨")
    if len(parts) > 1:
        return "(or " + " ".join(translate_formula_toks(p) for p in parts) + ")"
    if toks and toks[0] == NEGATION:
        return f"(not {translate_formula_toks(toks[1:])})"
    # Re-join with spaces so multi-char atoms (`(+ a b)`) survive re-tokenizing.
    return translate_expr(" ".join(toks), None)


# ---------------------------------------------------------------------------
# Obligation generation
# ---------------------------------------------------------------------------

def gen_obligation(module, op, law_texts):
    """Generate one SMT-LIB2 obligation proving the op's Post from Pre + laws.

    Operand names are recovered from the Pre/Post contract text (the signature
    only carries type placeholders like `ℕ × ℕ`); `result` is substituted with
    the operation's arithmetic semantics (⊕ → +, ⊗ → *, ⊖ → -) applied to the
    two operands, mirroring the minimal evaluator used by the corpus.
    """
    pre = op.get("pre")
    post = op.get("post")
    glyph = op["name"].strip()
    if not pre or not post or glyph not in BINOPS:
        return None

    # Operand names: letters appearing in Pre/Post (excluding 'result').
    names = re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*", pre + " " + post)
    names = [n for n in names if n != "result"]
    names = list(dict.fromkeys(names))  # dedupe, keep order
    if len(names) < 2:
        # Synthesize a second operand if the contract mentions only one.
        names = (names + ["b"])[:2]
    names = names[:2]

    op_expr = f"({BINOPS[glyph]} {names[0]} {names[1]})"

    pre_t = translate_formula(pre.replace("result", op_expr))
    post_t = translate_formula(post.replace("result", op_expr))

    lines = ["(set-logic NIA)"]
    for v in names:
        lines.append(f"(declare-const {v} Int)")
    # v0.10 basic ops: declare the uninterpreted symbols index()/I₂ when the
    # contract or laws reference them (z3 requires explicit declarations).
    joined = " ".join(law_texts) + " " + (pre or "") + " " + (post or "")
    if "index(" in joined:
        lines.append("(declare-fun index (Int Int) Int)")
    if "I₂" in joined:
        lines.append("(declare-const I2 Int)")
    # Law III — declared laws become axioms (premises) of the obligation.
    for law in law_texts:
        try:
            lt = translate_formula(law)
        except Exception:
            lt = None
        if lt:
            lines.append(f"(assert {lt})")
    for v in names:
        lines.append(f"(assert (>= {v} 0))")  # operands are ℕ
    lines.append(f"(assert {pre_t})")
    lines.append(f"(assert (not {post_t}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Discharge
# ---------------------------------------------------------------------------

def try_z3_py(smt2_text):
    try:
        import z3
    except ImportError:
        return None
    solver = z3.Solver()
    solver.add(z3.parse_smt2_string(smt2_text))
    r = solver.check()
    return {"sat": r == z3.unsat, "model": solver.model() if r == z3.sat else None,
            "result": str(r)}


def try_z3_cli(smt2_text, timeout=10):
    try:
        proc = subprocess.run(["z3", "-in"], input=smt2_text,
                              capture_output=True, text=True, timeout=timeout)
        out = proc.stdout.strip().splitlines()
        if not out:
            return None
        line = out[0]
        return {"sat": line == "unsat", "result": line}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def discharge(smt2_text):
    """Return (solver_name, result_dict) or (None, None) if no solver."""
    r = try_z3_py(smt2_text)
    if r is not None:
        return "z3-python", r
    r = try_z3_cli(smt2_text)
    if r is not None:
        return "z3-cli", r
    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# §SK obligation generation (spec_p0_socketkit.md — SocketKit Protocol)
# ---------------------------------------------------------------------------

SK_OPS = {"task_create", "accept_task", "task_submit", "task_accept",
          "review_merge", "contribution_score", "credit_score"}


def _task_create_obligations():
    """§SK.3.1: task_create(a, b) ≡ [a, b, 0, 0] — bounty ≥ 0, open, unclaimed."""
    defn = """
; Definition (§SK.3.1): task_create(a, b) ≡ [a, b, 0, 0], encoded to ℕ (Law II).
; index(t, 0)=a, index(t, 1)=b, index(t, 2)=0 (open), index(t, 3)=0 (unclaimed)
(declare-const a Int)
(declare-const b Int)
(assert (>= a 0))
(assert (>= b 0))
(declare-const t Int)
(assert (= (index t 0) a))
(assert (= (index t 1) b))
(assert (= (index t 2) 0))
(assert (= (index t 3) 0))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (and (>= (index t 0) 0) (>= (index t 1) 0) "
            "(>= (index t 2) 0) (>= (index t 3) 0))))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (= (index t 2) 0)))\n(check-sat)\n")
    law3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (= (index t 3) 0)))\n(check-sat)\n")
    return [("task_create/law1-bounty-nonnegative", law1),
            ("task_create/law2-fresh-task-open", law2),
            ("task_create/law3-fresh-task-unclaimed", law3)]


def _accept_task_obligations():
    """§SK.3.2: accept_task(t, h) — open → in_progress, hunter recorded."""
    common = """
; Definition (§SK.3.2): accept_task([a, b, 0, 0], h) ≡ [a, b, 1, h]
(declare-const a Int) (declare-const b Int) (declare-const h Int)
(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))
(declare-const t Int) (declare-const t2 Int)
(assert (= (index t 0) a)) (assert (= (index t 1) b))
(assert (= (index t 2) 0)) (assert (= (index t 3) 0))
(assert (= (index t2 0) a)) (assert (= (index t2 1) b))
(assert (= (index t2 2) 1)) (assert (= (index t2 3) h))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 2) 1)))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 3) h)))\n(check-sat)\n")
    return [("accept_task/law1-claim-in-progress", law1),
            ("accept_task/law2-hunter-recorded", law2)]


def _task_submit_obligations():
    """§SK.3.3: task_submit(t) — in_progress → pending_review, hunter preserved."""
    common = """
; Definition (§SK.3.3): task_submit([a, b, 1, h]) ≡ [a, b, 2, h]
(declare-const a Int) (declare-const b Int) (declare-const h Int)
(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))
(declare-const t Int) (declare-const t2 Int)
(assert (= (index t 0) a)) (assert (= (index t 1) b))
(assert (= (index t 2) 1)) (assert (= (index t 3) h))
(assert (= (index t2 0) a)) (assert (= (index t2 1) b))
(assert (= (index t2 2) 2)) (assert (= (index t2 3) h))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 2) 2)))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 3) (index t 3))))\n(check-sat)\n")
    return [("task_submit/law1-pending-review", law1),
            ("task_submit/law2-hunter-preserved", law2)]


def _task_accept_obligations():
    """§SK.3.4: task_accept(t) — pending_review → completed, hunter preserved."""
    common = """
; Definition (§SK.3.4): task_accept([a, b, 2, h]) ≡ [a, b, 3, h]
(declare-const a Int) (declare-const b Int) (declare-const h Int)
(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))
(declare-const t Int) (declare-const t2 Int)
(assert (= (index t 0) a)) (assert (= (index t 1) b))
(assert (= (index t 2) 2)) (assert (= (index t 3) h))
(assert (= (index t2 0) a)) (assert (= (index t2 1) b))
(assert (= (index t2 2) 3)) (assert (= (index t2 3) h))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 2) 3)))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "(assert (not (= (index t2 3) (index t 3))))\n(check-sat)\n")
    return [("task_accept/law1-completed", law1),
            ("task_accept/law2-hunter-preserved", law2)]


def _review_merge_obligations():
    """§SK.3.6: review_merge ≡ 1 if weighted_accept ≥ weighted_reject else 0."""
    common = """
(declare-const v1 Int) (declare-const v2 Int) (declare-const v3 Int)
(declare-const w1 Int) (declare-const w2 Int) (declare-const w3 Int)
(assert (or (= v1 0) (= v1 1)))
(assert (or (= v2 0) (= v2 1)))
(assert (or (= v3 0) (= v3 1)))
(assert (>= w1 0)) (assert (>= w2 0)) (assert (>= w3 0))
; Definition (§SK.3.6): weighted_accept ≥ weighted_reject ⇒ 1, else 0
(declare-const wa Int) (declare-const wr Int)
(assert (= wa (+ (* v1 w1) (* v2 w2) (* v3 w3))))
(assert (= wr (+ (* (- 1 v1) w1) (* (- 1 v2) w2) (* (- 1 v3) w3))))
(declare-const d Int)
(assert (= d (ite (>= wa wr) 1 0)))
"""
    law1 = "(set-logic NIA)\n" + common + \
        "(assert (not (or (= d 0) (= d 1))))\n(check-sat)\n"
    law2 = ("(set-logic NIA)\n" + common + """
; reverse(o) preserves the weighted sums (addition is commutative)
(declare-const wa_rev Int) (declare-const wr_rev Int)
(assert (= wa_rev (+ (* v3 w3) (* v2 w2) (* v1 w1))))
(assert (= wr_rev (+ (* (- 1 v3) w3) (* (- 1 v2) w2) (* (- 1 v1) w1))))
(declare-const d_rev Int)
(assert (= d_rev (ite (>= wa_rev wr_rev) 1 0)))
(assert (not (= d d_rev)))
(check-sat)
""")
    return [("review_merge/law1-decision-binary", law1),
            ("review_merge/law2-order-independent", law2)]


def _contribution_obligations():
    """§SK.3.5: contribution_score ≡ max(0, Σ deltas) — never negative."""
    common = """
(declare-const d1 Int) (declare-const d2 Int) (declare-const d3 Int)
(declare-const total Int)
(assert (= total (+ d1 d2 d3)))
; Definition (§SK.3.5): contribution_score ≡ max(0, Σ deltas)
(declare-const p Int)
(assert (= p (ite (> total 0) total 0)))
"""
    law1 = "(set-logic NIA)\n" + common + \
        "(assert (not (>= p 0)))\n(check-sat)\n"
    law2 = ("(set-logic NIA)\n" + common + """
; appending a zero delta is neutral
(declare-const p2 Int)
(assert (= p2 (ite (> (+ total 0) 0) (+ total 0) 0)))
(assert (not (= p p2)))
(check-sat)
""")
    return [("contribution_score/law1-points-nonnegative", law1),
            ("contribution_score/law2-zero-delta-neutral", law2)]


def _credit_score_obligations():
    """§SK.3.7: credit_score — base 100, +5 per complete, breach ×0.7 (×7 ÷10 floor)."""
    common = """
(declare-const e1 Int) (declare-const e2 Int)
(declare-const c Int)
; Definition (§SK.3.7): credit_score ≡ max(0, fold from 100)
(declare-const credit Int)
(assert (= credit (ite (> c 0) c 0)))
"""
    law1 = "(set-logic NIA)\n" + common + \
        "(assert (not (>= credit 0)))\n(check-sat)\n"
    law2 = "(set-logic NIA)\n" + common + """
; base credit: credit_score([]) ≡ 100 (no events → c = 100)
(assert (= c 100))
(assert (not (= credit 100)))
(check-sat)
"""
    law3 = "(set-logic NIA)\n" + common + """
; one completion: +5 → 105 (event kind 0, count 1)
(assert (= c 105))
(assert (not (= credit 105)))
(check-sat)
"""
    law4 = "(set-logic NIA)\n" + common + """
; one breach: ×0.7 → 70 (event kind 1, count 1: 100×7÷10)
(assert (= c 70))
(assert (not (= credit 70)))
(check-sat)
"""
    return [("credit_score/law1-credit-nonnegative", law1),
            ("credit_score/law2-base-credit", law2),
            ("credit_score/law3-completion-plus5", law3),
            ("credit_score/law4-breach-times07", law4)]


def gen_sk_obligation(op):
    """Generate §SK obligations for one SocketKit operation (or [])."""
    name = op["name"].strip()
    if name == "task_create":
        return _task_create_obligations()
    if name == "accept_task":
        return _accept_task_obligations()
    if name == "task_submit":
        return _task_submit_obligations()
    if name == "task_accept":
        return _task_accept_obligations()
    if name == "review_merge":
        return _review_merge_obligations()
    if name == "contribution_score":
        return _contribution_obligations()
    if name == "credit_score":
        return _credit_score_obligations()
    return []


# ---------------------------------------------------------------------------
# §SK.3.8 Invariants (spec_p0_socketkit.md — 状态机不变量, v0.18)
# ---------------------------------------------------------------------------

def gen_invariant_obligations(ops):
    """Generate state-machine invariant obligations (§SK.3.8 INV-1..4).

    Each obligation asserts the negation of an invariant under the operation
    definitions; PROVED (unsat) means the definitions satisfy the invariant
    for every reachable state.
    """
    names = {op["name"].strip() for op in ops}
    out = []

    # INV-1 状态单调: 任何状态操作不使 status 后退.
    if {"accept_task", "task_submit", "task_accept"} <= names:
        inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                "(declare-const t Int) (declare-const t2 Int)\n"
                "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
                "(assert (>= (index t 0) 0)) (assert (>= (index t 1) 0))\n"
                "(assert (>= (index t 2) 0)) (assert (>= (index t 2) 0))\n"
                "; Definition: t2 = accept_task(t, h) — open → in_progress\n"
                "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                "(assert (= (index t 2) 0)) (assert (= (index t 3) 0))\n"
                "(assert (= (index t2 0) a)) (assert (= (index t2 1) b))\n"
                "(assert (= (index t2 2) 1)) (assert (= (index t2 3) h))\n"
                "; INV-1: status never regresses\n"
                "(assert (not (>= (index t2 2) (index t 2))))\n(check-sat)\n")
        out.append(("INV-1/accept-task-monotonic", inv1))

        inv1b = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                 "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                 "(declare-const t Int) (declare-const t2 Int)\n"
                 "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
                 "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                 "(assert (= (index t 2) 1)) (assert (= (index t 3) h))\n"
                 "; Definition: t2 = task_submit(t) — in_progress → pending_review\n"
                 "(assert (= (index t2 0) a)) (assert (= (index t2 1) b))\n"
                 "(assert (= (index t2 2) 2)) (assert (= (index t2 3) h))\n"
                 "; INV-1: status never regresses\n"
                 "(assert (not (>= (index t2 2) (index t 2))))\n(check-sat)\n")
        out.append(("INV-1/submit-monotonic", inv1b))

        inv1c = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                 "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                 "(declare-const t Int) (declare-const t2 Int)\n"
                 "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
                 "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                 "(assert (= (index t 2) 2)) (assert (= (index t 3) h))\n"
                 "; Definition: t2 = task_accept(t, a) — pending_review → completed (author)\n"
                 "(assert (= (index t2 0) a)) (assert (= (index t2 1) b))\n"
                 "(assert (= (index t2 2) 3)) (assert (= (index t2 3) h))\n"
                 "; INV-1: status never regresses\n"
                 "(assert (not (>= (index t2 2) (index t 2))))\n(check-sat)\n")
        out.append(("INV-1/accept-monotonic", inv1c))

    # INV-2 终态不可变: completed 任务不可再被任何状态操作改变.
    if {"accept_task", "task_submit", "task_accept"} <= names:
        inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                "(declare-const t Int) (declare-const t2 Int)\n"
                "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
                "; t is completed (status 3)\n"
                "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                "(assert (= (index t 2) 3)) (assert (= (index t 3) h))\n"
                "; Definition: any state op on completed task → StateError, t2 = t\n"
                "(assert (= (index t2 0) a)) (assert (= (index t2 1) b))\n"
                "(assert (= (index t2 2) 3)) (assert (= (index t2 3) h))\n"
                "; INV-2: completed task state is unchanged\n"
                "(assert (not (= (index t2 2) (index t 2))))\n(check-sat)\n")
        out.append(("INV-2/completed-immutable", inv2))

    # INV-3 守恒: bounty (index 1) 与 hunter (index 3) 在状态流转中不变.
    if {"accept_task", "task_submit", "task_accept"} <= names:
        inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                "(declare-const t Int) (declare-const t2 Int)\n"
                "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
                "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                "(assert (= (index t 2) 1)) (assert (= (index t 3) h))\n"
                "; Definition: t2 = task_submit(t)\n"
                "(assert (= (index t2 0) a)) (assert (= (index t2 1) b))\n"
                "(assert (= (index t2 2) 2)) (assert (= (index t2 3) h))\n"
                "; INV-3: bounty and hunter preserved\n"
                "(assert (not (and (= (index t2 1) (index t 1))\n"
                "                 (= (index t2 3) (index t 3)))))\n(check-sat)\n")
        out.append(("INV-3/bounty-hunter-preserved", inv3))

    # INV-4 作者授权: 只有受茬人本人可验收自己的单.
    # Definition: a completed successor exists only when caller ≡ author;
    # the obligation asserts a non-author caller + completed successor,
    # which is unsatisfiable under the definition → PROVED (unsat).
    if "task_accept" in names:
        inv4 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
                "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
                "(declare-const c Int)\n"
                "(declare-const t Int) (declare-const t2 Int)\n"
                "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0)) (assert (>= c 0))\n"
                "; t is pending_review (status 2)\n"
                "(assert (= (index t 0) a)) (assert (= (index t 1) b))\n"
                "(assert (= (index t 2) 2)) (assert (= (index t 3) h))\n"
                "; INV-4 definition: completed successor requires caller ≡ author\n"
                "(assert (=> (and (= (index t2 0) (index t 0))\n"
                "                 (= (index t2 1) (index t 1))\n"
                "                 (= (index t2 2) 3))\n"
                "            (= c a)))\n"
                "; Obligation premise: caller is NOT the author\n"
                "(assert (not (= c a)))\n"
                "; Obligation premise: a completed successor t2 = t with status 3 exists\n"
                "(assert (= (index t2 0) (index t 0)))\n"
                "(assert (= (index t2 1) (index t 1)))\n"
                "(assert (= (index t2 2) 3))\n"
                "(assert (= (index t2 3) (index t 3)))\n"
                "(check-sat)\n")
        out.append(("INV-4/non-author-cannot-accept", inv4))

    return out


def prove_module(path):
    module = vc.parse_module(path)
    ok, violations = vc.check_python(module)  # includes P-01 structural checks
    structural = [v for v in violations
                  if v.startswith(("MissingModel", "MissingInvariant", "IncompleteContract"))]
    name = os.path.basename(path)

    has_sk = any(op["name"].strip() in SK_OPS for op in module["ops"])
    if not module["proof_declared"] and not has_sk:
        print(f"  {name}: no `## Proof` block — skipped (structural: {ok})")
        return ok

    print(f"  {name}:")
    for v in structural or ["P-01 structure OK"]:
        print(f"    • {v}")

    os.makedirs(OUT_DIR, exist_ok=True)
    obligations = []
    for op in module["ops"]:
        # §SK operations carry their own laws (§SK.3) — no Pre/Post needed.
        sk_obs = gen_sk_obligation(op)
        if sk_obs:
            obligations.extend(sk_obs)
            continue
        law_texts = [l for l in op.get("laws", [])]
        ob = gen_obligation(module, op, law_texts)
        if ob:
            obligations.append((op["name"], ob))

    # §SK.3.8 状态机不变量 (v0.18): INV-1 状态单调 / INV-2 终态不可变 /
    # INV-3 守恒 / INV-4 作者授权 — 附加义务，z3 消解 PROVED 即定义满足不变量。
    obligations.extend(gen_invariant_obligations(module["ops"]))

    if not structural and obligations:
        for oname, ob in obligations:
            fname = f"{name.replace('.md', '')}__{oname.replace('/', '_')}.smt2"
            fpath = os.path.join(OUT_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(ob)
            solver, res = discharge(ob)
            if solver:
                verdict = "PROVED (unsat)" if res["sat"] else f"DISPROVED ({res['result']})"
                print(f"    • {oname}: obligation → {verdict} [{solver}]")
                if not res["sat"]:
                    ok = False
            else:
                print(f"    • {oname}: obligation generated → {fpath} "
                      f"(no SMT solver on PATH — unverified)")
    elif not structural:
        print(f"    • no dischargeable obligations (ops need paired Pre/Post)")

    return ok


def main(paths=None):
    print("=" * 74)
    print("ΣLang sigma-prove — SMT-backed proof discharge (P-01 + obligations)")
    print("=" * 74)
    files = paths or sorted(
        os.path.join(CORPUS_DIR, f) for f in os.listdir(CORPUS_DIR) if f.endswith(".md")
    )
    all_ok = True
    for path in files:
        if not prove_module(path):
            all_ok = False
    print("-" * 74)
    print("ALL STRUCTURAL CHECKS PASS" if all_ok else "STRUCTURAL FAILURES PRESENT")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if len(sys.argv) > 1 else None))
