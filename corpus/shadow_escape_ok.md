# Module: shadow_escape_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops + shadowing (escape hatch)
# Intent: the qualified name `core.base.⊕` is always resolvable to the original
# symbol even inside a shadowing package (§S R2 escape hatch / canonical test
# S-10). A qualified-name shadow target (`core.base.⊕`) is an external-package
# reference, not a local math-domain redefinition — verification passes.

## Imports

```md
import core
```

## Shadowing

```md
shadow core.base.⊕ → local_add
```

## Operation: local_add

### Signature

```md
local_add : ℕ × ℕ → ℕ
Fingerprint: 0xFF03
```

### Laws

```md
∀ a b . local_add(a, b) ≡ local_add(b, a)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
