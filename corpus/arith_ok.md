# Module: arith_ok
# Version: 0.1.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: math
# Intent: locks numeric-literal edge parsing across verifiers — leading '+'
# and exponent literals must be rejected (M-4 literal grammar, matching
# Python's `-?\d+` / Elixir's `^-?\d+$`), while Unicode minus variants
# (U+2212 −, U+FE63 ﹣, U+FF0D －, U+2010 ‐, U+2011 ‑) normalize to ASCII '-'.

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
| +5 ⊕ 1 | ⊥ ParseError |
| 1e3 ⊕ 1 | ⊥ ParseError |
| −5 ⊕ 3 | -2 |
| 5 ⊕ −3 | 2 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
