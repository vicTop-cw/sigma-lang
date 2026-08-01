# Module: proof_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops + proof-carrying spec (spec_top_proofs.md P.3)
# Intent: declares `## Proof` with Model + Invariant, and the operation has
# paired Pre/Post contracts → P-01 satisfied.

## Imports

```md
import core
```

## Proof

### Model

```md
model(ledger) : Fmap[CoinId, ℤ]
```

### Invariant

```md
ledger_inv(l) : 𝔹
∀ c . c ∈ keys(l) ⇒ balance(c) > 0
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF301
```

# Pre: a ≥ 0
# Post: result ≥ a

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
∀ a b c . (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
