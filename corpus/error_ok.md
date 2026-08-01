# Module: error_ok
# Version: 0.1.0
# Expected: PASS
# Style: tensor_ops
# Domain: error (§E — Error Algebra)

## Imports

```md
import core
import error.base
```

## Operation: err_code (Error to Code)

### Signature

```md
err_code : Result⟨V,E⟩ → ℕ
Fingerprint: 0xF002
```

### Laws

```md
∀ e . err_code(err(e)) ≥ 1
∀ v . err_code(ok(v)) ≡ 0
∀ e₁ e₂ . e₁ ≠ e₂ ⇒ err_code(err(e₁)) ≠ err_code(err(e₂))
```

### Tests

| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
