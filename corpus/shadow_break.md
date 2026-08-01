# Module: shadow_break
# Version: 1.0.0
# Expected: FAIL (§S — Duplicate Symbol / Shadow Target Missing)
# Style: tensor_ops + shadowing
# Intent: defines the same operation name twice (DuplicateSymbol) and declares
# a `## Shadowing` target that does not exist (ShadowTargetMissing) →
# §S must reject both.

## Imports

```md
import core
```

## Shadowing

```md
shadow ghost_op
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xFA01
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

## Operation: ⊕ (Add Again)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xFA02
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 1 ⊕ 1 | 2 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
