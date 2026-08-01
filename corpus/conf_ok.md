# Module: conf_ok
# Version: 0.1.0
# Expected: PASS
# Style: tensor_ops
# Domain: ai (confidence — §C)

## Imports

```md
import core
import ai.confidence
```

## Operation: combine (Confidence Union)

### Signature

```md
combine : Conf × Conf → Conf
Fingerprint: 0xC001
```

### Laws

```md
∀ c . combine(c, 0) ≡ c
∀ c . combine(c, 1) ≡ 1
∀ c₁ c₂ . combine(c₁, c₂) ≡ combine(c₂, c₁)
```

### Tests

| Input | Output |
|-------|--------|
| 1 ⊕ 0 | 1 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
