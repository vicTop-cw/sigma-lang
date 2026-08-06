# Module: sigma_cross_domain_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (cross-domain chain — §SK → §PF → §IN one pipeline)
# Intent: verifier test set for ΣLang cross-domain integration — a 找茬 task
# creates bounty (points_hold), the reward flows to a portfolio (portfolio_new
# / buy / sell), and inventory moves in parallel (inventory_new / ship_stock).
# Each Operation's Tests chain one domain's output into the next, so the
# consensus gate (Law XIII) verifies that the three domains agree on the
# cross-domain semantics. Added at v0.164.

## Imports

```md
import core
```

## Exports

```md
points_hold
points_release
portfolio_new
buy
sell
portfolio_value
risk_score
inventory_new
ship_stock
stock_level
```

## Operation: points_hold (Bounty Escrow — §SK feeds §PF)

### Signature

```md
points_hold : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00C
```

### Laws

```md
index(points_hold(p, x), 0) ≡ index(p, 0) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_hold(points_new(), 100) | [100,0] |
| points_hold(5, 100) | ⊥ TypeError |

## Operation: points_release (Bounty Release — §SK escrow closes)

### Signature

```md
points_release : List⟨ℕ⟩ × ℕ → List⟨ℕ⟩
Fingerprint: 0xF00D
```

### Laws

```md
index(points_release(p, x), 1) ≡ index(p, 1) + x
```

### Tests

| Input | Output |
|-------|--------|
| points_release(points_hold(points_new(), 100), 100) | [0,100] |
| points_release(5, 100) | ⊥ TypeError |

## Operation: portfolio_new (Portfolio Open — reward lands here)

### Signature

```md
portfolio_new : ℕ → List⟨ℕ⟩
Fingerprint: 0xE001
```

### Laws

```md
portfolio_new(c) ≡ [c, 0, 0]
```

### Tests

| Input | Output |
|-------|--------|
| portfolio_new(100) | [100,0,0] |
| portfolio_new(-5) | ⊥ TypeError |

## Operation: buy (Reward Invested — §PF)

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
| buy(portfolio_new(100), 0, 30) | [70,30,0] |
| buy(portfolio_new(10), 0, 30) | ⊥ InsufficientFunds |

## Operation: sell (Reward Liquidated — §PF)

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
| sell(buy(portfolio_new(100), 0, 30), 0, 20) | [90,10,0] |
| sell([70,30,0], 0, 40) | ⊥ InsufficientShares |

## Operation: portfolio_value (Cross-Domain Total — §PF)

### Signature

```md
portfolio_value : List⟨ℕ⟩ → ℕ
Fingerprint: 0xE004
```

### Laws

```md
portfolio_value(p) ≡ index(p, 0) + index(p, 1)
```

### Tests

| Input | Output |
|-------|--------|
| portfolio_value(sell(buy(portfolio_new(100), 0, 30), 0, 20)) | 100 |
| portfolio_value(5) | ⊥ TypeError |

## Operation: risk_score (Exposure — §PF)

### Signature

```md
risk_score : List⟨ℕ⟩ → ℕ
Fingerprint: 0xE005
```

### Laws

```md
risk_score(p) ≡ index(p, 1)
```

### Tests

| Input | Output |
|-------|--------|
| risk_score(sell(buy(portfolio_new(100), 0, 30), 0, 20)) | 10 |
| risk_score(5) | ⊥ TypeError |

## Operation: inventory_new (Parallel Stock — §IN)

### Signature

```md
inventory_new : ℕ × ℕ → List⟨ℕ⟩
Fingerprint: 0xD001
```

### Laws

```md
inventory_new(a, b) ≡ [a, b]
```

### Tests

| Input | Output |
|-------|--------|
| inventory_new(10, 20) | [10,20] |
| inventory_new(-5, 10) | ⊥ TypeError |

## Operation: ship_stock (Parallel Shipment — §IN)

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
| ship_stock(inventory_new(10, 20), 0, 4) | [6,20] |
| ship_stock(inventory_new(10, 20), 0, 11) | ⊥ InsufficientStock |

## Operation: stock_level (Remaining — §IN)

### Signature

```md
stock_level : List⟨ℕ⟩ × ℕ → ℕ
Fingerprint: 0xD004
```

### Laws

```md
stock_level(inv, 0) ≡ index(inv, 0)
```

### Tests

| Input | Output |
|-------|--------|
| stock_level(ship_stock(inventory_new(10, 20), 0, 4), 0) | 6 |
| stock_level(5, 0) | ⊥ TypeError |

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
