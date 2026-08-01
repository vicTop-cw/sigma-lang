# Module: missing_tests
# Version: 0.1.0
# Expected: FAIL (Law IV — No Tests Defined)
# Style: tensor_ops
# Intent: an operation with a fingerprint and laws but NO canonical test must be rejected.

## Imports

```md
import core
```

## Operation: ⊖ (Sub)

### Signature

```md
⊖ : ℕ × ℕ → ℕ
Fingerprint: 0xE001
```

### Laws

```md
∀ a . a ⊖ 0 ≡ a
```
