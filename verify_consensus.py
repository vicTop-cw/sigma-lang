#!/usr/bin/env python3
"""
verify_consensus.py — Dual-verifier consensus check (E-01 candidate).

For every module in corpus/:
  1. Python-side MD check — an INDEPENDENT implementation of the same Iron Laws
     (I fingerprint uniqueness, II encoding to ℕ, III law declaration, IV test mandatory).
  2. Rust sigma-verifier run (impl/verifier).
  3. Compare both verdicts with the module's `# Expected:` marker.

Consensus is established when both verifiers agree with each other AND with the
expected verdict for every corpus module.

Run:  python3 verify_consensus.py            # full run
      python3 verify_consensus.py corpus/arith_ok.md   # single module
"""

import os
import re
import shutil
import subprocess
import sys

# Force UTF-8 on our own stdout/stderr so emoji/Unicode output (🏆 ⊕ ⊥ …)
# survives PowerShell pipes and redirection, where the locale codec may be
# GBK/cp936 and would raise UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

NUMERIC_TYPES = {"ℕ", "ℤ", "ℚ", "ℝ", "ℂ", "Conf", "Time"}

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
VERIFIER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "impl", "verifier", "target", "debug")
ELIXIR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "impl", "elixir_rt", "sigma_verify.exs")


# ============================================================
# Python-side MD parsing (mirrors the Rust parser's contract)
# ============================================================

def parse_module(path):
    """Parse a ΣLang MD module. Returns a dict with name, expected, imports, ops."""
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]

    module = {"name": "parsed_module", "version": "0.1.0", "expected": None,
              "imports": [], "exports": [], "compat_tests": [], "ops": [], "fns": [],
              "proof_declared": False, "proof_has_model": False, "proof_has_invariant": False,
              "guarantee_declared": False, "guarantee_metric": None,
              "guarantee_threshold": None, "guarantee_dataset": None,
              "determinism_declared": False, "determinism_precision": None,
              "determinism_rounding": None, "determinism_sort_stability": None,
              "signature_declared": False, "signature_signer": None,
              "signature_pubkey_fp": None, "signature_algorithm": None,
              "signature_value": None, "shadow_targets": [],
              "timing_contract": None, "capabilities": []}
    in_imports = False
    in_exports = False
    in_compat_tests = False
    in_proof = False
    in_guarantee = False
    in_determinism = False
    in_signature = False
    in_shadowing = False
    in_timing = False
    in_capabilities = False
    in_fence = False
    blk = None  # current pending block: dict(name, sig, fp, laws, tests)

    def flush():
        # Mirror the Rust flush_block semantics: a block with a fingerprint is an
        # operation (op); a signed, fingerprint-less block is a declared function
        # (e.g. an encoding); an unsigned block is discarded.
        nonlocal blk
        if blk is not None:
            if blk["fp"] is not None:
                module["ops"].append(blk)
            elif blk["sig"]:
                module["fns"].append(blk)
            blk = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^# Module:\s*(.+)$", line)
        if m:
            module["name"] = m.group(1).strip()
            continue
        m = re.match(r"^# Version:\s*(.+)$", line)
        if m:
            module["version"] = m.group(1).strip()
            continue
        m = re.match(r"^# Expected:\s*(.+)$", line)
        if m:
            module["expected"] = m.group(1).strip()
            continue
        if line == "## Imports":
            in_imports = True
            continue
        if line == "## Exports":
            in_exports = True
            in_imports = False
            continue
        if line == "## Compat Tests":
            in_compat_tests = True
            in_imports = False
            in_exports = False
            continue
        if line == "## Proof":
            in_proof = True
            module["proof_declared"] = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            continue
        if line == "## Guarantee":
            in_guarantee = True
            module["guarantee_declared"] = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            continue
        if line == "## Determinism":
            in_determinism = True
            module["determinism_declared"] = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            in_guarantee = False
            continue
        if line == "## Signature":
            in_signature = True
            module["signature_declared"] = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            in_guarantee = False
            in_determinism = False
            in_shadowing = False
            continue
        if line == "## Shadowing":
            in_shadowing = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            in_guarantee = False
            in_determinism = False
            in_signature = False
            continue
        if line == "## Timing":
            in_timing = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            in_guarantee = False
            in_determinism = False
            in_signature = False
            in_shadowing = False
            continue
        if line == "## Capabilities":
            in_capabilities = True
            in_imports = False
            in_exports = False
            in_compat_tests = False
            in_proof = False
            in_guarantee = False
            in_determinism = False
            in_signature = False
            in_shadowing = False
            in_timing = False
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_timing:
            if line.startswith("## ") or line.startswith("### "):
                in_timing = False  # next heading ends the block; fall through
            else:
                m = re.match(r"^(max_latency|max_retries|timeout_budget|deadline_miss_policy):\s*(.*)$", line)
                if m:
                    key, val = m.group(1), m.group(2).strip()
                    if module["timing_contract"] is None:
                        module["timing_contract"] = {}
                    module["timing_contract"][key] = val
                continue
        if in_capabilities:
            if line.startswith("## ") or line.startswith("### "):
                in_capabilities = False  # next heading ends the block; fall through
            else:
                for token in line.split(","):
                    t = token.strip()
                    if t and t != "```" and t not in module["capabilities"]:
                        module["capabilities"].append(t)
                continue
        if in_shadowing:
            if line.startswith("## ") or line.startswith("### "):
                in_shadowing = False  # next heading ends the block; fall through
            else:
                m = re.match(r"^shadow\s+(\S+)", line)
                if m:
                    target = m.group(1).split("→")[0].strip()
                    if target:
                        module["shadow_targets"].append(target)
                continue
        if in_signature:
            if line.startswith("## ") or line.startswith("### "):
                in_signature = False  # next heading ends the block; fall through
            else:
                m = re.match(r"^(signer|pubkey_fp|algorithm|signature):\s*(.*)$", line)
                if m:
                    key = "value" if m.group(1) == "signature" else m.group(1)
                    module[f"signature_{key}"] = m.group(2).strip()
                continue
        if in_determinism:
            if line.startswith("## ") or line.startswith("### "):
                in_determinism = False  # next heading ends the block; fall through
            else:
                m = re.match(r"^(precision|rounding|sort_stability):\s*(.*)$", line)
                if m:
                    key, val = m.group(1), m.group(2).strip()
                    module[f"determinism_{key}"] = val
                continue
        if in_guarantee:
            if line.startswith("## ") or line.startswith("### "):
                in_guarantee = False  # next heading ends the block; fall through
            else:
                m = re.match(r"^(metric|threshold|dataset):\s*(.*)$", line)
                if m:
                    key, val = m.group(1), m.group(2).strip()
                    module[f"guarantee_{key}"] = val
                continue
        if in_proof:
            if line.startswith("## ") or line.startswith("### "):
                if line == "### Model":
                    module["proof_has_model"] = True
                    continue
                if line == "### Invariant":
                    module["proof_has_invariant"] = True
                    continue
                if line == "### Trusted":
                    continue
                # Any other heading exits proof mode; fall through.
                in_proof = False
            else:
                continue  # proof content lines are not parsed
        if in_compat_tests:
            if not in_fence and (line.startswith("## ") or line.startswith("### ")):
                # A new heading ends the compat-tests section; fall through.
                in_compat_tests = False
            elif line.startswith("|"):
                if line.startswith("|-") or "Input" in line or "Output" in line or "Expected" in line:
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) >= 2:
                    module["compat_tests"].append((cells[0], cells[1]))
                continue
            else:
                continue
        if in_exports:
            if not (line.startswith("## ") or line.startswith("### ")):
                # Collect comma/whitespace-separated exported names.
                for tok in re.split(r"[,\s]+", line):
                    t = tok.strip()
                    if t and t != "```":
                        module["exports"].append(t)
                continue
            # A new heading ends the exports section; fall through.
            in_exports = False
        if in_imports:
            m = re.match(r"^import\s+(\S+)", line)
            if m:
                module["imports"].append(m.group(1).strip().rstrip(","))
                continue
            # Non-import line: the imports section ends here; reprocess this
            # line below (it is usually a heading that starts a new block).
            in_imports = False

        # Markdown headings outside fences are block boundaries.
        if not in_fence and (line.startswith("## ") or line.startswith("### ")):
            if line in ("### Signature", "### Laws", "## Laws", "### Tests", "## Tests"):
                # Sub-section markers switch modes inside the current block.
                if blk is not None:
                    if "Laws" in line:
                        blk["mode"] = "laws"
                    elif "Tests" in line:
                        blk["mode"] = "tests"
                    else:
                        blk["mode"] = "sig"
                continue
            flush()
            heading = line.lstrip("#").strip()
            heading = re.sub(r"^Operation:\s*", "", heading).strip()
            blk = {"name": heading, "sig": "", "fp": None, "laws": [], "tests": [],
                   "mode": "sig", "has_pre": False, "has_post": False,
                   "pre": None, "post": None}
            continue

        if in_fence and line in ("## Laws", "## Tests"):
            if blk is not None:
                blk["mode"] = "laws" if "Laws" in line else "tests"
            continue

        if blk is None:
            continue

        m = re.match(r"^Fingerprint:\s*(.+)$", line)
        if m:
            blk["fp"] = m.group(1).strip()
            continue
        if line.startswith("# Pre:"):
            blk["has_pre"] = True
            blk["pre"] = line[len("# Pre:"):].strip()
            continue
        if line.startswith("# Post:"):
            blk["has_post"] = True
            blk["post"] = line[len("# Post:"):].strip()
            continue
        if blk["mode"] == "tests" and line.startswith("|"):
            if line.startswith("|-") or "Input" in line or "Output" in line or "Expected" in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                blk["tests"].append((cells[0], cells[1]))
            continue
        # Signature detection must run BEFORE the `≡`-in-line law heuristic:
        # an operator whose glyph is `≡` (e.g. `≡ : ℕ × ℕ → ℕ`) would otherwise
        # be swallowed as a law line and lose its signature/name.
        if not blk["sig"] and ":" in line and "→" in line and not line.startswith("|"):
            blk["sig"] = line
            name = line.split(":", 1)[0].strip()
            if name and not re.search(r"\s", name):
                blk["name"] = name
            continue
        if blk["mode"] == "laws" or line.startswith(("∀", "∃")) or "≡" in line:
            if "|" not in line:
                blk["laws"].append(line)
            continue

    flush()
    return module


# ============================================================
# Python-side Iron Law checks (independent of the Rust verifier)
# ============================================================

def return_type(sig):
    """The semantic class = the type after the final →."""
    if not sig:
        return "Any"
    return sig.split("→")[-1].strip()


def check_python(module):
    """Apply Law I/II/III/IV. Returns (passed: bool, violations: list[str])."""
    violations = []

    # Law I — fingerprint uniqueness (within module).
    seen = set()
    for op in module["ops"]:
        if op["fp"] is None:
            violations.append(f"MissingFingerprint({op['name']})")
            continue
        if op["fp"] in seen:
            violations.append(f"FingerprintConflict({op['name']}, {op['fp']})")
        seen.add(op["fp"])

    # Law II — encoding to ℕ for non-numeric return types.
    encoders = [
        fn["name"] + " " + fn["sig"]
        for fn in module["fns"]
        if "encode" in (fn["name"] or "").lower()
    ]
    for op in module["ops"]:
        rt = return_type(op["sig"])
        if rt in NUMERIC_TYPES:
            continue
        has_enc = any("encode" in e and rt in e for e in encoders)
        if not has_enc:
            violations.append(f"MissingEncoding({op['name']})")

    # Law III — law declaration.
    for op in module["ops"]:
        if not op["laws"]:
            violations.append(f"NoLawsDeclared({op['name']})")

    # Law IV — test mandatory.
    for op in module["ops"]:
        if not op["tests"]:
            violations.append(f"NoTestsDefined({op['name']})")

    # E-02 (promoted 2026-08-01) — negative test mandatory:
    # every op needs ≥1 test whose expected output starts with ⊥.
    for op in module["ops"]:
        if not any(exp.strip().startswith("⊥") for _, exp in op["tests"]):
            violations.append(f"NoNegativeTest({op['name']})")

    # E-03 (promoted 2026-08-01) — test portability:
    # every test's expected output must be semantically structured —
    # an error (⊥-prefixed) or a parseable literal — never an
    # implementation-specific format (float string, Map rendering, …).
    for op in module["ops"]:
        for inp, exp in op["tests"]:
            e = exp.strip()
            if not (e.startswith("⊥") or parse_val(e) is not None):
                violations.append(f"UnportableAssertion({op['name']}, {exp})")

    # E-04 (promoted 2026-08-01) — export completeness:
    # `## Exports` must match defined symbols (no ghost, no hidden).
    # Modules without an Exports block are not checked (v0.1 policy).
    exports = module["exports"]
    if exports:
        defined_names = {op["name"] for op in module["ops"]}
        for exp in exports:
            if exp not in defined_names:
                violations.append(f"GhostExport({exp})")
        for op in module["ops"]:
            if op["name"] not in exports:
                violations.append(f"HiddenExport({op['name']})")

    # E-05 (promoted 2026-08-01) — compatibility proof:
    # `## Compat Tests` (previous version's canonical suite) must all pass,
    # otherwise the "backward compatible" claim is rejected.
    for inp, exp in module["compat_tests"]:
        result = eval_compat_test(inp, exp)
        if result is not True:
            violations.append(f"CompatTestFailed({inp}): {result}")

    # P-01 (spec_top_proofs.md) — proof-carrying spec structure:
    # a module declaring `## Proof` must have a `### Model` and a `### Invariant`,
    # and every operation must declare Pre and Post together (or neither).
    if module["proof_declared"]:
        if not module["proof_has_model"]:
            violations.append(f"MissingModel({module['name']})")
        if not module["proof_has_invariant"]:
            violations.append(f"MissingInvariant({module['name']})")
        for op in module["ops"]:
            if op["has_pre"] != op["has_post"]:
                violations.append(f"IncompleteContract({op['name']})")

    # E-06 (promoted 2026-08-01) — internal consistency adjudication:
    # test expected value must match the operation's declared return-type shape
    # (numeric return → numeric expectation, container return → list expectation).
    for op in module["ops"]:
        rt = return_type(op["sig"])
        numeric = rt in NUMERIC_TYPES
        container = any(k in rt for k in ("List", "Tensor", "Map", "Seq", "Fmap"))
        if not numeric and not container:
            continue  # unknown shape — cannot judge
        for inp, exp in op["tests"]:
            e = exp.strip()
            if e.startswith("⊥"):
                continue  # error path — no value shape to check
            val = parse_val(e)
            if val is None:
                continue  # unparseable — E-03 portability already flags
            kind = val[0]  # "num", "fnum", or "list"
            if (container and not numeric and kind in ("num", "fnum")) or \
               (numeric and not container and kind == "list"):
                violations.append(f"SignatureMismatch({op['name']}, {exp})")

    # E-09 (promoted 2026-08-01) — probabilistic guarantee: a prediction op must
    # declare a performance floor (metric, threshold, dataset) well-formed. The
    # Verifier certifies the declaration only; production conformance is runtime
    # monitoring's job.
    if module["guarantee_declared"]:
        metric = module.get("guarantee_metric") or ""
        if metric not in ("accuracy", "f1", "brier"):
            violations.append(f"MalformedGuarantee(invalid metric: {metric!r})")
        try:
            thr = float(module.get("guarantee_threshold") or "")
            if not (0.0 <= thr <= 1.0):
                violations.append("MalformedGuarantee(threshold out of range 0..=1)")
        except ValueError:
            violations.append("MalformedGuarantee(threshold not a number)")
        if not (module.get("guarantee_dataset") or "").strip():
            violations.append("MalformedGuarantee(missing dataset)")

    # E-10 (promoted 2026-08-01) — evaluation determinism: a module declaring
    # `## Determinism` must declare numeric precision (positive integer),
    # rounding (round|floor|ceil|trunc), and sort_stability (true|false).
    # Extends Law VIII (temporal determinism) to numeric evaluation.
    if module["determinism_declared"]:
        p = module.get("determinism_precision") or ""
        try:
            if int(p) < 1:
                violations.append(f"MalformedDeterminism(invalid precision: {p!r})")
        except ValueError:
            violations.append(f"MalformedDeterminism(invalid precision: {p!r})")
        r = module.get("determinism_rounding") or ""
        if r not in ("round", "floor", "ceil", "trunc"):
            violations.append(f"MalformedDeterminism(invalid rounding: {r!r})")
        s = module.get("determinism_sort_stability") or ""
        if s not in ("true", "false"):
            violations.append(f"MalformedDeterminism(invalid sort_stability: {s!r})")

    # E-08 S-01 Level 1 (2026-08-01) — package signature: a module declaring
    # `## Signature` must provide a well-formed signer, pubkey_fp (sha256:),
    # algorithm (ed25519), and a non-empty signature. Modules without a
    # signature still verify (backward compatible — Law VI).
    if module["signature_declared"]:
        if not (module.get("signature_signer") or "").strip():
            violations.append("MalformedSignature(missing signer)")
        fp = module.get("signature_pubkey_fp") or ""
        if not (fp.startswith("sha256:") and len(fp) > len("sha256:")):
            violations.append(f"MalformedSignature(invalid pubkey_fp: {fp!r})")
        if (module.get("signature_algorithm") or "") != "ed25519":
            violations.append(
                f"MalformedSignature(invalid algorithm: {module.get('signature_algorithm')!r})"
            )
        if not (module.get("signature_value") or "").strip():
            violations.append("MalformedSignature(missing signature)")

    # §S Shadowing & Binding Discipline (2026-08-01):
    # - DuplicateSymbol: a module must not define the same symbol name twice
    #   (Meta-Rule 2 / No Synonyms, §S R3 determinism).
    # - ShadowTargetMissing: every `## Shadowing` declaration must reference a
    #   symbol that actually exists (§S R1 explicit declaration).
    # - OpaqueShadowAttempt: math-domain symbols are Opaque-class and must not
    #   be shadowed (§S R5).
    OPAQUE_MATH = {"⊕", "⊗", "⊖", "⊘", "⊙", "≡", "≥", "≤", "∈", "ℕ", "ℤ", "ℚ", "ℝ"}
    seen_names = set()
    for op in module["ops"]:
        if op["name"] in seen_names:
            violations.append(f"DuplicateSymbol({op['name']})")
        seen_names.add(op["name"])
    warnings = []
    for target in module["shadow_targets"]:
        # §C constant fingerprints (0xK0xx math / 0xQ0xx physics) are Opaque
        # class too (§S.3.1 core-constant) — shadow attempts are violations.
        if target in OPAQUE_MATH or target.startswith(("0xK", "0xQ")):
            violations.append(f"OpaqueShadowAttempt({target})")
    defined = {op["name"] for op in module["ops"]}
    for target in module["shadow_targets"]:
        # Qualified names (e.g. finance.base.Δ) reference external-package
        # symbols; v0.1 cannot resolve them — only local names are checked.
        if "." in target:
            continue
        if target in defined:
            # R7: declared Free-class shadow — verification passes, but the
            # report flags a warning (spec_top_rules.md §S R7 / S-11).
            warnings.append(f"R7-warning: free-class shadow of {target}")
        elif target not in defined:
            violations.append(f"ShadowTargetMissing({target})")
    module["shadow_warnings"] = warnings

    return (len(violations) == 0, violations)


# ============================================================
# Minimal canonical-test evaluator (tensor ops subset)
# Mirrors the Rust/Elixir evaluator so E-05 verdicts agree.
# ============================================================

def eval_compat_test(inp, exp):
    """Evaluate a compat test; returns True on pass, else a failure string."""
    expect_err = exp.strip().startswith("⊥")
    v = eval_expr(inp)
    if isinstance(v, str):  # evaluation error
        return True if expect_err else f"evaluation failed: {v}"
    if expect_err:
        return f"expected error, got {fmt_val(v)}"
    ev = parse_val(exp)
    if ev is None:
        return f"unparseable expectation: {exp}"
    return True if ev == v else f"expected {fmt_val(ev)}, got {fmt_val(v)}"


# §C Real-World Constants (spec_top_rules.md §C) — resolvable by fingerprint.
# Values are the reference (non-normative precision) from the spec catalog,
# held as IEEE-754 doubles so Python/Rust/Elixir float handling agrees.
CONSTANTS = {
    # C.1 Mathematical (0xK0xx)
    "0xK001": ("fnum", 3.141592653589793),  # π
    "0xK002": ("fnum", 2.718281828459045),  # e
    "0xK003": ("fnum", 1.618033988749895),  # φ
    "0xK004": ("fnum", 0.5772156649015329),  # γ
    "0xK005": ("fnum", 1.4142135623730951),  # √2
    "0xK006": ("fnum", 0.6931471805599453),  # ln2
    "0xK007": ("fnum", 0.915965594177219),  # G_𝒦
    "0xK008": ("fnum", 1.2020569031595942),  # ζ3
    "0xK009": ("fnum", 4.66920160910299),  # δ_ℱ
    # C.2 Physics (0xQ0xx)
    "0xQ001": ("num", 299792458),  # c (exact SI integer)
    "0xQ002": ("fnum", 6.62607015e-34),  # h
    "0xQ003": ("fnum", 1.054571817e-34),  # ℏ
    "0xQ004": ("fnum", 6.67430e-11),  # G_𝔫
    "0xQ005": ("fnum", 8.8541878128e-12),  # ε₀
    "0xQ006": ("fnum", 1.25663706212e-6),  # μ₀
    "0xQ007": ("fnum", 1.602176634e-19),  # e
    "0xQ008": ("fnum", 1.380649e-23),  # k_B
    "0xQ009": ("fnum", 6.02214076e23),  # N_A
    "0xQ00A": ("fnum", 8.314462618),  # R
    "0xQ00B": ("fnum", 9.1093837015e-31),  # mₑ
    "0xQ00C": ("fnum", 1.67262192369e-27),  # mₚ
    "0xQ00D": ("fnum", 7.2973525693e-3),  # α (fine-structure constant)
    "0xQ00E": ("fnum", 5.670374419e-8),  # σ (Stefan–Boltzmann)
    "0xQ00F": ("fnum", 9.80665),  # g₀ (standard gravity, exact SI)
    "0xQ010": ("fnum", 10973731.568160),  # R_∞ (Rydberg constant)
}


def eval_expr(s):
    """Evaluate an expression: literal, ⊕, ⊗, index(...), I₂. Returns a value
    tuple or an error string."""
    s = s.strip()
    if s in CONSTANTS:
        return CONSTANTS[s]
    if "where shape mismatch" in s:
        return "ShapeError"
    if "⊕" in s:
        a, b = s.split("⊕", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return elemwise_add(va, vb)
    if "⊗" in s:
        a, b = s.split("⊗", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return mat_mul(va, vb)
    if "⊖" in s:
        a, b = s.split("⊖", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return elemwise_sub(va, vb)
    if "⊘" in s:
        a, b = s.split("⊘", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return elemwise_div(va, vb)
    if "⊙" in s:
        a, b = s.split("⊙", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return elemwise_mul(va, vb)
    if "≡" in s:
        a, b = s.split("≡", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return value_eq(va, vb)
    if "≥" in s:
        a, b = s.split("≥", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return value_cmp(va, vb, "ge")
    if "≤" in s:
        a, b = s.split("≤", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return value_cmp(va, vb, "le")
    if "∈" in s:
        a, b = s.split("∈", 1)
        va, vb = eval_expr(a), eval_expr(b)
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        return value_in(va, vb)
    if s.startswith("index(") and s.endswith(")"):
        inner = s[len("index("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad index args: {inner}"
        tv = eval_expr(parts[0])
        iv = parse_val(parts[1])
        if isinstance(tv, str):
            return tv
        if iv is None:
            return f"bad index: {parts[1]}"
        return index_into(tv, iv)
    # §SK — SocketKit Protocol operations (spec_p0_socketkit.md §SK.3).
    # Real function calls, not spec-expression aliases: the corpus tests now
    # exercise the same task_create/accept_task/task_submit/task_accept/
    # review_merge/contribution_score/credit_score semantics the reference
    # implementations (sigma_core.py / sk.rs / sigma_verify.exs) provide, so
    # the consensus gate verifies app behavior itself.
    if s.startswith("task_create(") and s.endswith(")"):
        inner = s[len("task_create("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad task_create args: {inner}"
        va = eval_expr(parts[0].strip())
        vb = eval_expr(parts[1].strip())
        if isinstance(va, str):
            return va
        if isinstance(vb, str):
            return vb
        if va[0] != "num" or vb[0] != "num":
            return "TypeError"
        if vb[1] < 0:  # Bounty : Type ≝ ℕ
            return "BountyErr"
        # [author, bounty, 0=open, 0=unclaimed]
        return ("list", [("num", va[1]), ("num", vb[1]), ("num", 0), ("num", 0)])
    if s.startswith("accept_task(") and s.endswith(")"):
        inner = s[len("accept_task("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad accept_task args: {inner}"
        vt = eval_expr(parts[0].strip())
        vh = eval_expr(parts[1].strip())
        if isinstance(vt, str):
            return vt
        if isinstance(vh, str):
            return vh
        if vt[0] != "list" or len(vt[1]) != 4 or vh[0] != "num":
            return "TypeError"
        task = vt[1]
        if task[2] != ("num", 0):  # status 0 = open
            return "StateError"
        return ("list", [task[0], task[1], ("num", 1), ("num", vh[1])])
    if s.startswith("task_submit(") and s.endswith(")"):
        inner = s[len("task_submit("):-1]
        vt = eval_expr(inner.strip())
        if isinstance(vt, str):
            return vt
        if vt[0] != "list" or len(vt[1]) != 4:
            return "TypeError"
        task = vt[1]
        if task[2] != ("num", 1):  # status 1 = in_progress
            return "StateError"
        return ("list", [task[0], task[1], ("num", 2), task[3]])
    if s.startswith("task_accept(") and s.endswith(")"):
        inner = s[len("task_accept("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad task_accept args: {inner}"
        vt = eval_expr(parts[0].strip())
        vc = eval_expr(parts[1].strip())
        if isinstance(vt, str):
            return vt
        if isinstance(vc, str):
            return vc
        if vt[0] != "list" or len(vt[1]) != 4 or vc[0] != "num":
            return "TypeError"
        task = vt[1]
        if task[2] != ("num", 2):  # status 2 = pending_review
            return "StateError"
        if vc[1] != task[0][1]:  # INV-4: only the author may accept
            return "AuthError"
        return ("list", [task[0], task[1], ("num", 3), task[3]])
    if s.startswith("review_merge(") and s.endswith(")"):
        inner = s[len("review_merge("):-1]
        v = eval_expr(inner.strip())
        if isinstance(v, str):
            return v
        if v[0] != "list":
            return "TypeError"
        w_accept = w_reject = 0
        for o in v[1]:
            if o[0] != "list" or len(o[1]) != 3:
                return "ShapeError"
            vote = o[1][1][1]
            weight = o[1][2][1]
            if vote == 1:
                w_accept += weight
            elif vote == 0:
                w_reject += weight
            else:
                return "TypeError"
        return ("num", 1 if w_accept >= w_reject else 0)
    if s.startswith("contribution_score(") and s.endswith(")"):
        inner = s[len("contribution_score("):-1]
        v = eval_expr(inner.strip())
        if isinstance(v, str):
            return v
        if v[0] != "list":
            return "TypeError"
        total = 0
        for a in v[1]:
            if a[0] != "list" or len(a[1]) != 3:
                return "ShapeError"
            total += a[1][2][1]
        return ("num", max(0, total))
    if s.startswith("credit_score(") and s.endswith(")"):
        inner = s[len("credit_score("):-1]
        v = eval_expr(inner.strip())
        if isinstance(v, str):
            return v
        if v[0] != "list":
            return "TypeError"
        credit = 100
        for e in v[1]:
            if e[0] != "list" or len(e[1]) != 2:
                return "ShapeError"
            kind = e[1][0][1]
            count = e[1][1][1]
            if kind == 0:  # complete: +5 per count
                credit += 5 * count
            elif kind == 1:  # breach: ×0.7 per count (×7 ÷10, floor)
                for _ in range(count):
                    credit = (credit * 7) // 10
            else:
                return "TypeError"
        return ("num", max(0, credit))
    # §PF — Portfolio Protocol operations (spec_p0_portfolio.md §PF.3).
    # Second novel domain: finance. Real function calls, mirrors
    # sigma_core.py §PF so the consensus gate verifies investment semantics.
    if s.startswith("portfolio_new(") and s.endswith(")"):
        inner = s[len("portfolio_new("):-1]
        vc = eval_expr(inner.strip())
        if isinstance(vc, str):
            return vc
        if vc[0] != "num":
            return "TypeError"
        if vc[1] < 0:  # Cash : Type ≝ ℕ
            return "TypeError"
        return ("list", [("num", vc[1]), ("num", 0), ("num", 0)])
    if s.startswith("buy(") and s.endswith(")"):
        inner = s[len("buy("):-1]
        parts = split_all_top_level(inner, ",")
        if len(parts) < 3:
            return f"bad buy args: {inner}"
        vp = eval_expr(parts[0].strip())
        va = eval_expr(parts[1].strip())
        vq = eval_expr(parts[2].strip())
        if isinstance(vp, str):
            return vp
        if isinstance(va, str):
            return va
        if isinstance(vq, str):
            return vq
        if vp[0] != "list" or len(vp[1]) != 3 or va[0] != "num" or vq[0] != "num":
            return "TypeError"
        asset, qty = va[1], vq[1]
        if asset not in (0, 1):
            return "UnknownAsset"
        cash, qA, qB = vp[1]
        if cash[1] < qty:
            return "InsufficientFunds"
        if asset == 0:
            return ("list", [("num", cash[1] - qty), ("num", qA[1] + qty), qB])
        return ("list", [("num", cash[1] - qty), qA, ("num", qB[1] + qty)])
    if s.startswith("sell(") and s.endswith(")"):
        inner = s[len("sell("):-1]
        parts = split_all_top_level(inner, ",")
        if len(parts) < 3:
            return f"bad sell args: {inner}"
        vp = eval_expr(parts[0].strip())
        va = eval_expr(parts[1].strip())
        vq = eval_expr(parts[2].strip())
        if isinstance(vp, str):
            return vp
        if isinstance(va, str):
            return va
        if isinstance(vq, str):
            return vq
        if vp[0] != "list" or len(vp[1]) != 3 or va[0] != "num" or vq[0] != "num":
            return "TypeError"
        asset, qty = va[1], vq[1]
        if asset not in (0, 1):
            return "UnknownAsset"
        cash, qA, qB = vp[1]
        held = qA[1] if asset == 0 else qB[1]
        if qty > held:
            return "InsufficientShares"
        if asset == 0:
            return ("list", [("num", cash[1] + qty), ("num", qA[1] - qty), qB])
        return ("list", [("num", cash[1] + qty), qA, ("num", qB[1] - qty)])
    if s.startswith("portfolio_value(") and s.endswith(")"):
        inner = s[len("portfolio_value("):-1]
        vp = eval_expr(inner.strip())
        if isinstance(vp, str):
            return vp
        if vp[0] != "list" or len(vp[1]) != 3:
            return "TypeError"
        cash, qA, qB = vp[1]
        return ("num", cash[1] + qA[1] + qB[1])
    if s.startswith("risk_score(") and s.endswith(")"):
        inner = s[len("risk_score("):-1]
        vp = eval_expr(inner.strip())
        if isinstance(vp, str):
            return vp
        if vp[0] != "list" or len(vp[1]) != 3:
            return "TypeError"
        _, qA, qB = vp[1]
        return ("num", qA[1] + qB[1])
    # §SK.3.9 额度制 quota — 每月额度 / 扣减 / 月底清零.
    if s.startswith("quota_new(") and s.endswith(")"):
        inner = s[len("quota_new("):-1]
        vm = eval_expr(inner.strip())
        if isinstance(vm, str):
            return vm
        if vm[0] != "num":
            return "TypeError"
        if vm[1] < 0:
            return "TypeError"
        return ("list", [("num", vm[1]), ("num", vm[1])])
    if s.startswith("quota_use(") and s.endswith(")"):
        inner = s[len("quota_use("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad quota_use args: {inner}"
        vq = eval_expr(parts[0].strip())
        va = eval_expr(parts[1].strip())
        if isinstance(vq, str):
            return vq
        if isinstance(va, str):
            return va
        if vq[0] != "list" or len(vq[1]) != 2 or va[0] != "num":
            return "TypeError"
        monthly, remaining = vq[1]
        if va[1] > remaining[1]:
            return "QuotaExhausted"
        return ("list", [monthly, ("num", remaining[1] - va[1])])
    if s.startswith("quota_reset(") and s.endswith(")"):
        inner = s[len("quota_reset("):-1]
        vq = eval_expr(inner.strip())
        if isinstance(vq, str):
            return vq
        if vq[0] != "list" or len(vq[1]) != 2:
            return "TypeError"
        monthly, _ = vq[1]
        return ("list", [monthly, monthly])
    # §SK.3.10 积分制 points — 托管 / 释放 / 提现.
    if s == "points_new()":
        return ("list", [("num", 0), ("num", 0)])
    if s.startswith("points_hold(") and s.endswith(")"):
        inner = s[len("points_hold("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad points_hold args: {inner}"
        vp = eval_expr(parts[0].strip())
        vx = eval_expr(parts[1].strip())
        if isinstance(vp, str):
            return vp
        if isinstance(vx, str):
            return vx
        if vp[0] != "list" or len(vp[1]) != 2 or vx[0] != "num":
            return "TypeError"
        escrow, available = vp[1]
        return ("list", [("num", escrow[1] + vx[1]), available])
    if s.startswith("points_release(") and s.endswith(")"):
        inner = s[len("points_release("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad points_release args: {inner}"
        vp = eval_expr(parts[0].strip())
        vx = eval_expr(parts[1].strip())
        if isinstance(vp, str):
            return vp
        if isinstance(vx, str):
            return vx
        if vp[0] != "list" or len(vp[1]) != 2 or vx[0] != "num":
            return "TypeError"
        escrow, available = vp[1]
        if vx[1] > escrow[1]:
            return "InsufficientEscrow"
        return ("list", [("num", escrow[1] - vx[1]), ("num", available[1] + vx[1])])
    if s.startswith("points_withdraw(") and s.endswith(")"):
        inner = s[len("points_withdraw("):-1]
        parts = split_top_level(inner, ",")
        if parts is None or len(parts) < 2:
            return f"bad points_withdraw args: {inner}"
        vp = eval_expr(parts[0].strip())
        vx = eval_expr(parts[1].strip())
        if isinstance(vp, str):
            return vp
        if isinstance(vx, str):
            return vx
        if vp[0] != "list" or len(vp[1]) != 2 or vx[0] != "num":
            return "TypeError"
        escrow, available = vp[1]
        if vx[1] > available[1]:
            return "InsufficientPoints"
        return ("list", [escrow, ("num", available[1] - vx[1])])
    # §SK.3.11 勋章制 badge_level — 0=铜 1=银 2=金 3=钻石.
    if s.startswith("badge_level(") and s.endswith(")"):
        inner = s[len("badge_level("):-1]
        vs = eval_expr(inner.strip())
        if isinstance(vs, str):
            return vs
        if vs[0] != "num":
            return "TypeError"
        score = vs[1]
        if score < 100:
            return ("num", 0)
        if score < 300:
            return ("num", 1)
        if score < 600:
            return ("num", 2)
        return ("num", 3)
    # §SK.3.12 核验师签发勋章 badge_issue — v ≥ 1000 授权核验师.
    if s.startswith("badge_issue(") and s.endswith(")"):
        inner = s[len("badge_issue("):-1]
        parts = split_all_top_level(inner, ",")
        if len(parts) < 3:
            return f"bad badge_issue args: {inner}"
        vv = eval_expr(parts[0].strip())
        vu = eval_expr(parts[1].strip())
        vsc = eval_expr(parts[2].strip())
        if isinstance(vv, str):
            return vv
        if isinstance(vu, str):
            return vu
        if isinstance(vsc, str):
            return vsc
        if vv[0] != "num" or vu[0] != "num" or vsc[0] != "num":
            return "TypeError"
        if vv[1] < 1000:  # 授权核验师编号段
            return "AuthError"
        score = vsc[1]
        if score < 100:
            lvl = 0
        elif score < 300:
            lvl = 1
        elif score < 600:
            lvl = 2
        else:
            lvl = 3
        return ("list", [("num", vv[1]), ("num", vu[1]), ("num", lvl)])
    # §SK.3.13 督导处理纠纷 dispute_review — 加权支持 ≥ 加权驳回.
    if s.startswith("dispute_review(") and s.endswith(")"):
        inner = s[len("dispute_review("):-1]
        v = eval_expr(inner.strip())
        if isinstance(v, str):
            return v
        if v[0] != "list":
            return "TypeError"
        w_support = w_reject = 0
        for e in v[1]:
            if e[0] != "list" or len(e[1]) != 3:
                return "ShapeError"
            side = e[1][1][1]
            weight = e[1][2][1]
            if side == 1:
                w_support += weight
            elif side == 0:
                w_reject += weight
            else:
                return "TypeError"
        return ("num", 1 if w_support >= w_reject else 0)
    if s == "I₂":
        return ("list", [("list", [("num", 1), ("num", 0)]),
                         ("list", [("num", 0), ("num", 1)])])
    v = parse_val(s)
    if v is None:
        # Unparseable literal (e.g. "+5", "1e3") → error string, mirroring
        # Rust's Err("unparseable: …") and Elixir's {:error, "unparseable: …"}.
        return f"unparseable: {s}"
    return v


def elemwise_add(a, b):
    if a[0] == "num" and b[0] == "num":
        return ("num", a[1] + b[1])
    if a[0] in ("num", "fnum") and b[0] in ("num", "fnum"):
        return ("fnum", float(a[1]) + float(b[1]))
    if a[0] == "list" and b[0] == "list":
        if len(a[1]) != len(b[1]):
            return "ShapeError"
        out = []
        for x, y in zip(a[1], b[1]):
            r = elemwise_add(x, y)
            if isinstance(r, str):
                return r
            out.append(r)
        return ("list", out)
    return "ShapeError"


def mat_mul(a, b):
    if a[0] == "list" and b[0] == "list":
        out = []
        for row in a[1]:
            if row[0] != "list":
                return "ShapeError"
            cells = row[1]
            if len(cells) != len(b[1]):
                return "ShapeError"
            acc = 0
            is_float = False
            for c, v in zip(cells, b[1]):
                if c[0] not in ("num", "fnum") or v[0] not in ("num", "fnum"):
                    return "TypeError"
                if c[0] == "fnum" or v[0] == "fnum":
                    is_float = True
                acc += float(c[1]) * float(v[1])
            out.append(("fnum", acc) if is_float else ("num", int(acc)))
        return ("list", out)
    return "ShapeError"


def elemwise_sub(a, b):
    """Element-wise subtraction (⊖), mirroring elemwise_add."""
    if a[0] == "num" and b[0] == "num":
        return ("num", a[1] - b[1])
    if a[0] in ("num", "fnum") and b[0] in ("num", "fnum"):
        return ("fnum", float(a[1]) - float(b[1]))
    if a[0] == "list" and b[0] == "list":
        if len(a[1]) != len(b[1]):
            return "ShapeError"
        out = []
        for x, y in zip(a[1], b[1]):
            r = elemwise_sub(x, y)
            if isinstance(r, str):
                return r
            out.append(r)
        return ("list", out)
    return "ShapeError"


def elemwise_div(a, b):
    """Element-wise division (⊘): num/num -> num when divisible, else fnum;
    division by zero is a DivByZero error."""
    if a[0] == "num" and b[0] == "num":
        if b[1] == 0:
            return "DivByZero"
        if a[1] % b[1] == 0:
            return ("num", a[1] // b[1])
        return ("fnum", a[1] / b[1])
    if a[0] in ("num", "fnum") and b[0] in ("num", "fnum"):
        if float(b[1]) == 0.0:
            return "DivByZero"
        return ("fnum", float(a[1]) / float(b[1]))
    if a[0] == "list" and b[0] == "list":
        if len(a[1]) != len(b[1]):
            return "ShapeError"
        out = []
        for x, y in zip(a[1], b[1]):
            r = elemwise_div(x, y)
            if isinstance(r, str):
                return r
            out.append(r)
        return ("list", out)
    return "ShapeError"


def elemwise_mul(a, b):
    """Element-wise multiplication (⊙, Hadamard), mirroring elemwise_add."""
    if a[0] == "num" and b[0] == "num":
        return ("num", a[1] * b[1])
    if a[0] in ("num", "fnum") and b[0] in ("num", "fnum"):
        return ("fnum", float(a[1]) * float(b[1]))
    if a[0] == "list" and b[0] == "list":
        if len(a[1]) != len(b[1]):
            return "ShapeError"
        out = []
        for x, y in zip(a[1], b[1]):
            r = elemwise_mul(x, y)
            if isinstance(r, str):
                return r
            out.append(r)
        return ("list", out)
    return "ShapeError"


def value_eq(a, b):
    """≡ — structural equality, returns num 1/0; mixed kinds are TypeError."""
    if a[0] != b[0]:
        return "TypeError"
    if a[0] == "list":
        if len(a[1]) != len(b[1]):
            return ("num", 0)
        for x, y in zip(a[1], b[1]):
            r = value_eq(x, y)
            if isinstance(r, str):
                return r
            if r == ("num", 0):
                return ("num", 0)
        return ("num", 1)
    if a[0] == "num":
        return ("num", 1) if a[1] == b[1] else ("num", 0)
    if a[0] == "fnum":
        return ("num", 1) if a[1] == b[1] else ("num", 0)
    return "TypeError"


def value_cmp(a, b, op):
    """≥ / ≤ — scalar comparison, returns num 1/0; lists are TypeError."""
    if a[0] == "list" or b[0] == "list":
        return "TypeError"
    if a[0] not in ("num", "fnum") or b[0] not in ("num", "fnum"):
        return "TypeError"
    x, y = float(a[1]), float(b[1])
    if op == "ge":
        return ("num", 1) if x >= y else ("num", 0)
    return ("num", 1) if x <= y else ("num", 0)


def value_in(a, b):
    """∈ — membership: element a in list b, returns num 1/0; non-list is TypeError."""
    if b[0] != "list":
        return "TypeError"
    for e in b[1]:
        r = value_eq(a, e)
        if isinstance(r, str):
            return r
        if r == ("num", 1):
            return ("num", 1)
    return ("num", 0)


def index_into(target, idx):
    path = collect_path(idx)
    cur = target
    for i in path:
        if cur[0] != "list":
            return "TypeError"
        items = cur[1]
        if i >= len(items):
            return "OutOfBounds"
        cur = items[i]
    return cur


def collect_path(idx):
    if idx[0] == "num":
        return [idx[1]]
    if idx[0] == "list":
        out = []
        for it in idx[1]:
            out.extend(collect_path(it))
        return out
    return []


def parse_val(s):
    """Parse a literal: `2`, `0.5`, `[1,2,3]`, `[[1,2],[3,4]]`, `(1,0)`. None on error."""
    # Normalize common Unicode minus/hyphen variants to ASCII '-' (M-4).
    for ch in ("−", "﹣", "－", "‐", "‑"):
        s = s.replace(ch, "-")
    s = s.strip()
    if re.fullmatch(r"-?\d+", s):
        return ("num", int(s))
    if re.fullmatch(r"-?\d+\.\d+", s):
        return ("fnum", float(s))
    if s.startswith("[") and s.endswith("]"):
        return parse_list(s[1:-1])
    if s.startswith("(") and s.endswith(")"):
        return parse_list(s[1:-1])
    return None


def parse_list(inner):
    if inner.strip() == "":
        return ("list", [])
    parts = split_all_top_level(inner, ",")
    items = []
    for p in parts:
        v = parse_val(p)
        if v is None:
            return None
        items.append(v)
    return ("list", items)


def split_top_level(s, sep):
    """Split at the first depth-0 occurrence of sep. Returns (left, right) or None."""
    depth = 0
    for i, c in enumerate(s):
        if c in "[(":
            depth += 1
        elif c in "])":
            depth -= 1
        elif c == sep and depth == 0:
            return (s[:i], s[i + 1:])
    return None


def split_all_top_level(s, sep):
    """Split at every depth-0 occurrence of sep. Returns list of pieces."""
    pieces = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c in "[(":
            depth += 1
        elif c in "])":
            depth -= 1
        elif c == sep and depth == 0:
            pieces.append(s[start:i].strip())
            start = i + 1
    pieces.append(s[start:].strip())
    return [p for p in pieces if p != ""]


def fmt_val(v):
    if v[0] == "num":
        return str(v[1])
    if v[0] == "fnum":
        return repr(v[1])
    return "[" + ",".join(fmt_val(x) for x in v[1]) + "]"


# ============================================================
# Rust verifier driver
# ============================================================

def find_rust_verifier():
    for name in ("sigma-verifier.exe", "sigma-verifier"):
        p = os.path.join(VERIFIER_DIR, name)
        if os.path.exists(p):
            return p
    return None


def run_rust(path):
    """Run the Rust verifier. Returns (passed, output)."""
    binary = find_rust_verifier()
    if binary is None:
        return (None, "Rust verifier not built — run: cd impl/verifier && cargo build")
    proc = subprocess.run(
        [binary, path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = proc.stdout + proc.stderr
    passed = proc.returncode == 0
    return (passed, out)


def run_elixir(path):
    """Run the Elixir verifier. Returns (passed, output)."""
    if not os.path.exists(ELIXIR_SCRIPT):
        return (None, "Elixir verifier not found — run: elixir --version")
    binary = find_elixir()
    if binary is None:
        return (None, "elixir not found on PATH")
    proc = subprocess.run(
        [binary, ELIXIR_SCRIPT, path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = proc.stdout + proc.stderr
    # Filter compiler warnings (unused-variable noise) from the summary line.
    summary = next(
        (ln for ln in out.splitlines() if ln.startswith(("PASS:", "FAIL:"))),
        out.strip().splitlines()[-1] if out.strip() else "",
    )
    passed = proc.returncode == 0
    return (passed, summary)


def find_elixir():
    """Locate the elixir executable (bash shims aren't resolvable by CreateProcess)."""
    for name in ("elixir.bat", "elixir.exe", "elixir"):
        p = shutil.which(name)
        if p:
            return p
    return None


# ============================================================
# Verdict normalization & reporting
# ============================================================

def expected_verdict(module):
    """Parse the `# Expected:` marker into (pass, detail) or None if absent."""
    exp = module.get("expected")
    if not exp:
        return None
    return (exp.upper().startswith("PASS"), exp)


def verdict_of(passed):
    if passed is None:
        return "SKIP"
    return "PASS" if passed else "FAIL"


def extract_violation_kinds(text):
    """Extract violation category names from Rust/Elixir verifier text output.

    Rust:   "   - MissingEncoding(\"⊕\")"  (tuple) or
            "   - UndeclaredEffect { func: ... }"  (struct — brace form)
    Elixir: "FAIL: MissingEncoding(⊕); NoLawsDeclared(⊗)"
    Returns a set of category names (e.g. {"MissingEncoding", "NoLawsDeclared"}).
    """
    kinds = set()
    for m in re.finditer(r"(?:-\s*|FAIL:\s*)([A-Z][A-Za-z]+)(?:\(|\s*\{)", text):
        kinds.add(m.group(1))
    return kinds


def violation_kinds_of(violations):
    """Category names of Python-side violation strings like 'MissingEncoding(⊕)'."""
    return {v.split("(")[0] for v in violations}


def main(paths=None):
    if paths:
        files = paths
    else:
        files = sorted(
            os.path.join(CORPUS_DIR, f)
            for f in os.listdir(CORPUS_DIR)
            if f.endswith(".md")
        )

    print("=" * 78)
    print("ΣLang E-01 — Three-Verifier Consensus Check (Python / Rust / Elixir)")
    print("=" * 78)

    rows = []
    agree_all = True
    for path in files:
        module = parse_module(path)
        py_pass, py_violations = check_python(module)
        rust_pass, rust_out = run_rust(path)
        ex_pass, ex_out = run_elixir(path)

        exp = expected_verdict(module)
        if exp is not None:
            exp_pass, exp_label = exp
        else:
            exp_pass, exp_label = None, "—"

        verdicts = [v for v in (py_pass, rust_pass, ex_pass) if v is not None]
        agree = (len(verdicts) == 3
                 and len(set(verdicts)) == 1
                 and (exp_pass is None or verdicts[0] == exp_pass))

        # M-3: for FAIL verdicts, the three verifiers must also agree on at
        # least one violation category (stronger than binary pass/fail alone).
        kinds_agree = True
        if agree and verdicts[0] is False:
            py_kinds = violation_kinds_of(py_violations)
            rust_kinds = extract_violation_kinds(rust_out)
            ex_kinds = extract_violation_kinds(ex_out)
            available = [k for k in (py_kinds, rust_kinds, ex_kinds) if k]
            if available:
                kinds_agree = bool(set.intersection(*available))
            else:
                kinds_agree = False
        agree = agree and kinds_agree

        if not agree:
            agree_all = False

        detail = "; ".join(py_violations[:3]) if py_violations else (
            ex_out if ex_pass is not None else rust_out.strip().splitlines()[0] if rust_out.strip() else ""
        )
        if agree and verdicts and verdicts[0] is False and not kinds_agree:
            detail = "⚠️ kinds mismatch: " + detail

        rows.append({
            "module": os.path.basename(path),
            "expected": exp_label,
            "python": verdict_of(py_pass),
            "rust": verdict_of(rust_pass),
            "elixir": verdict_of(ex_pass),
            "agree": "✅" if agree else "❌",
            "detail": detail[:60],
        })

    hdr = f"{'Module':<20}{'Expected':<10}{'Python':<8}{'Rust':<8}{'Elixir':<8}{'Agree':<6}Detail"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['module']:<20}{r['expected']:<10}{r['python']:<8}{r['rust']:<8}{r['elixir']:<8}{r['agree']:<6}{r['detail']}")

    passed = sum(1 for r in rows if r["agree"] == "✅")
    print("-" * len(hdr))
    print(f"Consensus: {passed}/{len(rows)} modules agree (Python == Rust == Elixir == Expected)")
    if agree_all:
        print("🏆 E-01 VERIFIER CONSENSUS ESTABLISHED on the shared corpus")
    else:
        print("⚠️  E-01 consensus NOT yet established — investigate the ❌ rows above")
    return 0 if agree_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
