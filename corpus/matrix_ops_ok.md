# Module: matrix_ops_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: math
# Intent: exercises the v0.10 basic-operation set — identity I₂, matrix ×
# vector ⊗, elementwise ⊕ on lists, and index() with tuple paths — on PASS
# and FAIL (⊥) sides, across all three verifiers.

## Imports

```md
import core
import math.linear
```

## Exports

```md
⊕
⊗
index
```

## Operation: ⊕ (Elemwise Add)

### Signature

```md
⊕ : List⟨ℕ⟩ × List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xA020
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
∀ a . a ⊕ [] ≡ a
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |

## Operation: ⊗ (MatMul)

### Signature

```md
⊗ : List⟨List⟨ℕ⟩⟩ × List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xA021
```

### Laws

```md
∃ I₂ . ∀ A . A ⊗ I₂ ≡ A
∀ A B C . A ⊗ (B ⊕ C) ≡ (A ⊗ B) ⊕ (A ⊗ C)
```

### Tests

| Input | Output |
|-------|--------|
| I₂ ⊗ [1,2] | [1,2] |
| [[1,2],[3,4]] ⊗ [1,0] | [1,3] |
| [[1,2],[3,4]] ⊗ [1] | ⊥ ShapeError |

## Operation: index

### Signature

```md
index : List⟨ℕ⟩ × (ℕ,ℕ) → ℕ
Fingerprint: 0xA022
```

### Laws

```md
∀ l i . i < |l| ⇒ index(l, i) < ∞
∀ l . index(l, 0) ≡ head(l)
```

### Tests

| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| index([[1,2],[3,4]], (1,0)) | 3 |
| index([1,2], 9) | ⊥ OutOfBounds |

## Functions

### encode_vec

```md
encode_vec : List⟨ℕ⟩ → ℕ
```
