# Module: encoding_ok
# Version: 0.1.0
# Expected: PASS
# Style: demographics (`### Name` + fenced signature + in-fence `## Laws`/`## Tests`)
# Domain: data

## Imports

```md
import core
```

## Operations

### encode_surname

```md
encode_surname : Sym → ℕ
Fingerprint: 0xB001

## Laws
∀ s . encode_surname(s) ≥ 100
∀ s₁ s₂ . s₁ ≠ s₂ ⇒ encode_surname(s₁) ≠ encode_surname(s₂)

## Tests
| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| [1] ⊕ [1,2] | ⊥ ShapeError |
```

### nth

```md
nth : List(ℕ) × ℕ → ℕ
Fingerprint: 0xB002

## Laws
∀ l i . i < |l| ⇒ nth(l, i) < ∞
∀ l . nth(l, 0) ≡ head(l)

## Tests
| Input | Output |
|-------|--------|
| index([1,2,3], 1) | 2 |
| index([5], 0) | 5 |
| index([1,2], 9) | ⊥ OutOfBounds |
```
