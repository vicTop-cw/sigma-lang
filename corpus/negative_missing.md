# Module: negative_missing
# Version: 0.1.0
# Expected: FAIL (E-02 — No Negative Test)
# Style: tensor_ops
# Intent: an operation with a fingerprint, laws, and a success test but NO
# negative (⊥/error-path) test must be rejected by E-02.

## Imports

```md
import core
```

## Operation: ∘ (Compose)

### Signature

```md
∘ : ℕ × ℕ → ℕ
Fingerprint: 0xF003
```

### Laws

```md
∀ a . a ∘ 0 ≡ a
∀ a b . a ∘ b ≡ b ∘ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
