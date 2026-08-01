# ΣLang Top-Level Rules — Foundations

> **Status**: P0 — Foundational. Binding on ALL packages, modules, and verifiers.
> **Version**: 1.0 (consolidated 2026-08-01)
> **Scope**: the top-level rule layer of ΣLang — rules that govern the whole protocol.
> **License**: MIT

---

## T.0 Top-Level Rule Index

| Layer | Where | Binding |
|-------|-------|---------|
| 11 Meta-Rules | `spec_p0_foundations.md` §0.1 | Always |
| Iron Laws I–XII | `spec_p0_foundations.md` §0.1/§0.2 | Always |
| Law XIII — Verifier Consensus | `spec_p0_foundations.md` §V.4 + `spec_top_extensions.md` E-01 | Always (promoted 2026-08-01) |
| Law XIV — Negative Test Mandatory | `spec_top_extensions.md` E-02 | Always (promoted 2026-08-01) |
| Law XV — Export Completeness | `spec_top_extensions.md` E-04 | Always (promoted 2026-08-01) |
| Law XVI — Compatibility Proof | `spec_top_extensions.md` E-05 | Always (promoted 2026-08-01) |
| E-03 Test Portability / E-06 Internal Consistency / E-07 Conflict Adjudication | `spec_top_extensions.md` / §G | Always (promoted 2026-08-01) |
| Law XVII — Probabilistic Guarantee (E-09, declaration check) | `spec_top_extensions.md` | Always (promoted 2026-08-01) |
| Law VIII ext. — Evaluation Determinism (E-10, declaration check) | `spec_top_extensions.md` | Always (promoted 2026-08-01) |
| **§S Shadowing & Binding Discipline** | **this file** | **Always** (decided 2026-08-01) |
| Extension Candidate (E-08 Strategy Bundle) | `spec_top_extensions.md` | NOT normative yet (RFC → adopt) |

> Migration note: §S was previously `spec_p0_shadowing.md` v0.2 — consolidated here 2026-08-01.
> The Iron Laws I–XII and the Meta-Rules remain canonically defined in `spec_p0_foundations.md` §0.

---

## §S Shadowing & Binding Discipline

> **Status**: P0 — Foundational (name resolution must be deterministic for cross-AI consistency)
> **Depends**: core@1.0, §0 Meta-Rules, Law I (Fingerprint Uniqueness), Law VI (Backward Compatibility)
> **Verifier**: `check_shadowing(module)` — **implemented in all three verifiers (2026-08-01)**;
> v0.1 checks: `DuplicateSymbol` (same symbol name defined twice), `ShadowTargetMissing`
> (`## Shadowing` target must resolve to a defined symbol), **R5** `OpaqueShadowAttempt`
> (math-domain symbols cannot be shadowed), **R7-warning** (declared Free-class shadows
> pass with a report warning). Corpus: `shadow_break.md`/`shadow_opaque_break.md` FAIL,
> `shadow_free_ok.md` PASS (R7-warning), `shadow_escape_ok.md` PASS (R2 escape hatch),
> **30/30 modules agree (Python == Rust == Elixir)**.
> Full §S semantics (R2 escape hatch, R4 propagation, R6 declarative domains) are v0.2 scope.

---

### S.1 Motivation

AI Agents resolve names from many packages. Two failure modes destroy ΣLang's determinism:

1. **Silent replacement** — a user package redefines `⊕` without declaring it; two AIs reading the
   same spec resolve different semantics.
2. **Import-order dependence** — `import A` then `import B` vs `import B` then `import A` yield
   different meanings for the same name. Both must be impossible.

At the same time, packages need **local naming freedom**: a tensor package may legitimately want a
local `⊕`-like name without disturbing the global math namespace.

ΣLang's answer: separate **symbol identity** from **name binding**, and grade shadowability.

---

### S.2 Two-Layer Model

#### S.2.1 Symbol (Identity Layer)

- A symbol is the semantic atom (元规则 1: Symbol Primacy).
- Globally unique via fingerprint (Law I). Immutable once published (Law VI).
- **Never redefinable, never shadowable** — regardless of class.

#### S.2.2 Binding (Resolution Layer)

- A binding is a mapping `name → symbol` valid in some scope.
- Bindings may be **shadowed** (re-bound to another symbol) — but only per the rules below.
- The original symbol always remains reachable via its **qualified name** (escape hatch, §S.4 R2).

> This preserves Meta-Rule 2 (No Synonyms): a *symbol* has exactly one semantics.
> Shadowing re-binds a *name*; it never redefines a *symbol*.

---

### S.3 Shadowing Classes

| Class | Covers | Shadowable? | Declaration required? | Examples |
|-------|--------|-------------|----------------------|----------|
| **Opaque** | core@1.0 constants + all math-domain symbols | ❌ No (error) | — | `ℕ`, `𝔹`, `π`, `⊕`, `∫`, `∂`, `ℝ` |
| **Shadowable** | symbols of non-math domains (finance, ai, tcm, …) | ✅ Yes | ✅ Yes (`shadow`) | `finance.base.Δ`, `tcm.wuzang.心` |
| **Free** | non-symbol semantics: type names, function/op names, variables, labels | ✅ Yes | ✅ Yes (informational) | `combine`, `Tensor`, `consensus` |

#### S.3.1 Opaque — definition

```md
opaque ::= core-constant | math-domain-symbol

core-constant  : any symbol defined by core@1.0
math-symbol    : any symbol exported by a package declared
                 `Domain: math` (declarative — see §S.4 R6)
```

#### S.3.2 Free — definition of "non-symbol semantics"

Non-symbol semantics = identifiers that carry meaning but are **not Sym atoms**:
type constructors (`Tensor⟨·,·⟩`), function names (`combine`), variables, labels.
They are shadowable but the shadow **must still be declared** — implicit shadowing is a bug source.

---

### S.4 Rules

#### R1 — Explicit Declaration
Every shadow must be declared with the `shadow` keyword (§S.5). An undeclared name collision is a
Verifier error, not a silent resolution.

#### R2 — Escape Hatch (qualified names)
Every symbol remains reachable by qualified name regardless of shadowing:

```md
finance.greeks.Δ    # always resolves to the original symbol
math.base.⊕         # even if ⊕ is locally shadowed
```

Qualified names are **never** shadowable.

#### R3 — Deterministic Resolution (import-order independence)
Resolution priority is fixed, in this order:

```text
1. Local explicit shadow (declared in current package)   → wins
2. Imported bindings (in package-declared import order)   → next
3. core@1.0                                               → always available
```

Same-layer name conflicts (two imports expose the same name, no local shadow) are
**ambiguous shadows** → Verifier error. Never guessed, never import-order-dependent.

#### R4 — No Propagation
A shadow is local to the package (or scope) that declares it. Downstream packages importing that
package **do not inherit** its shadows. One package's local decision cannot pollute the dependency tree.

#### R5 — Math Domain Is a Single Namespace
Within the math domain, a name collision (e.g. `math.calculus.δ` vs `math.linear.δ` with different
semantics) is a **definition error** — the package must rename, not shadow. Math never enters the
shadowing mechanism.

#### R6 — Domain Is Declarative, Not Hardcoded
`Domain: math` is a package-header declaration, not a string match on package names. A package may
voluntarily enter the opaque class (`Opaque: true`) to protect its symbols. Verifier checks the
declaration for consistency with exported symbol types.

#### R7 — Free-Class Shadows Are Declared Too
Type/function/variable shadows use the same `shadow` syntax. No justification is required, but the
declaration must exist. The Verifier emits a **warning** for every declared Free-class shadow
(R7-warning): verification still passes, but the shadow is flagged in the report — nudging authors
toward fresh names while keeping the freedom to shadow.

#### R8 — Auditability
The Verifier emits a **shadow report**: every shadow point (name, original symbol, new symbol,
scope). Business logic stays mathematically auditable.

---

### S.5 Syntax

```md
# Package: tensor.net
# Version: 0.1.0
# Domain: ai
# Opaque: false
# Depends: core@1.0, math.base@1.0, finance.base@1.0

## Imports
import core
import math.base
import finance.base

## Shadowing
# R2: escape hatch — qualified name preserved
shadow finance.base.Δ → as finance_Δ
# R1: local rebinding of an imported symbol (shadowable class only)
shadow combine
# R7: free-class shadow (function name)
shadow tensor_add → local_add
# v0.2 (reserved): shadow combine scope: <fn|section> — v0.1 is package-level only
```

#### S.5.1 Grammar

```text
shadow-decl  ::= "shadow" qualified-name ["→" ["as"] identifier]
               | "shadow" identifier ["→" identifier]
qualified-name ::= package-name "." symbol-name
```

---

### S.6 Resolution Algorithm (reference)

> v0.1: `scope` is a **package**. Finer scopes (function/section) are reserved for v0.2
> via an optional `scope:` parameter on the `shadow` declaration.

```text
resolve(name, scope):
  if scope has explicit shadow for name:      return shadow.target        # R1
  if qualified name:                          return package.symbol       # R2, never shadowed
  candidates = imports exposing name
  if len(candidates) == 1:                    return candidates[0]        # deterministic
  if len(candidates) > 1:                     → AMBIGUOUS SHADOW error    # R3
  if name in core@1.0:                        return core.symbol          # opaque, always
  → UNRESOLVED error
```

---

### S.7 Verifier Integration

**Implemented (2026-08-01)** in `impl/verifier/src/main.rs`, `verify_consensus.py`,
`impl/elixir_rt/sigma_verify.exs` — v0.1 check (+ R5, R7-warnings):

```text
fn check_shadowing(module) -> violations:
  DuplicateSymbol      # same symbol name defined twice (No Synonyms / R3)
  ShadowTargetMissing  # every `shadow <target>` must resolve to a defined symbol (R1)
  OpaqueShadowAttempt  # math-domain symbols (⊕ ⊗ ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈ ℕ ℤ ℚ ℝ) cannot be
                       # shadowed (R5, Opaque class) — violation
  R7-warning           # declared Free-class shadow of a local symbol → warning,
                       # verification still passes (S-11)
```

Remaining full-pipeline items (v0.2 scope — R2 escape hatch, R3 order-independence,
R4 propagation, R6 declarative domains):

```text
fn check_shadowing_full(module) -> violations:
  R1  every `shadow` targets an existing binding (shadowable/free class)
  R3  no ambiguous shadows (same-layer conflicts)
  R4  shadow targets resolve within current package scope
  R5  no math-domain symbols are shadowed (opaque class)
  R6  Domain/Opaque header declarations are consistent
  output: shadow_report[]  (+ R7-warnings[])
```

Verifier JSON output extension:

```json
{
  "spec": "tensor.net@0.1.0",
  "pass": true,
  "shadowing": {
    "report": [
      {"name": "Δ", "from": "finance.base.Δ", "to": "finance_Δ", "scope": "tensor.net"}
    ],
    "warnings": [
      {"name": "tensor_add", "class": "free", "scope": "tensor.net", "reason": "R7-warning"}
    ],
    "opaque_shadow_attempts": 0
  }
}
```

---

### S.8 Canonical Tests

| # | Scenario | Expect |
|---|----------|--------|
| S-01 | Shadow a finance symbol with explicit `shadow` | ✅ resolves locally, qualified name still works |
| S-02 | Shadow `⊕` from `math.base` (opaque class) | ❌ opaque shadow attempt |
| S-03 | Shadow a core constant `π` (opaque class) | ❌ opaque shadow attempt |
| S-04 | Two imports expose same name, no local shadow | ❌ ambiguous shadow |
| S-05 | Same as S-04 but with local `shadow` declared | ✅ local shadow wins |
| S-06 | Package A shadows `combine`; package B imports A | ✅ B sees original `combine` (no propagation) |
| S-07 | Swap import order in S-04/S-05 | ✅ identical result (order-independent) |
| S-08 | `math.calculus.δ` vs `math.linear.δ` collision | ❌ rename required (single namespace) |
| S-09 | Function-name shadow without `shadow` declaration | ❌ undeclared shadow |
| S-10 | Qualified name `math.base.⊕` inside a shadowing package | ✅ always resolves to original |
| S-11 | Declared Free-class shadow (e.g. `shadow tensor_add`) | ✅ passes with R7-warning in report |
| S-12 | `shadow` with `scope:` parameter (v0.1) | ❌ unsupported in v0.1 (reserved for v0.2) |

---

### S.9 Relationship to Existing Rules

| Rule | Relationship |
|------|--------------|
| Law I (Fingerprint Uniqueness) | unchanged — fingerprints identify **symbols**, which are never shadowed |
| Meta-Rule 2 (No Synonyms) | preserved — shadowing never gives a symbol a second semantics |
| Law VI (Backward Compatibility) | strengthened — escape hatch keeps old semantics reachable |
| §2.3 Import Syntax | extended — `finance.greeks.Δ` qualified access is now normative |
| Meta-Rule 6 (Human Text Non-normative) | unchanged |

---

### S.10 Resolved Decisions

Recorded 2026-08-01:

1. **Free-class shadows emit a non-blocking R7-warning** — declared Free-class shadows pass
   verification but are flagged in the Verifier report (nudge toward fresh names).
2. **Shadow scope is package-level in v0.1** — finer scopes (function/section) are reserved for
   v0.2 via an optional `scope:` parameter; v0.1 rejects `scope:` usage (S-12).
3. **`Opaque` is package-level in v0.1** (`Opaque: true`) — per-symbol opacity
   (`Opaque: 0xN001, 0xN004`) is deferred to v0.2.

---

## §C Real-World Constants (Opaque Catalog)

> **Status**: Opaque class (§S.3.1) — never redefinable, never shadowable, always available
> via qualified name. Shadow attempts are violations (S-02/S-03).
> **Note**: numeric values below are **reference** (non-normative precision). Semantic
> definitions are normative; implementation precision bounds are declared per Law VIII
> and E-08 (Eval Determinism).
> **Fingerprint prefixes**: `0xK0xx` (mathematical), `0xQ0xx` (physics) — registry placeholders.

### C.1 Mathematical Constants

| Glyph | Name | Definition (normative) | Reference value | FP |
|-------|------|------------------------|-----------------|----|
| `π` | Circle constant | circumference / diameter | 3.14159… | 0xK001 |
| `e` | Euler's number | limₙ (1+1/n)ⁿ | 2.71828… | 0xK002 |
| `φ` | Golden ratio | (1+√5)/2 | 1.61803… | 0xK003 |
| `γ` | Euler–Mascheroni | limₙ (Hₙ − ln n) | 0.57721… | 0xK004 |
| `√2` | Pythagoras' constant | x>0 ∧ x²=2 | 1.41421… | 0xK005 |
| `ln2` | Natural log of 2 | ∫₁² dx/x | 0.69314… | 0xK006 |
| `G_𝒦` | Catalan's constant | Σ (−1)ᵏ/(2k+1)² | 0.91596… | 0xK007 |
| `ζ3` | Apéry's constant | Σ 1/k³ | 1.20205… | 0xK008 |
| `δ_ℱ` | Feigenbaum's delta | period-doubling ratio | 4.66920… | 0xK009 |

### C.2 Physics Constants (SI / CODATA 2018–2019 reference)

> Post-2019 SI redefinition makes `c`, `h`, `e`, `k_B`, `N_A` **exact by definition**.

| Glyph | Name | Definition (normative) | Reference value | FP |
|-------|------|------------------------|-----------------|----|
| `c` | Speed of light | exact SI constant | 299 792 458 m/s | 0xQ001 |
| `h` | Planck constant | exact SI constant | 6.62607015×10⁻³⁴ J·s | 0xQ002 |
| `ℏ` | Reduced Planck | h/2π | 1.054571817…×10⁻³⁴ J·s | 0xQ003 |
| `G_𝔫` | Gravitational constant | Newtonian coupling | 6.67430×10⁻¹¹ m³·kg⁻¹·s⁻² | 0xQ004 |
| `ε₀` | Vacuum permittivity | exact (from c, μ₀) | 8.8541878128…×10⁻¹² F/m | 0xQ005 |
| `μ₀` | Vacuum permeability | exact SI constant | 1.25663706212…×10⁻⁶ H/m | 0xQ006 |
| `e` | Elementary charge | exact SI constant | 1.602176634×10⁻¹⁹ C | 0xQ007 |
| `k_B` | Boltzmann constant | exact SI constant | 1.380649×10⁻²³ J/K | 0xQ008 |
| `N_A` | Avogadro constant | exact SI constant | 6.02214076×10²³ mol⁻¹ | 0xQ009 |
| `R` | Molar gas constant | N_A · k_B | 8.314462618… J/(mol·K) | 0xQ00A |
| `mₑ` | Electron mass | CODATA | 9.1093837015…×10⁻³¹ kg | 0xQ00B |
| `mₚ` | Proton mass | CODATA | 1.67262192369…×10⁻²⁷ kg | 0xQ00C |
| `α` | Fine-structure constant | e²/(4πε₀ℏc) | 7.2973525693…×10⁻³ | 0xQ00D |
| `σ` | Stefan–Boltzmann | π²k_B⁴/(60ℏ³c²) | 5.670374419…×10⁻⁸ W·m⁻²·K⁻⁴ | 0xQ00E |
| `g₀` | Standard gravity | exact SI constant | 9.80665 m/s² | 0xQ00F |
| `R_∞` | Rydberg constant | mₑe⁴/(8ε₀²h³c) | 10 973 731.568160… m⁻¹ | 0xQ010 |

### C.3 Constant Rules

1. **Opaque** — shadowing or redefinition of any §C constant is a Verifier violation (§S R5 family).
2. **No Synonyms** — a constant may not be exported under a second glyph (Meta-Rule 2).
3. **Precision** — implementations must honor declared precision bounds (Law VIII; E-08 candidate).
   Reference values above carry exactness notes (SI-exact vs CODATA-derived).
4. **Units** — physics constants carry unit metadata; units are part of the semantic definition,
   not decorative prose.
5. **New constants** — additions follow the RFC → registry path (§Z); prefixes above are reserved.

---

## §G Conflict Adjudication Process (E-07, promoted 2026-08-01)

> **Status**: Meta-rule — normative governance. Complements Law I: fingerprints must be unique,
> and when they are not, this is the resolution path. Governance, not code: the Verifier refuses
> to certify an unresolved conflict; the registry records the outcome.

### G.1 Scope

Applies to:

- **Fingerprint conflicts** — two packages claim the same fingerprint (Law I violation).
- **Semantic disputes** — a symbol's meaning is contested between packages (Meta-Rule 2).
- **Qualified-name collisions** — imports expose the same name without a declared shadow (§S R3).

### G.2 Resolution Path

```md
1. RFC submission — conflict description + both parties' evidence (template §G.3).
2. Arbitration review — human committee + dual-verifier cross-check (Law XIII).
3. Verdict recorded in the registry (winner keeps the fingerprint; loser is reassigned).
4. During the dispute, old versions remain loadable (Law VI holds; disputes do not freeze them).
```

### G.3 RFC Template

```md
# RFC: Fingerprint/Semantic Conflict

- Fingerprint or symbol in dispute: `0x…` / `glyph`
- Packages involved: `pkg_a@ver` vs `pkg_b@ver`
- Claim (each side): semantic definition + laws + canonical tests
- Verifier evidence: run `verify_consensus.py` on both (Law XIII cross-check)
- Proposed resolution: keep A / keep B / reassign / merge
- Maintainers: …
```

### G.4 Registry `adjudication` Field

```json
{
  "fingerprint": "0x…",
  "status": "disputed | decided",
  "rfc": "rfc-0042",
  "winner": "pkg_a@1.2.0",
  "loser": "pkg_b@2.0.0",
  "reassigned_fingerprint": "0x…",
  "decision_date": "2026-08-01"
}
```

### G.5 Verifier Interaction

- A module whose imports reference a `disputed` fingerprint is **not certified** until the
  registry marks it `decided` (hard fail, not a warning).
- The corpus does not contain disputed fingerprints; the check is exercised by the registry.

### G.6 Adoption

- [x] Governance doc published (this section, incl. RFC template §G.3)
- [x] Registry `adjudication` field specified (§G.4)
- [ ] Registry implementation (future: `sigma-pkg` registry backend)

---

*End of ΣLang Top-Level Rules — Foundations v1.0*
