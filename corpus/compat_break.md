# Module: compat_break
# Version: 2.0.0
# Expected: FAIL (E-05 — Compatibility Proof)
# Style: tensor_ops
# Domain: evolution (E-05 — Compatibility Proof)
# Intent: declares `## Compat Tests` (the v1.0 canonical suite); the v2.0
# definitions break one of them → "backward compatible" claim rejected.

## Imports

```md
import core
import math.base
```

## Compat Tests

```md
## From v1.0 canonical suite (must all pass on v2.0)

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| 2 ⊕ 3 | 4 |
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF102
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
