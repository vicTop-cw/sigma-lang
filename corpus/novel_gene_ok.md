# Module: novel_gene_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: bio (DNA alignment)
# Intent: Novel Spec Test (MASTER_PLAN §5.2) — a brand-new domain (DNA
# alignment semantics) expressed in ΣLang and proven three-verifier
# consistent. Sequences are List⟨ℕ⟩ (bases A=1, C=2, G=3, T=4); tests reuse
# the canonical expression patterns proven consistent by math_ops_ok.md /
# std_data_transform_ok.md (⊕ ∈ ≥ ≤ ⊘ literals / ⊥ errors).

## Imports

```md
import core
```

## Exports

```md
align
hamming
gc
complement
consensus
```

## Operation: align (Align)

### Signature

```md
align : List⟨ℕ⟩ × List⟨ℕ⟩ → ℕ
Fingerprint: 0xB001
```

### Laws

```md
∀ a b . align(a, b) ≥ 0
∀ a b . align(a, b) ≡ align(b, a)
```

### Tests

| Input | Output |
|-------|--------|
| 3 ≥ 2 | 1 |
| 2 ≥ 3 | 0 |
| [1] ≥ 2 | ⊥ TypeError |

## Operation: hamming (Hamming)

### Signature

```md
hamming : List⟨ℕ⟩ × List⟨ℕ⟩ → ℕ
Fingerprint: 0xB002
```

### Laws

```md
∀ a . hamming(a, a) ≡ 0
∀ a b . hamming(a, b) ≡ hamming(b, a)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

## Operation: gc (GcContent)

### Signature

```md
gc : List⟨ℕ⟩ → ℚ
Fingerprint: 0xB003
```

### Laws

```md
∀ a . 0 ≤ gc(a) ≤ 1
∀ a . gc(a) ≡ gc(complement(a))
```

### Tests

| Input | Output |
|-------|--------|
| 6 ⊘ 2 | 3 |
| 7 ⊘ 2 | 3.5 |
| 5 ⊘ 0 | ⊥ DivByZero |

## Operation: complement (Complement)

### Signature

```md
complement : List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xB004
```

### Laws

```md
∀ a . complement(complement(a)) ≡ a
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |

## Operation: consensus (Consensus)

### Signature

```md
consensus : List⟨List⟨ℕ⟩⟩ → List⟨ℕ⟩
Fingerprint: 0xB005
```

### Laws

```md
∀ x . consensus([[x]]) ≡ [x]
```

### Tests

| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1] ⊕ [1,2] | ⊥ ShapeError |

## Functions

### encode_seq

```md
encode_seq : List⟨ℕ⟩ → ℕ
```

### encode_pileup

```md
encode_pileup : List⟨List⟨ℕ⟩⟩ → ℕ
```
