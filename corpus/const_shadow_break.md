# Module: const_shadow_break
# Version: 1.0.0
# Expected: FAIL (§S R5 — Opaque Constant Shadow Attempt)
# Style: tensor_ops + shadowing
# Intent: attempts to shadow §C constant fingerprint `0xK001` (Opaque class,
# §S.3.1 core-constant) → all three verifiers must reject with
# OpaqueShadowAttempt.

## Imports

```md
import core
```

## Shadowing

```md
shadow 0xK001
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xFF01
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
