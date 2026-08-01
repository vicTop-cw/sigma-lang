# Module: arith_ok
# Version: 0.1.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: math

## Imports

```md
import core
import math.base
```

## Exports

```md
⊕
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xA001
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
∀ a b c . (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
