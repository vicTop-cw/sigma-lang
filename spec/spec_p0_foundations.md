# ΣLang P0 Foundations — Complete Specification

> **Version**: 0.3.0  
> **Status**: P0 — Foundational (without these, ΣLang cannot function)  
> **Verification**: 95/95 tests passing  
> **License**: MIT

---

## Table of Contents

- [§0 Meta-Rules & Iron Laws](#0-meta-rules--iron-laws)
- [§1 Core Types (from core@1.0)](#1-core-types)
- [§2 Package System](#2-package-system)
- [§T Time & Causal Order](#t-time--causal-order)
- [§E Error Algebra](#e-error-algebra)
- [§C Confidence & Probabilistic Logic](#c-confidence--probabilistic-logic)
- [§I I/O Boundary & Effects](#i-io-boundary--effects)
- [§V Verifier Architecture](#v-verifier-architecture)
- [§A Appendix: Complete Symbol Index](#a-appendix-complete-symbol-index)

---

## §0 Meta-Rules & Iron Laws

### §0.1 Meta-Semantics (11 Rules)

```md
1. Symbol Primacy
   每个符号是语义原子，不可拆分，不可重定义。

2. No Synonyms
   一个语义只有一个符号，一个符号只有一个语义。

3. Definition = Constraint
   定义不是解释，是约束集合。

4. Equality by Test
   语义等价 ⇔ 通过同一测试集。

5. No Implementation in Spec
   规范中不得出现算法、性能、内存布局描述。

6. Human Text is Non-normative
   所有自然语言描述仅为辅助，不构成语义。

7. Fingerprint Uniqueness (Law I)
   每个符号的 fingerprint 全局唯一，不可冲突。

8. Encoding to ℕ (Law II)
   包内所有非数值概念，必须有 ℕ 编码函数。

9. Law Declaration (Law III)
   每个操作必须声明其代数定律。

10. Test Mandatory (Law IV)
    每个操作至少 1 个 canonical test。

11. Internal Consistency Adjudication (E-06)
    类型签名、定律、测试、自然语言四者冲突时：
    优先级 测试 ≥ 定律 ≥ 类型签名 > 自然语言。
    Verifier 检测明显冲突（如测试期望与签名返回类型形状不符）。
```

### §0.2 Extended Iron Laws (P0)

```md
Law V   — No Implementation in Spec
Law VI  — Backward Compatibility (published semantics immutable)
Law VII — Explicit Dependencies (no circular deps)
Law VIII — Temporal Determinism (timing bounds declared)
Law IX  — Calibration Requirement (confidence matches accuracy)
Law X  — Effect Transparency (all effects declared)
Law XI  — Capability Discipline (FFI needs explicit caps)
Law XII — Resource Linearity (opened = closed exactly once)
```

> **Promoted top-level laws (2026-08-01)** — defined in `spec_top_extensions.md`,
> enforced by all three verifiers (Python / Rust / Elixir):
> Law XIII — Verifier Consensus (§V.4), Law XIV — Negative Test Mandatory,
> Law XV — Export Completeness, Law XVI — Compatibility Proof.

### §0.3 Verification Status

```
⏰ Module T (Time):        17/17 ✅
⚠️  Module E (Error):       16/16 ✅
🎲 Module C (Confidence):   37/37 ✅
🔌 Module I (I/O):         25/25 ✅
                          ─────
                    TOTAL:  95/95 ✅
```

---

## §1 Core Types

```md
## Primitive Types
ℕ : Type    # natural numbers
ℤ : Type    # integers
ℚ : Type    # rationals
ℝ : Type    # real numbers (idealized, no Float)
ℂ : Type    # complex numbers (ℝ[i]/(i²+1))
𝔹 : Type    # boolean {⊤, ⊥}
Sym : Type   # atomic symbol (opaque)
String : Type  # opaque byte sequence
Prop : Type  # propositions

## Type Constructors
A × B : Type    # product (pair)
A + B : Type    # sum (either)
A → B : Type    # function (pure)
A ↝ B : Type    # function (effectful)
Result⟨V,E⟩ : Type  # V + E (from §E)
P⟨T⟩ : Type     # T × Conf (from §C)
Dist⟨T⟩ : Type  # probability distribution
Effect : Type   # effect tag (from §I)
Event : Type    # causal event (from §T)
Time : Type     # logical time
AgentID : Type  # agent identifier
Resource : Type # IO resource
Capability : Type # permission
Conf : Type     # ℚ ∩ [0,1]
```

---

## §2 Package System

### §2.1 Three-Layer Architecture

```
L0 — Core (core@1.0) — immutable, always loaded
     ℕ ℤ ℚ ℝ ℂ 𝔹 Sym Prop λ ∀ ∃
     + Iron Laws + Verifier interface

L1 — Standard Library (community maintained, versioned)
     math.calculus / math.linear / finance.base
     signal.fourier / stat.prob / opt.gradient
     graph.core / crypto.hash / logic.temporal

L2 — User Packages (anyone can publish)
     emoji.finance / tcm.wuzang / physics.qft
     must pass Verifier Iron Laws
```

### §2.2 Package Format

```md
# Package: finance.base
# Version: 1.0.0
# Fingerprint Prefix: 0xN000-0xNFFF
# Depends: core@1.0, math.calculus@1.0
# Maintainer: sigma-finance-wg
# License: MIT

## Imports
import core
import math.calculus

## Exports
PV, FV, NPV, IRR, Δ, Γ, Θ, ν, ρ, N

## Symbols
### PV : Present Value
Type: ℝ → ℝ → ℕ → ℝ
Fingerprint: 0xN001
Definition: PV(C, r, n) ≡ C / (1+r)^n

Laws:
- Monotonic in C: C₁ < C₂ ⇒ PV(C₁) < PV(C₂)

Tests:
| C | r | n | Expected |
|----|---|---|----------|
| 100 | 0.05 | 1 | 95.238… |
```

### §2.3 Import Syntax

```md
import core                       # always available
import math.calculus              # ∫ ∂
import finance.base@>=1.0,<2.0   # version constraint
import signal.fourier    optional # warn if missing
import my_emoji_pack      custom # user-defined

## Qualified access on conflict
math.calculus.Δ     # Laplacian
finance.greeks.Δ     # Delta
```

### §2.4 Custom Symbol Packages

```md
# Package: emoji.finance
# Version: 0.1.0

### 📈 : Bull Market
Type: Market → 𝔹
Fingerprint: 0xE001
Definition: 📈(m) ≡ trend(m) > 0

### 🔥 : Burn Rate
Type: Company → ℝ⁺
Fingerprint: 0xE004
Definition: 🔥(c) ≡ −d/dt(cash(c))

Laws:
∀ m . 📈(m) ∧ 📉(m) ≡ ⊥

# Package: tcm.wuzang (中医·五脏)
### 心 : Heart  → Organ, Fingerprint: 0xC001
### 肝 : Liver  → Organ, Fingerprint: 0xC002
### 生 : Generates → Organ × Organ
### 克 : Overcomes → Organ × Organ

encode(心) ≝ 1
encode(肝) ≝ 2
∀ o . ∃! o' . 生(o, o')
```

---

## §T Time & Causal Order

> **Full specification**: see `spec_p0_time.md`  
> **Verification**: 17/17 tests passing

### §T.1 Primitives

| Glyph | Type | Fingerprint | Meaning |
|-------|------|-------------|---------|
| `⏰` | `Unit → Time` | `0xT001` | Current logical time |
| `⏳` | `Future⟨T⟩ → T` | `0xT002` | Await |
| `⏱` | `Time → Effect` | `0xT003` | Deadline |
| `⌛` | `Time × Time → ℕ` | `0xT004` | Duration |
| `→ᵢₒ` | `Event × Event → 𝔹` | `0xT005` | Happens-before |
| `∥ᵢₒ` | `Event × Event → 𝔹` | `0xT006` | Concurrent |
| `clock` | `Agent → ℕ` | `0xT007` | Lamport clock |
| `vc` | `Agent → ℕ^∞` | `0xT008` | Vector clock |
| `tick` | `Agent → Effect` | `0xT009` | Advance clock |
| `timeout` | `Effect × ℕ → Result⟨T,TimeoutErr⟩` | `0xT00A` | Bounded wait |
| `retry` | `Effect × ℕ → Effect` | `0xT00B` | Retry n times |
| `race` | `Effect × Effect → Effect` | `0xT00C` | First wins |
| `after` | `Effect × ℕ → Effect` | `0xT00D` | Delay |
| `periodic` | `Effect × ℕ → Effect` | `0xT00E` | Every n ticks |

### §T.2 Core Laws

```md
## Happens-Before (irreflexive)
∀ e . ¬(e →ᵢₒ e)

## Happens-Before (transitive)
∀ a b c . a →ᵢₒ b ∧ b →ᵢₒ c ⇒ a →ᵢₒ c

## Happens-Before (antisymmetric)
∀ a b . a →ᵢₒ b ⇒ ¬(b →ᵢₒ a)

## Message causality
∀ send recv . send_msg(m) →ᵢₒ recv_msg(m)

## Vector clock update
vc_recv(vc_loc, vc_rem) ≝ λx. max(vc_loc(x), vc_rem(x)) then +1

## Timeout laws
∀ eff . timeout(eff, 0) ≡ err(TimeoutErr)
∃ t . eff completes in t ⇒ timeout(eff, t+1) ≡ ok(result)

## Retry laws
retry(eff, 0) ≡ eff
deterministic(eff) ∧ failed(eff) ⇒ retry always fails

## Race-freedom
∀ e₁ e₂ . access_same_resource(e₁,e₂)
          ∧ (write(e₁) ∨ write(e₂))
          ⇒ e₁ →ᵢₒ e₂ ∨ e₂ →ᵢₒ e₁
```

### §T.3 Agent Lifecycle

```md
spawn : Agent → Effect
die   : Agent → Effect
join  : Agent → Effect
link  : Agent × Agent → Effect  # supervision

## Supervision law
∀ p c . linked(p,c) ⇒ c_dies ⇒ p_notified
```

### §T.4 Timing Contract (Mandatory for Async)

```md
timing_contract {
  max_latency: 1000 ticks,
  max_retries: 3,
  timeout_budget: 5000 ticks,
  deadline_miss_policy: "fail_fast"
}
```

---

## §E Error Algebra

> **Full specification**: see `spec_p0_error.md`  
> **Verification**: 16/16 tests passing

### §E.1 The Result Type

```md
Result⟨V, E⟩ ≝ V + E

ok  : V → Result⟨V, E⟩
err : E → Result⟨V, E⟩
```

### §E.2 Built-in Errors

```md
TimeoutErr    : Error
NetworkErr    : Error
DecodeErr     : Error
EncodeErr     : Error
NotFound      : Error
PermissionErr : Error
OutOfMem      : Error
OverflowErr   : Error
UnderflowErr  : Error
NaNErr        : Error
AssertErr     : Error
PanicErr      : Error
UnknownErr    : Error
```

### §E.3 Core Combinators

| Glyph | Type | Fingerprint | Meaning |
|-------|------|-------------|---------|
| `>>=` | `Result⟨V,E⟩ → (V→Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE001` | Bind |
| `>>` | `Result⟨V,E⟩ → Result⟨W,E⟩ → Result⟨W,E⟩` | `0xE002` | Sequence |
| `\|>` | `V → (V→Result⟨W,E⟩) → Result⟨W,E⟩` | `0xE003` | Pipe |
| `try` | `Effect → Result⟨V,E⟩` | `0xE004` | Catch |
| `throw` | `E → Result⟨V,E⟩` | `0xE005` | Throw |
| `catch` | `Result⟨V,E₁⟩ → (E₁→Result⟨V,E₂⟩) → Result⟨V,E₂⟩` | `0xE006` | Recover |
| `map` | `Result⟨V,E⟩ → (V→W) → Result⟨W,E⟩` | `0xE007` | Transform ok |
| `map_err` | `Result⟨V,E₁⟩ → (E₁→E₂) → Result⟨V,E₂⟩` | `0xE008` | Transform err |
| `flatten` | `Result⟨Result⟨V,E⟩,E⟩ → Result⟨V,E⟩` | `0xE009` | Remove nesting |
| `or_else` | `Result⟨V,E₁⟩ → Result⟨V,E₂⟩ → Result⟨V,E₁+E₂⟩` | `0xE00A` | Fallback |
| `unwrap_or` | `Result⟨V,E⟩ → V → V` | `0xE00B` | Default |
| `expect` | `Result⟨V,E⟩ → String → V` | `0xE00C` | Force unwrap |

### §E.4 Monad Laws

```md
## Left identity
∀ v f . ok(v) >>= f ≡ f(v)

## Right identity
∀ m . m >>= ok ≡ m

## Associativity
∀ m f g . (m >>= f) >>= g ≡ m >>= (λx. f(x) >>= g)

## Short-circuit
∀ e f . err(e) >>= f ≡ err(e)
```

### §E.5 Do-Notation

```md
do {
  x ← ok(1);
  y ← ok(2);
  return (x + y)
}
≡ ok(3)

## First error stops the chain
do {
  x ← ok(1);
  y ← err(e);
  return (x + y)
}
≡ err(e)
```

---

## §C Confidence & Probabilistic Logic

> **Full specification**: see `spec_p0_confidence.md`  
> **Verification**: 37/37 tests passing

### §C.1 Core Types

```md
Conf : Type ≝ ℚ ∩ [0, 1]    # confidence value
𝔹̃ : Type ≝ Conf               # fuzzy boolean
P⟨T⟩ : Type ≝ T × Conf       # value with confidence
Dist⟨T⟩ : Type ≝ T → ℝ⁺      # probability distribution
```

### §C.2 Confidence Operations

| Glyph | Type | Fingerprint | Definition |
|-------|------|-------------|------------|
| `⊗̃` | `Conf×Conf→Conf` | `0xC001` | c₁⊗̃c₂ ≝ c₁⊗c₂ |
| `⊕̃` | `Conf×Conf→Conf` | `0xC002` | c₁⊕̃c₂ ≝ c₁⊕c₂⊖c₁⊗c₂ |
| `¬̃` | `Conf→Conf` | `0xC003` | ¬̃c ≝ 1⊖c |
| `⊓` | `Conf×Conf→Conf` | `0xC004` | c₁⊓c₂ ≝ min(c₁,c₂) |
| `⊔` | `Conf×Conf→Conf` | `0xC005` | c₁⊔c₂ ≝ max(c₁,c₂) |
| `≈̃` | `Conf×Conf→Conf` | `0xC006` | tolerance-based |
| `with_c` | `T→Conf→P⟨T⟩` | `0xC007` | attach confidence |
| `conf` | `P⟨T⟩→Conf` | `0xC008` | extract confidence |
| `val` | `P⟨T⟩→T` | `0xC009` | extract value |

### §C.3 Confidence Laws

```md
## Bounds
∀ c:Conf . 0 ≤ c ≤ 1

## Involution
∀ c . ¬̃(¬̃(c)) ≡ c

## Multiplicative identity
∀ c . c ⊗̃ 1 ≡ c

## Multiplicative annihilation
∀ c . c ⊗̃ 0 ≡ 0

## Additive identity
∀ c . c ⊕̃ 0 ≡ c

## Additive bound
∀ c . c ⊕̃ 1 ≡ 1

## De Morgan
¬̃(c₁ ⊓ c₂) ≡ ¬̃(c₁) ⊔ ¬̃(c₂)
¬̃(c₁ ⊔ c₂) ≡ ¬̃(c₁) ⊓ ¬̃(c₂)

## Monotonicity
∀ c₁ c₂ . c₁ ≤ c₂ ⇒ ∀ op . op(c₁) ≤ op(c₂)
```

### §C.4 Distributions

| Glyph | Type | Fingerprint | Notes |
|-------|------|-------------|-------|
| `Bern(p)` | `ℝ→Dist 𝔹` | `0xC010` | coin flip, Bern(p)(⊤)=p |
| `Bin(n,p)` | `ℝ×ℝ→Dist ℕ` | `0xC011` | n flips |
| `Norm(μ,σ²)` | `ℝ×ℝ⁺→Dist ℝ` | `0xC012` | bell curve |
| `Exp(λ)` | `ℝ⁺→Dist ℝ⁺` | `0xC013` | waiting time |
| `Unif(a,b)` | `ℝ×ℝ→Dist ℝ` | `0xC014` | flat |
| `Beta(α,β)` | `ℝ⁺×ℝ⁺→Dist [0,1]` | `0xC015` | prior for p |
| `Cat(probs)` | `List⟨ℝ⟩→Dist ℕ` | `0xC016` | multi-class |
| `Dirac(v)` | `T→Dist⟨T⟩` | `0xC017` | certain value |

### §C.5 Distribution Laws

```md
## Normalization (discrete)
∀ dist:Dist⟨ℕ⟩ . Σₙ dist(n) ≡ 1

## Normalization (continuous)
∀ dist:Dist⟨ℝ⟩ . ∫ dist(x)dx ≡ 1

## Bernoulli
Bern(p)(⊤) ≡ p
Bern(p)(⊥) ≡ 1⊖p

## Dirac (certainty)
∀ v . Dirac(v)(v) ≡ 1
∀ v w . v≠w ⇒ Dirac(v)(w) ≡ 0

## Expectation linearity
expect(λx.a⊗x⊕b, dist) ≡ a⊗expect(dist)⊕b

## Variance of linear transform
var(λx.a⊗x, dist) ≡ a²⊗var(dist)
```

### §C.6 Bayes' Theorem (Declarative)

```md
## Canonical form
∀ H E . P(H|E) ≡ P(E|H) ⊗ P(H) / P(E)

## Law of Total Probability
∀ H₁…Hₙ partition . P(E) ≡ Σᵢ P(E|Hᵢ)⊗P(Hᵢ)

## Chain Rule
∀ A B . P(A∩B) ≡ P(A)⊗P(B|A)

## Conditional Independence
A ⊥ B | C  ⇔  P(A|B,C) ≡ P(A|C)
```

### §C.7 Inference Operations

| Glyph | Type | Fingerprint | Meaning |
|-------|------|-------------|---------|
| `observe` | `Dist⟨T⟩→(T→𝔹)→Dist⟨T⟩` | `0xC020` | Bayesian update |
| `infer` | `Dist⟨T⟩→(T→𝔹)→Dist⟨T⟩` | `0xC021` | alias for observe |
| `expect` | `Dist⟨ℝ⟩→ℝ` | `0xC022` | E[X] |
| `var` | `Dist⟨ℝ⟩→ℝ⁺` | `0xC023` | Var(X) |
| `sample` | `Dist⟨T⟩→T` | `0xC024` | random draw |
| `n_samples` | `Dist⟨T⟩→ℕ→List⟨T⟩` | `0xC025` | MC sampling |
| `mcmc` | `Dist⟨T⟩→ℕ→List⟨T⟩` | `0xC026` | Markov chain |
| `map_est` | `Dist⟨T⟩→T` | `0xC027` | argmax posterior |
| `entropy` | `Dist⟨T⟩→ℝ⁺` | `0xC028` | H(X) = −Σp·log(p) |

### §C.8 AI Communication with Confidence

```md
## Message with confidence
Msg⟨T⟩ ≝ {
  sender    : AgentID,
  payload   : P⟨T⟩,
  timestamp : Time,
  evidence  : List⟨Fact⟩
}

## Take more confident
combine_msgs(m₁, m₂) ≝
  if conf(m₁) > conf(m₂) then m₁ else m₂

## Weighted consensus
consensus(msgs) : P⟨T⟩ ≝
  let total ≝ Σ conf(m) in
  let weighted ≝ Σ val(m)⊗conf(m) / total in
  (weighted, pooled_conf)

## Trust calibration
trust : AgentID → Conf
calibrated_conf(m) ≝ conf(m) ⊗ trust(sender(m))
```

### §C.9 Fuzzy Logic (Kleene 3-Valued)

```md
𝔹₃ ≝ {⊥, ?, ⊤}

## AND (min)
a ⊓ b ≝ min(a, b)

## OR (max)
a ⊔ b ≝ max(a, b)

## NOT
¬⊥ ≡ ⊤
¬? ≡ ?
¬⊤ ≡ ⊥

## Ordering
⊥ < ? < ⊤
```

### §C.10 Calibration Iron Law

> **Law IX**: Any AI claiming confidence `c` MUST, over a
> sufficiently large test set, achieve empirical accuracy
> within ±0.05 of `c`. Overconfident AIs are penalized
> in `consensus()`.

---

## §I I/O Boundary & Effects

> **Full specification**: see `spec_p0_io.md`  
> **Verification**: 25/25 tests passing

### §I.1 Effect Tags

```md
Effect : Type

Pure      : Effect   # no observable effect
IO(String): Effect   # input/output with resource
Comm(Ch)  : Effect   # communication on channel
Spawn     : Effect   # create agent
Die       : Effect   # terminate
Net(Addr) : Effect   # network call
FS(Path)  : Effect   # file system
Time      : Effect   # time-dependent
Rand      : Effect   # random number
```

### §I.2 Effect Operations

| Glyph | Type | Fingerprint | Meaning |
|-------|------|-------------|---------|
| `⊕ₑ` | `Effect×Effect→Effect` | `0xI001` | Effect sum |
| `≤ₑ` | `Effect×Effect→𝔹` | `0xI002` | Effect ordering |
| `print` | `String→IO Unit` | `0xI001` | Write stdout |
| `readln` | `IO String` | `0xI002` | Read stdin |
| `read_file` | `Path→IO Result⟨String,IOErr⟩` | `0xI003` | File read |
| `write_file` | `Path→String→IO Result⟨Unit,IOErr⟩` | `0xI004` | File write |
| `append_file` | `Path→String→IO Result⟨Unit,IOErr⟩` | `0xI005` | File append |
| `delete_file` | `Path→IO Result⟨Unit,IOErr⟩` | `0xI006` | File delete |
| `exists` | `Path→IO 𝔹` | `0xI007` | Exists check |
| `mkdir` | `Path→IO Result⟨Unit,IOErr⟩` | `0xI008` | Mkdir |
| `list_dir` | `Path→IO Result⟨List⟨Path⟩,IOErr⟩` | `0xI009` | List dir |
| `send` | `Addr→Msg→IO Result⟨Unit,NetErr⟩` | `0xI00A` | Network send |
| `recv` | `Addr→IO Result⟨Msg,NetErr⟩` | `0xI00B` | Network recv |
| `connect` | `Addr→IO Result⟨Conn,NetErr⟩` | `0xI00C` | Open conn |
| `close` | `Conn→IO Unit` | `0xI00D` | Close conn |
| `http_get` | `URL→IO Result⟨Response,NetErr⟩` | `0xI00E` | HTTP GET |
| `http_post` | `URL→Body→IO Result⟨Response,NetErr⟩` | `0xI00F` | HTTP POST |
| `now` | `IO Time` | `0xI010` | Wall clock |
| `rand` | `IO ℝ` | `0xI011` | Random [0,1) |
| `rand_int` | `ℕ→ℕ→IO ℕ` | `0xI012` | Random [a,b] |
| `sleep` | `ℕ→IO Unit` | `0xI013` | Block n ticks |
| `spawn_io` | `IO()→IO AgentID` | `0xI014` | Create agent |
| `kill` | `AgentID→IO Unit` | `0xI015` | Terminate |
| `log` | `Level→String→IO Unit` | `0xI016` | Structured log |

### §I.3 Effect System

```md
## Effect sum
IO(a) ⊕ₑ IO(b) ≝ IO(a+b)
IO(a) ⊕ₑ Comm(c) ≝ IO(a) + Comm(c)

## Effect ordering
Pure ≤ₑ Comm ≤ₑ IO

## Effect laws
∀ e . Pure ⊕ₑ e ≡ e
∀ e . e ⊕ₑ e ≡ e          # idempotent
∀ a b c . (a⊕ₑb)⊕ₑc ≡ a⊕ₑ(b⊕ₑc)  # associative

## Function effect annotations
f : A → B       # pure
g : A →ᵢₒ B     # has IO effect
h : A →ᶜ B      # has communication
k : A →^{IO+Comm} B  # multiple effects
```

### §I.4 I/O Laws

```md
## Write-then-read (causal)
write_file(p, s); read_file(p) ≡ ok(s)

## Delete-then-exists
delete_file(p); exists(p) ≡ ok(⊥)

## Append associativity
write_file(p,a); append_file(p,b) ≡ write_file(p, a⊕b)

## GET idempotent
http_get(url); http_get(url) ≡ http_get(url)

## POST not idempotent
http_post(url,b); http_post(url,b) ≠ http_post(url,b)

## Resource linearity
∀ r . open(r); use(r); close(r)  # exactly one close
∀ r . close(r); close(r) ≡ err(DoubleClose)
∀ r . close(r); use(r) ≡ err(UseAfterClose)
```

### §I.5 Resource Safety

```md
## RAII-style
with_file : Path → (Handle→IO A) → IO Result⟨A,IOErr⟩
with_file(p, f) ≝
  do {
    h ← open(p);
    result ← f(h);
    close(h);
    return result
  }

## Verifier checks:
## - every open has exactly one close
## - no use after close
## - no double close
## - resource not leaked on error paths
```

### §I.6 FFI (Foreign Function Interface)

```md
## FFI Declaration Syntax
foreign import "rust" sqrt : ℝ → ℝ
  ensures: result ≥ 0
  ensures: result² ≈ input (within 1e-10)
  effect: Pure

foreign import "python" torch_infer : Tensor → Tensor
  effect: IO
  ensures: output.shape ≡ input.shape
  timeout: 30000

foreign import "sql" query : String → IO Result⟨Rows,SqlErr⟩
  effect: IO + Comm
  ensures: read-only if starts with "SELECT"
  timeout: 5000

foreign import "system" exec : String → IO Result⟨String,ExecErr⟩
  effect: IO + FS + Net
  ⚠️ requires: capability(CmdExec)
```

### §I.7 FFI Laws

```md
## Opaque functions: only contracts matter
∀ f:foreign . cannot_reason_about(f's internals)

## Pre-conditions must be checked by caller
foreign "x" f : A → B requires: pre(A)
caller must prove: pre(a) before calling

## Post-conditions are enforced by Verifier
foreign "x" f : A → B ensures: post(B)
Verifier checks: post(f(a)) via testing

## Effects must be declared
foreign "x" f : A →ᵢₒ B
caller's effect type must include IO
```

### §I.8 Capability System

```md
Capability : Type

ReadFile   : Capability
WriteFile  : Capability
Network    : Capability
CmdExec    : Capability
SpawnAgent : Capability

## Granting
grant : Capability → Agent → Effect
revoke : Capability → Agent → Effect

## Laws
∀ c a . grant(c,a); revoke(c,a) ≡ unit
∀ c a . ¬has_cap(c,a) ⇒ foreign_call_requiring(c) fails

## Safe ops (idempotent)
safe_ops ≝ { http_get, read_file, exists, list_dir, recv, connect, now, rand, log }

## Unsafe ops
unsafe_ops ≝ { http_post, http_put, http_delete, write_file, delete_file, send, exec, kill }
```

### §I.9 Iron Laws for I/O

> **Law X (Effect Transparency)**: Every function performing
> I/O MUST declare its effect type. Undeclared = rejected.
>
> **Law XI (Capability Discipline)**: No foreign call may
> execute without required capabilities explicitly granted.
>
> **Law XII (Resource Linearity)**: Every opened resource
> must be closed exactly once, or use a `with_*` combinator.

---

## §V Verifier Architecture

### §V.1 Verifier Pipeline

```
┌──────────────┐
│  MD Source    │  (human/AI authored)
└──────┬───────┘
       ▼
┌──────────────┐
│  Parser       │  → AST (typed)
└──────┬───────┘
       ▼
┌──────────────┐
│ Package Loader│  → resolve imports, check fingerprints
└──────┬───────┘
       ▼
┌──────────────┐
│ Type Checker  │  → effect inference, capability check
└──────┬───────┘
       ▼
┌──────────────┐
│ Law Checker   │  → verify algebraic laws
└──────┬───────┘
       ▼
┌──────────────┐
│ Test Runner   │  → execute canonical tests
└──────┬───────┘
       ▼
┌──────────────┐
│ Race Detector │  → happens-before analysis
└──────┬───────┘
       ▼
┌──────────────┐
│ Resource Check│  → linearity verification
└──────┬───────┘
       ▼
┌──────────────┐
│ Verdict       │  → ✅ Certified / ❌ Rejected
└──────────────┘
```

### §V.2 Verifier Pseudo-Code

```rust
struct Verifier {
    symbols: HashMap<Fingerprint, Symbol>,
    packages: HashMap<PackageName, Package>,
    laws: Vec<Law>,
    tests: Vec<TestCase>,
}

impl Verifier {
    fn verify(&mut self, source: &Module) -> Result<Certification, Vec<Violation>> {
        let mut violations = vec![];

        // 1. Parse
        let ast = match parse(source) {
            Ok(ast) => ast,
            Err(e) => return Err(vec![Violation::ParseError(e)]),
        };

        // 2. Load packages & check Iron Laws
        for pkg in &ast.imports {
            if let Err(e) = self.load_package(pkg) {
                violations.push(e);
            }
        }

        // 3. Type check + effect inference
        if let Err(e) = self.type_check(&ast) {
            violations.push(e);
        }

        // 4. Law verification
        for law in &self.laws {
            if let Err(e) = self.verify_law(law, &ast) {
                violations.push(e);
            }
        }

        // 5. Test execution
        for test in &ast.tests {
            if let Err(e) = self.run_test(test) {
                violations.push(e);
            }
        }

        // 6. Race detection
        if let Err(e) = self.check_race_free(&ast) {
            violations.push(e);
        }

        // 7. Resource linearity
        if let Err(e) = self.check_resource_safety(&ast) {
            violations.push(e);
        }

        // 8. Timing contracts (if async)
        if ast.has_async() {
            if let Err(e) = self.check_timing_contract(&ast) {
                violations.push(e);
            }
        }

        if violations.is_empty() {
            Ok(Certification::new(ast.fingerprint()))
        } else {
            Err(violations)
        }
    }
}
```

### §V.3 What Verifier Does NOT Do

```md
❌ Does not execute business logic
❌ Does not benchmark performance
❌ Does not choose algorithms
❌ Does not optimize code
❌ Does not interpret natural language
❌ Does not train models

✅ Only checks: laws satisfied?
✅ Only checks: tests pass?
✅ Only checks: effects declared?
✅ Only checks: resources linear?
✅ Only checks: races absent?
✅ Only checks: fingerprints unique?
```

### §V.4 Verifier Consensus Conformance Clause (Law XIII, promoted 2026-08-01)

```md
## Conformance
A Verifier implementation is "conforming" iff:

1. Reproducibility: same spec → same verdict, across runs, machines, and time.
2. Cross-implementation agreement: on the shared corpus (`corpus/`),
   every conforming Verifier yields the same pass/fail verdict per module
   as the reference set (Python / Rust / Elixir).
3. Shared corpus: `corpus/*.md` (12 modules, covering `## Operation:` and
   `###` block styles, PASS/FAIL verdicts, §T/§E/§C semantics, Laws XIII–XVI).

## Verification record (2026-08-01)
12/12 corpus modules agree across Python / Rust / Elixir:
- PASS×6 (arith, conf, encoding, error, time, compat_ok) — all tests executed
- FAIL×6 (missing_laws → Law III, missing_tests → Law IV, negative_missing → Law XIV,
  ghost_export → Law XV, hidden_export → Law XV, compat_break → Law XVI)

## Enforcement
- New Verifier implementations must pass the corpus before being trusted.
- Spec changes must not break corpus agreement without an explicit
  RFC + corpus update (Law VI).
```

---

## §A Appendix: Complete Symbol Index

### A.1 Core (always available)

```
ℕ ℤ ℚ ℝ ℂ 𝔹 Sym String Prop
× + → ↝ λ ∀ ∃
⊤ ⊥ ⊨ ⊢ ¬ ∧ ∨ ⇒ ⇔
≡ ≠ ≤ ≥ < >
∑ ∏ ∫ ∂ ∇ Δ d/dx lim ∞
∈ ∉ ⊆ ⊂ ∪ ∩ ∅
```

### A.2 Time Module (§T)

```
⏰ ⏳ ⏱ ⌛ →ᵢₒ ∥ᵢₒ clock vc tick timeout retry race after periodic
```

### A.3 Error Module (§E)

```
Result⟨V,E⟩ ok err
>>= >> |> try throw catch map map_err flatten or_else unwrap_or expect
```

### A.4 Confidence Module (§C)

```
Conf 𝔹̃ P⟨T⟩ Dist⟨T⟩
⊗̃ ⊕̃ ¬̃ ⊓ ⊔ ≈̃ with_c conf val
Bern Bin Norm Exp Unif Beta Cat Dirac
observe infer expect var sample n_samples mcmc map_est entropy
⊢_c ~ ⊥ (indep) | (conditional)
```

### A.5 I/O Module (§I)

```
Effect Pure IO Comm Spawn Die Net FS Time Rand
⊕ₑ ≤ₑ
print readln read_file write_file append_file delete_file exists mkdir list_dir
send recv connect close http_get http_post now rand rand_int sleep spawn_io kill log
foreign import grant revoke capability
```

### A.6 Math Domains (standard library, import required)

```
# math.calculus
∫ ∂ ∇ Δ d/dt ℱ ℱ⁻¹ * δ sinc

# math.linear
M(m×n,R) v·w Aᵀ A⁻¹ det(A) tr(A) rank(A) ‖v‖ λᵢ Iₙ ⊕ ⨁

# finance.base
PV FV NPV IRR Δ Γ Θ ν ρ N e^{rt} max(a,b)

# stat.probability
P(A) E[X] Var(X) Cov(X,Y) ρ(X,Y) ∼ ⊥ |

# opt.gradient
argmin argmax ∇f=0 H(f) s.t. λ KKT
```

### A.7 Iron Laws Summary

```
Law I    — Fingerprint Uniqueness
Law II   — Encoding to ℕ
Law III  — Law Declaration
Law IV   — Test Mandatory
Law V    — No Implementation in Spec
Law VI   — Backward Compatibility
Law VII  — Explicit Dependencies
Law VIII — Temporal Determinism
Law IX   — Calibration Requirement
Law X    — Effect Transparency
Law XI   — Capability Discipline
Law XII  — Resource Linearity
```

---

## §Z Versioning & Evolution

```md
## Core Versioning
core@1.0  — frozen forever (ℕ ℤ ℚ ℝ ℂ + logic)
core@1.x  — bug fixes only, no semantic changes

## Standard Library
math.calculus@1.0  → 1.x (additive: new symbols, no breaking)
finance.base@1.0     → 2.0 (breaking: new required laws)

## Breaking Change Protocol
1. RFC process (Request for Comments)
2. 6-month deprecation warning
3. Migration tool provided
4. Old version remains loadable
5. Compatibility Proof (Law XVI): any version claiming "backward compatible"
   must pass the previous version's canonical suite, embedded as
   `## Compat Tests` in the new spec. Verifier rejects the claim on failure.
   (See spec_top_extensions.md E-05; enforced by all three verifiers.)

## Custom Packages
emoji.finance@0.1 → 1.0 (stable, fingerprint prefix locked)
tcm.wuzang@0.1 (experimental)
```

---

## §F Final Notes

> **ΣLang is not a programming language.**
> **It is a contract between intelligences.**
>
> Humans write the laws.
> AIs write the implementations.
> The Verifier judges.
> The tests decide.

### What ΣLang is:
✅ A semantic protocol  
✅ A mathematical specification language  
✅ A verifiable AI communication standard  
✅ A package system for domain knowledge  

### What ΣLang is NOT:
❌ A general-purpose programming language  
❌ A replacement for Python/Rust/Elixir  
❌ A natural language processing tool  
❌ A machine learning framework  
❌ A human-friendly syntax  

### The Vision

```
┌─────────────────────────────────────────────┐
│             AI Agent A                      │
│  writes ΣLang code → Verifier checks → ✅   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           ΣLang Verifier                    │
│  Laws ✓  Tests ✓  Effects ✓  Races ✓      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│             AI Agent B                      │
│  reads ΣLang spec → implements → tests ✓   │
│  output ≡ Agent A's output (by test suite)  │
└─────────────────────────────────────────────┘
```

**This is the end goal: AI-to-AI semantic interoperability,**
**guaranteed by mathematics, not by hope.**

---

*End of ΣLang P0 Foundations Specification v0.3.0*  
*Verified: 95/95 tests passing*  
*License: MIT*
