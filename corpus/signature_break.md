# Module: signature_break
# Version: 1.0.0
# Expected: FAIL (E-08 S-01 — Malformed Signature)
# Style: tensor_ops + package signature
# Intent: declares `## Signature` with a missing signer, a pubkey_fp without
# the sha256: prefix, a non-ed25519 algorithm, and an empty signature →
# Level 1 check must reject.

## Imports

```md
import core
```

## Signature

```md
pubkey_fp: abc123
algorithm: rsa-sha256
signature: 
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF802
```

### Laws

```md
∀ a b . a ⊕ b ≡ b ⊕ a
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
