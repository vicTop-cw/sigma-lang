# Module: portability_break
# Version: 0.1.0
# Expected: FAIL (E-03 — Unportable Assertion)
# Style: tensor_ops
# Intent: a test whose expected output is an implementation-specific format
# (a raw Map rendering "Map{scode → [p₁,p₂]}") — E-03 must reject it as
# non-portable. (Note: float strings like "0.333333" are first-class literals
# since the evaluator gained FNum support; a Map rendering is not.)

## Imports

```md
import core
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF203
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 1 ⊕ 2 | Map{scode → [p₁,p₂]} |
| [1] ⊕ [1,2] | ⊥ ShapeError |
