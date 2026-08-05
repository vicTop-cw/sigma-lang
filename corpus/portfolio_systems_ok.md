# Module: portfolio_systems_ok
# Version: 1.0.0
# Expected: PASS
# Style: tensor_ops (`## Operation:` + `### Signature/Laws/Tests`)
# Domain: app behavior (Portfolio finance domain — cross-operation chain)
# Intent: verifier test set for the §PF finance domain working as one
# portfolio — open (portfolio_new) → buy → sell chains with valuation and
# risk linked across operations (buy→sell→value/risk). The Tests exercise
# real function calls chaining one operation's output into the next, so the
# consensus gate (Law XIII) verifies cross-operation integration semantics.
# Added at v0.144.

## Imports

```md
import core
```

## Exports

```md
portfolio_new
buy
sell
portfolio_value
risk_score
```

## Operation: portfolio_new (Portfolio Creation)

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
| portfolio_new(0) | [0,0,0] |
| portfolio_new(-5) | ⊥ TypeError |

## Operation: buy (Buy Asset)

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
| buy(portfolio_new(100), 1, 25) | [75,0,25] |
| buy(buy(portfolio_new(100), 0, 20), 0, 10) | [70,30,0] |
| buy(portfolio_new(10), 0, 30) | ⊥ InsufficientFunds |

## Operation: sell (Sell Asset)

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
| sell(sell(buy(portfolio_new(100), 0, 30), 0, 10), 0, 10) | [90,10,0] |
| sell([70,30,0], 0, 30) | [100,0,0] |
| sell([70,30,0], 0, 40) | ⊥ InsufficientShares |

## Operation: portfolio_value (Total Valuation)

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
| portfolio_value(portfolio_new(100)) | 100 |
| portfolio_value(buy(portfolio_new(100), 0, 30)) | 100 |
| portfolio_value(sell(buy(portfolio_new(100), 0, 30), 0, 20)) | 100 |
| portfolio_value(5) | ⊥ TypeError |

## Operation: risk_score (Position Exposure)

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
| risk_score(portfolio_new(100)) | 0 |
| risk_score(buy(portfolio_new(100), 0, 30)) | 30 |
| risk_score(sell(buy(portfolio_new(100), 0, 30), 0, 20)) | 10 |
| risk_score(5) | ⊥ TypeError |

### encode_portfolio

```md
encode_portfolio : List⟨ℕ⟩ → ℕ
```
