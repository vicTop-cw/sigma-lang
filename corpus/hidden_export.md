# Module: hidden_export
# Version: 0.1.0
# Expected: FAIL (E-04 — Hidden Export)
# Style: tensor_ops
# Intent: a defined symbol (`⊗`) is missing from `## Exports`;
# E-04 must report HiddenExport.

## Imports

```md
import core
```

## Exports

```md
⊕
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF005
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

## Operation: ⊗ (Mul)

### Signature

```md
⊗ : ℕ × ℕ → ℕ
Fingerprint: 0xF006
```

### Laws

```md
∀ a b . a ⊗ b ≡ b ⊗ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊗ 3 | 6 |
| [1] ⊗ [1,2] | ⊥ ShapeError |
