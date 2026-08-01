# Module: eval_break
# Version: 1.0.0
# Expected: FAIL (E-10 — Malformed Determinism)
# Style: tensor_ops + determinism declaration
# Intent: declares `## Determinism` with an invalid precision (zero) and an
# unsupported rounding mode → E-10 must reject.

## Imports

```md
import core
```

## Determinism

```md
precision: 0
rounding: banker
sort_stability: maybe
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF602
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
