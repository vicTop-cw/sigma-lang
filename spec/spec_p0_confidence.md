# §C — Confidence & Probabilistic Logic

> **Status**: P0 — Foundational (AI lives in uncertainty, not boolean)
> **Depends**: core@1.0, error@1.0
> **Fingerprint prefix**: `0xC000`–`0xC0FF`

---

## C.1 Motivation

AI never says "true" or "false". It says:
- "I'm 73% sure this is a cat"
- "There's a 0.2% chance this transaction is fraud"
- "Confidence: low — need more data"

A boolean `𝔹 = {⊤, ⊥}` is **insufficient**. ΣLang must provide:
- Graded truth (confidence values)
- Probabilistic reasoning (Bayes, conditioning)
- Uncertain communication between AIs
- Verifiable uncertainty (not just "vibes")

---

## C.2 Core Types

```md
## Confidence
Conf : Type ≝ ℚ ∩ [0, 1]

## Fuzzy Boolean
𝔹̃ : Type ≝ Conf   # degree of truth

## Probabilistic Value
P⟨T⟩ : Type ≝ T × Conf   # value with confidence

## Distribution
Dist⟨T⟩ : Type ≝ T → ℝ⁺   # probability density/mass
  Constraint: Σₜ density(t) ≡ 1  (for discrete)
  Constraint: ∫ density(t)dt ≡ 1  (for continuous)
```

---

## C.3 Confidence Operations

| Glyph | Name | Type | Fingerprint | Meaning |
|-------|------|------|-------------|---------|
| `⊗̃` | Conf multiply | `Conf × Conf → Conf` | `0xC001` | c₁ ⊗̃ c₂ ≝ c₁⊗c₂ |
| `⊕̃` | Conf add (union) | `Conf × Conf → Conf` | `0xC002` | c₁⊕̃c₂ ≝ c₁⊕c₂⊖c₁⊗c₂ |
| `¬̃` | Conf negate | `Conf → Conf` | `0xC003` | ¬̃c ≝ 1⊖c |
| `⊓` | Conf min (AND) | `Conf × Conf → Conf` | `0xC004` | c₁ ⊓ c₂ ≝ min(c₁,c₂) |
| `⊔` | Conf max (OR) | `Conf × Conf → Conf` | `0xC005` | c₁ ⊔ c₂ ≝ max(c₁,c₂) |
| `≈̃` | Conf equivalence | `Conf × Conf → Conf` | `0xC006` | tolerance-based |
| `with_c` | Attach confidence | `T → Conf → P⟨T⟩` | `0xC007` | v with_c c ≝ (v, c) |
| `conf` | Extract confidence | `P⟨T⟩ → Conf` | `0xC008` | conf((v,c)) ≝ c |
| `val` | Extract value | `P⟨T⟩ → T` | `0xC009` | val((v,c)) ≝ v |

---

## C.4 Confidence Laws

### C.4.1 Bounds

```md
∀ c:Conf . 0 ≤ c ≤ 1

∀ c . ¬̃(¬̃(c)) ≡ c
```

### C.4.2 Multiplicative (Independent Events)

```md
## ⊗̃ = multiply
c₁ ⊗̃ c₂ ≝ c₁ ⊗ c₂

## Laws
∀ c . c ⊗̃ 1 ≡ c          # identity
∀ c . c ⊗̃ 0 ≡ 0          # annihilation
∀ c₁ c₂ c₃ . (c₁⊗̃c₂)⊗̃c₃ ≡ c₁⊗̃(c₂⊗̃c₃)  # associative
∀ c₁ c₂ . c₁⊗̃c₂ ≡ c₂⊗̃c₁                            # commutative
```

### C.4.3 Additive (Union of Events)

```md
## ⊕̃ = probabilistic union
c₁ ⊕̃ c₂ ≝ c₁ ⊕ c₂ ⊖ c₁⊗c₂

## Laws
∀ c . c ⊕̃ 0 ≡ c
∀ c . c ⊕̃ 1 ≡ 1
∀ c₁ c₂ . c₁⊕̃c₂ ≡ c₂⊕̃c₁
```

### C.4.4 De Morgan for Confidence

```md
¬̃(c₁ ⊓ c₂) ≡ ¬̃(c₁) ⊔ ¬̃(c₂)
¬̃(c₁ ⊔ c₂) ≡ ¬̃(c₁) ⊓ ¬̃(c₂)
```

### C.4.5 Monotonicity

```md
∀ c₁ c₂ . c₁ ≤ c₂ ⇒ ∀ op . op(c₁) ≤ op(c₂)
```

---

## C.5 Probabilistic Programming

### C.5.1 Distribution Type

```md
## Discrete distribution
Dist⟨T⟩ : Type ≝ T → ℝ⁺
Constraint: Σ_{t:T} dist(t) ≡ 1

## Continuous distribution
Dist⟨ℝⁿ⟩ : Type ≝ ℝⁿ → ℝ⁺
Constraint: ∫_{ℝⁿ} dist(x)dx ≡ 1
```

### C.5.2 Built-in Distributions

| Glyph | Name | Type | Fingerprint | Notes |
|-------|------|------|-------------|-------|
| `Bern(p)` | Bernoulli | `ℝ → Dist 𝔹` | `0xC010` | coin flip |
| `Bin(n,p)` | Binomial | `ℝ×ℝ → Dist ℕ` | `0xC011` | n flips |
| `Norm(μ,σ²)` | Gaussian | `ℝ×ℝ⁺ → Dist ℝ` | `0xC012` | bell curve |
| `Exp(λ)` | Exponential | `ℝ⁺ → Dist ℝ⁺` | `0xC013` | waiting time |
| `Unif(a,b)` | Uniform | `ℝ×ℝ → Dist ℝ` | `0xC014` | flat |
| `Beta(α,β)` | Beta | `ℝ⁺×ℝ⁺ → Dist [0,1]` | `0xC015` | prior for p |
| `Cat(probs)` | Categorical | `List⟨ℝ⟩ → Dist ℕ` | `0xC016` | multi-class |
| `Dirac(v)` | Point mass | `T → Dist⟨T⟩` | `0xC017` | certain value |

### C.5.3 Distribution Laws

```md
## Bernoulli
Σ_{b:𝔹} Bern(p)(b) ≡ 1
Bern(p)(⊤) ≡ p
Bern(p)(⊥) ≡ 1⊖p

## Normalization
∀ dist:Dist⟨ℝ⟩ . ∫ dist(x)dx ≡ 1

## Dirac (certainty)
∀ v . Dirac(v)(v) ≡ 1
∀ v w . v≠w ⇒ Dirac(v)(w) ≡ 0

## Composition
∀ dist f . (dist ∘ f)(x) ≝ dist(f(x))  # pushforward
```

---

## C.6 Bayes' Theorem (Declarative)

```md
## Bayes (canonical form)
∀ H E . P(H|E) ≡ P(E|H) ⊗ P(H) / P(E)

## Law of Total Probability
∀ H₁…Hₙ partition . P(E) ≡ Σᵢ P(E|Hᵢ) ⊗ P(Hᵢ)

## Chain Rule
∀ A B . P(A∩B) ≡ P(A) ⊗ P(B|A)

## Conditional Independence
A ⊥ B | C  ⇔  P(A|B,C) ≡ P(A|C)
```

---

## C.7 Inference Operations

| Glyph | Name | Type | Fingerprint | Meaning |
|-------|------|------|-------------|---------|
| `observe` | Condition | `Dist⟨T⟩ → (T→𝔹) → Dist⟨T⟩` | `0xC020` | Bayesian update |
| `infer` | Infer posterior | `Dist⟨T⟩ → (T→𝔹) → Dist⟨T⟩` | `0xC021` | alias for observe |
| `expect` | Expected value | `Dist⟨ℝ⟩ → ℝ` | `0xC022` | E[X] |
| `var` | Variance | `Dist⟨ℝ⟩ → ℝ⁺` | `0xC023` | Var(X) |
| `sample` | Draw sample | `Dist⟨T⟩ → T` | `0xC024` | random draw |
| `n_samples` | n draws | `Dist⟨T⟩ → ℕ → List⟨T⟩` | `0xC025` | MC sampling |
| `mcmc` | MCMC inference | `Dist⟨T⟩ → ℕ → List⟨T⟩` | `0xC026` | Markov chain |
| `map_est` | MAP estimate | `Dist⟨T⟩ → T` | `0xC027` | argmax posterior |
| `entropy` | Entropy | `Dist⟨T⟩ → ℝ⁺` | `0xC028` | H(X) = −Σp·log(p) |

### Inference Laws

```md
## Expectation linearity
expect(λx. a⊗x⊕b, dist) ≡ a⊗expect(dist)⊕b

## Variance of linear transform
var(λx. a⊗x, dist) ≡ a² ⊗ var(dist)

## Conditioning on truth
∀ dist p . observe(dist, λx. ⊤) ≡ dist

## Bayes as observe
infer(prior, evidence) ≡ observe(prior, evidence)

## Entropy bounds
∀ dist . 0 ≤ entropy(dist) ≤ log(|support|)
```

---

## C.8 Confidence Propagation

### C.8.1 Lifting Functions

```md
## lift : (A→B) → P⟨A⟩ → P⟨B⟩
lift(f, (v,c)) ≝ (f(v), c)

## lift2 : (A×B→C) → P⟨A⟩ → P⟨B⟩ → P⟨C⟩
lift2(f, (a,ca), (b,cb)) ≝ (f(a,b), ca ⊓ cb)
  # confidence is min (pessimistic)
  # alternative: ca ⊗̃ cb (independence assumption)
```

### C.8.2 Propagation Laws

```md
## Monotonicity of confidence under functions
∀ f . monotonic(f) ⇒ conf(lift(f, x)) ≡ conf(x)

## Composition preserves confidence
∀ f g x . conf(lift(g ∘ f, x)) ≡ conf(lift(f, x))

## Confidence drops with chaining
∀ f g x . conf(lift(g, lift(f, x))) ≤ conf(x)
```

---

## C.9 Fuzzy Logic (Three-Valued & Beyond)

### C.9.1 Kleene Logic

```md
## Truth values
𝔹₃ ≝ {⊥, ?, ⊤}   # false, unknown, true

## Ordering
⊥ < ? < ⊤

## AND (min)
a ⊓ b ≝ min(a, b)

## OR (max)
a ⊔ b ≝ max(a, b)

## NOT
¬⊥ ≡ ⊤
¬? ≡ ?
¬⊤ ≡ ⊥
```

### C.9.2 Łukasiewicz Logic

```md
## Truth values in [0,1]
a ⊕̃ b ≝ min(1, a+b)
a ⊗̃ b ≝ max(0, a+b−1)

## Implication
a →̃ b ≝ min(1, 1−a+b)

## Laws
a →̃ a ≡ 1
a ⊗̃ (a →̃ b) ≤ b        # modus ponens
```

---

## C.10 AI Communication with Confidence

### C.10.1 Message Format

```md
## AI-to-AI message with confidence
Msg⟨T⟩ ≝ {
  sender    : AgentID,
  payload   : P⟨T⟩,        # value + confidence
  timestamp : Time,
  evidence  : List⟨Fact⟩   # supporting facts
}

## Confidence combination across AIs
combine_msgs(m₁:Msg⟨T⟩, m₂:Msg⟨T⟩) : Msg⟨T⟩ ≝
  if conf(m₁) > conf(m₂)
    then m₁
    else m₂   # take more confident

## Weighted consensus
consensus(msgs : List⟨Msg⟨T⟩⟩) : P⟨T⟩ ≝
  let total ≝ Σ conf(m) in
  let weighted ≝ Σ val(m)⊗conf(m) / total in
  (weighted, Σ conf(m)⊗conf(m)/total²)  # pooled confidence
```

### C.10.2 Trust & Calibration

```md
## Trust score
trust : AgentID → Conf

## Calibrated confidence
calibrated_conf(m) ≝ conf(m) ⊗ trust(sender(m))

## Overconfidence penalty
penalty(m) ≝
  if stated_conf(m) > empirical_accuracy(m)
    then reduce_conf(m)
    else m
```

---

## C.11 Canonical Tests

| Expression | Expected |
|-----------|----------|
| `0.7 ⊗̃ 0.8` | `0.56` |
| `0.7 ⊕̃ 0.8` | `0.94` |
| `¬̃(0.3)` | `0.7` |
| `Bern(0.5)(⊤)` | `0.5` |
| `Norm(0,1) at 0` | `≈ 0.3989` |
| `expect(Norm(μ,σ²))` | `μ` |
| `var(Norm(μ,σ²))` | `σ²` |
| `observe(Bern(0.5), λx.x)` | `Bern(1)` |
| `entropy(Bern(0.5))` | `1.0` |
| `entropy(Dirac(v))` | `0.0` |
| `map_est(Norm(5,1))` | `5` |
| `lift(λx.x+1, (3, 0.9))` | `(4, 0.9)` |
| `lift2(+, (1,0.8), (2,0.9))` | `(3, 0.8)` (min) |
| `¬⊥(⊤)` in Kleene | `⊥` |
| `? ⊔ ⊤` in Kleene | `⊤` |

---

## Implementation Checklist (for AI)

### To pass this module, implement exactly these

1. `conf_mul(c1, c2)` / `conf_add(c1, c2)` / `conf_not(c)` / `conf_min` / `conf_max` — bounded in [0,1], De Morgan holds  [C-01]
2. `bernoulli(p, value)` — `P(X = value)` for `Bern(p)`  [C-02]
3. `normal_pdf(x, mu, sigma)` — Gaussian density with `sigma > 0`  [C-03]
4. `bayes(p_h, p_e_given_h, p_e)` — `P(E)·P(H|E) = P(E|H)·P(H)`; `0` when `P(E) = 0`  [C-04]
5. `entropy_bernoulli(p)` — `0` at the extremes, `1.0` at `p = 0.5`  [C-05]
6. `lift(f, v, c)` / `lift2(f, v1, c1, v2, c2)` — confidence propagates with `min`  [C-06]
7. `kleene_and` / `kleene_or` / `kleene_not` — three-valued truth tables over `{⊤, ?, ⊥}`  [C-07]
8. `weighted_consensus(messages)` — confidence-weighted mean + pooled confidence; `None` on zero total confidence  [C-08]

Reference implementation: `impl/python/sigma_core.py` (§C), self-check via `python3 impl/python/sigma_core.py`.

### What NOT to implement
- Do NOT pick a specific PRNG algorithm — sampling is not part of the semantics.
- Do NOT implement arbitrary-distribution sampling or statistical calibration training.
- Do NOT let confidence escape the [0,1] bounds (Law IX).

---

## C.12 Verifier Rules for Confidence Module

```rust
impl Verifier {
    fn verify_confidence_laws(&self, impl: &dyn ConfImpl) -> Result<(), Violation> {
        // Bounds: 0 ≤ c ≤ 1
        for c in self.conf_values() {
            if c < 0.0 || c > 1.0 {
                return Err(Violation::OutOfBounds(c));
            }
        }

        // Identity: c ⊗̃ 1 ≡ c
        for c in self.conf_values() {
            let result = impl.conf_mul(c, 1.0);
            if !approx_eq(result, c, 1e-10) {
                return Err(Violation::LawFailure {
                    law: "c ⊗̃ 1 ≡ c".to_string(),
                    got: result,
                    expected: c,
                });
            }
        }

        // Involution: ¬̃(¬̃(c)) ≡ c
        for c in self.conf_values() {
            let result = impl.conf_not(impl.conf_not(c));
            if !approx_eq(result, c, 1e-10) {
                return Err(Violation::LawFailure {
                    law: "¬̃(¬̃(c)) ≡ c".to_string(),
                    got: result,
                    expected: c,
                });
            }
        }

        // Distribution normalization
        for dist in self.distributions() {
            let sum = impl.integrate(&dist);
            if !approx_eq(sum, 1.0, 1e-6) {
                return Err(Violation::NotNormalized(sum));
            }
        }

        // Bayes: P(H|E) = P(E|H)P(H)/P(E)
        for (prior, evidence) in self.bayes_pairs() {
            let lhs = impl.condition(prior.clone(), evidence);
            let rhs = impl.bayes_formula(prior, evidence);
            if !impl.dist_approx_eq(&lhs, &rhs, 1e-6) {
                return Err(Violation::BayesViolation);
            }
        }

        Ok(())
    }
}
```

---

## C.13 Iron Law for Confidence Module

> **Law IX (Calibration Requirement)**:
> Any AI claiming a confidence `c` for a prediction MUST,
> over a sufficiently large test set, achieve empirical
> accuracy within ±0.05 of `c`.
>
> Overconfident AIs are penalized in `consensus()`.

---

## C.14 Non-Goals

```md
❌ This module does NOT provide:
  - Frequentist hypothesis testing (p-values) as primitive
    → can be built on top via packages
  - Confidence intervals as primitive
    → build from distributions
  - Fuzzy membership functions as primitive
    → build from 𝔹̃ if needed
  - Dempster-Shafer theory
    → separate package: `uncertainty.ds`
```
