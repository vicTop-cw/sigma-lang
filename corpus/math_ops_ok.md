# Module: math_ops_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: math
# Intent: exercises the full math-domain operator set (⊖ ⊘ ⊙ ≡ ≥ ≤ ∈)
# in canonical tests, PASS and FAIL (⊥) sides, across all three verifiers.

## Imports

```md
import core
import math.base
```

## Exports

```md
⊖
⊘
⊙
≡
≥
≤
∈
```

## Operation: ⊖ (Sub)

### Signature

```md
⊖ : ℕ × ℕ → ℕ
Fingerprint: 0xA010
```

### Laws

```md
∀ a b c . (a ⊖ b) ⊖ c ≡ a ⊖ (b ⊕ c)
∀ a b . a ⊖ b ≡ a ⊕ (⊖ b)
```

### Tests

| Input | Output |
|-------|--------|
| 5 ⊖ 3 | 2 |
| 10 ⊖ 4 | 6 |
| [1] ⊖ [1,2] | ⊥ ShapeError |

## Operation: ⊘ (Div)

### Signature

```md
⊘ : ℕ × ℕ → ℚ
Fingerprint: 0xA011
```

### Laws

```md
∀ a b c . (a ⊘ b) ⊘ c ≡ a ⊘ (b ⊗ c)
∀ a . a ⊘ 1 ≡ a
```

### Tests

| Input | Output |
|-------|--------|
| 6 ⊘ 2 | 3 |
| 7 ⊘ 2 | 3.5 |
| 5 ⊘ 0 | ⊥ DivByZero |

## Operation: ⊙ (Hadamard)

### Signature

```md
⊙ : ℕ × ℕ → ℕ
Fingerprint: 0xA012
```

### Laws

```md
∀ a b . a ⊙ b ≡ b ⊙ a
∀ a b c . (a ⊙ b) ⊙ c ≡ a ⊙ (b ⊙ c)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊙ 3 | 6 |
| 4 ⊙ 0 | 0 |
| [1] ⊙ [1,2] | ⊥ ShapeError |

## Operation: ≡ (Eq)

### Signature

```md
≡ : ℕ × ℕ → ℕ
Fingerprint: 0xA013
```

### Laws

```md
∀ a . a ≡ a
∀ a b . a ≡ b ⇒ b ≡ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ≡ 2 | 1 |
| 2 ≡ 3 | 0 |
| 2 ≡ [1] | ⊥ TypeError |

## Operation: ≥ (Ge)

### Signature

```md
≥ : ℕ × ℕ → ℕ
Fingerprint: 0xA014
```

### Laws

```md
∀ a . a ≥ a
∀ a b c . a ≥ b ∧ b ≥ c ⇒ a ≥ c
```

### Tests

| Input | Output |
|-------|--------|
| 3 ≥ 2 | 1 |
| 2 ≥ 3 | 0 |
| [1] ≥ 2 | ⊥ TypeError |

## Operation: ≤ (Le)

### Signature

```md
≤ : ℕ × ℕ → ℕ
Fingerprint: 0xA015
```

### Laws

```md
∀ a . a ≤ a
∀ a b . a ≤ b ∨ b ≤ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ≤ 3 | 1 |
| 3 ≤ 2 | 0 |
| 2 ≤ [1] | ⊥ TypeError |

## Operation: ∈ (In)

### Signature

```md
∈ : ℕ × List⟨ℕ⟩ → ℕ
Fingerprint: 0xA016
```

### Laws

```md
∀ x . x ∈ [x]
∀ x . x ∈ [x] ⇒ x ∈ [x, y]
```

### Tests

| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |
