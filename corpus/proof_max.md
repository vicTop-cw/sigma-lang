# Module: proof_max
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops + proof-carrying spec (spec_top_proofs.md P.3)
# Intent: like proof_ok, but the laws reference max()/min() — exercising the
# sigma-prove function-call translation (max/min → ite encoding) inside the
# CI corpus. P-01 structure + obligation discharge must still pass.

## Imports

```md
import core
```

## Proof

### Model

```md
model(pairs) : Fmap[ℕ, ℕ]
```

### Invariant

```md
pairs_inv(m) : 𝔹
∀ k v . (k, v) ∈ entries(m) ⇒ v ≥ 0
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF401
```

# Pre: a ≥ 0
# Post: result ≥ a

### Laws

```md
∀ a b . max(a, b) ≡ max(b, a)
∀ a b c . max(a, b) ⊕ c ≡ max(a ⊕ c, b ⊕ c)
∀ a b . min(a, b) ≤ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
