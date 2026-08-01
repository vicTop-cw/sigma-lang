# ΣLang Proof-Carrying Specs — Formal Verification

> **Status**: PARTIALLY NORMATIVE — P-01 (proof structure check) is **enforced** by all three
> verifiers (2026-08-01); the SMT discharge backend (`sigma-prove`) remains future work.
> **Origin**: adapted from MoonBit's formal-verification design
> (`moon prove` + `.mbt`/`.mbtp` split, docs.moonbitlang.cn/language/verification.html).
> **Relationship**: extends Laws XIII–XVI with a **proof-style authoring convention**
> (P-01 structural check is part of the Verifier contract); does not change the corpus contract.

---

## P.1 Why Formal Verification for ΣLang

ΣLang's Iron Laws and canonical tests give **test-grounded** semantics (Meta-Rule 4:
Equality by Test). Tests prove behavior on *sampled* inputs. Formal verification proves
behavior on *all* inputs of a declared shape — closing the gap between "95 tests pass"
and "the laws hold for every input the spec admits."

MoonBit demonstrates a workable shape for this in a general-purpose language:
- executable code (`.mbt`) separated from logical predicates and lemmas (`.mbtp`)
- named predicates (`model`, `*_inv`, `*_pre`, `*_post`) instead of inline formulas
- contracts (`proof_require` / `proof_ensure`), loop invariants (`proof_invariant`),
  local facts (`proof_assert`), and an explicit trust boundary (`proof_axiomatized`)
- obligations discharged by an SMT-backed prover (`moon prove`)

ΣLang adapts this: the **spec is the proof surface**, and the Verifier is the
judge of both tests and proof blocks.

---

## P.2 Method Mapping (MoonBit → ΣLang)

| MoonBit concept | ΣLang equivalent | Role |
|-----------------|------------------|------|
| `.mbt` (executable) | spec module operations + tests | program side |
| `.mbtp` (predicates/lemmas) | `## Proof` section (laws, invariants, model) | logic side |
| `model(x)` abstraction | `## Model` block: semantic view of a value | bridge concrete → abstract |
| `*_inv` representation invariant | `## Invariant` block | well-formedness of the state |
| `proof_require` (precondition) | `## Pre` block on an operation | what must hold on entry |
| `proof_ensure` (postcondition) | `## Post` block on an operation | what must hold on exit |
| `proof_assert` (local fact) | canonical test row | concrete witness of a step |
| `proof_invariant` (loop) | `## Invariant` block for stateful ops | induction hypothesis |
| `proof_axiomatized` (trust bridge) | `## Trusted` block | explicit, narrow trust boundary |
| `moon prove` (SMT discharge) | `sigma-prove.py` (z3 backend) + `sigma-moonbit.py` (translation bridge, 2026-08-01) | discharge obligations — two independent backends over the same `## Proof` |
| `moon check` (type/parse) | Verifier Iron Laws | structural gate |
| `moon test` (runtime) | canonical test execution | behavioral gate |

---

## P.3 Proof-Carrying Spec Structure

A module that carries proofs declares a `## Proof` section:

```md
# Module: balance@1.0
# Version: 1.0.0

## Proof

### Model
balance(m) : Fmap[CoinId, ℤ]
  # abstract semantic view of the concrete ledger

### Invariant
ledger_inv(l) : 𝔹
  # shape: every entry has a positive balance
  ∀ c . c ∈ keys(l) ⇒ balance(c) > 0

### Operation: deposit
# Pre:  amount > 0
# Post: balance' = balance ⊕ {coin ↦ balance(coin) + amount}
#       ledger_inv(l')

### Trusted
init_ledger : Unit → Ledger
  # proof_axiomatized — constructed outside the verified core
```

Rules:

1. **Two layers, narrow bridge** — `## Proof` blocks are the logic side; operations +
   tests are the program side. They connect only through named predicates in `## Model`.
2. **Named predicates over inline formulas** — every contract references a named
   predicate (`ledger_inv`, `deposit_post`), never a raw boolean blob.
3. **Small, stable invariants** — `*_inv` describes shape/bounds/well-formedness;
   semantic equalities live in `## Post` blocks, not inside the invariant.
4. **Every proof-relevant stateful op declares `Pre` and `Post`.**
5. **Trust is explicit and temporary** — `## Trusted` blocks are narrow bridges with
   concrete preconditions; they are shrunk from constructors outward, never the design
   endpoint.
6. **Tests remain mandatory** (Law IV, XIV) — proof blocks do not replace tests;
   they generalize them.

---

## P.4 Verification Obligations (what `sigma-prove` would check)

Mapping `moon prove`'s obligations to a spec:

| # | Obligation | ΣLang form |
|---|------------|------------|
| 1 | Precondition suffices for safe execution | every `## Pre` implies the op's signature constraints |
| 2 | Postcondition holds on every return path | every `## Post` follows from the op's laws |
| 3 | Local facts are valid | each test row is a valid instance of the laws |
| 4 | Invariant is established and maintained | `## Invariant` holds initially and after each op |
| 5 | Termination measure decreases | declared for recursive/stateful ops |
| 6 | Bounds/safety are discharged | `Model`/`Invariant` imply index/range safety |

Not yet implemented: a `sigma-prove` SMT backend is **future work** (P.6). The
methodology is adopted now so specs are written proof-ready.

---

## P.5 Recommended Style & Anti-Patterns

### Style

- Prefer `model(...)` as the default name for the semantic view.
- Use `*_inv`, `*_pre`, `*_post` suffixes consistently.
- Start from a simple verified slice (monomorphic) before generalizing.
- Add helper lemmas **only after** seeing a concrete failing obligation.
- Keep the trusted surface explicit and minimal.

### Anti-patterns

- ❌ Repeating large inline formulas inside every contract
- ❌ Putting the whole semantics into the invariant
- ❌ Adding many helper lemmas without a failing VC to justify them
- ❌ Storing semantic theorems only inside `## Trusted` blocks
- ❌ Changing the abstraction model and solver guidance in one step

---

## P.6 Adoption Path

1. **RFC** — approve `## Proof` block syntax and naming conventions.
2. **Verifier support** — extend all three verifiers to parse `## Proof` blocks
   (structural: `Model`/`Invariant`/`Pre`/`Post` present for stateful ops).
3. **Corpus** — add proof-style modules with `# Expected:` verdicts; require
   three-verifier agreement (Law XIII gate).
4. **SMT backend** — `tools/sigma-prove.py` (2026-08-01): lowers Pre/Post contracts to
   SMT-LIB2 obligations (ℕ→Int, ⊕→+, ⊗→*, ⊖→-); discharges via z3 when available,
   degrades gracefully to "obligation generated (unverified)" otherwise.

Adoption criteria:

- [ ] RFC for `## Proof` syntax (P.3)
- [x] Verifier parses `## Proof` blocks (all three implementations) — `check_proof_structure` / P-01
- [x] ≥2 proof-style corpus modules, three-verifier agreement (proof_ok PASS, proof_break FAIL; 15/15 agree)
- [x] SMT discharge path implemented (`tools/sigma-prove.py`; z3 required for full discharge)

### sigma-prove (SMT backend, 2026-08-01)

`python3 tools/sigma-prove.py [module.md]` performs, per module:

1. **P-01 structural check** (reuses `verify_consensus.check_python`): `## Proof` must have
   Model + Invariant; ops must pair Pre/Post.
2. **Obligation generation**: for each op with `# Pre:`/`# Post:` + arithmetic glyph,
   emit an SMT-LIB2 query asserting operands ∈ ℕ, the Pre, and the negation of Post
   (with `result` substituted by the op semantics). `check-sat` = unsat ⇒ Post is
   discharged from Pre.
3. **Discharge**: z3 Python API, then z3 CLI; with no solver on PATH the obligation is
   written to `tools/_sigma_prove_out/` and reported unverified.

Exit: 0 = structure OK (and obligations discharged if a solver exists); 1 = structural
failure or a disproved obligation. Verified on `proof_ok.md` (obligation generated,
P-01 OK, exit 0) and `proof_break.md` (MissingModel + IncompleteContract, exit 1).

### P-01 Promotion record (2026-08-01)

P-01 (proof-carrying spec structure) is now enforced by all three verifiers. A module declaring
`## Proof` must have a `### Model` and a `### Invariant`; every operation must declare
`# Pre:` and `# Post:` together (or neither). Violations: `MissingModel`, `MissingInvariant`,
`IncompleteContract`.

Corpus: `proof_ok.md` (PASS) and `proof_break.md` (FAIL — missing Model + incomplete contract).
Full run: **15/15 modules agree (Python == Rust == Elixir == Expected)**.

---

*End of ΣLang Proof-Carrying Specs — v0.2 (P-01 enforced 2026-08-01)*
