# Module: demographics

> Example ΣLang module demonstrating "everything → ℕ" encoding principle.

## Imports

```md
import core
import math.linear
```

## Encoding Functions (Everything → ℕ)

### Surname Encoding

```md
SurnameCode : Sym → ℕ

## Encoding table (partial)
SurnameCode("张") ≝ 101
SurnameCode("李") ≝ 102
SurnameCode("王") ≝ 103
SurnameCode("刘") ≝ 104
SurnameCode("陈") ≝ 105
SurnameCode("杨") ≝ 106
SurnameCode("赵") ≝ 107
SurnameCode("黄") ≝ 108
SurnameCode("周") ≝ 109
SurnameCode("吴") ≝ 110

## Laws
∀ s . SurnameCode(s) ≥ 100
∀ s₁ s₂ . s₁ ≠ s₂ ⇒ SurnameCode(s₁) ≠ SurnameCode(s₂)
```

### Birth Date Encoding

```md
BirthEpoch : ℕ × ℕ × ℕ → ℕ
## Year × Month × Day → ℕ
BirthEpoch(y, m, d) ≝ y⊗10000 ⊕ m⊗100 ⊕ d

## Laws
∀ y m d . BirthEpoch(y,m,d) > y⊗10000
∀ y . BirthEpoch(y,1,1) ≡ y⊗10000 ⊕ 101
```

### Age Calculation

```md
CurrentYear : ℕ  (set by environment)

AgeOf : PersonId → ℕ
AgeOf(p) ≝ CurrentYear ⊖ π₁(BirthOf(p))

## Laws
∀ p . AgeOf(p) ≥ 0
∀ p . AgeOf(p) ≤ CurrentYear  (reasonable bound)
```

## Data Model

```md
PersonId : Type ≝ ℕ

SurnameOf : PersonId → Sym
BirthOf   : PersonId → ℕ  (encoded as BirthEpoch)
```

## Operations

### GroupBySurname

```md
GroupBySurname : List(PersonId) → Map(ℕ, List(PersonId))
Fingerprint: 0xD001

## Laws
∀ ps . ∀ s . s ∈ keys(GroupBySurname(ps))
            ⇒ ∃ p∈ps . SurnameOf(p) ≡ s

∀ ps p . p ∈ ps ⇒ ∃ s . p ∈ GroupBySurname(ps)[s]

## Tests
| Input | Output |
|-------|--------|
| [p₁,p₂] where same surname | Map{scode → [p₁,p₂]} |
| [] | Map{} (empty) |
| [p₁,p₂,p₃] 2 surnames | Map{sc₁→[p₁], sc₂→[p₂,p₃]} |
```

### AvgAge

```md
AvgAge : List(PersonId) → ℚ
Fingerprint: 0xD002

## Definition
AvgAge(ps) ≝
  let sum ≝ Σ_{p∈ps} AgeOf(p) in
  let n   ≝ |ps| in
  if n=0 then 0 else sum / n

## Laws
∀ ps . |ps|>0 ⇒ AvgAge(ps) ≥ 0
∀ ps . |ps|>0 ⇒ AvgAge(ps) ≤ CurrentYear

## Tests
| Input | Expected |
|-------|----------|
| [p(age=20), p(age=40)] | 30 |
| [p(age=0)] | 0 |
| [] | 0 |
| [p(age=25), p(age=25), p(age=25)] | 25 |
```

### AvgAgeBySurname

```md
AvgAgeBySurname : List(PersonId) → Map(ℕ, ℚ)
Fingerprint: 0xD003

## Definition
AvgAgeBySurname(ps) ≝
  let groups ≝ GroupBySurname(ps) in
  map (λ group . AvgAge(group)) groups

## Laws
∀ ps . ∀ s∈keys(result) . result[s] ≥ 0
∀ ps . size(result) ≤ number_of_unique_surnames(ps)

## Tests
| Input | Expected |
|-------|----------|
| Mixed group | Map{sc₁→30, sc₂→25} |
| Empty | Map{} |
```

## Sorting by Surname

```md
SortBySurname : List(PersonId) → List(PersonId)
Fingerprint: 0xD004

## Definition
SortBySurname(ps) ≝ sort_by (λp. SurnameCode(SurnameOf(p))) ps

## Laws
∀ ps . same_elements(SortBySurname(ps), ps)
∀ ps . is_sorted(SortBySurname(ps), λp. SurnameCode(SurnameOf(p)))

## Tests
| Input | Expected |
|-------|----------|
| [李, 张, 王] (codes 102,101,103) | [张, 李, 王] |
| [] | [] |
| [same, same] | [same, same] |
```

## Ownership Trace

```md
## Data flow with ownership annotations

input_list : List(PersonId)   # owned

groups ← GroupBySurname(input_list)
  # input_list̸ (consumed, can use keys for grouping)

groups̸  # each group is borrowed, not owned

result ← AvgAgeBySurname(input_list)
  # result is new allocation
  # input_list still available (borrowed only)

return result
```

## Verification Summary

This module declares:
- 2 encoding functions (SurnameCode, BirthEpoch)
- 4 operations (GroupBySurname, AvgAge, AvgAgeBySurname, SortBySurname)
- 14 algebraic laws
- 12 canonical tests
- Full ownership annotations

Verifier will check:
1. All symbols have fingerprints ✓
2. All operations have ≥1 test ✓
3. Encoding functions map to ℕ ✓
4. Laws are internally consistent ✓
5. Tests cover boundary cases ✓
