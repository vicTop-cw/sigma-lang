# Module: socketkit_points_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (SocketKit 「来找茬」— points & badge systems)
# Intent: verifier test set for the §SK.3.10–3.11 points and badge systems
# (spec_p0_socketkit.md) — points_new / points_hold / points_release /
# points_withdraw / badge_level. The Tests exercise the §SK operations as real
# function calls, so the consensus gate (Law XIII) verifies the app behavior
# itself. Split from socketkit_ok at v0.57 (corpus expansion).

## Imports

```md
import core
```

## Exports

```md
points_new
points_hold
points_release
points_withdraw
badge_level
```

## Operation: points_new (Points Creation)

### Signature

```md
points_new : → List⟨ℕ⟩
Fingerprint: 0xF00B
```

### Laws

```md
points_new() ≡ [0, 0]
```

### Tests

| Input | Output |
|-------|--------|
| points_new() | [0,0] |
| points_new(5) | ⊥ TypeError |

## Operation: points_hold (Points Hold)

### Signature

```md
points_hold : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00C
```

### Laws

```md
∀ p x . index(points_hold(p, x), 0) ≡ index(p, 0) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_hold(points_new(), 100) | [100,0] |
| points_hold(points_new(), 0) | [0,0] |
| points_hold(5, 100) | ⊥ TypeError |

## Operation: points_release (Points Release)

### Signature

```md
points_release : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00D
```

### Laws

```md
∀ p x . index(p, 0) ≥ x ⇒ index(points_release(p, x), 1) ≡ index(p, 1) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_release(points_hold(points_new(), 100), 100) | [0,100] |
| points_release(points_hold(points_new(), 50), 50) | [0,50] |
| points_release(points_new(), 10) | ⊥ InsufficientEscrow |

## Operation: points_withdraw (Points Withdraw)

### Signature

```md
points_withdraw : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00E
```

### Laws

```md
∀ p x . index(p, 1) ≥ x ⇒ index(points_withdraw(p, x), 1) ≡ index(p, 1) − x
```

### Tests

| Input | Output |
|-------|--------|
| points_withdraw(points_release(points_hold(points_new(), 100), 100), 40) | [0,60] |
| points_withdraw([0,100], 100) | [0,0] |
| points_withdraw(points_new(), 10) | ⊥ InsufficientPoints |

## Operation: badge_level (Badge Level)

### Signature

```md
badge_level : ℕ → ℕ
Fingerprint: 0xF00F
```

### Laws

```md
∀ s . 0 ≤ badge_level(s) ≤ 3
∀ s . badge_level(s) ≤ badge_level(s + 100)
```

### Tests

| Input | Output |
|-------|--------|
| badge_level(0) | 0 |
| badge_level(150) | 1 |
| badge_level(450) | 2 |
| badge_level(900) | 3 |
| badge_level([5]) | ⊥ TypeError |

## Functions

### encode_points

```md
encode_points : List⟨ℕ⟩ → ℕ
```
