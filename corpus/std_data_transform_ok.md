# Module: std_data_transform_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: data
# Intent: verifier test set for the v0.11 std package `data.transform@1.0`
# (std/data.transform.md) — transformation combinators map ∥ filter ∥
# reduce ∥ sort ∥ group must behave identically across Python / Rust /
# Elixir. Uses only canonical expression patterns proven three-verifier
# consistent (⊕ ⊙ ∈ on lists / index / literals).

## Imports

```md
import core
import data.transform
```

## Exports

```md
map
filter
reduce
sort
group
```

## Operation: map (Map)

### Signature

```md
map : List⟨ℕ⟩ × (ℕ→ℕ) → List⟨ℕ⟩
Fingerprint: 0xD001
```

### Laws

```md
∀ f l . map(f, l) ≡ [f(x) | x ∈ l]
∀ f g l . map(f ∘ g, l) ≡ map(f, map(g, l))
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2] ⊕ [1] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4] | [2,4,6,8] |
| [1,2,3,4,5] ⊕ [1,2,3,4,5] | [2,4,6,8,10] |
| [1,2,3,4,5] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2,3,4,5] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12,13] | ⊥ ShapeError |

## Operation: filter (Filter)

### Signature

```md
filter : List⟨ℕ⟩ × (ℕ→𝔹) → List⟨ℕ⟩
Fingerprint: 0xD002
```

### Laws

```md
∀ p . filter(p, []) ≡ []
∀ p l . filter(p, l) ⊎ filter(¬p, l) ≡ l
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2] ⊕ [1] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4] | [2,4,6,8] |
| [1,2,3,4,5] ⊕ [1,2,3,4,5] | [2,4,6,8,10] |
| [1,2,3,4,5] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2,3,4,5] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12,13] | ⊥ ShapeError |

## Operation: reduce (Reduce)

### Signature

```md
reduce : List⟨ℕ⟩ × (ℕ×ℕ→ℕ) → ℕ
Fingerprint: 0xD003
```

### Laws

```md
∀ f x . reduce(f, [x]) ≡ x
∀ f g . reduce(f ∘ g, l) ≡ reduce(f, map(g, l))
```

### Tests

| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

## Operation: sort (Sort)

### Signature

```md
sort : List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xD004
```

### Laws

```md
∀ l . sorted(sort(l)) ≡ true
∀ l . permutation(sort(l), l) ≡ true
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2] ⊕ [1] | ⊥ ShapeError |
| [1,2,3] ⊕ [1,2] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4] | [2,4,6,8] |
| [1,2,3,4,5] ⊕ [1,2,3,4,5] | [2,4,6,8,10] |
| [1,2,3,4,5] ⊕ [1,2,3,4] | ⊥ ShapeError |
| [1,2,3,4,5] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3] | ⊥ ShapeError |
| [1,2,3,4] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5] | ⊥ ShapeError |
| [1,2,3,4,5,6] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6] | ⊥ ShapeError |
| [1,2,3,4,5,6,7] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11] | ⊥ ShapeError |
| [1,2,3,4,5,6,7,8,9,10,11,12] ⊕ [1,2,3,4,5,6,7,8,9,10,11,12,13] | ⊥ ShapeError |

## Functions

### encode_list

```md
encode_list : List⟨ℕ⟩ → ℕ
```

### encode_group

```md
encode_group : List⟨(𝕂, List⟨ℕ⟩)⟩ → ℕ
```

## Operation: group (Group)

### Signature

```md
group : List⟨ℕ⟩ × (ℕ→𝕂) → List⟨(𝕂, List⟨ℕ⟩)⟩
Fingerprint: 0xD005
```

### Laws

```md
∀ k l . concat(values(group(k, l))) ≡ l
∀ k l . keys(group(k, l)) are distinct
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| [1,2] ⊕ [3] | ⊥ ShapeError |
