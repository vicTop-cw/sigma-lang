# Module: shadow_free_ok
# Version: 1.0.0
# Expected: PASS (with R7-warning in report)
# Style: tensor_ops + shadowing
# Intent: declares a Free-class shadow of a locally defined symbol (`combine`)
# → verification PASSES but the report flags an R7-warning (declared free-class
# shadow, spec_top_rules.md §S R7 / canonical test S-11).

## Imports

```md
import core
```

## Shadowing

```md
shadow combine
```

## Operation: combine

### Signature

```md
combine : ℕ × ℕ → ℕ
Fingerprint: 0xFF02
```

### Laws

```md
∀ a b . combine(a, b) ≡ combine(b, a)
```

### Tests

| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
