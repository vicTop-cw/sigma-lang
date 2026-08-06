# Module: sigma_errors_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (three-domain error boundaries — §SK / §PF / §IN)
# Intent: verifier test set for ΣLang error semantics — every business
# error path across the three domains must reject with ⊥ consistently:
# quota exhaustion, insufficient points/funds/shares/stock, unknown
# asset/item, auth errors, team full, divide-by-zero, and generic
# TypeError. The consensus gate (Law XIII) verifies that Python / Rust /
# Elixir agree on every error boundary. Added at v0.174.

## Imports

```md
import core
```

## Exports

```md
quota_use
points_withdraw
task_accept
badge_issue
team_join
buy
sell
ship_stock
fill_rate
```

## Operation: quota_use (Quota Spending — §SK boundary)

### Signature

```md
quota_use : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF009
```

### Laws

```md
index(quota_use(q, x), 1) ≡ index(q, 1) − x
```

### Tests

| Input | Output |
|-------|--------|
| quota_use([50,50], 1) | [50,49] |
| quota_use([50,1], 2) | ⊥ QuotaExhausted |
| quota_use(5, 1) | ⊥ TypeError |

## Operation: points_withdraw (Points Withdraw — §SK boundary)

### Signature

```md
points_withdraw : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00E
```

### Laws

```md
index(points_withdraw(p, x), 1) ≡ index(p, 1) − x
```

### Tests

| Input | Output |
|-------|--------|
| points_withdraw([0,100], 40) | [0,60] |
| points_withdraw([0,5], 10) | ⊥ InsufficientPoints |
| points_withdraw(5, 10) | ⊥ TypeError |

## Operation: task_accept (Task Accept — §SK auth boundary)

### Signature

```md
task_accept : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF004
```

### Laws

```md
task_accept(t, c) ≡ completed if c ≡ index(t, 0)
```

### Tests

| Input | Output |
|-------|--------|
| task_accept([7,100,2,3], 7) | [7,100,3,3] |
| task_accept([7,100,2,3], 5) | ⊥ AuthError |

## Operation: badge_issue (Badge Issue — §SK verifier boundary)

### Signature

```md
badge_issue : ℕ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF010
```

### Laws

```md
index(badge_issue(v, u, s), 0) ≡ v
```

### Tests

| Input | Output |
|-------|--------|
| badge_issue(1001, 3, 105) | [1001,3,1] |
| badge_issue(999, 3, 105) | ⊥ AuthError |

## Operation: team_join (Team Join — §SK capacity boundary)

### Signature

```md
team_join : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF013
```

### Laws

```md
index(team_join(t, m), 2) ≡ index(t, 2) + 1
```

### Tests

| Input | Output |
|-------|--------|
| team_join([7,0,1,3], 5) | [7,0,2,3] |
| team_join([7,0,3,3], 5) | ⊥ TeamFull |
| team_join(5, 1) | ⊥ TypeError |

## Operation: buy (Buy — §PF boundary)

### Signature

```md
buy : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xE002
```

### Laws

```md
index(buy(p, a, q), 0) ≡ index(p, 0) − q
```

### Tests

| Input | Output |
|-------|--------|
| buy([100,0,0], 0, 30) | [70,30,0] |
| buy([10,0,0], 0, 30) | ⊥ InsufficientFunds |
| buy([100,0,0], 2, 30) | ⊥ UnknownAsset |
| buy(5, 0, 30) | ⊥ TypeError |

## Operation: sell (Sell — §PF boundary)

### Signature

```md
sell : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xE003
```

### Laws

```md
index(sell(p, a, q), 1) ≡ index(p, 1) − q
```

### Tests

| Input | Output |
|-------|--------|
| sell([70,30,0], 0, 20) | [90,10,0] |
| sell([70,30,0], 0, 40) | ⊥ InsufficientShares |
| sell([70,30,0], 2, 10) | ⊥ UnknownAsset |

## Operation: ship_stock (Shipment — §IN boundary)

### Signature

```md
ship_stock : List⟨ℕ⟩ × ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD003
```

### Laws

```md
index(ship_stock(inv, 0, q), 0) ≡ index(inv, 0) − q
```

### Tests

| Input | Output |
|-------|--------|
| ship_stock([10,20], 0, 4) | [6,20] |
| ship_stock([10,20], 0, 11) | ⊥ InsufficientStock |
| ship_stock([10,20], 2, 4) | ⊥ UnknownItem |
| ship_stock(5, 0, 4) | ⊥ TypeError |

## Operation: fill_rate (Fill Rate — §IN boundary)

### Signature

```md
fill_rate : ℕ × ℕ → ℝ
Fingerprint: 0xD005
```

### Laws

```md
fill_rate(s, d) ≡ s / d
```

### Tests

| Input | Output |
|-------|--------|
| fill_rate(6, 10) | 0.6 |
| fill_rate(6, 0) | ⊥ DivByZero |

### encode_quota

```md
encode_quota : List⟨ℕ⟩ → ℕ
```

### encode_points

```md
encode_points : List⟨ℕ⟩ → ℕ
```

### encode_portfolio

```md
encode_portfolio : List⟨ℕ⟩ → ℕ
```

### encode_inventory

```md
encode_inventory : List⟨ℕ⟩ → ℕ
```
