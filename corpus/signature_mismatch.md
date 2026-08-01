# Module: signature_mismatch
# Version: 0.1.0
# Expected: FAIL (E-06 — Signature Mismatch)
# Style: tensor_ops
# Intent: the operation's signature returns ℕ but one test expects a list —
# an obvious signature/test type conflict that E-06 must reject.

## Imports

```md
import core
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF401
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 2 ⊕ 3 | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
