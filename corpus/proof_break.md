# Module: proof_break
# Version: 1.0.0
# Expected: FAIL (P-01 — Missing Model / Incomplete Contract)
# Style: tensor_ops + proof-carrying spec
# Intent: declares `## Proof` but has NO `### Model` block, and the operation
# declares `# Pre:` without a matching `# Post:` → P-01 must reject.

## Imports

```md
import core
```

## Proof

### Invariant

```md
ledger_inv(l) : 𝔹
∀ c . c ∈ keys(l) ⇒ balance(c) > 0
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF302
```

# Pre: a ≥ 0

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
