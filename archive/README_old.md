# ΣLang — AI-Native Semantic Protocol

> **Sigma Language** — A deterministic semantic protocol for AI systems.
> One symbol, one meaning, one result — across all models.

## What is ΣLang?

ΣLang is **not a programming language** in the traditional sense.
It is a **contract between intelligences**.

- ✅ Deterministic semantics
- ✅ Symbol-anchored meaning
- ✅ Markdown as source code
- ✅ Ownership-aware dataflow
- ✅ Zero syntactic ambiguity
- ✅ Verifier-enforced consistency

## Status

| Module | Tests | Status |
|--------|-------|--------|
| §T Time & Causal Order | 17/17 | ✅ |
| §E Error Algebra | 16/16 | ✅ |
| §C Confidence & Probabilistic Logic | 37/37 | ✅ |
| §I I/O Boundary & Effects | 25/25 | ✅ |
| **Total** | **95/95** | **✅** |

## Repository Structure

```
sigma-lang/
├── README.md                  # This file
├── LICENSE                    # MIT
├── spec_p0_foundations.md    # ⭐ Main P0 specification (整合版)
├── spec_p0_time.md           # §T Full time & causality spec
├── spec_p0_error.md          # §E Full error algebra spec
├── spec_p0_confidence.md     # §C Full confidence & probability spec
├── spec_p0_io.md             # §I Full I/O & effects spec
├── spec_top_rules.md         # ⭐ Top-level rules: §S shadowing + §C constants (foundational)
├── spec_top_extensions.md    # Top-level rules: Law XIII–XVII + E-03/E-06/E-07/E-10 (promoted) + candidate E-08
├── verify_p0.py              # Algorithmic verification (95 tests)
├── verify_consensus.py       # Three-verifier consensus check (Law XIII gate)
├── corpus/                   # Shared corpus: 20 modules (PASS/FAIL × 3 verifiers)
├── impl/
│   ├── verifier/             # Rust reference Verifier (MD parse + Iron Laws + tests)
│   └── elixir_rt/            # Elixir/BEAM verifier + runtime
├── .github/workflows/        # CI: consensus gate
└── examples/
    ├── tensor_ops.md         # Tensor operations example
    ├── demographics.md       # Surname statistics example
    └── agent_protocol.md    # AI Agent protocol example
```

## Quick Start

### Run the verifier

```bash
python3 verify_p0.py
```

Expected output:
```
⏰ MODULE T: 17/17 passed
⚠️  MODULE E: 16/16 passed
🎲 MODULE C: 37/37 passed
🔌 MODULE I: 25/25 passed

  🎯 TOTAL: 95/95 tests passed
  🏆 ALL P0 FOUNDATIONS VERIFIED — ΣLang is sound!
```

### Read the spec

Start with `spec_p0_foundations.md` — it's the整合版 that ties all four P0 modules together.

## Design Philosophy

### Three-Layer Architecture

```
L0 — Core (core@1.0)        ← immutable, always loaded
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + Iron Laws + Verifier interface

L1 — Standard Library          ← community maintained, versioned
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient

L2 — User Packages            ← anyone can publish
     emoji.finance / tcm.wuzang / physics.qft
     must pass Verifier Iron Laws
```

### The Iron Laws

```
Law I    — Fingerprint Uniqueness (global)
Law II   — Encoding to ℕ (everything → number)
Law III  — Law Declaration (every op has laws)
Law IV   — Test Mandatory (≥1 canonical test per op)
Law V    — No Implementation in Spec
Law VI   — Backward Compatibility (published = frozen)
Law VII  — Explicit Dependencies (no circular deps)
Law VIII — Temporal Determinism (timing bounds declared)
Law IX   — Calibration Requirement (confidence matches accuracy)
Law X    — Effect Transparency (all effects declared)
Law XI   — Capability Discipline (FFI needs explicit caps)
Law XII  — Resource Linearity (open = closed exactly once)
Law XIII — Verifier Consensus (promoted 2026-08-01)
Law XIV  — Negative Test Mandatory (promoted 2026-08-01)
Law XV   — Export Completeness (promoted 2026-08-01)
Law XVI  — Compatibility Proof (promoted 2026-08-01)
```

Laws XIII–XVI are enforced by all three verifiers (Python / Rust / Elixir) against the shared
corpus; see `verify_consensus.py` and `spec_top_extensions.md`.

## Why ΣLang?

### The Problem

Today, when you give the same Markdown document to different AIs:
- GPT-4 interprets it one way
- Claude interprets it another way
- Gemini interprets it a third way

**Same input, different outputs. This is unacceptable for production AI systems.**

### The Solution

ΣLang replaces ambiguous natural language with **mathematically anchored symbols**:

| Traditional | ΣLang |
|------------|--------|
| "add the numbers" | `a ⊕ b` with associativity law |
| "if score >= 90" | `grade(s) ≝ if s<60 then 𝗀𝖣 else…` + boundary tests |
| "probably true" | `⊢_0.73 P` with calibration law |
| "send message" | `send(addr, msg)` with causal ordering |

## Package System

### Installing Standard Packages

```bash
sigma-pkg install finance.base@1.0
sigma-pkg install math.calculus@1.0
sigma-pkg install emoji.finance --from github:user/repo
```

### Publishing Your Own

```bash
sigma-pkg publish my-pack.md
# ✅ All iron laws satisfied
# ✅ 12 symbols registered
# ✅ 47 tests defined
# ✅ 8 laws declared
# ✅ No fingerprint conflicts
```

### Custom Symbol Example

```md
# Package: emoji.finance
# Version: 0.1.0

### 📈 : Bull Market
Type: Market → 𝔹
Definition: 📈(m) ≡ trend(m) > 0

### 🔥 : Burn Rate
Type: Company → ℝ⁺
Definition: 🔥(c) ≡ −d/dt(cash(c))

Laws:
∀ m . 📈(m) ∧ 📉(m) ≡ ⊥
```

## Examples

### Tensor Operations

```md
# Module: tensor_ops

⊕ : Tensor⟨D,R⟩ × Tensor⟨D,R⟩ → Tensor⟨D,R⟩
Associative: (a⊕b)⊕c ≡ a⊕(b⊕c)
Commutative: a⊕b ≡ b⊕a

Tests:
| Input | Output |
| [1,2,3]⊕[4,5,6] | [5,7,9] |
| [1]⊕[1,2] | ⊥ BroadcastError |
```

### Agent Protocol

```md
research(topic):
  1. docs ← search(topic) ⏳
  2. summaries ← docs ∥ map(summarize)
  3. h ← synthesize(summaries)
  4. if confidence(h) < 0.8:
       h ← h ⊕ human_feedback(ctx.user)
  5. return h ↦ ctx.user
```

### Confidence Propagation

```md
## AI message with confidence
msg ≝ (value, confidence)

## Combine two AIs' opinions
combine(m₁, m₂) ≝
  if conf(m₁) > conf(m₂) then m₁ else m₂

## Weighted consensus
consensus(msgs) ≝
  let total ≝ Σ conf(m) in
  (Σ val(m)⊗conf(m)/total, pooled_conf)
```

## License

MIT License — see LICENSE file.

## Contributing

ΣLang is in early stage (v0.3). We welcome:
- RFC proposals for new standard packages
- Verification tools for additional backends
- Test suites for existing packages
- Documentation improvements

## Citation

If you use ΣLang in research, please cite:

```
ΣLang: An AI-Native Semantic Protocol
Version 0.3.0
https://github.com/sigma-lang/sigma-lang
```
