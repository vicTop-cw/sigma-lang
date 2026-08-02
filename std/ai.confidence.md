# Package: ai.confidence
# Version: 1.0.0
# Fingerprint Prefix: 0xC000-0xC0FF
# Depends: core@1.0, math.base@1.0
# Maintainer: sigma-wg
# License: MIT
# Domain: ai
# Intent: v0.11 standard-library package — confidence calibration and
# opinion combination (§C). Installable via:
# python3 tools/sigma-cli.py install std/ai.confidence.md

## Imports

```md
import core
import math.base
```

## Exports

```md
calibrate
combine
```

## Symbols

### calibrate : Calibrate

Type: Conf × Conf → Conf
Fingerprint: 0xC001
Definition: calibrate(c, actual) ≡ c' with accuracy(c') ≈ confidence(c')
(Law IX — calibration requirement)

Laws:
- calibrate(c, actual) ∈ [0, 1]
- accuracy(calibrate(c, actual)) ≡ confidence(calibrate(c, actual))

Tests:
| Input | Output |
|-------|--------|
| 1 ⊕ 0 | 1 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |

### combine : Confidence Union

Type: Conf × Conf → Conf
Fingerprint: 0xC010
Definition: combine(c₁, c₂) ≡ consensus of two opinions

Laws:
- combine(c, 0) ≡ c
- combine(c, 1) ≡ 1
- commutative: combine(c₁, c₂) ≡ combine(c₂, c₁)

Tests:
| Input | Output |
|-------|--------|
| 1 ⊕ 0 | 1 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
