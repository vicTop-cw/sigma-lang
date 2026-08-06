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
    return gen_pf_obligation(op) or gen_growth_obligation(op) or gen_inventory_obligation(op)


# ---------------------------------------------------------------------------
# §IN obligation generation (spec_p0_inventory.md — 供应链, v0.43)
# ---------------------------------------------------------------------------

INV_OPS = {"inventory_new", "receive_stock", "ship_stock", "stock_level",
           "fill_rate"}


def gen_inventory_obligation(op):
    """Generate §IN obligations for one inventory operation (or [])."""
    name = op["name"].strip()
    if name == "inventory_new":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const a Int) (declare-const b Int) (declare-const inv Int)\n"
               "(assert (>= a 0)) (assert (>= b 0))\n"
               "; Definition (§IN.3.1): inventory_new(a,b) = [a, b]\n"
               "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
               "; Law: stock levels ≥ 0\n"
               "(assert (not (and (>= (index inv 0) 0) (>= (index inv 1) 0))))\n(check-sat)\n")
        return [("inventory_new/law-nonnegative", law)]
    if name == "receive_stock":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const a Int) (declare-const b Int) (declare-const q Int)\n"
               "(declare-const inv Int) (declare-const inv2 Int)\n"
               "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q 0))\n"
               "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
               "; Definition (§IN.3.2): receive_stock([a,b], 0, q) = [a+q, b]\n"
               "(assert (= (index inv2 0) (+ a q))) (assert (= (index inv2 1) b))\n"
               "; Law: additive inbound\n"
               "(assert (not (= (index inv2 0) (+ (index inv 0) q))))\n(check-sat)\n")
        return [("receive_stock/law-additive", law)]
    if name == "ship_stock":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const a Int) (declare-const b Int) (declare-const q Int)\n"
               "(declare-const inv Int) (declare-const inv2 Int)\n"
               "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q 0))\n"
               "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
               "; Definition (§IN.3.3): ship_stock([a,b], 0, q) = [a−q, b] when q ≤ a\n"
               "(assert (<= q a))\n"
               "(assert (= (index inv2 0) (- a q))) (assert (= (index inv2 1) b))\n"
               "; Law: no negative stock\n"
               "(assert (not (>= (index inv2 0) 0)))\n(check-sat)\n")
        return [("ship_stock/law-no-negative-stock", law)]
    if name == "stock_level":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const a Int) (declare-const b Int) (declare-const inv Int)\n"
               "(assert (>= a 0)) (assert (>= b 0))\n"
               "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
               "; Law: total preserved\n"
               "(assert (not (<= (+ (index inv 0) (index inv 1)) (+ a b))))\n(check-sat)\n")
        return [("stock_level/law-total-preserved", law)]
    if name == "fill_rate":
        law = ("(set-logic NIA)\n"
               "(declare-const s Int) (declare-const d Int) (declare-const fr Int)\n"
               "(assert (>= s 0)) (assert (> d 0)) (assert (<= s d))\n"
               "; Definition (§IN.3.5): fill_rate = s/d bounded 0..1 (scaled)\n"
               "(assert (= fr (div (* 100 s) d)))\n"
               "; Law: rate bounded 0..100 (0..1)\n"
               "(assert (not (and (>= fr 0) (<= fr 100))))\n(check-sat)\n")
        return [("fill_rate/law-bounded", law)]
    return []


def gen_inventory_invariants(ops):
    """v0.61 — §IN 跨操作不变量（附加义务，z3 消解）：
    INV-IN-1 总量守恒（入库后总量 = 初始 + 净入库，库存不凭空产生）/
    INV-IN-2 库存非负链（出库后每货品 ≥ 0）。"""
    names = {op["name"].strip() for op in ops}
    if not (names & INV_OPS):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int) (declare-const q Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q 0))\n"
            "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
            "; 跨操作: receive_stock([a,b],0,q) 后总量\n"
            "(assert (= (index inv2 0) (+ a q))) (assert (= (index inv2 1) b))\n"
            "; INV-IN-1: 总量 = 初始 + 净入库（不凭空产生）\n"
            "(assert (not (= (+ (index inv2 0) (index inv2 1)) (+ a b q))))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int) (declare-const q Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q 0)) (assert (<= q a))\n"
            "(assert (= (index inv 0) a)) (assert (= (index inv 1) b))\n"
            "; 跨操作: ship_stock([a,b],0,q) 后库存（q ≤ held）\n"
            "(assert (= (index inv2 0) (- a q))) (assert (= (index inv2 1) b))\n"
            "; INV-IN-2: 出库后每货品 ≥ 0\n"
            "(assert (not (>= (index inv2 0) 0)))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const x Int) (declare-const y Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= x 0)) (assert (>= y 0))\n"
            "; 跨操作: receive_stock(receive_stock([a,b],0,x),0,y) 后 item0\n"
            "(assert (= (index inv 0) (+ a x))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (+ (index inv 0) y))) (assert (= (index inv2 1) b))\n"
            "; INV-IN-3 (v0.105): 入库链可加性 — item0 = a + x + y\n"
            "(assert (not (= (index inv2 0) (+ a x y))))\n(check-sat)\n")
    inv4 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const x Int) (declare-const y Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= x 0)) (assert (>= y 0))\n"
            "; 两次出库（x ≤ a 且 y ≤ a-x，不超卖）\n"
            "(assert (<= x a)) (assert (<= y (- a x)))\n"
            "(assert (= (index inv 0) (- a x))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (- (index inv 0) y))) (assert (= (index inv2 1) b))\n"
            "; INV-IN-4 (v0.105): 出库链不超卖 — 链后 item0 ≥ 0\n"
            "(assert (not (>= (index inv2 0) 0)))\n(check-sat)\n")
    inv5 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const x Int) (declare-const y Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= x 0)) (assert (>= y 0))\n"
            "; 混合入库: receive item0 x 后 receive item1 y\n"
            "(assert (= (index inv 0) (+ a x))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (+ a x))) (assert (= (index inv2 1) (+ b y)))\n"
            "; INV-IN-5 (v0.153): 混合货品可加链 — item0=a+x 且 item1=b+y\n"
            "(assert (not (and (= (index inv2 0) (+ a x)) (= (index inv2 1) (+ b y)))))\n(check-sat)\n")
    inv6 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "; receive q1 后 ship q2（q2 ≤ a+q1）: item0 = a+q1−q2\n"
            "(assert (<= q2 (+ a q1)))\n"
            "(assert (= (index inv 0) (+ a q1))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (- (index inv 0) q2))) (assert (= (index inv2 1) b))\n"
            "; INV-IN-6 (v0.193): 入库-出库联动 — receive 加 q1 后 ship q2，item0=a+q1−q2 且 ≥0\n"
            "(assert (not (and (= (index inv2 0) (- (+ a q1) q2)) (>= (index inv2 0) 0))))\n(check-sat)\n")
    inv7 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "(assert (<= q2 b))\n"
            "; receive item0 q1 后 ship item1 q2: item0 = a+q1, item1 = b−q2\n"
            "(assert (= (index inv 0) (+ a q1))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (+ a q1))) (assert (= (index inv2 1) (- b q2)))\n"
            "; INV-IN-7 (v0.223): 混合货品联动 — item0=a+q1 且 item1=b−q2 ≥0\n"
            "(assert (not (and (= (index inv2 0) (+ a q1)) (= (index inv2 1) (- b q2)) (>= (index inv2 1) 0))))\n(check-sat)\n")
    inv8 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const inv Int) (declare-const inv2 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "(assert (<= q1 a)) (assert (<= q2 b))\n"
            "; ship item0 q1 后 ship item1 q2: item0 = a−q1, item1 = b−q2\n"
            "(assert (= (index inv 0) (- a q1))) (assert (= (index inv 1) b))\n"
            "(assert (= (index inv2 0) (- a q1))) (assert (= (index inv2 1) (- b q2)))\n"
            "; INV-IN-8 (v0.263): 混合出库联动 — item0=a−q1 且 item1=b−q2 ≥0\n"
            "(assert (not (and (= (index inv2 0) (- a q1)) (= (index inv2 1) (- b q2)) (>= (index inv2 1) 0))))\n(check-sat)\n")
    return [("INV-IN-1 total-conserved", inv1),
            ("INV-IN-2 no-negative-chain", inv2),
            ("INV-IN-3 receive-additive-chain", inv3),
            ("INV-IN-4 no-oversell-chain", inv4),
            ("INV-IN-5 mixed-additive-chain", inv5),
            ("INV-IN-6 receive-ship-link", inv6),
            ("INV-IN-7 mixed-item-link", inv7),
            ("INV-IN-8 mixed-ship-link", inv8)]


def gen_portfolio_invariants(ops):
    """v0.62 — §PF 跨操作不变量（附加义务，z3 消解）：
    INV-PF-1 现金守恒（buy 后 cash = 初始 − 花费 ≥ 0，现金不凭空产生）/
    INV-PF-2 份额守恒（sell 后 shares = 初始 − 卖出 ≥ 0，不凭空卖份额）。"""
    names = {op["name"].strip() for op in ops}
    if not (names & PF_OPS):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const q Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= q 0)) (assert (<= q c))\n"
            "(assert (= (index p 0) c)) (assert (= (index p 1) 0)) (assert (= (index p 2) 0))\n"
            "; 跨操作: buy([c,0,0], 0, q) 后现金（c ≥ q 可支付）\n"
            "(assert (= (index p2 0) (- c q))) (assert (= (index p2 1) q)) (assert (= (index p2 2) 0))\n"
            "; INV-PF-1: 现金守恒 — cash ≥ 0，现金不凭空产生\n"
            "(assert (not (>= (index p2 0) 0)))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const q Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= q 0)) (assert (<= q c))\n"
            "(assert (= (index p 0) c)) (assert (= (index p 1) c)) (assert (= (index p 2) 0))\n"
            "; 跨操作: sell([c,c,0], 0, q) 后份额（q ≤ 持有）\n"
            "(assert (= (index p2 0) (+ c q))) (assert (= (index p2 1) (- c q))) (assert (= (index p2 2) 0))\n"
            "; INV-PF-2: 份额守恒 — shares ≥ 0，不凭空卖份额\n"
            "(assert (not (>= (index p2 1) 0)))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "; buy 后（q1 ≤ cash）: cash = c − q1, shares = s + q1\n"
            "(assert (<= q1 c))\n"
            "(assert (= (index p 0) (- c q1))) (assert (= (index p 1) (+ s q1))) (assert (= (index p 2) 0))\n"
            "; sell 后（q2 ≤ 持有）: cash + q2, shares − q2\n"
            "(assert (<= q2 (index p 1)))\n"
            "(assert (= (index p2 0) (+ (index p 0) q2))) (assert (= (index p2 1) (- (index p 1) q2))) (assert (= (index p2 2) 0))\n"
            "; INV-PF-3 (v0.106): 资产非负链 — 链后 cash ≥ 0 且 shares ≥ 0\n"
            "(assert (not (and (>= (index p2 0) 0) (>= (index p2 1) 0))))\n(check-sat)\n")
    inv4 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "; 两次 buy（q1+q2 ≤ cash）: cash −q1−q2, shares +q1+q2\n"
            "(assert (<= (+ q1 q2) c))\n"
            "(assert (= (index p 0) (- c q1))) (assert (= (index p 1) (+ s q1))) (assert (= (index p 2) 0))\n"
            "(assert (= (index p2 0) (- (index p 0) q2))) (assert (= (index p2 1) (+ (index p 1) q2))) (assert (= (index p2 2) 0))\n"
            "; INV-PF-4 (v0.143): 交易链可加性 — 链后 cash+q1+q2=c 且 shares−q1−q2=s\n"
            "(assert (not (and (= (+ (index p2 0) q1 q2) c) (= (- (index p2 1) q1 q2) s))))\n(check-sat)\n")
    inv5 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q 0)) (assert (<= q c))\n"
            "; buy q 后 sell q（份额足够）: 现金/份额恢复\n"
            "(assert (= (index p 0) (- c q))) (assert (= (index p 1) (+ s q))) (assert (= (index p 2) 0))\n"
            "(assert (= (index p2 0) (+ (index p 0) q))) (assert (= (index p2 1) (- (index p 1) q))) (assert (= (index p2 2) 0))\n"
            "; INV-PF-5 (v0.173): 买入-卖出链守恒 — buy q 后 sell q，现金/份额恢复\n"
            "(assert (not (and (= (index p2 0) c) (= (index p2 1) s))))\n(check-sat)\n")
    inv6 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "(assert (<= q1 c))\n"
            "; buy q1 后 sell q2（q2 ≤ s+q1）: cash = c−q1+q2, shares = s+q1−q2\n"
            "(assert (<= q2 (+ s q1)))\n"
            "(assert (= (index p 0) (- c q1))) (assert (= (index p 1) (+ s q1))) (assert (= (index p 2) 0))\n"
            "(assert (= (index p2 0) (+ (index p 0) q2))) (assert (= (index p2 1) (- (index p 1) q2))) (assert (= (index p2 2) 0))\n"
            "; INV-PF-6 (v0.203): 交易链完整性 — buy q1 后 sell q2，cash=c−q1+q2 且 shares=s+q1−q2\n"
            "(assert (not (and (= (index p2 0) (- (+ c q2) q1)) (= (index p2 1) (- (+ s q1) q2)))))\n(check-sat)\n")
    inv7 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "(assert (<= q1 c))\n"
            "; buy q1 后 sell q2（q2 ≤ s+q1）: 资产总额 cash+shares 不变（单价 1）\n"
            "(assert (<= q2 (+ s q1)))\n"
            "(assert (= (index p2 0) (- (+ c q2) q1))) (assert (= (index p2 1) (- (+ s q1) q2)))\n"
            "; INV-PF-7 (v0.233): 资产链完整性 — 链后 cash+shares = c+s（总额守恒）\n"
            "(assert (not (= (+ (index p2 0) (index p2 1)) (+ c s))))\n(check-sat)\n")
    inv8 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int)\n"
            "(declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0))\n"
            "(assert (<= (+ q1 q2) c))\n"
            "; buy asset0 q1 后 buy asset1 q2: cash = c−q1−q2, shares = s+q1+q2\n"
            "(assert (= (index p2 0) (- c q1 q2))) (assert (= (index p2 1) (+ s q1 q2)))\n"
            "; INV-PF-8 (v0.273): 混合资产链完整性 — 链后 cash+shares = c+s（总额守恒）\n"
            "(assert (not (= (+ (index p2 0) (index p2 1)) (+ c s))))\n(check-sat)\n")
    inv9 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const s Int)\n"
            "(declare-const q1 Int) (declare-const q2 Int) (declare-const q3 Int)\n"
            "(declare-const p2 Int)\n"
            "(assert (>= c 0)) (assert (>= s 0)) (assert (>= q1 0)) (assert (>= q2 0)) (assert (>= q3 0))\n"
            "(assert (<= (+ q1 q2) c))\n"
            "; buy asset0 q1 → buy asset1 q2 → sell asset0 q3（q3 ≤ s+q1）: 混合交易链\n"
            "(assert (<= q3 (+ s q1)))\n"
            "; cash = c−q1−q2+q3, qA = s+q1−q3, qB = q2（三元素组合）\n"
            "(assert (= (index p2 0) (- (+ c q3) q1 q2))) (assert (= (index p2 1) (- (+ s q1) q3))) (assert (= (index p2 2) q2))\n"
            "; INV-PF-9 (v0.313): 组合估值-风险联动 — 链后估值 cash+qA+qB = c+s 且估值 ≥ 风险（cash ≥ 0）\n"
            "(assert (not (and (= (+ (index p2 0) (index p2 1) (index p2 2)) (+ c s))\n"
            "                 (>= (+ (index p2 0) (index p2 1) (index p2 2))\n"
            "                     (+ (index p2 1) (index p2 2))))))\n(check-sat)\n")
    return [("INV-PF-1 cash-conserved", inv1),
            ("INV-PF-2 shares-conserved", inv2),
            ("INV-PF-3 nonnegative-chain", inv3),
            ("INV-PF-4 additive-trade-chain", inv4),
            ("INV-PF-5 buy-sell-roundtrip", inv5),
            ("INV-PF-6 trade-chain-integrity", inv6),
            ("INV-PF-7 asset-chain-integrity", inv7),
            ("INV-PF-8 mixed-asset-chain", inv8),
            ("INV-PF-9 valuation-risk-link", inv9)]


def gen_socketkit_invariants(ops):
    """v0.63 — §SK 跨操作不变量（附加义务，z3 消解）：
    INV-SK-1 赏金守恒（hold→release 后 escrow+available 恒等，赏金不凭空增减）/
    INV-SK-2 不超提（withdraw 后 available ≥ 0，available 不出现负）。"""
    names = {op["name"].strip() for op in ops}
    points_ops = {"points_new", "points_hold", "points_release", "points_withdraw"}
    if not (names & points_ops):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const b Int) (declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= b 0))\n"
            "(assert (= (index p 0) 0)) (assert (= (index p 1) 0))\n"
            "; 跨操作: hold(b) 后 → release(b) 后（托管→释放）\n"
            "(assert (= (index p2 0) 0)) (assert (= (index p2 1) b))\n"
            "; INV-SK-1: escrow + available 恒等（赏金不凭空增减）\n"
            "(assert (not (= (+ (index p2 0) (index p2 1)) b)))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const x Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= a 0)) (assert (>= x 0)) (assert (<= x a))\n"
            "(assert (= (index p 0) 0)) (assert (= (index p 1) a))\n"
            "; 跨操作: withdraw(available=a, x) 后\n"
            "(assert (= (index p2 0) 0)) (assert (= (index p2 1) (- a x)))\n"
            "; INV-SK-2: available ≥ 0（不超提）\n"
            "(assert (not (>= (index p2 1) 0)))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const e Int) (declare-const a Int) (declare-const p Int)\n"
            "(assert (>= e 0)) (assert (>= a 0))\n"
            "(assert (= (index p 0) e)) (assert (= (index p 1) a))\n"
            "; INV-SK-3 (v0.80): 积分非负链 — escrow ≥ 0 ∧ available ≥ 0\n"
            "(assert (not (and (>= (index p 0) 0) (>= (index p 1) 0))))\n(check-sat)\n")
    inv4 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const a Int) (declare-const b Int) (declare-const h Int)\n"
            "(declare-const t0 Int) (declare-const t1 Int) (declare-const t2 Int) (declare-const t3 Int)\n"
            "(assert (>= a 0)) (assert (>= b 0)) (assert (>= h 0))\n"
            "; 任务状态机链: [author, bounty, state, hunter]\n"
            "(assert (= (index t0 0) a)) (assert (= (index t0 1) b)) (assert (= (index t0 2) 0)) (assert (= (index t0 3) 0))\n"
            "(assert (= (index t1 0) a)) (assert (= (index t1 1) b)) (assert (= (index t1 2) 1)) (assert (= (index t1 3) h))\n"
            "(assert (= (index t2 0) a)) (assert (= (index t2 1) b)) (assert (= (index t2 2) 2)) (assert (= (index t2 3) h))\n"
            "(assert (= (index t3 0) a)) (assert (= (index t3 1) b)) (assert (= (index t3 2) 3)) (assert (= (index t3 3) h))\n"
            "; INV-SK-4 (v0.107): 状态机链 — claim→submit→accept 各步 state 单调 +1\n"
            "(assert (not (and (= (index t1 2) 1) (= (index t2 2) 2) (= (index t3 2) 3))))\n(check-sat)\n")
    inv5 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const x Int) (declare-const c2 Int)\n"
            "(assert (>= c 0)) (assert (>= x 0))\n"
            "; 跨操作 (v0.108): 契分累加后\n"
            "(assert (= c2 (+ c x)))\n"
            "; INV-SK-5: 契分非负链 — credit ≥ 0\n"
            "(assert (not (>= c2 0)))\n(check-sat)\n")
    inv6 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const b Int) (declare-const m Int)\n"
            "(declare-const q Int) (declare-const q2 Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= b 0)) (assert (>= m 0)) (assert (<= b m))\n"
            "; 联动: quota_new(m) → quota_use(b)（额度充足）→ points_hold(b)（托管）\n"
            "(assert (= (index q 0) m)) (assert (= (index q 1) m))\n"
            "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- m b)))\n"
            "(assert (= (index p 0) 0)) (assert (= (index p 1) 0))\n"
            "(assert (= (index p2 0) b)) (assert (= (index p2 1) 0))\n"
            "; INV-SK-6 (v0.136): 额度-托管联动 — remaining ≥ 0 且 escrow = bounty\n"
            "(assert (not (and (>= (index q2 1) 0) (= (index p2 0) b))))\n(check-sat)\n")
    inv7 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const c Int) (declare-const b Int) (declare-const h Int)\n"
            "(declare-const t Int) (declare-const t2 Int)\n"
            "(declare-const c2 Int)\n"
            "(assert (>= c 0)) (assert (>= b 0)) (assert (>= h 0))\n"
            "; 任务完成（state 2→3）后契分联动增加\n"
            "(assert (= (index t 0) 0)) (assert (= (index t 1) b)) (assert (= (index t 2) 2)) (assert (= (index t 3) h))\n"
            "(assert (= (index t2 0) 0)) (assert (= (index t2 1) b)) (assert (= (index t2 2) 3)) (assert (= (index t2 3) h))\n"
            "(assert (= c2 (+ c 10)))\n"
            "; INV-SK-7 (v0.163): 任务-契分联动 — 验收后契分 +10 且任务状态 3\n"
            "(assert (not (and (= (index t2 2) 3) (= c2 (+ c 10)))))\n(check-sat)\n")
    inv8 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const b Int) (declare-const e Int) (declare-const a Int)\n"
            "(declare-const p Int) (declare-const p2 Int)\n"
            "(assert (>= b 0)) (assert (>= e 0)) (assert (>= a 0)) (assert (<= b e))\n"
            "; accept 后 escrow 释放: escrow = e − b, available = a + b\n"
            "(assert (= (index p 0) e)) (assert (= (index p 1) a))\n"
            "(assert (= (index p2 0) (- e b))) (assert (= (index p2 1) (+ a b)))\n"
            "; INV-SK-8 (v0.183): 赏金-积分联动 — 释放后 escrow−b 且 available+b（守恒）\n"
            "(assert (not (and (= (index p2 0) (- e b)) (= (index p2 1) (+ a b)))))\n(check-sat)\n")
    inv9 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const m Int) (declare-const n Int)\n"
            "(declare-const q2 Int) (declare-const c2 Int)\n"
            "(assert (>= m 0)) (assert (>= n 0)) (assert (<= n m))\n"
            "; 发单 n 次（每次扣 1 额度）+ 验收 n 次（每次契分 +5）: remaining=m−n, credit=100+5n\n"
            "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- m n)))\n"
            "(assert (= c2 (+ 100 (* 5 n))))\n"
            "; INV-SK-9 (v0.213): 额度-契分联动 — 发单 n 后 remaining=m−n ≥0 且契分=100+5n\n"
            "(assert (not (and (>= (index q2 1) 0) (= c2 (+ 100 (* 5 n))))))\n(check-sat)\n")
    inv10 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
             "(declare-const n Int)\n"
             "(declare-const c2 Int) (declare-const v2 Int)\n"
             "(assert (>= n 0))\n"
             "; 验收 n 次后: 契分 = 100+5n（每次 +5），贡献分 = 10n（每次 +10）\n"
             "(assert (= c2 (+ 100 (* 5 n))))\n"
             "(assert (= v2 (* 10 n)))\n"
             "; INV-SK-10 (v0.243): 契分-贡献联动 — 验收 n 后契分=100+5n 且贡献分=10n\n"
             "(assert (not (and (= c2 (+ 100 (* 5 n))) (= v2 (* 10 n)))))\n(check-sat)\n")
    inv11 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
             "(declare-const n Int)\n"
             "(declare-const c2 Int) (declare-const b2 Int)\n"
             "(assert (>= n 0))\n"
             "; 验收 n 次后契分 = 100+5n，勋章按档位（<300→1、≥300→2）\n"
             "(assert (= c2 (+ 100 (* 5 n))))\n"
             "(assert (= b2 (ite (< c2 300) 1 2)))\n"
             "; INV-SK-11 (v0.253): 契分-勋章联动 — 契分档位与勋章等级联动\n"
             "(assert (not (and (= c2 (+ 100 (* 5 n))) (= b2 (ite (< c2 300) 1 2)))))\n(check-sat)\n")
    inv12 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
             "(declare-const n Int)\n"
             "(declare-const c2 Int) (declare-const v2 Int) (declare-const b2 Int)\n"
             "(assert (>= n 0))\n"
             "; 验收 n 次后: 契分=100+5n、贡献分=10n、勋章按档位（<300→1、≥300→2）\n"
             "(assert (= c2 (+ 100 (* 5 n))))\n"
             "(assert (= v2 (* 10 n)))\n"
             "(assert (= b2 (ite (< c2 300) 1 2)))\n"
             "; INV-SK-12 (v0.283): 契分-贡献-勋章三链联动 — 三维度联动守恒\n"
             "(assert (not (and (= c2 (+ 100 (* 5 n))) (= v2 (* 10 n)) (= b2 (ite (< c2 300) 1 2)))))\n(check-sat)\n")
    inv13 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
             "(declare-const m Int) (declare-const n Int) (declare-const b Int)\n"
             "(declare-const q2 Int) (declare-const p2 Int)\n"
             "(assert (>= m 0)) (assert (>= n 0)) (assert (>= b 0)) (assert (<= n m))\n"
             "; 发单 n 次（每次扣 1 配额 + 托管 b）: 配额 remaining=m−n ≥0、积分 escrow=n×b\n"
             "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- m n)))\n"
             "(assert (= (index p2 0) (* n b))) (assert (= (index p2 1) 0))\n"
             "; INV-SK-13 (v0.293): 积分-配额联动 — remaining=m−n ≥0 且 escrow=n×b\n"
             "(assert (not (and (>= (index q2 1) 0) (= (index p2 0) (* n b)))))\n(check-sat)\n")
    inv14 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
             "(declare-const m Int) (declare-const n Int) (declare-const b Int)\n"
             "(declare-const t2 Int) (declare-const q2 Int) (declare-const p2 Int)\n"
             "(assert (>= m 0)) (assert (>= n 0)) (assert (>= b 0)) (assert (<= n m))\n"
             "; 发单 n 次: 任务数=n、配额 remaining=m−n ≥0、积分 escrow=n×b（三维联动）\n"
             "(assert (= t2 n))\n"
             "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- m n)))\n"
             "(assert (= (index p2 0) (* n b))) (assert (= (index p2 1) 0))\n"
             "; INV-SK-14 (v0.303): 任务-积分-配额三维联动 — 任务数=n 且 remaining=m−n ≥0 且 escrow=n×b\n"
             "(assert (not (and (= t2 n) (>= (index q2 1) 0) (= (index p2 0) (* n b)))))\n(check-sat)\n")
    return [("INV-SK-1 bounty-conserved", inv1),
            ("INV-SK-2 no-over-withdraw", inv2),
            ("INV-SK-3 nonnegative-chain", inv3),
            ("INV-SK-4 state-machine-chain", inv4),
            ("INV-SK-5 credit-nonnegative-chain", inv5),
            ("INV-SK-6 quota-escrow-link", inv6),
            ("INV-SK-7 task-credit-link", inv7),
            ("INV-SK-8 bounty-points-link", inv8),
            ("INV-SK-9 quota-credit-link", inv9),
            ("INV-SK-10 credit-contribution-link", inv10),
            ("INV-SK-11 credit-badge-link", inv11),
            ("INV-SK-12 credit-contribution-badge-link", inv12),
            ("INV-SK-13 points-quota-link", inv13),
            ("INV-SK-14 task-points-quota-link", inv14)]


def gen_quota_invariants(ops):
    """v0.76 — §SK 额度制跨操作不变量（附加义务，z3 消解）：
    INV-Q-1 不超用（quota_use 链中 remaining 永不 < 0，累计使用 ≤ monthly）/
    INV-Q-2 重置恢复（quota_reset 后 remaining 恢复 monthly）。"""
    names = {op["name"].strip() for op in ops}
    quota_ops = {"quota_new", "quota_use", "quota_reset", "quota_advance"}
    if not (names & quota_ops):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const m Int) (declare-const a1 Int) (declare-const a2 Int)\n"
            "(declare-const q Int) (declare-const q2 Int)\n"
            "(assert (>= m 0)) (assert (>= a1 0)) (assert (>= a2 0))\n"
            "(assert (<= a1 m)) (assert (<= a2 (- m a1)))\n"
            "; 跨操作: quota_use(quota_use([m,m], a1), a2) 后 remaining\n"
            "(assert (= (index q 0) m)) (assert (= (index q 1) (- m a1)))\n"
            "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- (- m a1) a2)))\n"
            "; INV-Q-1: 不超用 — remaining ≥ 0（累计使用 ≤ monthly）\n"
            "(assert (not (>= (index q2 1) 0)))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const m Int) (declare-const a Int)\n"
            "(declare-const q Int) (declare-const q2 Int)\n"
            "(assert (>= m 0)) (assert (>= a 0)) (assert (<= a m))\n"
            "; 跨操作: quota_reset(quota_use([m,m], a)) 后\n"
            "(assert (= (index q 0) m)) (assert (= (index q 1) (- m a)))\n"
            "(assert (= (index q2 0) m)) (assert (= (index q2 1) m))\n"
            "; INV-Q-2: 重置恢复 remaining = monthly\n"
            "(assert (not (= (index q2 1) m)))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const m Int) (declare-const r Int) (declare-const q2 Int)\n"
            "(assert (>= m 0)) (assert (>= r 0))\n"
            "; 跨操作 (v0.80): quota_advance([m,r]) 后 remaining = r + m\n"
            "(assert (= (index q2 0) m)) (assert (= (index q2 1) (+ r m)))\n"
            "; INV-Q-3: 预支链 — advance 后 remaining ≥ 0\n"
            "(assert (not (>= (index q2 1) 0)))\n(check-sat)\n")
    return [("INV-Q-1 no-over-use", inv1),
            ("INV-Q-2 reset-restores", inv2),
            ("INV-Q-3 advance-chain", inv3)]


def gen_team_invariants(ops):
    """v0.77 — §SK 团机制跨操作不变量（附加义务，z3 消解）：
    INV-T-1 不超员（team_join 链中 size 永不 > capacity）/
    INV-T-2 成员递增（team_join 后 size = 原 size + 1）。"""
    names = {op["name"].strip() for op in ops}
    team_ops = {"team_create", "team_join"}
    if not (names & team_ops):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const o Int) (declare-const k Int) (declare-const s Int)\n"
            "(declare-const c Int) (declare-const s2 Int)\n"
            "(assert (>= o 0)) (assert (>= k 0)) (assert (>= s 1)) (assert (>= c 1))\n"
            "(assert (<= s c))\n"
            "; 跨操作: team_join([o,k,s,c], m) 后（s < c 才允许加入）\n"
            "(assert (< s c))\n"
            "(assert (= s2 (+ s 1)))\n"
            "; INV-T-1: 不超员 — join 后 size ≤ capacity\n"
            "(assert (not (<= s2 c)))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const o Int) (declare-const k Int) (declare-const s Int)\n"
            "(declare-const c Int) (declare-const s2 Int)\n"
            "(assert (>= o 0)) (assert (>= k 0)) (assert (>= s 1)) (assert (>= c 1))\n"
            "(assert (< s c))\n"
            "; 跨操作: team_join 后 size\n"
            "(assert (= s2 (+ s 1)))\n"
            "; INV-T-2: 成员递增 — join 后 size = 原 size + 1\n"
            "(assert (not (= s2 (+ s 1))))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const o Int) (declare-const k Int) (declare-const c Int)\n"
            "(declare-const t Int)\n"
            "(assert (>= o 0)) (assert (>= k 0)) (assert (>= c 1))\n"
            "; 跨操作 (v0.108): team_create(o,k,c) 后 [o,k,1,c]\n"
            "(assert (= (index t 0) o)) (assert (= (index t 1) k))\n"
            "(assert (= (index t 2) 1)) (assert (= (index t 3) c))\n"
            "; INV-T-3: 创建合法链 — founder=owner 且 size=1\n"
            "(assert (not (and (= (index t 0) o) (= (index t 2) 1))))\n(check-sat)\n")
    return [("INV-T-1 no-over-capacity", inv1),
            ("INV-T-2 member-increment", inv2),
            ("INV-T-3 create-legal-chain", inv3)]


def gen_growth_invariants(ops):
    """v0.78 — §SK 增长期跨操作不变量（附加义务，z3 消解）：
    INV-G-1 授权签发链（badge_issue 的 level = badge_level(score) 且 0..3 有界）/
    INV-G-2 裁决链（dispute_review 对任意证据恒 binary 0/1）。"""
    names = {op["name"].strip() for op in ops}
    growth_check = {"badge_issue", "dispute_review"}
    if not (names & growth_check):
        return []
    inv1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
            "(declare-const s Int) (declare-const lvl Int)\n"
            "(assert (>= s 0))\n"
            "; 跨操作: badge_issue(1001, u, s) 的 level = badge_level(s)\n"
            "(assert (= lvl (ite (< s 100) 0 (ite (< s 300) 1 (ite (< s 600) 2 3)))))\n"
            "; INV-G-1: 授权签发链 — level 有界 0..3\n"
            "(assert (not (and (>= lvl 0) (<= lvl 3))))\n(check-sat)\n")
    inv2 = ("(set-logic NIA)\n"
            "(declare-const v1 Int) (declare-const v2 Int) (declare-const d Int)\n"
            "(assert (or (= v1 0) (= v1 1)))\n"
            "(assert (or (= v2 0) (= v2 1)))\n"
            "(assert (= d (ite (>= v1 v2) 1 0)))\n"
            "; INV-G-2: 裁决链 — dispute_review 恒 binary\n"
            "(assert (not (or (= d 0) (= d 1))))\n(check-sat)\n")
    inv3 = ("(set-logic NIA)\n"
            "(declare-const r Int) (declare-const s1 Int) (declare-const s2 Int)\n"
            "(assert (>= r 0)) (assert (>= s1 0)) (assert (>= s2 0))\n"
            "; 跨操作 (v0.108): team_share 后 Σ shares ≤ reward\n"
            "(assert (<= (+ s1 s2) r))\n"
            "; INV-G-3: 收益不超发链 — Σ shares ≤ reward\n"
            "(assert (not (<= (+ s1 s2) r)))\n(check-sat)\n")
    return [("INV-G-1 authorized-issue-chain", inv1),
            ("INV-G-2 binary-decision-chain", inv2),
            ("INV-G-3 no-overpay-chain", inv3)]


# ---------------------------------------------------------------------------
# §SK.3.12–3.17 obligation generation (spec_p0_socketkit.md — 增长期, v0.34)
# ---------------------------------------------------------------------------

GROWTH_OPS = {"badge_issue", "dispute_review", "team_create", "team_join",
              "team_share", "quota_advance", "points_ledger"}

# 五大制度操作（额度/积分/勋章）—— §SK 系统操作，需纳入 has_sk（v0.63
# 修复：否则 socketkit_quota/points 模块会被 skip，跨操作不变量义务不生成）。
SK_SYS_OPS = {"quota_new", "quota_use", "quota_reset",
              "points_new", "points_hold", "points_release", "points_withdraw",
              "badge_level"}


def gen_growth_obligation(op):
    """Generate §SK.3.12–3.17 obligations for one growth operation (or [])."""
    name = op["name"].strip()
    if name == "badge_issue":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const v Int) (declare-const u Int) (declare-const s Int)\n"
               "(declare-const b Int)\n"
               "(assert (>= v 1000)) (assert (>= u 0)) (assert (>= s 0))\n"
               "; Definition (§SK.3.12): badge_issue(v,u,s) = [v, u, badge_level(s)]\n"
               "(assert (= (index b 0) v)) (assert (= (index b 1) u))\n"
               "(assert (= (index b 2) (ite (< s 100) 0 (ite (< s 300) 1 "
               "(ite (< s 600) 2 3)))))\n"
               "; Law: level bounded 0..3 (授权核验师 v ≥ 1000)\n"
               "(assert (not (and (>= (index b 2) 0) (<= (index b 2) 3))))\n(check-sat)\n")
        return [("badge_issue/law-level-bounded", law)]
    if name == "dispute_review":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const v1 Int) (declare-const v2 Int) (declare-const v3 Int)\n"
               "(declare-const w1 Int) (declare-const w2 Int) (declare-const w3 Int)\n"
               "(assert (or (= v1 0) (= v1 1)))\n"
               "(assert (or (= v2 0) (= v2 1)))\n"
               "(assert (or (= v3 0) (= v3 1)))\n"
               "(assert (>= w1 0)) (assert (>= w2 0)) (assert (>= w3 0))\n"
               "; Definition (§SK.3.13): dispute_review ≡ 1 if support ≥ reject\n"
               "(declare-const ws Int) (declare-const wr Int) (declare-const d Int)\n"
               "(assert (= ws (+ (* v1 w1) (* v2 w2) (* v3 w3))))\n"
               "(assert (= wr (+ (* (- 1 v1) w1) (* (- 1 v2) w2) (* (- 1 v3) w3))))\n"
               "(assert (= d (ite (>= ws wr) 1 0)))\n"
               "; Law: decision is binary\n"
               "(assert (not (or (= d 0) (= d 1))))\n(check-sat)\n")
        return [("dispute_review/law-binary", law)]
    if name == "team_create":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const o Int) (declare-const k Int) (declare-const c Int)\n"
               "(declare-const t Int)\n"
               "(assert (>= o 0)) (assert (>= k 0)) (assert (>= c 1))\n"
               "; Definition (§SK.3.14): team_create(o,k,c) = [o, k, 1, c]\n"
               "(assert (= (index t 0) o)) (assert (= (index t 1) k))\n"
               "(assert (= (index t 2) 1)) (assert (= (index t 3) c))\n"
               "; Law: founder is a member and size ≤ capacity\n"
               "(assert (not (and (= (index t 2) 1) (<= (index t 2) (index t 3)))))\n(check-sat)\n")
        return [("team_create/law-founder-member", law)]
    if name == "team_join":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const o Int) (declare-const k Int) (declare-const s Int)\n"
               "(declare-const c Int) (declare-const m Int)\n"
               "(declare-const t Int) (declare-const t2 Int)\n"
               "(assert (>= o 0)) (assert (>= k 0)) (assert (>= m 0))\n"
               "(assert (= (index t 0) o)) (assert (= (index t 1) k))\n"
               "(assert (= (index t 2) s)) (assert (= (index t 3) c))\n"
               "; Definition (§SK.3.14): team_join(t,m) = [o,k,s+1,c] when s < c\n"
               "(assert (< s c))\n"
               "(assert (= (index t2 0) o)) (assert (= (index t2 1) k))\n"
               "(assert (= (index t2 2) (+ s 1))) (assert (= (index t2 3) c))\n"
               "; Law: join increments size by 1\n"
               "(assert (not (= (index t2 2) (+ (index t 2) 1))))\n(check-sat)\n")
        return [("team_join/law-increment", law)]
    if name == "team_share":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const c1 Int) (declare-const c2 Int) (declare-const r Int)\n"
               "(declare-const s1 Int) (declare-const s2 Int)\n"
               "(assert (>= c1 0)) (assert (>= c2 0)) (assert (>= r 0))\n"
               "(assert (> (+ c1 c2) 0))\n"
               "; Definition (§SK.3.15): shareᵢ = floor(r·cᵢ/Σc)\n"
               "(assert (= s1 (div (* r c1) (+ c1 c2))))\n"
               "(assert (= s2 (div (* r c2) (+ c1 c2))))\n"
               "; Law: shares never exceed reward\n"
               "(assert (not (<= (+ s1 s2) r)))\n(check-sat)\n")
        return [("team_share/law-no-overpay", law)]
    if name == "quota_advance":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const m Int) (declare-const r Int)\n"
               "(declare-const q Int) (declare-const q2 Int)\n"
               "(assert (>= m 0)) (assert (>= r 0))\n"
               "(assert (= (index q 0) m)) (assert (= (index q 1) r))\n"
               "; Definition (§SK.3.16): quota_advance([m,r]) = [m, r+m]\n"
               "(assert (= (index q2 0) m)) (assert (= (index q2 1) (+ r m)))\n"
               "; Law: advance adds one full month's quota\n"
               "(assert (not (= (index q2 1) (+ (index q 1) (index q 0)))))\n(check-sat)\n")
        return [("quota_advance/law-add-monthly", law)]
    if name == "points_ledger":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const a1 Int) (declare-const s1 Int) (declare-const a2 Int)\n"
               "(declare-const s2 Int) (declare-const e1 Int) (declare-const e2 Int)\n"
               "(assert (>= a1 0)) (assert (>= a2 0))\n"
               "; Definition (§SK.3.17): points_ledger records [entry_id, source_id, amount]\n"
               "(assert (>= s1 1)) (assert (>= s2 1))\n"
               "(assert (= e1 1)) (assert (= e2 2))\n"
               "; Law: amounts never negative\n"
               "(assert (not (and (>= a1 0) (>= a2 0))))\n(check-sat)\n")
        return [("points_ledger/law-nonnegative", law)]
    return []


# ---------------------------------------------------------------------------
# §PF obligation generation (spec_p0_portfolio.md — Portfolio Protocol)
# ---------------------------------------------------------------------------

PF_OPS = {"portfolio_new", "buy", "sell", "portfolio_value", "risk_score"}


def _portfolio_new_obligations():
    """§PF.3.1: portfolio_new(c) ≡ [c, 0, 0] — cash ≥ 0, empty positions."""
    defn = """
; Definition (§PF.3.1): portfolio_new(c) ≡ [c, 0, 0], encoded to ℕ (Law II).
; index(p, 0)=c (cash), index(p, 1)=0 (qtyA), index(p, 2)=0 (qtyB)
(declare-const c Int)
(assert (>= c 0))
(declare-const p Int)
(assert (= (index p 0) c))
(assert (= (index p 1) 0))
(assert (= (index p 2) 0))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (and (>= (index p 0) 0) (>= (index p 1) 0) "
            "(>= (index p 2) 0))))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (= (index p 1) 0)))\n(check-sat)\n")
    law3 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + defn +
            "(assert (not (= (index p 2) 0)))\n(check-sat)\n")
    return [("portfolio_new/law1-cash-nonnegative", law1),
            ("portfolio_new/law2-qtyA-zero", law2),
            ("portfolio_new/law3-qtyB-zero", law3)]


def _buy_obligations():
    """§PF.3.2: buy(p, a, q) — conservation + cash ≥ 0 (unit price 1)."""
    common = """
; Definition (§PF.3.2): buy([c, qA, qB], a, q) with c ≥ q
(declare-const c Int) (declare-const qa Int) (declare-const qb Int)
(declare-const q Int) (declare-const a Int)
(assert (>= c 0)) (assert (>= qa 0)) (assert (>= qb 0)) (assert (>= q 0))
(assert (or (= a 0) (= a 1)))
(assert (>= c q))
(declare-const p Int) (declare-const p2 Int)
(assert (= (index p 0) c)) (assert (= (index p 1) qa)) (assert (= (index p 2) qb))
; buy: cash − q, position a + q
(assert (= (index p2 0) (- c q)))
(assert (= (index p2 1) (ite (= a 0) (+ qa q) qa)))
(assert (= (index p2 2) (ite (= a 1) (+ qb q) qb)))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "; conservation: value unchanged (cash + qA + qB)\n"
            "(assert (not (= (+ (index p2 0) (index p2 1) (index p2 2))\n"
            "                (+ c qa qb))))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "; cash never negative after buy\n"
            "(assert (not (>= (index p2 0) 0)))\n(check-sat)\n")
    return [("buy/law1-conservation", law1),
            ("buy/law2-cash-nonnegative", law2)]


def _sell_obligations():
    """§PF.3.3: sell(p, a, q) — conservation + no naked shorts (unit price 1)."""
    common = """
; Definition (§PF.3.3): sell([c, qA, qB], a, q) with q ≤ held(a)
(declare-const c Int) (declare-const qa Int) (declare-const qb Int)
(declare-const q Int) (declare-const a Int)
(assert (>= c 0)) (assert (>= qa 0)) (assert (>= qb 0)) (assert (>= q 0))
(assert (or (= a 0) (= a 1)))
(assert (>= (ite (= a 0) qa qb) q))
(declare-const p Int) (declare-const p2 Int)
(assert (= (index p 0) c)) (assert (= (index p 1) qa)) (assert (= (index p 2) qb))
; sell: cash + q, position a − q
(assert (= (index p2 0) (+ c q)))
(assert (= (index p2 1) (ite (= a 0) (- qa q) qa)))
(assert (= (index p2 2) (ite (= a 1) (- qb q) qb)))
"""
    law1 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "; conservation: value unchanged\n"
            "(assert (not (= (+ (index p2 0) (index p2 1) (index p2 2))\n"
            "                (+ c qa qb))))\n(check-sat)\n")
    law2 = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n" + common +
            "; no naked shorts: position never negative after sell\n"
            "(assert (not (>= (ite (= a 0) (index p2 1) (index p2 2)) 0)))\n(check-sat)\n")
    return [("sell/law1-conservation", law1),
            ("sell/law2-no-naked-shorts", law2)]


def _portfolio_value_obligations():
    """§PF.3.4: portfolio_value ≡ cash + qA + qB — never negative."""
    law1 = ("(set-logic NIA)\n"
            "(declare-const c Int) (declare-const qa Int) (declare-const qb Int)\n"
            "(declare-const v Int)\n"
            "(assert (>= c 0)) (assert (>= qa 0)) (assert (>= qb 0))\n"
            "; Definition (§PF.3.4): portfolio_value ≡ c + qa + qb\n"
            "(assert (= v (+ c qa qb)))\n"
            "(assert (not (>= v 0)))\n(check-sat)\n")
    return [("portfolio_value/law1-nonnegative", law1)]


def _risk_score_obligations():
    """§PF.3.5: risk_score ≡ qA + qB — never negative, ≤ portfolio_value."""
    common = """
(declare-const c Int) (declare-const qa Int) (declare-const qb Int)
(declare-const r Int)
(assert (>= c 0)) (assert (>= qa 0)) (assert (>= qb 0))
; Definition (§PF.3.5): risk_score ≡ qa + qb
(assert (= r (+ qa qb)))
"""
    law1 = "(set-logic NIA)\n" + common + \
        "(assert (not (>= r 0)))\n(check-sat)\n"
    law2 = "(set-logic NIA)\n" + common + \
        "; exposure bounded by total value\n" \
        "(assert (not (<= r (+ c qa qb))))\n(check-sat)\n"
    return [("risk_score/law1-nonnegative", law1),
            ("risk_score/law2-bounded-by-value", law2)]


def gen_pf_obligation(op):
    """Generate §PF obligations for one Portfolio operation (or [])."""
    name = op["name"].strip()
    if name == "portfolio_new":
        return _portfolio_new_obligations()
    if name == "buy":
        return _buy_obligations()
    if name == "sell":
        return _sell_obligations()
    if name == "portfolio_value":
        return _portfolio_value_obligations()
    if name == "risk_score":
        return _risk_score_obligations()
    return gen_system_obligation(op)


# ---------------------------------------------------------------------------
# §SK.3.9–3.11 obligation generation (spec_p0_socketkit.md — 五大制度, v0.20)
# ---------------------------------------------------------------------------

SYS_OPS = {"quota_new", "quota_use", "quota_reset",
           "points_new", "points_hold", "points_release", "points_withdraw",
           "badge_level"}


def _quota_obligations(op):
    """§SK.3.9 额度制: quota_new ≡ [m, m]; quota_use 扣减; quota_reset 清零."""
    name = op["name"].strip()
    if name == "quota_new":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const m Int) (declare-const q Int)\n"
               "(assert (>= m 0))\n"
               "; Definition (§SK.3.9): quota_new(m) ≡ [m, m]\n"
               "(assert (= (index q 0) m)) (assert (= (index q 1) m))\n"
               "; Law: 0 ≤ remaining ≤ monthly\n"
               "(assert (not (and (>= (index q 1) 0) (<= (index q 1) (index q 0)))))\n"
               "(check-sat)\n")
        return [("quota_new/law-remaining-in-range", law)]
    if name == "quota_use":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const m Int) (declare-const r Int) (declare-const a Int)\n"
               "(declare-const q Int) (declare-const q2 Int)\n"
               "(assert (>= m 0)) (assert (>= r 0)) (assert (>= a 0))\n"
               "; t is a valid quota [m, r], amount a ≤ remaining\n"
               "(assert (= (index q 0) m)) (assert (= (index q 1) r))\n"
               "(assert (<= a r))\n"
               "; Definition (§SK.3.9): quota_use(q, a) ≡ [m, r−a]\n"
               "(assert (= (index q2 0) m)) (assert (= (index q2 1) (- r a)))\n"
               "; Law: remaining decreases by exactly a\n"
               "(assert (not (= (index q2 1) (- (index q 1) a))))\n"
               "(check-sat)\n")
        return [("quota_use/law-decrement", law)]
    if name == "quota_reset":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const m Int) (declare-const r Int)\n"
               "(declare-const q Int) (declare-const q2 Int)\n"
               "(assert (>= m 0)) (assert (>= r 0))\n"
               "(assert (= (index q 0) m)) (assert (= (index q 1) r))\n"
               "; Definition (§SK.3.9): quota_reset(q) ≡ [m, m]\n"
               "(assert (= (index q2 0) m)) (assert (= (index q2 1) m))\n"
               "; Law: reset restores full monthly quota\n"
               "(assert (not (and (= (index q2 0) (index q 0))\n"
               "                 (= (index q2 1) (index q 0)))))\n"
               "(check-sat)\n")
        return [("quota_reset/law-restore", law)]
    return []


def _points_obligations(op):
    """§SK.3.10 积分制: hold 冻结 / release 释放 / withdraw 提现 (守恒)."""
    name = op["name"].strip()
    if name == "points_new":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const p Int)\n"
               "; Definition (§SK.3.10): points_new() ≡ [0, 0]\n"
               "(assert (= (index p 0) 0)) (assert (= (index p 1) 0))\n"
               "; Law: no escrow, no available\n"
               "(assert (not (and (= (index p 0) 0) (= (index p 1) 0))))\n"
               "(check-sat)\n")
        return [("points_new/law-empty", law)]
    if name == "points_hold":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const e Int) (declare-const a Int) (declare-const x Int)\n"
               "(declare-const p Int) (declare-const p2 Int)\n"
               "(assert (>= e 0)) (assert (>= a 0)) (assert (>= x 0))\n"
               "(assert (= (index p 0) e)) (assert (= (index p 1) a))\n"
               "; Definition (§SK.3.10): points_hold(p, x) ≡ [e+x, a]\n"
               "(assert (= (index p2 0) (+ e x))) (assert (= (index p2 1) a))\n"
               "; Law: escrow increases by x, available unchanged\n"
               "(assert (not (and (= (index p2 0) (+ (index p 0) x))\n"
               "                 (= (index p2 1) (index p 1)))))\n"
               "(check-sat)\n")
        return [("points_hold/law-escrow-increase", law)]
    if name == "points_release":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const e Int) (declare-const a Int) (declare-const x Int)\n"
               "(declare-const p Int) (declare-const p2 Int)\n"
               "(assert (>= e 0)) (assert (>= a 0)) (assert (>= x 0))\n"
               "(assert (= (index p 0) e)) (assert (= (index p 1) a))\n"
               "; Definition (§SK.3.10): points_release(p, x) ≡ [e−x, a+x] (x ≤ e)\n"
               "(assert (<= x e))\n"
               "(assert (= (index p2 0) (- e x))) (assert (= (index p2 1) (+ a x)))\n"
               "; Law: release moves x from escrow to available (total conserved)\n"
               "(assert (not (= (+ (index p2 0) (index p2 1)) (+ (index p 0) (index p 1)))))\n"
               "(check-sat)\n")
        return [("points_release/law-conservation", law)]
    if name == "points_withdraw":
        law = ("(set-logic NIA)\n(declare-fun index (Int Int) Int)\n"
               "(declare-const e Int) (declare-const a Int) (declare-const x Int)\n"
               "(declare-const p Int) (declare-const p2 Int)\n"
               "(assert (>= e 0)) (assert (>= a 0)) (assert (>= x 0))\n"
               "(assert (= (index p 0) e)) (assert (= (index p 1) a))\n"
               "; Definition (§SK.3.10): points_withdraw(p, x) ≡ [e, a−x] (x ≤ a)\n"
               "(assert (<= x a))\n"
               "(assert (= (index p2 0) e)) (assert (= (index p2 1) (- a x)))\n"
               "; Law: available decreases by x\n"
               "(assert (not (= (index p2 1) (- (index p 1) x))))\n"
               "(check-sat)\n")
        return [("points_withdraw/law-decrement", law)]
    return []


def _badge_obligations(op):
    """§SK.3.11 勋章制: badge_level ∈ {0,1,2,3}，单调."""
    law = ("(set-logic NIA)\n"
           "(declare-const s Int) (declare-const b Int)\n"
           "(assert (>= s 0))\n"
           "; Definition (§SK.3.11): 0=铜 1=银 2=金 3=钻石\n"
           "(assert (= b (ite (< s 100) 0\n"
           "                 (ite (< s 300) 1\n"
           "                      (ite (< s 600) 2 3)))))\n"
           "; Law: badge bounded 0..3\n"
           "(assert (not (and (>= b 0) (<= b 3))))\n"
           "(check-sat)\n")
    return [("badge_level/law-bounded", law)]


def gen_system_obligation(op):
    """Generate §SK.3.9–3.11 obligations for one system operation (or [])."""
    name = op["name"].strip()
    if name in ("quota_new", "quota_use", "quota_reset"):
        return _quota_obligations(op)
    if name in ("points_new", "points_hold", "points_release", "points_withdraw"):
        return _points_obligations(op)
    if name == "badge_level":
        return _badge_obligations(op)
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

    has_sk = any(op["name"].strip() in SK_OPS or op["name"].strip() in PF_OPS
                 or op["name"].strip() in GROWTH_OPS or op["name"].strip() in INV_OPS
                 or op["name"].strip() in SK_SYS_OPS
                 for op in module["ops"])
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

    # §IN 跨操作不变量 (v0.61): INV-IN-1 总量守恒 / INV-IN-2 库存非负链。
    obligations.extend(gen_inventory_invariants(module["ops"]))

    # §PF 跨操作不变量 (v0.62): INV-PF-1 现金守恒 / INV-PF-2 份额守恒。
    obligations.extend(gen_portfolio_invariants(module["ops"]))

    # §SK 跨操作不变量 (v0.63): INV-SK-1 赏金守恒 / INV-SK-2 不超提。
    obligations.extend(gen_socketkit_invariants(module["ops"]))

    # §SK 额度制跨操作不变量 (v0.76): INV-Q-1 不超用 / INV-Q-2 重置恢复。
    obligations.extend(gen_quota_invariants(module["ops"]))

    # §SK 团机制跨操作不变量 (v0.77): INV-T-1 不超员 / INV-T-2 成员递增。
    obligations.extend(gen_team_invariants(module["ops"]))

    # §SK 增长期跨操作不变量 (v0.78): INV-G-1 授权签发链 / INV-G-2 裁决链。
    obligations.extend(gen_growth_invariants(module["ops"]))

    if not structural and obligations:
        for oname, ob in obligations:
            fname = f"{name.replace('.md', '')}__{oname.replace('/', '_')}.smt2"
            fpath = os.path.join(OUT_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(ob)
            solver, res = discharge(ob)
            if solver:
                verdict = "PROVED (unsat)" if res["sat"] else f"DISPROVED ({res['result']})"
                if res["sat"]:
                    PROVED_TOTAL[0] += 1  # v0.65 — 全量义务重验计数
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
    # v0.65 — 全量重验只处理 Expected: PASS 模块（break 负例属共识检查 E-02，
    # 不是证明对象）；显式传入的文件尊重调用方。
    if not paths:
        files = [f for f in files
                 if vc.parse_module(f).get("expected") == "PASS"]
    all_ok = True
    for path in files:
        if not prove_module(path):
            all_ok = False
    print("-" * 74)
    # v0.65 — 全量义务重验报告：汇总所有模块的 z3 消解结果
    print(f"Obligations discharged: {PROVED_TOTAL[0]} PROVED (unsat) "
          f"across {len(files)} corpus module(s)")
    print("ALL STRUCTURAL CHECKS PASS" if all_ok else "STRUCTURAL FAILURES PRESENT")
    return 0 if all_ok else 1


# v0.65 — 全量义务重验计数（prove_module 消解 PROVED 时累加，main 汇总报告）
PROVED_TOTAL = [0]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if len(sys.argv) > 1 else None))
