# Package: math.base
# Version: 1.0.0
# Fingerprint Prefix: 0xA000-0xA0FF
# Depends: core@1.0
# Maintainer: sigma-wg
# License: MIT
# Domain: math
# Intent: v0.11 standard-library package — core arithmetic operators
# (⊕ ⊖ ⊗ ⊘ ⊙ ≡ ≥ ≤ ∈) with associativity/commutativity laws, plus the
# transcendental family √ pow log with declared precision bounds.
# Installable via: python3 tools/sigma-cli.py install std/math.base.md

## Imports

```md
import core
```

## Exports

```md
⊕
⊖
⊗
⊘
⊙
≡
≥
≤
∈
√
pow
log
```

## Symbols

### ⊕ : Add

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA001
Definition: a ⊕ b ≡ b + a

Laws:
- Commutative: a ⊕ b ≡ b ⊕ a
- Associative: (a ⊕ b) ⊕ c ≡ a ⊕ (b ⊕ c)
- Identity: a ⊕ 0 ≡ a

Tests:
| Input | Output |
|-------|--------|
| 2 ⊕ 3 | 5 |
| 0 ⊕ 0 | 0 |
| [1] ⊕ [1,2] | ⊥ ShapeError |

### ⊖ : Sub

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA010
Definition: a ⊖ b ≡ a + (⊖ b)

Laws:
- (a ⊖ b) ⊖ c ≡ a ⊖ (b ⊕ c)

Tests:
| Input | Output |
|-------|--------|
| 5 ⊖ 3 | 2 |
| 10 ⊖ 4 | 6 |
| [1] ⊖ [1,2] | ⊥ ShapeError |

### ⊗ : MatMul

Type: List⟨List⟨ℕ⟩⟩ × List⟨ℕ⟩ → List⟨ℕ⟩
Fingerprint: 0xA021
Definition: A ⊗ B ≡ matrix × vector product

Laws:
- ∃ I₂ . ∀ A . A ⊗ I₂ ≡ A
- Distributive: A ⊗ (B ⊕ C) ≡ (A ⊗ B) ⊕ (A ⊗ C)

Tests:
| Input | Output |
|-------|--------|
| I₂ ⊗ [1,2] | [1,2] |
| [[1,2],[3,4]] ⊗ [1,0] | [1,3] |
| [[1,2],[3,4]] ⊗ [1] | ⊥ ShapeError |

### ⊘ : Div

Type: ℕ × ℕ → ℚ
Fingerprint: 0xA011
Definition: a ⊘ b ≡ a / b (b ≠ 0)

Laws:
- (a ⊘ b) ⊘ c ≡ a ⊘ (b ⊗ c)
- a ⊘ 1 ≡ a

Tests:
| Input | Output |
|-------|--------|
| 6 ⊘ 2 | 3 |
| 7 ⊘ 2 | 3.5 |
| 5 ⊘ 0 | ⊥ DivByZero |

### ⊙ : Hadamard

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA012
Definition: a ⊙ b ≡ a · b

Laws:
- Commutative: a ⊙ b ≡ b ⊙ a
- Associative: (a ⊙ b) ⊙ c ≡ a ⊙ (b ⊙ c)

Tests:
| Input | Output |
|-------|--------|
| 2 ⊙ 3 | 6 |
| 4 ⊙ 0 | 0 |
| [1] ⊙ [1,2] | ⊥ ShapeError |

### ≡ : Eq

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA013
Definition: a ≡ b ≡ 1 if a = b, else 0

Laws:
- Reflexive: a ≡ a
- Symmetric: a ≡ b ⇒ b ≡ a

Tests:
| Input | Output |
|-------|--------|
| 2 ≡ 2 | 1 |
| 2 ≡ 3 | 0 |
| 2 ≡ [1] | ⊥ TypeError |

### ≥ : Ge

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA014
Definition: a ≥ b ≡ 1 if a ≥ b, else 0

Laws:
- Reflexive: a ≥ a
- Transitive: a ≥ b ∧ b ≥ c ⇒ a ≥ c

Tests:
| Input | Output |
|-------|--------|
| 3 ≥ 2 | 1 |
| 2 ≥ 3 | 0 |
| [1] ≥ 2 | ⊥ TypeError |

### ≤ : Le

Type: ℕ × ℕ → ℕ
Fingerprint: 0xA015
Definition: a ≤ b ≡ 1 if a ≤ b, else 0

Laws:
- Reflexive: a ≤ a
- Total: a ≤ b ∨ b ≤ a

Tests:
| Input | Output |
|-------|--------|
| 2 ≤ 3 | 1 |
| 3 ≤ 2 | 0 |
| 2 ≤ [1] | ⊥ TypeError |

### ∈ : In

Type: ℕ × List⟨ℕ⟩ → ℕ
Fingerprint: 0xA016
Definition: x ∈ l ≡ 1 if x in l, else 0

Laws:
- x ∈ [x]
- x ∈ [x] ⇒ x ∈ [x, y]

Tests:
| Input | Output |
|-------|--------|
| 2 ∈ [1,2,3] | 1 |
| 5 ∈ [1,2,3] | 0 |
| 2 ∈ 3 | ⊥ TypeError |

### √ : Sqrt

Type: ℚ → ℚ
Fingerprint: 0xA040
Definition: √x ≡ principal square root of x
Precision: IEEE-754 double, relative error ≤ 2⁻⁵² (transcendental family)

Laws:
- √(x ⊙ x) ≡ x for x ≥ 0
- √0 ≡ 0

Tests:
| Input | Output |
|-------|--------|
| √4 | 2.0 |
| √0 | 0.0 |
| √(−1) | ⊥ DomainError |

### pow : Power

Type: ℚ × ℚ → ℚ
Fingerprint: 0xA041
Definition: pow(x, y) ≡ x^y
Precision: IEEE-754 double, relative error ≤ 2⁻⁵² (transcendental family)

Laws:
- pow(x, 0) ≡ 1
- pow(x, 1) ≡ x

Tests:
| Input | Output |
|-------|--------|
| pow(2, 3) | 8.0 |
| pow(2, 0) | 1.0 |
| pow(0, −1) | ⊥ DomainError |

### log : Logarithm

Type: ℚ → ℚ
Fingerprint: 0xA042
Definition: log(x) ≡ natural logarithm of x
Precision: IEEE-754 double, relative error ≤ 2⁻⁵² (transcendental family)

Laws:
- log(1) ≡ 0
- log(e) ≡ 1

Tests:
| Input | Output |
|-------|--------|
| log(1) | 0.0 |
| log(e) | 1.0 |
| log(0) | ⊥ DomainError |
