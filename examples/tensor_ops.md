# Module: tensor_ops

> Example ΣLang module demonstrating tensor operations with full semantic specification.

## Imports

```md
import core
import math.linear
```

## Type Definition

```md
Tensor⟨D, R⟩ : Type
  D ∈ ℕ  (dimensionality)
  R ∈ {ℝ, ℤ, ℚ}  (element type)

Invariant: rank(Tensor) ≡ D
```

## Operation: ⊕ (Element-wise Addition)

### Signature

```md
⊕ : Tensor⟨D,R⟩ × Tensor⟨D,R⟩ → Tensor⟨D,R⟩
Fingerprint: 0xM100
```

### Laws

```md
## Associativity
∀ a b c . (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)

## Commutativity
∀ a b . a ⊕ b ≡ b ⊕ a

## Identity
∃ 0 : Tensor⟨D,R⟩ . ∀ a . a ⊕ 0 ≡ a

## Shape constraint
∀ a b . shape(a) ≡ shape(b) ⇒ shape(a⊕b) ≡ shape(a)
```

### Ownership

```md
&a ↶ lhs
&b ↶ rhs
→ new allocation (cannot reuse a or b's storage)
```

### Tests

| Input | Output |
|-------|--------|
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| [0,0] ⊕ [0,0] | [0,0] |
| [−1,2] ⊕ [1,−2] | [0,0] |

## Operation: ⊗ (Matrix Multiplication)

### Signature

```md
⊗ : Tensor⟨2,R⟩ × Tensor⟨2,R⟩ → Tensor⟨2,R⟩
Fingerprint: 0xM101
```

### Laws

```md
## Associativity
∀ A B C . (A⊗B)⊗C ≡ A⊗(B⊗C)

## Distributivity over ⊕
∀ A B C . A⊗(B⊕C) ≡ (A⊗B)⊕(A⊗C)

## Identity
∃ I . ∀ A . A⊗I ≡ I⊗A ≡ A
```

### Tests

| Input | Output |
|-------|--------|
| I₂ ⊗ [1,2] | [1,2] |
| [[1,2],[3,4]] ⊗ [1,0] | [1,3] |
| A⊗B where shape mismatch | ⊥ ShapeError |

## Operation: index

### Signature

```md
index : Tensor⟨D,R⟩ × ℕ^D → R
Fingerprint: 0xM102
```

### Laws

```md
∀ t . index(t, (0,0)) ≡ t[0,0]
∀ t i j . index(t, (i,j)) ≡ t[i,j]
```

### Tests

| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| index([[1,2],[3,4]], (1,0)) | 3 |

## Verification

This module declares:
- 3 operations with fingerprints
- 8 algebraic laws
- 9 canonical tests

Verifier will check:
1. Fingerprint uniqueness ✓
2. Law adherence (via tests) ✓
3. Encoding to ℕ for all non-numeric types ✓
4. Ownership annotations present ✓
