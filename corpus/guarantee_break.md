# Module: guarantee_break
# Version: 1.0.0
# Expected: FAIL (E-09 — Malformed Guarantee)
# Style: tensor_ops + guarantee declaration
# Intent: declares `## Guarantee` with an invalid metric and a threshold out of
# range → E-09 must reject the malformed declaration.

## Imports

```md
import core
import ai.confidence
```

## Guarantee

```md
metric: precision
threshold: 1.50
dataset: 
```

## Operation: predict (Direction)

### Signature

```md
predict : Conf × Conf → Conf
Fingerprint: 0xF502
```

### Laws

```md
∀ c . predict(c, 0) ≡ c
```

### Tests

| Input | Output |
|-------|--------|
| 1 ⊕ 0 | 1 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
