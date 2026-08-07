# Module: std_math_base_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: math
# Intent: verifier test set for the v0.11 std package `math.base@1.0`
# (std/math.base.md) — arithmetic operators ⊖ ⊘ ⊙ ≡ ≥ ≤ ∈ must behave
# identically across Python / Rust / Elixir. Reuses the canonical
# expression patterns already proven by math_ops_ok.md.

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
Fingerprint: 0xA030
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
| 5 ⊖ 0 | 5 |
| [1] ⊖ [1,2] | ⊥ ShapeError |
| [1,2,3,4] ⊖ [1,2,3] | ⊥ ShapeError |
| [1,2,3,4,5] ⊖ [1,2,3,4] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊖ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊖ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊖ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊖ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊖ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊖ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊖ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊖ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊖ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊖ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊖ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊖ [1,2,3,4,5,6,7,8,9,10,11,12] | ⊥ ShapeError |

## Operation: ⊘ (Div)

### Signature

```md
⊘ : ℕ × ℕ → ℚ
Fingerprint: 0xA031
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
| 0 ⊘ 2 | 0 |
| 5 ⊘ 0 | ⊥ DivByZero |

## Operation: ⊙ (Hadamard)

### Signature

```md
⊙ : ℕ × ℕ → ℕ
Fingerprint: 0xA032
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
| [1,2] ⊙ [1] | ⊥ ShapeError |
| [1,2,3,4] ⊙ [1,2,3] | ⊥ ShapeError |
| [1,2,3,4,5] ⊙ [1,2,3,4] | ⊥ ShapeError |
| [1] ⊙ [1,2] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊙ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊙ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊙ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊙ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊙ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊙ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊙ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊙ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊙ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊙ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊙ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊙ [1,2,3,4,5,6,7,8,9,10,11,12] | ⊥ ShapeError |

## Operation: ≡ (Eq)

### Signature

```md
≡ : ℕ × ℕ → ℕ
Fingerprint: 0xA033
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
Fingerprint: 0xA034
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
| 2 ≥ 2 | 1 |
| [1] ≥ 2 | ⊥ TypeError |

## Operation: ≤ (Le)

### Signature

```md
≤ : ℕ × ℕ → ℕ
Fingerprint: 0xA035
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
| 2 ≤ 2 | 1 |
| 2 ≤ [1] | ⊥ TypeError |

## Operation: ∈ (In)

### Signature

```md
∈ : ℕ × List⟨ℕ⟩ → ℕ
Fingerprint: 0xA036
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
| 2 ∈ [] | 0 |
| 2 ∈ 3 | ⊥ TypeError |
