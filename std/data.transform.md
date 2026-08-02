# Package: data.transform
# Version: 1.0.0
# Fingerprint Prefix: 0xD000-0xD0FF
# Depends: core@1.0, math.base@1.0
# Maintainer: sigma-wg
# License: MIT
# Domain: data
# Intent: v0.11 standard-library package — data transformation combinators
# (map ∥ filter ∥ reduce with lazy/eager semantics, sort ∥ group with
# ordering laws). Installable via:
# python3 tools/sigma-cli.py install std/data.transform.md

## Imports

```md
import core
import math.base
```

## Exports

```md
map
filter
reduce
sort
group
```

## Symbols

### map : Map

Type: List⟨ℕ⟩ × (ℕ→ℕ) → List⟨ℕ⟩
Fingerprint: 0xD001
Definition: map(f, l) ≡ [f(x) | x ∈ l]  (eager evaluation)

Laws:
- map(id, l) ≡ l
- map(f ∘ g, l) ≡ map(f, map(g, l))

Tests:
| Input | Output |
|-------|--------|
| [1,2] ⊕ [3,4] | [4,6] |
| [1,2,3] ⊕ [4,5,6] | [5,7,9] |
| [1] ⊕ [1,2] | ⊥ ShapeError |

### filter : Filter

Type: List⟨ℕ⟩ × (ℕ→𝔹) → List⟨ℕ⟩
Fingerprint: 0xD002
Definition: filter(p, l) ≡ [x | x ∈ l, p(x)]  (eager evaluation)

Laws:
- filter(p, []) ≡ []
- filter(p, l) ⊎ filter(¬p, l) ≡ l  (partition)

Tests:
| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| index([5], 0) | 5 |
| index([1,2], 9) | ⊥ OutOfBounds |

### reduce : Reduce

Type: List⟨ℕ⟩ × (ℕ×ℕ→ℕ) → ℕ
Fingerprint: 0xD003
Definition: reduce(f, l) ≡ fold-left of f over l

Laws:
- reduce(f, [x]) ≡ x
- reduce(⊕, l) is associative/commutative when ⊕ is

Tests:
| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

### sort : Sort

Type: List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xD004
Definition: sort(l) ≡ l ordered by ≤ (stable)

Laws:
- sorted(sort(l)) ≡ true
- permutation(sort(l), l) ≡ true

Tests:
| Input | Output |
|-------|--------|
| 2 ≤ 3 | 1 |
| 3 ≤ 2 | 0 |
| 2 ≤ [1] | ⊥ TypeError |

### group : Group

Type: List⟨ℕ⟩ × (ℕ→𝕂) → List⟨(𝕂, List⟨ℕ⟩)⟩
Fingerprint: 0xD005
Definition: group(k, l) ≡ list of (k(x), [x …]) runs

Laws:
- concat(values(group(k, l))) ≡ l
- keys(group(k, l)) are distinct

Tests:
| Input | Output |
|-------|--------|
| 2 ≡ 2 | 1 |
| 2 ≡ 3 | 0 |
| 2 ≡ [1] | ⊥ TypeError |
