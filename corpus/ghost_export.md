# Module: ghost_export
# Version: 0.1.0
# Expected: FAIL (E-04 — Ghost Export)
# Style: tensor_ops
# Intent: `## Exports` declares a symbol (`ghost_op`) that is never defined;
# E-04 must report GhostExport.

## Imports

```md
import core
```

## Exports

```md
⊕, ghost_op
```

## Operation: ⊕ (Add)

### Signature

```md
⊕ : ℕ × ℕ → ℕ
Fingerprint: 0xF004
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
