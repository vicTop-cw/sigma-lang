# Module: proof_ops
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops + proof-carrying spec (spec_top_proofs.md P.3)
# Intent: exercises the v0.10 basic-operation set — index()/I₂ — inside a
# proof-carrying module: laws reference index() and I₂ so sigma-prove must
# translate them (uninterpreted index function / I₂ constant) and still
# discharge the ⊕ obligation. P-01 structure + consensus must hold.

## Imports

```md
import core
```

## Proof

### Model

```md
model(vec) : Fmap[ℕ, ℕ]
```

### Invariant

```md
vec_inv(v) : 𝔹
∀ i . index(v, i) ≥ 0
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF901
```

# Pre: a ≥ 0
# Post: result ≥ a

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
∀ a b c . (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)
∀ v i . index(v, i) ≥ 0
∀ v . I₂ ⊗ v ≡ v
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| index([1,2,3], 1) | 2 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
| index([1,2], 9) | ⊥ OutOfBounds |
